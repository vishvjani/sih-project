"""
SignalScope Dataset & Data Augmentation Module
Supports CIFAKE (REAL vs FAKE) and custom synthetic datasets.
Includes robustness augmentations (JPEG compression, Gaussian blur, resizing)
to prevent memorizing generator-specific noise and generalize to unseen generators.
All transform classes are top-level and picklable for DataLoader multiprocessing.
"""

import os
import io
import random
from pathlib import Path
from typing import Tuple, List, Optional
from PIL import Image, ImageFilter
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

try:
    from torchvision import transforms
    HAS_TORCHVISION = True
except ImportError:
    HAS_TORCHVISION = False


class RandomJPEGCompression:
    """Simulates social media and messaging app JPEG compression degradation."""
    def __init__(self, quality_range: Tuple[int, int] = (50, 95), p: float = 0.4):
        self.quality_range = quality_range
        self.p = p

    def __call__(self, img: Image.Image) -> Image.Image:
        if random.random() < self.p:
            quality = random.randint(self.quality_range[0], self.quality_range[1])
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=quality)
            buf.seek(0)
            return Image.open(buf).convert("RGB")
        return img


class FallbackTransform:
    """Picklable fallback transform using PIL and NumPy when torchvision is absent."""
    def __init__(self, img_size: int = 224, is_train: bool = False):
        self.img_size = img_size
        self.is_train = is_train
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

    def __call__(self, img: Image.Image) -> torch.Tensor:
        if self.is_train and random.random() > 0.5:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        resized = img.resize((self.img_size, self.img_size), Image.Resampling.BILINEAR)
        arr = np.array(resized, dtype=np.float32) / 255.0
        norm = (arr - self.mean) / self.std
        return torch.from_numpy(norm.transpose(2, 0, 1))


def get_transforms(is_train: bool = True, img_size: int = 224):
    """Constructs training or evaluation transform pipeline."""
    if HAS_TORCHVISION:
        if is_train:
            return transforms.Compose([
                RandomJPEGCompression(quality_range=(50, 95), p=0.35),
                transforms.Resize((img_size + 32, img_size + 32)),
                transforms.RandomCrop((img_size, img_size)),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.1),
                transforms.RandomApply([
                    transforms.GaussianBlur(kernel_size=(3, 3), sigma=(0.1, 1.5))
                ], p=0.25),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
        else:
            return transforms.Compose([
                transforms.Resize((img_size, img_size)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
    else:
        return FallbackTransform(img_size=img_size, is_train=is_train)


class ImageAuthenticityDataset(Dataset):
    """
    Dataset loader for binary Real vs AI-Generated image classification
    with fine-grained generator attribution labels and metadata.
    """
    def __init__(
        self,
        file_paths: List[str],
        labels: List[int],
        attribution_labels: Optional[List[int]] = None,
        generator_names: Optional[List[str]] = None,
        transform=None
    ):
        self.file_paths = file_paths
        self.labels = labels
        self.attribution_labels = attribution_labels or [0 if l == 0 else 1 for l in labels]
        self.generator_names = generator_names or ["Unknown" for _ in labels]
        self.transform = transform or get_transforms(is_train=False)

    def __len__(self):
        return len(self.file_paths)

    def __getitem__(self, idx: int):
        img_path = self.file_paths[idx]
        try:
            image = Image.open(img_path).convert("RGB")
        except Exception:
            image = Image.new("RGB", (224, 224), color=(128, 128, 128))

        if self.transform:
            image = self.transform(image)

        binary_label = torch.tensor(self.labels[idx], dtype=torch.float32)
        attr_label = torch.tensor(self.attribution_labels[idx], dtype=torch.long)

        return image, binary_label, attr_label


def create_dataset_from_manifest(
    manifest_path_or_dir: str,
    split: str = "train",
    img_size: int = 224,
    batch_size: int = 32,
    num_workers: int = 2
):
    """
    Constructs DataLoader from auditable dataset_manifest.csv.
    Supports splits: 'train', 'val', 'test_unseen', 'test_seen', 'test'
    """
    import csv
    manifest_file = Path(manifest_path_or_dir)
    if manifest_file.is_dir():
        manifest_file = manifest_file / "dataset_manifest.csv"

    images_dir = manifest_file.parent / "images"

    file_paths = []
    labels = []
    attr_labels = []
    gen_names = []

    with open(manifest_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_split = row.get("split", "train")
            # If user asks for 'test', include both 'test_unseen' and 'test_seen'
            if split == "test":
                if "test" not in row_split:
                    continue
            elif row_split != split:
                continue

            img_p = images_dir / row["filename"]
            if img_p.exists():
                file_paths.append(str(img_p))
                labels.append(int(row["label"]))
                attr_labels.append(int(row.get("generator_family_id", 0)))
                gen_names.append(row.get("generator", "Unknown"))

    is_train = (split == "train")
    dataset = ImageAuthenticityDataset(
        file_paths=file_paths,
        labels=labels,
        attribution_labels=attr_labels,
        generator_names=gen_names,
        transform=get_transforms(is_train=is_train, img_size=img_size)
    )

    effective_workers = 0 if (os.name == "nt" or len(file_paths) < 100) else num_workers

    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=is_train,
        num_workers=effective_workers,
        pin_memory=True if torch.cuda.is_available() else False
    )

    return dataset, loader


def create_dataset_from_directory(root_dir: str, split: str = "train", img_size: int = 224, batch_size: int = 32, num_workers: int = 2):
    """
    Scans a directory expecting either:
      root_dir/REAL and root_dir/FAKE
    or:
      root_dir/train/REAL, root_dir/train/FAKE, root_dir/test/REAL, root_dir/test/FAKE
    """
    base_path = Path(root_dir)
    target_split_path = base_path / split if (base_path / split).exists() else base_path

    real_dir = target_split_path / "REAL"
    fake_dir = target_split_path / "FAKE"

    if not real_dir.exists() or not fake_dir.exists():
        for d in target_split_path.iterdir():
            if d.is_dir() and "real" in d.name.lower():
                real_dir = d
            elif d.is_dir() and ("fake" in d.name.lower() or "ai" in d.name.lower() or "synthetic" in d.name.lower()):
                fake_dir = d

    exts = ("*.jpg", "*.jpeg", "*.png", "*.webp")
    real_files = []
    fake_files = []

    if real_dir.exists():
        for ext in exts:
            real_files.extend([str(p) for p in real_dir.glob(ext)])
    if fake_dir.exists():
        for ext in exts:
            fake_files.extend([str(p) for p in fake_dir.glob(ext)])

    file_paths = real_files + fake_files
    labels = [0] * len(real_files) + [1] * len(fake_files)
    attr_labels = [0] * len(real_files) + [1] * len(fake_files)

    is_train = (split == "train")
    dataset = ImageAuthenticityDataset(
        file_paths=file_paths,
        labels=labels,
        attribution_labels=attr_labels,
        transform=get_transforms(is_train=is_train, img_size=img_size)
    )

    effective_workers = 0 if (os.name == 'nt' or len(file_paths) < 100) else num_workers

    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=is_train,
        num_workers=effective_workers,
        pin_memory=True if torch.cuda.is_available() else False
    )

    return dataset, loader


def load_dataset(source: str, split: str = "train", img_size: int = 224, batch_size: int = 32, num_workers: int = 2):
    """
    Universal dataset factory:
    Automatically detects if source is a manifest-based curated dataset or standard folder.
    """
    path = Path(source)
    if (path / "dataset_manifest.csv").exists() or (path.suffix == ".csv" and path.exists()):
        return create_dataset_from_manifest(
            manifest_path_or_dir=source,
            split=split,
            img_size=img_size,
            batch_size=batch_size,
            num_workers=num_workers
        )
    else:
        return create_dataset_from_directory(
            root_dir=source,
            split=split,
            img_size=img_size,
            batch_size=batch_size,
            num_workers=num_workers
        )

