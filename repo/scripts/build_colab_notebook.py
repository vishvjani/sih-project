"""
Builder script to generate the official SignalScope Google Colab Fine-Tuning Notebook.
Ensures valid JSON notebook format with 10 structured steps for Colab GPU execution.
"""

import json
from pathlib import Path

def create_signalscope_notebook():
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 0,
        "metadata": {
            "accelerator": "GPU",
            "colab": {
                "provenance": [],
                "gpuType": "T4"
            },
            "language_info": {
                "name": "python"
            }
        },
        "cells": []
    }

    def add_md(text):
        notebook["cells"].append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [line + "\n" for line in text.split("\n")]
        })

    def add_code(text):
        notebook["cells"].append({
            "cell_type": "code",
            "metadata": {},
            "execution_count": None,
            "outputs": [],
            "source": [line + "\n" for line in text.split("\n")]
        })

    # Cell 1: Overview
    add_md("""# SignalScope — Dual-Stream ConvNeXt-Tiny + Forensic SRM Model Fine-Tuning
### Telling Real From Synthetic in the Age of Generative Media (SIH 2026)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/vishvjani/sih-project/blob/master/notebooks/1_SignalScope_Model_FineTuning_Colab.ipynb)

This notebook provides the complete, state-of-the-art training, calibration, and evaluation pipeline for **SignalScope**, strictly engineered to prevent shortcut learning and achieve **80%+ generalization accuracy on unseen AI generators**.

---
### 📌 Forensic Architecture & Strategy
1. **Dataset Sources**:
   - **AI-Generated**: `lesc-unifi/dragon` (25 diffusion models: FLUX.1, SD3, SDXL, PixArt-Sigma, Kolors, Lumina, Kandinsky, IF, etc. across 1,000 prompt classes).
   - **Real Images**: `bitmind/open-images-v7` (High-resolution authentic photographs).
2. **Forensic Anti-Leakage & Shortcut Destruction**:
   - Exact duplicate (MD5) + Perceptual near-duplicate (pHash) filtering.
   - **Strict Generator-Wise Partitioning**: Train/Val on seen generators, evaluate on strictly held-out **UNSEEN** generators (`Flux_1`, `SD_3`, `Kolors`, `Lumina`, `PixArt_Sigma`).
   - Resolution, format (JPEG vs PNG), and metadata shortcuts destroyed.
3. **Modern Architecture Attribution**:
   - Classifies and profiles modern frontier models: FLUX.1, SD3, Midjourney v6, DALL-E 3 / GPT-4o, Google Gemini Nano, Kimi (Moonshot), Banana / Grok-Imagine.
4. **Dual-Stream ConvNeXt-Tiny + SRM Residuals**:
   - Combines semantic representations (768-d) with high-frequency noise residual lattice (256-d) into a 512-d calibrated representation.
5. **Target Performance**: $\\ge 80\\%$ accuracy and ROC-AUC on both seen and held-out unseen generators without overfitting.""")

    # Cell 2: Step 1
    add_md("## Step 1: Verify GPU Accelerator & PyTorch Environment")
    add_code("""!nvidia-smi
import torch
print('PyTorch Version:', torch.__version__)
print('CUDA Available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('Active GPU:', torch.cuda.get_device_name(0))""")

    # Cell 3: Step 2
    add_md("""## Step 2: Set Up Workspace & Clone Repository
*(Google Drive mount is completely optional — you can run directly in fast Colab local disk)*""")
    add_code("""MOUNT_DRIVE = False  # Set to True if you want to mount Google Drive for persistence

if MOUNT_DRIVE:
    try:
        from google.colab import drive
        drive.mount('/content/drive', force_remount=False)
        print('✓ Google Drive mounted.')
    except Exception as e:
        print('ℹ Drive mount skipped:', e)
else:
    print('✓ Running directly in Colab fast local storage.')

# Clone or update SignalScope repository
!git clone https://github.com/vishvjani/sih-project.git /content/sih-project || (cd /content/sih-project && git pull)
%cd /content/sih-project/repo""")

    # Cell 4: Step 3
    add_md("## Step 3: Install Required Dependencies")
    add_code("""!pip install -q -r requirements-colab.txt || pip install -q timm torchvision datasets scikit-learn matplotlib albumentations imagehash""")

    # Cell 5: Step 4
    add_md("""## Step 4: Automated Forensic Ingestion & Curation Pipeline
Ingests from:
- **`bitmind/open-images-v7`** (Authentic Real Images)
- **`lesc-unifi/dragon`** (AI Images across 25 diffusion models)

Applies **exact MD5 deduplication**, **perceptual pHash near-duplicate removal**, **resolution standardization**, and builds `dataset_manifest.csv` with strict seen/unseen generator partitions.

> **💡 Rate Limiting Tip**:
> To bypass Hugging Face public rate limits completely, paste a free read token below (generate one at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)). Even without a token, SignalScope's curator includes polite rate-limiting delays and automatic exponential backoff retries.""")

    add_code("""import os

# Optional: Hugging Face Token (paste for elevated quota; leave blank for anonymous rate-limited mode)
# Free tokens available at: https://huggingface.co/settings/tokens
HF_TOKEN = ""  # @param {type:"string"}
if HF_TOKEN.strip():
    os.environ["HF_TOKEN"] = HF_TOKEN.strip()
    print("✓ Hugging Face Token configured.")
else:
    print("ℹ Running with public anonymous access (curator rate-limiting delays & backoff active).")

# Select Curation Scale for Colab:
# - 'fast_demo'   : 300 Real + 300 AI (~2 mins, rapid test)
# - 'standard'    : 500 Real + 500 AI (~4 mins, recommended safe default)
# - 'benchmark'   : 800 Real + 800 AI (~7 mins, optimal benchmark target)
# - 'large'       : 2,000 Real + 2,000 AI (~18 mins)
# - 'full_scale'  : 10,000 Real + 10,000 AI (for multi-hour background training)
CURATION_SCALE = "standard"  # @param ["fast_demo", "standard", "benchmark", "large", "full_scale"]

scale_targets = {
    "fast_demo": (300, 300),
    "standard": (500, 500),
    "benchmark": (800, 800),
    "large": (2000, 2000),
    "full_scale": (10000, 10000)
}
target_real, target_ai = scale_targets[CURATION_SCALE]
print(f"Selected Scale: {CURATION_SCALE} -> Target: {target_real} Real + {target_ai} AI images")

!python data/curator.py \\
    --output_dir "data/curated_dataset" \\
    --target_real {target_real} \\
    --target_ai {target_ai} \\
    --config Regular \\
    --batch_size 25 \\
    --delay 1.5 \\
    --workers 5""")

    # Cell 6: Step 5
    add_md("""## Step 5: Data Audit & Forensic Distribution Verification
Visualizes the dataset partitions, class balance, and confirms that held-out unseen generators (`Flux_1`, `SD_3`, `Kolors`, `Lumina`, `PixArt_Sigma`) are strictly isolated from training.""")
    add_code("""import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

manifest_file = Path("data/curated_dataset/dataset_manifest.csv")
if manifest_file.exists():
    df = pd.read_csv(manifest_file)
    print(f"✓ Total Curated Samples in Manifest: {len(df)}")
    print("\\n--- Split Distribution ---")
    print(df['split'].value_counts())
    print("\\n--- Generator Distribution ---")
    print(df['generator'].value_counts())

    # Plot Distribution
    fig, axs = plt.subplots(1, 2, figsize=(14, 5))
    df['split'].value_counts().plot(kind='bar', ax=axs[0], color=['#3b82f6', '#10b981', '#f59e0b', '#ef4444'])
    axs[0].set_title('Dataset Split Distribution (Anti-Leakage Partition)')
    axs[0].set_ylabel('Image Count')

    df[df['label'] == 1]['generator'].value_counts().head(12).plot(kind='barh', ax=axs[1], color='#8b5cf6')
    axs[1].set_title('Top AI Generators Represented (DRAGON)')
    axs[1].set_xlabel('Image Count')
    plt.tight_layout()
    plt.show()
else:
    print("Manifest not found. Run Step 4 first.")""")

    # Cell 7: Step 6
    add_md("""## Step 6: Phase 1 Training — Linear Probe (Frozen ConvNeXt Backbone)
In Phase 1, the ConvNeXt-Tiny semantic backbone is **FROZEN**.
The Spatial Rich Model (SRM) High-Pass noise residual stream and the classification heads adapt to the multi-generator dataset without distorting deep semantic feature maps.""")
    add_code("""!python -m model.train \\
    --data-dir "data/curated_dataset" \\
    --save-dir "./model/weights" \\
    --phase1-epochs 2 \\
    --phase2-epochs 0 \\
    --batch-size 64 \\
    --lr-head 0.001 \\
    --device cuda""")

    # Cell 8: Step 7
    add_md("""## Step 7: Phase 2 Fine-Tuning — Differential Stage Unfreezing (Stages 3 & 4)
Stages 3 & 4 of ConvNeXt-Tiny are **UNFROZEN** with a small learning rate (`1e-5`) and Cosine Annealing.
The stem and stages 1-2 remain frozen to prevent catastrophic forgetting.
Label smoothing (0.05) and random JPEG compression augmentations prevent shortcut learning.""")
    add_code("""!python -m model.train \\
    --data-dir "data/curated_dataset" \\
    --save-dir "./model/weights" \\
    --phase1-epochs 0 \\
    --phase2-epochs 5 \\
    --batch-size 64 \\
    --lr-head 0.0001 \\
    --lr-backbone 0.00001 \\
    --device cuda""")

    # Cell 9: Step 8
    add_md("""## Step 8: Comprehensive Benchmark Evaluation (Seen vs Unseen Generators)
Evaluates on the held-out test split:
1. **Overall ROC-AUC & Accuracy**
2. **Unseen Generator ROC-AUC & Accuracy** (strictly measured on `Flux_1`, `SD_3`, `Kolors`, `Lumina`, `PixArt_Sigma`)
3. **Cross-Generator Accuracy Matrix**
4. **Degradation Robustness Suite** (JPEG Q90, Q70, Q50, downscaling 50%)
5. **Expected Calibration Error (ECE)**""")
    add_code("""!python -m model.evaluate \\
    --checkpoint "./model/weights/signalscope_convnext_tiny.pth" \\
    --data-dir "data/curated_dataset" \\
    --batch-size 64 \\
    --device cuda \\
    --output "evaluation_report.json\"""")

    # Cell 10: Step 9
    add_md("""## Step 9: Interactive Grad-CAM & Modern Generator Attribution
Tests any image interactively to inspect:
- **Calibrated Authenticity Verdict**
- **Grad-CAM Visual Heatmap Overlay**
- **Modern Frontier Model Attribution** (FLUX.1, SD3, Midjourney v6, DALL-E 3, GPT-4o, Gemini Nano, Kimi, Banana)""")
    add_code("""import io
import base64
import json
import glob
import matplotlib.pyplot as plt
from PIL import Image
from model.predict import predict_image
from model.forensic import extract_visual_noise_residual

# Pick a sample image from the test set
test_images = glob.glob("data/curated_dataset/images/*.jpg")
if test_images:
    sample_path = test_images[0]
    image = Image.open(sample_path)
    result = predict_image(image, device="cuda" if torch.cuda.is_available() else "cpu")

    # Decode Grad-CAM heatmap
    heatmap_data = base64.b64decode(result['gradcam_heatmap_base64'])
    heatmap_img = Image.open(io.BytesIO(heatmap_data))
    residual_img = extract_visual_noise_residual(image)

    # Plot Side-by-Side
    fig, axs = plt.subplots(1, 3, figsize=(16, 5))
    axs[0].imshow(image)
    axs[0].set_title('Input Image')
    axs[0].axis('off')

    axs[1].imshow(residual_img, cmap='gray')
    axs[1].set_title('Forensic SRM Noise Residual')
    axs[1].axis('off')

    axs[2].imshow(heatmap_img)
    axs[2].set_title(f"Grad-CAM: {result['verdict']} ({result['confidence_percentage']}%)")
    axs[2].axis('off')

    pred_title = result['generator_attribution'].get('predicted_model', result['generator_attribution'].get('predicted_family'))
    plt.suptitle(
        f"SignalScope Detection: {result['verdict']} | Model: {pred_title}",
        fontsize=14,
        fontweight='bold'
    )
    plt.tight_layout()
    plt.show()

    print("\\n--- Forensic Attribution Summary ---")
    print(json.dumps(result['generator_attribution'], indent=2))
else:
    print("No sample images found. Please run Step 4 curation first.")""")

    # Cell 11: Step 10
    add_md("## Step 10: 1-Click Export Model Weights to Google Drive or Local Disk")
    add_code("""import shutil
from pathlib import Path

weights_dir = Path("./model/weights")
checkpoint = weights_dir / "signalscope_convnext_tiny.pth"
calibration = weights_dir / "calibration_config.json"

if checkpoint.exists():
    mb_size = checkpoint.stat().st_size / (1024 * 1024)
    print(f"✓ Checkpoint found: {checkpoint} ({mb_size:.1f} MB)")
    
    # If Google Drive is mounted, copy weights
    drive_dest = Path("/content/drive/MyDrive/SignalScope_Weights")
    if Path("/content/drive/MyDrive").exists():
        drive_dest.mkdir(parents=True, exist_ok=True)
        shutil.copy(checkpoint, drive_dest / "signalscope_convnext_tiny.pth")
        if calibration.exists():
            shutil.copy(calibration, drive_dest / "calibration_config.json")
        print("✓ Model checkpoint and calibration exported to Google Drive:", drive_dest)
    else:
        print("ℹ Google Drive not mounted. Model weights saved locally in ./model/weights/")
        print("To download via browser in Colab:")
        print("from google.colab import files; files.download('./model/weights/signalscope_convnext_tiny.pth')")
else:
    print("Checkpoint not found. Run training in Step 6 & 7 first.")""")

    # Write notebook files
    Path("notebooks").mkdir(parents=True, exist_ok=True)
    Path("colab").mkdir(parents=True, exist_ok=True)

    with open("notebooks/1_SignalScope_Model_FineTuning_Colab.ipynb", "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=2)

    with open("colab/1_SignalScope_Model_FineTuning_Colab.ipynb", "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=2)

    print("Successfully built Colab notebooks at:")
    print("  - notebooks/1_SignalScope_Model_FineTuning_Colab.ipynb")
    print("  - colab/1_SignalScope_Model_FineTuning_Colab.ipynb")

if __name__ == "__main__":
    create_signalscope_notebook()
