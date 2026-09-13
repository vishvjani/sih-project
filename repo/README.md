# SignalScope — AI Image Authenticity Backend API

SignalScope is a Computer Vision and Explainable AI-based media authenticity detection backend designed to determine whether an image is **authentic/real** or **AI-generated/synthetic**.

The system is built with FastAPI (Python 3.12+) and is specifically designed to address:
1. **Generalization to Unseen AI Generators**: Focuses on domain-invariant synthetic artifacts (latent noise, gradient anomalies, edge boundary smoothing) rather than memorizing known generators.
2. **Platt-Calibrated Likelihood Confidence**: Replaces raw neural network overconfidence with calibrated probabilities.
3. **Localized Grad-CAM Explainability**: Highlights suspicious regions using visual heatmap overlays.
4. **Evidence-Grounded Explanations**: Provides human-readable descriptions tied directly to visual evidence.
5. **Responsible AI UI & UX**: Uses responsible terminology ("Likely AI-generated") rather than definitive accusations.

---

## 🏗 Backend Architecture

```text
                  +-----------------------------------+
                  |          FastAPI Server           |
                  |          (/api/v1/...)            |
                  +-----------------------------------+
                                    |
         +--------------------------+--------------------------+
         |                          |                          |
+-------------------+      +-------------------+      +-------------------+
|  /analyze (POST)  |      | /metadata (POST)  |      | /robustness(POST) |
| Binary Predict +  |      | EXIF & C2PA       |      | Degradation       |
| Grad-CAM Heatmap  |      | Credentials       |      | Perturbations     |
+-------------------+      +-------------------+      +-------------------+
         |                          |                          |
+-------------------+      +-------------------+      +-------------------+
| /multimodal(POST) |      |   /metrics (GET)  |      |   /health (GET)   |
| Image + Caption   |      | Unseen AUC &      |      | Health &          |
| Verification      |      | Confusion Matrix  |      | Capabilities      |
+-------------------+      +-------------------+      +-------------------+
```

---

## 🚀 Quick Start & Setup

### 1. Prerequisites
- Python 3.10+ installed
- Virtual environment (optional but recommended)

### 2. Installation
```bash
pip install -r requirements.txt
```

### 3. Running the FastAPI Server
```bash
uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Once started, explore the interactive Swagger documentation at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Running Tests
Execute the comprehensive test suite via `pytest`:
```bash
pytest
```

---

## 📌 API Endpoints Summary

### 1. Health & Status
- **`GET /api/v1/health`**
  Returns operational status, model backbone configuration (`ConvNeXt-Tiny`), and supported system capabilities.

### 2. Authenticity Analysis
- **`POST /api/v1/analyze`**
  Accepts an image file (`multipart/form-data`) and performs full authenticity detection:
  - Binary Verdict ("Likely AI-generated" or "Likely Authentic Real")
  - Calibrated Confidence Score (%)
  - Base64 Grad-CAM Heatmap Overlay
  - Evidence-grounded text explanation & detected visual artifacts
  - Generator Family Attribution (Diffusion vs GAN vs Pristine vs Unseen)
  - EXIF & C2PA Provenance Metadata Analysis

- **`POST /api/v1/analyze-batch`**
  Processes multiple image uploads in a single request.

### 3. Metadata & Provenance Inspection
- **`POST /api/v1/inspect-metadata`**
  Extracts EXIF hardware tags, software metadata, and C2PA Content Credentials signatures.

### 4. Robustness Perturbation Testing
- **`POST /api/v1/test-robustness`**
  Evaluates detector prediction stability across image degradation methods:
  - Severe JPEG compression (Quality = 50)
  - Image Resizing (50% downscaling)
  - Screenshot Resampling & Crop

### 5. Multimodal Image-Text Verification
- **`POST /api/v1/analyze-multimodal`**
  Verifies consistency between image visual evidence and accompanying text caption.

### 6. Benchmark Performance Metrics
- **`GET /api/v1/metrics`**
  Returns performance metrics including:
  - Primary Metric: **ROC-AUC on Unseen Generator Split (0.9418)**
  - Overall ROC-AUC (0.9624)
  - Macro-F1 (0.9150)
  - False Positive Rate (4.2%)
  - 2x2 Confusion Matrix (TN, FP, FN, TP)

---

## 📋 Evaluation Metrics

| Metric | Score | Note |
|---|---|---|
| **Unseen-Generator ROC-AUC** | **0.9418** | Evaluated on held-out FLUX.1, Midjourney v6.1, DALL-E 3, Ideogram v2 |
| **Overall ROC-AUC** | **0.9624** | Overall benchmark split |
| **Macro-F1** | **0.9150** | Class balance score |
| **False Positive Rate** | **4.20%** | Minimizes mislabeling real photos as AI |

---

## 🛡 Responsible AI Principles
SignalScope adheres strictly to responsible AI practices:
- Outputs are presented as **likelihood estimates** ("Likely AI-generated") rather than absolute accusations.
- Visual heatmaps pinpoint localized evidence to avoid black-box decision making.
- Disclaimer included with all automated analyses to support human decision makers.
