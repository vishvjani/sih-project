# SignalScope — Telling Real From Synthetic in the Age of Generative Media

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/vishvjani/sih-project/blob/master/notebooks/1_SignalScope_Model_FineTuning_Colab.ipynb)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-orange.svg)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Smart India Hackathon (SIH 2026) | Problem Statement 2**  
Domain: **AI / Media Forensics / Trust & Safety**

SignalScope is an advanced Computer Vision and Explainable AI-based media authenticity detection system designed to determine whether an image is **authentic/real** or **AI-generated/synthetic**, with a primary focus on **generalizing to unseen AI generators** and providing **faithful, localized visual explanations**.

---

## 🚀 Quick Links & Notebooks

| Notebook / Resource | Description | Colab Link |
|---|---|:---:|
| **1. Model Fine-Tuning & Evaluation** | Complete two-phase fine-tuning on ConvNeXt-Tiny + SRM Forensic Residuals with 1-click CIFAKE dataset download and Drive export. | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/vishvjani/sih-project/blob/master/notebooks/1_SignalScope_Model_FineTuning_Colab.ipynb) |
| **2. Colab GPU Backend Server** | Host the entire FastAPI backend on free Colab GPU with a public HTTPS tunnel. | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/vishvjani/sih-project/blob/master/notebooks/2_SignalScope_Colab_GPU_Backend.ipynb) |
| **3. One-Page Model Report** | Official SIH Section 7.3 Model Report detailing task, split, architecture, and metrics. | [model_report.md](report/model_report.md) |

---

## 🏆 Implemented Modules Summary

| Module | Status | Description |
|---|:---:|---|
| **Mandatory Core Task** | ✅ Completed | Binary Real vs AI classification with Platt calibrated confidence score (ROC-AUC: 0.9842). |
| **Bonus Module A: Faithful Explanation** | ✅ Completed | Real PyTorch Grad-CAM heatmaps highlighting suspicious regions + grounded natural-language explanations. |
| **Bonus Module B: Generator Attribution** | ✅ Completed | Multi-class attribution: Pristine Real, Latent Diffusion (SD/Midjourney), GAN (StyleGAN), Autoregressive. |
| **Bonus Module C: Robustness to Degradation** | ✅ Completed | Evaluates predictor stability across severe JPEG compression (Q=50), resizing (50%), and screenshot resampling. |
| **Bonus Module D: Metadata & Provenance** | ✅ Completed | EXIF hardware tags inspection and C2PA Content Credentials signature extraction. |
| **Bonus Module E: Multimodal Verification** | ✅ Completed | Text-image semantic consistency alignment between image content and accompanying caption. |

---

## 🏗 Dual-Stream Architecture Overview

```text
                       INPUT IMAGE (RGB)
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
   [Semantic Stream]                     [Forensic Stream]
   ConvNeXt-Tiny (Pretrained)            Spatial Rich Model (SRM) High-Pass
   Feature Maps: 768-d                   Noise Residuals: 256-d
            │                                     │
            └──────────────────┬──────────────────┘
                               ▼
                     [Feature Fusion Layer]
                    Concatenation + Linear (1024-d)
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
   [Binary Classification Head]         [Generator Attribution Head]
   Real (0) vs AI-Generated (1)         Pristine / Diffusion / GAN / Other
            │                                     │
            ▼                                     ▼
     Platt Calibration (T)                  Attribution Probabilities
            │
            ▼
   Calibrated Verdict + Grad-CAM Heatmap
```

### Why ConvNeXt-Tiny + Forensic SRM Residuals?
Standard CNNs overfit to the color and semantic styles of seen generators. Our forensic stream passes the image through **Spatial Rich Model (SRM) high-pass filters** that subtract low-frequency scene semantics and isolate high-frequency noise residuals $R = I - \text{smooth}(I)$. This exposes latent diffusion upsampling patterns and GAN checkerboards common to all generative models.

---

## 📊 Evaluation & Benchmark Results

Evaluated on the held-out test split of the 100k+ **CIFAKE benchmark**:

| Primary Metric | Value | Meaning |
|---|:---:|---|
| **Overall ROC-AUC** | **0.9842** | Near-optimal separation across all decision thresholds |
| **Unseen-Generator Split ROC-AUC** | **0.9576** | Primary SIH differentiator: high generalization to unseen models |
| **Macro-F1 Score** | **0.9380** | Balanced precision & recall across both classes |
| **Expected Calibration Error (ECE)** | **0.0384** | Honest confidence output, avoids neural network overconfidence |

### Confusion Matrix (10,000 Samples)
```text
                         Predicted
                    Real       AI
Actual Real         4,705      295
Actual AI             325    4,675
```

---

## ⏱ Reproduce Prediction in Under 10 Minutes

### Option 1: Quick Local Run
```bash
# 1. Clone repository
git clone https://github.com/vishvjani/sih-project.git
cd sih-project/repo

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run prediction via CLI contract (SIH Section 4.1)
python -c "
from model.predict import predict_image
res = predict_image('tests/sample.png')
print('Verdict:', res['verdict'])
print('Confidence:', res['confidence_percentage'], '%')
print('Attribution:', res['generator_attribution']['predicted_family'])
"

# 4. Start the FastAPI backend
uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API docs are available at `http://localhost:8000/docs`.

### Option 2: 1-Click Run in Google Colab
1. Click the **Open in Colab** badge at the top of this README.
2. Run all cells sequentially in `notebooks/1_SignalScope_Model_FineTuning_Colab.ipynb`.
3. The notebook automatically downloads the dataset, trains with GPU acceleration, runs Grad-CAM, and exports weights directly to your Google Drive!

---

## 💻 Running the Web Frontend

```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.  
To connect the frontend to a Google Colab GPU backend, create a `.env` file in `frontend/`:
```env
VITE_API_URL=https://your-ngrok-tunnel-url.ngrok-free.app
```

---

## 📁 Repository Structure

```
sih/
├── README.md                                  # Entry point & reproduction guide
├── report/
│   └── model_report.md                        # Official 1-page Model Report (SIH Section 7.3)
├── notebooks/                                 # Google Colab notebooks
│   ├── 1_SignalScope_Model_FineTuning_Colab.ipynb
│   └── 2_SignalScope_Colab_GPU_Backend.ipynb
├── repo/                                      # FastAPI Backend & Deep Learning Core
│   ├── model/                                 # SIH Model Section
│   │   ├── network.py                         # Dual-Stream ConvNeXt-Tiny + Forensic SRM
│   │   ├── forensic.py                        # Spatial Rich Model high-pass filters
│   │   ├── dataset.py                         # CIFAKE dataset loader with robust augmentations
│   │   ├── train.py                           # Two-phase differential fine-tuning script
│   │   ├── evaluate.py                        # SIH evaluation metrics reporter
│   │   ├── gradcam.py                         # PyTorch Grad-CAM explainability module
│   │   ├── predict.py                         # SIH Section 4.1 predict interface contract
│   │   └── weights/                           # Model checkpoints & calibration configs
│   ├── src/app/                               # FastAPI Application
│   │   ├── api/v1/                            # API route endpoints
│   │   └── services/                          # Business logic services
│   ├── requirements.txt                       # Backend dependencies
│   └── requirements-colab.txt                 # Google Colab optimized dependencies
└── frontend/                                  # React + Vite + TailwindCSS Frontend
```

---

## ⚖️ Ethics & Responsible AI Disclosure
SignalScope is built strictly as a **decision-support forensic system**. It communicates results using responsible likelihood terminology ("Likely AI-generated") and confidence intervals rather than absolute legal assertions. The system operates solely on image-level visual artifacts and is not intended for profiling identifiable individuals or adjudicating political claims.
