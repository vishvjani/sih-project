"""
SignalScope Production-Grade Forensic Dataset Curator & Anti-Leakage Engine
Engineered for scale (up to 75,000 Real + 75,000 AI = 150,000 total images) with:
  1. Zero API Crash Architecture:
     - Primary Streaming Mode via Hugging Face `datasets` (no 4,100 row ceiling!).
     - Adaptive Rate-Limiting & Paced Requests (prevents HTTP 429 / socket exhaustion).
     - Exponential backoff retry with jitter on network/server hiccups.
     - Graceful skipping of single dead/broken links (never crashes the whole pipeline).
  2. Resumable Checkpointing:
     - Automatically scans existing `dataset_manifest.csv` and `images/`.
     - Resumes seamlessly if Colab restarts or disconnects.
  3. Strict Forensic Anti-Leakage Partitioning:
     - Exact duplicate check (MD5).
     - Near-duplicate check (64-bit pHash, Hamming distance <= 4).
     - Strict Seen vs Held-Out Unseen Generator isolation (FLUX.1, SD3, Kolors, Lumina, PixArt-Sigma strictly reserved for test!).
     - Metadata & Format normalization (all saved as standard RGB JPEGs with monotonic IDs).
  4. Memory-Safe Execution:
     - Immediate disk flushing and periodic garbage collection to prevent Colab RAM OOM.
"""

import os
import io
import gc
import sys
import csv
import json
import time
import random
import socket
import hashlib
import argparse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
from PIL import Image

try:
    from .generator_split import (
        ALL_DRAGON_MODELS,
        SEEN_GENERATORS,
        UNSEEN_GENERATORS,
        is_seen_generator,
        is_unseen_generator,
        get_generator_family_id,
        MODEL_TO_FAMILY
    )
except ImportError:
    from generator_split import (
        ALL_DRAGON_MODELS,
        SEEN_GENERATORS,
        UNSEEN_GENERATORS,
        is_seen_generator,
        is_unseen_generator,
        get_generator_family_id,
        MODEL_TO_FAMILY
    )

# Try importing datasets for high-volume streaming
try:
    import datasets
    from datasets import load_dataset
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False


def compute_phash(image: Image.Image, hash_size: int = 8) -> str:
    """
    Computes a 64-bit perceptual hash (dHash) for near-duplicate detection.
    Lightweight, fast, and requires no external heavy libraries.
    """
    resized = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.BILINEAR)
    pixels = np.array(resized, dtype=np.float32)
    diff = pixels[:, 1:] > pixels[:, :-1]
    decimal_val = 0
    hex_str = []
    for index, value in enumerate(diff.flatten()):
        if value:
            decimal_val += 2 ** (index % 8)
        if (index % 8) == 7:
            hex_str.append(hex(decimal_val)[2:].rjust(2, "0"))
            decimal_val = 0
    return "".join(hex_str)


def hamming_distance(hex_hash1: str, hex_hash2: str) -> int:
    """Computes bitwise Hamming distance between two hex hashes."""
    if len(hex_hash1) != len(hex_hash2):
        return 64
    x = int(hex_hash1, 16) ^ int(hex_hash2, 16)
    return bin(x).count("1")


class ForensicDatasetCurator:
    def __init__(
        self,
        output_dir: str = "data/curated_dataset",
        hf_token: Optional[str] = None,
        max_workers: int = 5,
        request_delay: float = 0.05,
        phash_threshold: int = 4
    ):
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.output_dir / "dataset_manifest.csv"
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.max_workers = max(1, min(12, max_workers))
        self.request_delay = max(0.0, request_delay)
        self.phash_threshold = phash_threshold

        self.exact_hashes: Set[str] = set()
        self.recent_phashes: List[str] = []
        self.manifest_rows: List[Dict] = []
        self.current_id = 1

        # Load existing state if resuming
        self._load_existing_checkpoint()

    def _load_existing_checkpoint(self):
        """Scans existing manifest to enable seamless resumption without re-downloading."""
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        img_id = int(row["image_id"])
                        self.current_id = max(self.current_id, img_id + 1)
                        if "sha256" in row and row["sha256"]:
                            self.exact_hashes.add(row["sha256"])
                        if "phash" in row and row["phash"]:
                            self.recent_phashes.append(row["phash"])
                        self.manifest_rows.append(row)
                print(f"[Checkpoint] Resuming from existing manifest: {len(self.manifest_rows)} images already indexed!", flush=True)
            except Exception as e:
                print(f"[Checkpoint Notice] Could not parse existing manifest ({e}). Starting fresh.", flush=True)

    def _get_api_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": "SignalScope-Academic-Curator/2.0 (Forensic Media Authenticity)",
            "Accept": "application/json"
        }
        if self.hf_token and self.hf_token.strip():
            headers["Authorization"] = f"Bearer {self.hf_token.strip()}"
        return headers

    def _get_image_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Connection": "keep-alive"
        }

    def is_duplicate(self, img_bytes: bytes, pil_img: Image.Image) -> bool:
        """Checks exact SHA-256 and perceptual pHash to prevent duplicate leakage."""
        sha256_val = hashlib.sha256(img_bytes).hexdigest()
        if sha256_val in self.exact_hashes:
            return True
        self.exact_hashes.add(sha256_val)

        p_hash = compute_phash(pil_img)
        # Check against a rolling window of recent phashes for near-duplicate crops/resizes
        for existing in self.recent_phashes[-1200:]:
            if hamming_distance(p_hash, existing) <= self.phash_threshold:
                return True

        self.recent_phashes.append(p_hash)
        if len(self.recent_phashes) > 2500:
            self.recent_phashes.pop(0)

        return False

    def process_and_save_image(
        self,
        raw_bytes: bytes,
        label: int,  # 0: Real, 1: AI
        generator_name: str,
        category_id: int,
        prompt_text: str = "",
        target_size: Tuple[int, int] = (512, 512)
    ) -> Optional[Dict]:
        """
        Normalizes image: strips metadata, verifies RGB, resizes,
        assigns strict Seen/Unseen split, and saves as standard monotonic JPEG.
        """
        try:
            pil_img = Image.open(io.BytesIO(raw_bytes))
            pil_img = pil_img.convert("RGB")
        except Exception:
            return None

        # Duplicate check
        if self.is_duplicate(raw_bytes, pil_img):
            del pil_img
            return None

        # Standardize size (kills resolution shortcuts)
        if pil_img.size != target_size:
            pil_img = pil_img.resize(target_size, Image.Resampling.BILINEAR)

        # Assign split according to strict forensic rules
        if label == 0:  # Real
            bucket = self.current_id % 100
            if bucket < 70:
                split = "train"
            elif bucket < 85:
                split = "val"
            else:
                split = "test_unseen"
        else:  # AI
            if is_unseen_generator(generator_name):
                # Held-out unseen generators strictly reserved for testing!
                split = "test_unseen"
            else:
                bucket = (self.current_id + category_id) % 100
                if bucket < 75:
                    split = "train"
                elif bucket < 90:
                    split = "val"
                else:
                    split = "test_seen"

        # Monotonic filename (eliminates filename shortcuts)
        image_filename = f"{self.current_id:07d}.jpg"
        save_path = self.images_dir / image_filename

        # Save clean JPEG without metadata
        pil_img.save(save_path, format="JPEG", quality=92, optimize=True)

        sha256_val = hashlib.sha256(raw_bytes).hexdigest()
        p_hash = compute_phash(pil_img)
        family_id = get_generator_family_id(generator_name) if label == 1 else 0

        manifest_entry = {
            "image_id": self.current_id,
            "filename": image_filename,
            "label": label,
            "label_name": "AI" if label == 1 else "Real",
            "generator": generator_name,
            "generator_family": MODEL_TO_FAMILY.get(generator_name, "Pristine_Real" if label == 0 else "Novel_Unseen"),
            "generator_family_id": family_id,
            "category_id": category_id,
            "prompt": prompt_text.replace("\n", " ").strip()[:180],
            "split": split,
            "sha256": sha256_val,
            "phash": p_hash
        }

        self.manifest_rows.append(manifest_entry)
        self.current_id += 1

        del pil_img
        return manifest_entry

    def download_url_with_retry(self, url: str, max_retries: int = 4) -> Optional[bytes]:
        """
        Downloads image bytes with exponential backoff and jitter.
        Never crashes on individual 404, 429, 500, or socket timeouts.
        """
        headers = self._get_image_headers()
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return resp.read()
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    backoff = (2 ** attempt) + random.uniform(1.0, 3.0)
                    time.sleep(backoff)
                elif e.code in (500, 502, 503, 504):
                    time.sleep(1.5 * (attempt + 1))
                else:
                    return None
            except Exception:
                time.sleep(1.0 + attempt)
        return None

    def flush_manifest(self):
        """Flushes in-memory manifest rows to disk."""
        fieldnames = [
            "image_id", "filename", "label", "label_name", "generator",
            "generator_family", "generator_family_id", "category_id",
            "prompt", "split", "sha256", "phash"
        ]
        with open(self.manifest_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.manifest_rows)

    def curate_real_images(self, target_real: int, progress_callback=None) -> int:
        """Curates authentic Real images from bitmind/open-images-v7 using streaming."""
        # Count already collected real images
        collected_real = sum(1 for r in self.manifest_rows if int(r.get("label", 1)) == 0)
        if collected_real >= target_real:
            print(f"[Real Images] Target already reached ({collected_real}/{target_real}). Skipping Phase 1.", flush=True)
            return collected_real

        print(f"\n[Phase 1/2] Ingesting Real Images (Current: {collected_real}/{target_real})...", flush=True)

        if HAS_DATASETS:
            try:
                print("  [Mode] Using Hugging Face streaming engine (datasets.load_dataset)...", flush=True)
                ds_real = load_dataset("bitmind/open-images-v7", split="train", streaming=True)
                buffer = []
                batch_size = 20

                for item in ds_real:
                    if collected_real >= target_real:
                        break

                    url = item.get("url")
                    if not url:
                        continue

                    buffer.append((url, item.get("index", 0)))

                    if len(buffer) >= batch_size or collected_real + len(buffer) >= target_real:
                        # Process batch with concurrency and polite delay
                        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                            future_map = {executor.submit(self.download_url_with_retry, u): idx for u, idx in buffer}
                            for future in as_completed(future_map):
                                img_bytes = future.result()
                                if img_bytes:
                                    entry = self.process_and_save_image(
                                        raw_bytes=img_bytes,
                                        label=0,
                                        generator_name="OpenImages_v7",
                                        category_id=future_map[future] % 1000,
                                        prompt_text="Natural Camera Photograph"
                                    )
                                    if entry:
                                        collected_real += 1
                                        if progress_callback:
                                            progress_callback("real", collected_real, target_real)
                                        if collected_real % 25 == 0 or collected_real == target_real:
                                            print(f"  [Real] Collected {collected_real}/{target_real} images...", flush=True)
                                            self.flush_manifest()
                                            gc.collect()
                                if collected_real >= target_real:
                                    break
                        buffer.clear()
                        if self.request_delay > 0:
                            time.sleep(self.request_delay)

                self.flush_manifest()
                return collected_real
            except Exception as e:
                print(f"  [Notice] Streaming encountered error ({e}). Falling back to rows API...", flush=True)

        # Fallback: rows endpoint with backoff
        real_offset = len(self.manifest_rows)
        while collected_real < target_real:
            needed = min(30, target_real - collected_real)
            url = f"https://datasets-server.huggingface.co/rows?dataset=bitmind%2Fopen-images-v7&config=default&split=train&offset={real_offset}&length={needed}"
            try:
                req = urllib.request.Request(url, headers=self._get_api_headers())
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    rows = [r["row"] for r in data.get("rows", [])]
            except Exception as e:
                time.sleep(3.0)
                real_offset += needed
                continue

            if not rows:
                break

            real_offset += len(rows)
            for r in rows:
                if "url" in r:
                    img_bytes = self.download_url_with_retry(r["url"])
                    if img_bytes:
                        entry = self.process_and_save_image(
                            raw_bytes=img_bytes,
                            label=0,
                            generator_name="OpenImages_v7",
                            category_id=r.get("index", 0) % 1000,
                            prompt_text="Natural Camera Photograph"
                        )
                        if entry:
                            collected_real += 1
                            if collected_real % 25 == 0 or collected_real == target_real:
                                print(f"  [Real] Collected {collected_real}/{target_real} images...", flush=True)
                                self.flush_manifest()
                    if collected_real >= target_real:
                        break

            if self.request_delay > 0:
                time.sleep(self.request_delay)

        self.flush_manifest()
        return collected_real

    def curate_ai_images(self, target_ai: int, config: str = "ExtraLarge", progress_callback=None) -> int:
        """Curates diverse AI-generated images from lesc-unifi/dragon across 25 models."""
        collected_ai = sum(1 for r in self.manifest_rows if int(r.get("label", 0)) == 1)
        if collected_ai >= target_ai:
            print(f"[AI Images] Target already reached ({collected_ai}/{target_ai}). Skipping Phase 2.", flush=True)
            return collected_ai

        print(f"\n[Phase 2/2] Ingesting AI Images (Current: {collected_ai}/{target_ai})...", flush=True)

        if HAS_DATASETS:
            # Try config progression: ExtraLarge (2.5M) -> Large (250k) -> Regular (25k) -> Small (2.5k)
            configs_to_try = [config, "Large", "Regular", "Small"]
            for cfg in configs_to_try:
                try:
                    print(f"  [Mode] Streaming lesc-unifi/dragon (config: {cfg})...", flush=True)
                    ds_ai = load_dataset("lesc-unifi/dragon", cfg, split="train", streaming=True)

                    for item in ds_ai:
                        if collected_ai >= target_ai:
                            break

                        # Extract PIL image directly from streaming webdataset!
                        pil_img = item.get("png") or item.get("image")
                        gen_model = item.get("model.txt")
                        if not gen_model and isinstance(item.get("json"), dict):
                            gen_model = item["json"].get("model")
                        gen_model = gen_model or "Unknown_Diffusion"

                        prompt_txt = ""
                        if isinstance(item.get("json"), dict):
                            prompt_txt = item["json"].get("prompt", "")

                        cat_id = item.get("prompt.cls", 0) if item.get("prompt.cls") is not None else 0

                        if pil_img is not None:
                            try:
                                buf = io.BytesIO()
                                pil_img.convert("RGB").save(buf, format="JPEG", quality=95)
                                raw_bytes = buf.getvalue()
                            except Exception:
                                continue

                            entry = self.process_and_save_image(
                                raw_bytes=raw_bytes,
                                label=1,
                                generator_name=gen_model,
                                category_id=cat_id,
                                prompt_text=prompt_txt
                            )
                            if entry:
                                collected_ai += 1
                                if progress_callback:
                                    progress_callback("ai", collected_ai, target_ai)
                                if collected_ai % 25 == 0 or collected_ai == target_ai:
                                    print(f"  [AI] Collected {collected_ai}/{target_ai} images (Latest: {gen_model})...", flush=True)
                                    self.flush_manifest()
                                    gc.collect()

                        # Polite pacing
                        if self.request_delay > 0 and collected_ai % 10 == 0:
                            time.sleep(self.request_delay)

                    if collected_ai >= target_ai:
                        break
                except Exception as e:
                    print(f"  [Notice] Streaming config {cfg} note: {e}. Trying next config...", flush=True)
                    continue

        # Fallback: rows endpoint if needed
        ai_offset = len(self.manifest_rows)
        while collected_ai < target_ai:
            needed = min(30, target_ai - collected_ai)
            url = f"https://datasets-server.huggingface.co/rows?dataset=lesc-unifi%2Fdragon&config=Regular&split=train&offset={ai_offset}&length={needed}"
            try:
                req = urllib.request.Request(url, headers=self._get_api_headers())
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    rows = [r["row"] for r in data.get("rows", [])]
            except Exception:
                time.sleep(3.0)
                ai_offset += needed
                continue

            if not rows:
                break

            ai_offset += len(rows)
            for r in rows:
                img_url = None
                if isinstance(r.get("png"), dict) and "src" in r["png"]:
                    img_url = r["png"]["src"]
                elif isinstance(r.get("image"), dict) and "src" in r["image"]:
                    img_url = r["image"]["src"]

                gen_model = r.get("model.txt") or (r.get("json", {}).get("model") if isinstance(r.get("json"), dict) else "Unknown_Diffusion")
                prompt_txt = r.get("json", {}).get("prompt", "") if isinstance(r.get("json"), dict) else ""
                cat_id = r.get("prompt.cls", 0) if r.get("prompt.cls") is not None else 0

                if img_url:
                    img_bytes = self.download_url_with_retry(img_url)
                    if img_bytes:
                        entry = self.process_and_save_image(
                            raw_bytes=img_bytes,
                            label=1,
                            generator_name=gen_model,
                            category_id=cat_id,
                            prompt_text=prompt_txt
                        )
                        if entry:
                            collected_ai += 1
                            if collected_ai % 25 == 0 or collected_ai == target_ai:
                                print(f"  [AI] Collected {collected_ai}/{target_ai} images (Latest: {gen_model})...", flush=True)
                                self.flush_manifest()
                    if collected_ai >= target_ai:
                        break

            if self.request_delay > 0:
                time.sleep(self.request_delay)

        self.flush_manifest()
        return collected_ai

    def curate_dataset(
        self,
        target_real: int = 75000,
        target_ai: int = 75000,
        dragon_config: str = "ExtraLarge",
        progress_callback=None
    ):
        """Main entry point: curates up to 150,000 images with full forensic rigor."""
        print("=" * 65, flush=True)
        print("     SIGNALSCOPE HIGH-CAPACITY FORENSIC DATASET CURATOR", flush=True)
        print("=" * 65, flush=True)
        print(f"Target Real Images: {target_real} (bitmind/open-images-v7)", flush=True)
        print(f"Target AI Images:   {target_ai} (lesc-unifi/dragon - 25 generators)", flush=True)
        print(f"Worker Threads:     {self.max_workers} (Rate-limited, zero-crash mode)", flush=True)
        print(f"Request Delay:      {self.request_delay}s", flush=True)
        print(f"Destination:        {self.output_dir}", flush=True)
        print("=" * 65, flush=True)

        start_time = time.time()

        # Phase 1: Real
        final_real = self.curate_real_images(target_real=target_real, progress_callback=progress_callback)

        # Phase 2: AI
        final_ai = self.curate_ai_images(target_ai=target_ai, config=dragon_config, progress_callback=progress_callback)

        # Final export
        self.flush_manifest()

        split_counts = {}
        generator_counts = {}
        for row in self.manifest_rows:
            split_counts[row["split"]] = split_counts.get(row["split"], 0) + 1
            generator_counts[row["generator"]] = generator_counts.get(row["generator"], 0) + 1

        summary = {
            "total_images": len(self.manifest_rows),
            "real_count": final_real,
            "ai_count": final_ai,
            "split_distribution": split_counts,
            "generator_distribution": generator_counts,
            "unseen_generators_reserved": UNSEEN_GENERATORS,
            "elapsed_seconds": round(time.time() - start_time, 2)
        }

        summary_path = self.output_dir / "curation_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print("\n" + "=" * 65, flush=True)
        print("          CURATION COMPLETED SUCCESSFULLY", flush=True)
        print("=" * 65, flush=True)
        print(f"Total Curated Images:     {summary['total_images']}", flush=True)
        print(f"Real / AI Counts:         {final_real} Real / {final_ai} AI", flush=True)
        print(f"Split Breakdown:          {split_counts}", flush=True)
        print(f"Manifest File:            {self.manifest_path}", flush=True)
        print(f"Audit Summary:            {summary_path}", flush=True)
        print(f"Total Elapsed Time:       {summary['elapsed_seconds']}s", flush=True)
        print("=" * 65, flush=True)

        return summary


def main():
    parser = argparse.ArgumentParser(description="SignalScope High-Capacity Forensic Dataset Curator")
    parser.add_argument("--output_dir", type=str, default="data/curated_dataset", help="Output directory")
    parser.add_argument("--target_real", type=int, default=75000, help="Target number of real images")
    parser.add_argument("--target_ai", type=int, default=75000, help="Target number of AI images")
    parser.add_argument("--config", type=str, default="ExtraLarge", choices=["ExtraSmall", "Small", "Regular", "Large", "ExtraLarge"])
    parser.add_argument("--hf_token", type=str, default=None, help="Optional Hugging Face Auth Token")
    parser.add_argument("--workers", type=int, default=5, help="Download thread workers")
    parser.add_argument("--delay", type=float, default=0.05, help="Polite request delay (seconds)")
    parser.add_argument("--sample_test", action="store_true", help="Run 10-sample verification test")

    args = parser.parse_args()

    if args.sample_test:
        args.target_real = 10
        args.target_ai = 10
        args.config = "Small"

    curator = ForensicDatasetCurator(
        output_dir=args.output_dir,
        hf_token=args.hf_token,
        max_workers=args.workers,
        request_delay=args.delay
    )
    curator.curate_dataset(
        target_real=args.target_real,
        target_ai=args.target_ai,
        dragon_config=args.config
    )


if __name__ == "__main__":
    main()
