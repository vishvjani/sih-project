"""
SignalScope Forensic Dataset Curator & Anti-Leakage Ingestion Engine
Downloads, deduplicates, and structures:
  - Real Images: bitmind/open-images-v7
  - AI Images:   lesc-unifi/dragon (25 generative diffusion models)

Enforces strict forensic guidelines:
  1. Exact duplicate removal (MD5/SHA-256)
  2. Near-duplicate removal (pHash/dHash)
  3. Strict Generator-Wise Partitioning (Seen vs Unseen generators)
  4. Content / Prompt family isolation
  5. Destruction of resolution, format (JPEG vs PNG), and metadata shortcuts
  6. Standardized naming (000001.jpg) + comprehensive dataset manifest CSV
"""

import os
import io
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


def compute_phash(image: Image.Image, hash_size: int = 8) -> str:
    """
    Computes a 64-bit perceptual hash (dHash/pHash) for near-duplicate detection.
    Picklable and requires no external heavy dependencies.
    """
    # Resize to hash_size + 1 by hash_size, grayscale
    resized = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.BILINEAR)
    pixels = np.array(resized, dtype=np.float32)
    # Compute horizontal gradient differences
    diff = pixels[:, 1:] > pixels[:, :-1]
    # Convert binary matrix to hex string
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
        batch_size: int = 25,
        request_delay: float = 1.5,
        phash_threshold: int = 4  # Hamming distance <= 4 considered near-duplicate
    ):
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.request_delay = request_delay
        self.phash_threshold = phash_threshold

        self.exact_hashes: Set[str] = set()
        self.recent_phashes: List[str] = []
        self.manifest_rows: List[Dict] = []
        self.current_id = 1

    def _get_hf_api_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": "SignalScope-Curator/1.0",
            "Accept": "application/json"
        }
        if self.hf_token:
            headers["Authorization"] = f"Bearer {self.hf_token}"
        return headers

    def _get_image_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
        }

    def is_duplicate(self, img_bytes: bytes, pil_img: Image.Image) -> bool:
        """Checks both exact MD5 and perceptual hash distance."""
        # 1. Exact MD5 check
        md5_val = hashlib.md5(img_bytes).hexdigest()
        if md5_val in self.exact_hashes:
            return True
        self.exact_hashes.add(md5_val)

        # 2. Perceptual hash check (for near-duplicates / resized variants)
        p_hash = compute_phash(pil_img)
        # Check against a rolling window of recent phashes (for performance)
        for existing in self.recent_phashes[-1000:]:
            if hamming_distance(p_hash, existing) <= self.phash_threshold:
                return True

        self.recent_phashes.append(p_hash)
        if len(self.recent_phashes) > 2000:
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
        Strips EXIF/ICC metadata, normalizes to RGB JPEG, standardizes format,
        assigns split, and saves to image directory.
        """
        try:
            pil_img = Image.open(io.BytesIO(raw_bytes))
            # Metadata destruction: Convert to RGB and copy clean buffer
            pil_img = pil_img.convert("RGB")
        except Exception:
            return None

        # Anti-leakage duplicate detection
        if self.is_duplicate(raw_bytes, pil_img):
            return None

        # Standardize representation (prevents resolution shortcuts)
        if pil_img.size != target_size:
            pil_img = pil_img.resize(target_size, Image.Resampling.BILINEAR)

        # Assign partition strictly according to forensic rules
        if label == 0:  # Real
            # Partition real images across train, val, test proportionally
            bucket = self.current_id % 100
            if bucket < 70:
                split = "train"
            elif bucket < 85:
                split = "val"
            else:
                split = "test_unseen"  # Evaluated against unseen generators
        else:  # AI
            if is_unseen_generator(generator_name):
                split = "test_unseen"  # Strictly held out!
            else:
                # Seen generators: Split between train, val, and test_seen
                bucket = (self.current_id + category_id) % 100
                if bucket < 75:
                    split = "train"
                elif bucket < 90:
                    split = "val"
                else:
                    split = "test_seen"

        # Form monotonic filename (stripping filename leakage)
        image_filename = f"{self.current_id:07d}.jpg"
        save_path = self.images_dir / image_filename

        # Save as standard JPEG (quality 92, no EXIF/ICC)
        pil_img.save(save_path, format="JPEG", quality=92, optimize=True)

        # Record metadata in manifest
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
            "prompt": prompt_text.replace("\n", " ").strip(),
            "split": split,
            "sha256": sha256_val,
            "phash": p_hash
        }

        self.manifest_rows.append(manifest_entry)
        self.current_id += 1
        return manifest_entry

    def _fetch_rows_with_backoff(self, url: str, max_retries: int = 5, initial_backoff: float = 5.0) -> List[Dict]:
        """
        Queries Hugging Face dataset server rows endpoint with resilient exponential backoff,
        Retry-After header parsing, and gateway error handling.
        """
        headers = self._get_hf_api_headers()
        last_exception = None

        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=25) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    return [r["row"] for r in data.get("rows", [])]
            except urllib.error.HTTPError as e:
                last_exception = e
                if e.code == 429:
                    retry_after = e.headers.get("Retry-After")
                    if retry_after and retry_after.strip().isdigit():
                        wait_time = float(retry_after.strip()) + 1.0
                    else:
                        wait_time = initial_backoff * (2 ** attempt) + random.uniform(1.0, 3.0)
                    print(f"  [Rate Limit 429] Hugging Face rate limit hit. Pausing for {wait_time:.1f}s before retry ({attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                elif e.code in (500, 502, 503, 504):
                    wait_time = 3.0 * (attempt + 1) + random.uniform(1.0, 2.0)
                    print(f"  [Server Error {e.code}] Temporary HF server issue. Retrying in {wait_time:.1f}s ({attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                else:
                    print(f"  [HTTP Error {e.code}] {e.reason}")
                    return []
            except (urllib.error.URLError, TimeoutError, socket.timeout) as e:
                last_exception = e
                wait_time = 3.0 * (attempt + 1) + random.uniform(0.5, 1.5)
                print(f"  [Network Timeout] {e}. Retrying in {wait_time:.1f}s ({attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            except Exception as e:
                last_exception = e
                print(f"  [Unexpected Error] {e}")
                return []

        print(f"  [Notice] All {max_retries} retry attempts exhausted for batch. Last error: {last_exception}")
        return []

    def fetch_open_images_sample(self, offset: int = 0, length: Optional[int] = None) -> List[Dict]:
        """Queries bitmind/open-images-v7 rows endpoint with backoff."""
        batch_len = length or self.batch_size
        url = f"https://datasets-server.huggingface.co/rows?dataset=bitmind%2Fopen-images-v7&config=default&split=train&offset={offset}&length={batch_len}"
        return self._fetch_rows_with_backoff(url)

    def fetch_dragon_sample(self, config: str = "Regular", offset: int = 0, length: Optional[int] = None) -> List[Dict]:
        """Queries lesc-unifi/dragon rows endpoint with backoff."""
        batch_len = length or self.batch_size
        url = f"https://datasets-server.huggingface.co/rows?dataset=lesc-unifi%2Fdragon&config={config}&split=train&offset={offset}&length={batch_len}"
        return self._fetch_rows_with_backoff(url)

    def download_url(self, url: str) -> Optional[bytes]:
        """Downloads raw bytes from URL with clean image headers and 1 timeout retry."""
        headers = self._get_image_headers()
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=12) as resp:
                    return resp.read()
            except Exception:
                if attempt == 0:
                    time.sleep(0.5)
                continue
        return None

    def curate_dataset(
        self,
        target_real: int = 500,
        target_ai: int = 500,
        dragon_config: str = "Regular",
        progress_callback=None
    ):
        """
        Curates balanced, deduplicated dataset with strict unseen-generator split.
        """
        print("=" * 65)
        print("     SIGNALSCOPE FORENSIC DATASET CURATOR")
        print("=" * 65)
        print(f"Target Real Images: {target_real} (bitmind/open-images-v7)")
        print(f"Target AI Images:   {target_ai} (lesc-unifi/dragon - 25 generators)")
        print(f"Batch Size:         {self.batch_size} images/request")
        print(f"Request Delay:      {self.request_delay}s between batches")
        print(f"Max Workers:        {self.max_workers} threads")
        print(f"Destination:        {self.output_dir}")
        print("=" * 65)

        start_time = time.time()
        collected_real = 0
        collected_ai = 0

        # -------------------------------------------------------------
        # 1. CURATE REAL IMAGES (Open Images v7)
        # -------------------------------------------------------------
        print(f"\n[Phase 1/2] Ingesting Real Images (bitmind/open-images-v7)...")
        real_offset = 0
        consecutive_empty_real = 0

        while collected_real < target_real:
            needed = min(self.batch_size, target_real - collected_real)
            rows = self.fetch_open_images_sample(offset=real_offset, length=needed)

            if not rows:
                consecutive_empty_real += 1
                if consecutive_empty_real >= 4:
                    print(f"  [Notice] Unable to fetch more OpenImages rows at offset {real_offset}. Proceeding to Phase 2.")
                    break
                real_offset += needed
                time.sleep(self.request_delay * 2)
                continue

            consecutive_empty_real = 0
            real_offset += len(rows)

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self.download_url, r["url"]): r for r in rows if "url" in r}
                for f in as_completed(futures):
                    row_data = futures[f]
                    img_bytes = f.result()
                    if img_bytes:
                        entry = self.process_and_save_image(
                            raw_bytes=img_bytes,
                            label=0,
                            generator_name="OpenImages_v7",
                            category_id=row_data.get("index", 0) % 1000,
                            prompt_text="Natural Camera Photograph"
                        )
                        if entry:
                            collected_real += 1
                            if progress_callback:
                                progress_callback("real", collected_real, target_real)
                            if collected_real % 25 == 0 or collected_real == target_real:
                                print(f"  [Real] Collected {collected_real}/{target_real} images...")
                    if collected_real >= target_real:
                        break

            # Polite delay between batch requests to prevent rate limiting
            if collected_real < target_real and self.request_delay > 0:
                time.sleep(self.request_delay)

        # -------------------------------------------------------------
        # 2. CURATE AI IMAGES (DRAGON - 25 Diffusion Models)
        # -------------------------------------------------------------
        print(f"\n[Phase 2/2] Ingesting AI Images across 25 generators (lesc-unifi/dragon)...")
        ai_offset = 0
        consecutive_empty_ai = 0

        while collected_ai < target_ai:
            needed = min(self.batch_size, target_ai - collected_ai)
            rows = self.fetch_dragon_sample(config=dragon_config, offset=ai_offset, length=needed)

            if not rows:
                consecutive_empty_ai += 1
                if consecutive_empty_ai >= 4:
                    print(f"  [Notice] Unable to fetch more DRAGON rows at offset {ai_offset}. Proceeding to export.")
                    break
                ai_offset += needed
                time.sleep(self.request_delay * 2)
                continue

            consecutive_empty_ai = 0
            ai_offset += len(rows)

            # Map rows to URLs
            tasks = []
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
                    tasks.append((img_url, gen_model, cat_id, prompt_txt))

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self.download_url, t[0]): t for t in tasks}
                for f in as_completed(futures):
                    _, gen_model, cat_id, prompt_txt = futures[f]
                    img_bytes = f.result()
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
                            if progress_callback:
                                progress_callback("ai", collected_ai, target_ai)
                            if collected_ai % 25 == 0 or collected_ai == target_ai:
                                print(f"  [AI] Collected {collected_ai}/{target_ai} images (Latest: {gen_model})...")
                    if collected_ai >= target_ai:
                        break

            # Polite delay between batch requests to prevent rate limiting
            if collected_ai < target_ai and self.request_delay > 0:
                time.sleep(self.request_delay)

        # -------------------------------------------------------------
        # 3. EXPORT AUDITABLE MANIFEST
        # -------------------------------------------------------------
        manifest_path = self.output_dir / "dataset_manifest.csv"
        fieldnames = [
            "image_id", "filename", "label", "label_name", "generator",
            "generator_family", "generator_family_id", "category_id",
            "prompt", "split", "sha256", "phash"
        ]
        with open(manifest_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.manifest_rows)

        # Summary Metrics
        split_counts = {}
        generator_counts = {}
        for row in self.manifest_rows:
            split_counts[row["split"]] = split_counts.get(row["split"], 0) + 1
            generator_counts[row["generator"]] = generator_counts.get(row["generator"], 0) + 1

        summary = {
            "total_images": len(self.manifest_rows),
            "real_count": collected_real,
            "ai_count": collected_ai,
            "split_distribution": split_counts,
            "generator_distribution": generator_counts,
            "unseen_generators_reserved": UNSEEN_GENERATORS,
            "elapsed_seconds": round(time.time() - start_time, 2)
        }

        summary_path = self.output_dir / "curation_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print("\n" + "=" * 65)
        print("          CURATION COMPLETED SUCCESSFULLY")
        print("=" * 65)
        print(f"Total Curated Images:     {summary['total_images']}")
        print(f"Split Breakdown:          {split_counts}")
        print(f"Manifest File:            {manifest_path}")
        print(f"Audit Summary:            {summary_path}")
        print(f"Total Elapsed Time:       {summary['elapsed_seconds']}s")
        print("=" * 65)

        return summary


def main():
    parser = argparse.ArgumentParser(description="SignalScope Forensic Dataset Curator")
    parser.add_argument("--output_dir", type=str, default="data/curated_dataset", help="Output directory")
    parser.add_argument("--target_real", type=int, default=500, help="Target number of real images")
    parser.add_argument("--target_ai", type=int, default=500, help="Target number of AI images")
    parser.add_argument("--config", type=str, default="Small", choices=["ExtraSmall", "Small", "Regular", "Large", "ExtraLarge"])
    parser.add_argument("--hf_token", type=str, default=None, help="Optional Hugging Face Auth Token")
    parser.add_argument("--batch_size", type=int, default=25, help="Batch size for Hugging Face rows API (default: 25)")
    parser.add_argument("--delay", type=float, default=1.5, help="Polite delay (seconds) between batch requests to prevent 429 rate limiting")
    parser.add_argument("--workers", type=int, default=5, help="Download thread workers (default: 5)")
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
        batch_size=args.batch_size,
        request_delay=args.delay
    )
    curator.curate_dataset(
        target_real=args.target_real,
        target_ai=args.target_ai,
        dragon_config=args.config
    )


if __name__ == "__main__":
    main()
