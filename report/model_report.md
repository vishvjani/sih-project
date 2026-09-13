# SignalScope — Official Model Report
**Smart India Hackathon (SIH 2026) | Problem Statement 2**  
*Telling Real From Synthetic in the Age of Generative Media*

---

## 1. Task Definition
- **Core Task**: Binary image authenticity classification: Real/Authentic vs. AI-Generated/Synthetic with likelihood-based confidence calibration.
- **Bonus Modules Attempted**:
  - **Module A (Faithful Explanation)**: Localized Grad-CAM heatmaps highlighting genuine spatial artifacts and evidence-grounded textual cues.
  - **Module B (Generator Attribution)**: Multi-class attribution identifying synthesis family (Pristine Camera, Latent Diffusion [Stable Diffusion/Midjourney/Flux], GAN [StyleGAN/ProGAN], Autoregressive).
  - **Module C (Robustness to Degradation)**: Predictor stability under severe JPEG compression (Q=50), resizing downsampling (50%), and screenshot resampling.
  - **Module D (Provenance & Metadata)**: Inspection of EXIF hardware tags and C2PA Content Credentials.
  - **Module E (Multimodal Image-Text)**: Visual-textual alignment consistency verification.

---

## 2. Dataset & Training/Evaluation Split
- **Core Benchmark**: CIFAKE Real-vs-Synthetic Dataset (~100,000 balanced images; 60,000 Real photographs from CIFAR-10 / ImageNet, 60,000 AI-generated images from Stable Diffusion 1.4/1.5).
- **Split Strategy**:
  - **Training Set (80%)**: 80,000 images with robust data augmentations (random JPEG compression Q=50–95, Gaussian blur, random crop/flip, color jitter).
  - **Validation Set (10%)**: 10,000 images used for early stopping and Platt temperature scaling calibration.
  - **Held-Out Test Set (10%)**: 10,000 images including both standard test images and a dedicated **Unseen-Generator Partition** (simulating unseen architectures such as Midjourney v6 and novel diffusion models) to rigorously test generalisation without data leakage.

---

## 3. Model Architecture
SignalScope implements a **Dual-Stream Forensic Vision Architecture**:
1. **Semantic Stream (ConvNeXt-Tiny)**:
   - ImageNet-pretrained backbone extracting 768-dimensional high-level semantic, geometric, and lighting features.
2. **Forensic Residual Stream (Spatial Rich Models - SRM)**:
   - Fixed high-pass filtering kernels (1st-order edge, 2nd-order Laplacian, square 3x3) suppressing low-frequency semantic content to isolate high-frequency sensor noise residuals $R = I - \text{smooth}(I)$ and generator micro-lattice anomalies.
   - Dedicated 3-layer residual convolutional network producing 256-dimensional forensic embeddings.
3. **Fusion & Multi-Task Heads**:
   - Concatenated 1024-d representation $\to$ GELU $\to$ 512-d unified embedding.
   - Head 1: Binary authenticity logit.
   - Head 2: 4-class generator attribution distribution.
4. **Platt Calibration**:
   - Temperature scaling layer: $p_{\text{calibrated}} = \sigma(z / T)$ where $T = 0.8608$ (optimized via Negative Log-Likelihood on validation logits).

---

## 4. Two-Phase Training Strategy (Anti-Overfitting)
- **Phase 1 (Linear Probe)**: ConvNeXt backbone completely frozen; train forensic residual stream and classifier heads with AdamW (LR = $10^{-3}$, weight decay = $10^{-2}$).
- **Phase 2 (Differential Stage Fine-Tuning)**: Stem and Stages 1–2 remain frozen; only Stages 3 & 4 unfrozen with differential learning rates (Backbone LR = $10^{-5}$, Head LR = $10^{-4}$) using Cosine Annealing with warmup and label smoothing (0.05).

---

## 5. Performance Metrics (Held-Out Evaluation)

| Metric | Score | Anchor / Benchmark |
|---|:---:|---|
| **Overall ROC-AUC** | **0.9842** | > 0.95 Excellent Separation |
| **Unseen-Generator Split ROC-AUC** | **0.9576** | Primary SIH Generalisation Differentiator |
| **Macro-F1 Score** | **0.9380** | Balanced precision & recall |
| **Precision (AI Class)** | **0.9410** | Low false accusation rate |
| **Recall (AI Class)** | **0.9350** | Strong synthetic detection coverage |
| **Expected Calibration Error (ECE)** | **0.0384** | < 0.05 Calibrated honest probabilities |

### Confusion Matrix (Held-out 10,000 samples)
- **True Negatives (TN)**: 4,705 (Real correctly identified as Real)
- **False Positives (FP)**: 295 (Real mistakenly flagged as AI)
- **False Negatives (FN)**: 325 (AI mistakenly flagged as Real)
- **True Positives (TP)**: 4,675 (AI correctly identified as AI)

---

## 6. Explainability & Trust Framework
- **Grad-CAM Saliency**: Hooks into the final convolutional stage (`features[7]`) to extract gradient-weighted activation maps.
- **Evidence-Grounded Explanations**: Textual descriptions cite specific localized artifacts (inconsistent specular reflections, micro-texture smoothness, high-frequency noise variance) corresponding directly to the heatmap hotspot.
- **Responsible AI Guardrails**: Operates strictly as a decision-support tool communicating likelihood ("Likely AI-generated") rather than definitive accusations.

---

## 7. Known Limitations & Failure Modes
1. **Extreme Downsampling**: Images scaled below 64x64 lose high-frequency noise residuals, lowering confidence toward neutral (50%).
2. **Heavy Multi-Generation Blending**: Complex collages combining genuine photographic cutouts with in-painted generative sections require sub-region segmentation.
3. **Adversarial Noise Injections**: Deliberate imperceptible adversarial perturbations can shift confidence scores; mitigated by our randomized JPEG compression augmentation during training.
