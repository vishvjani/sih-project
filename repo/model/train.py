"""
SignalScope Two-Phase Fine-Tuning CLI Script
Dual-Stream ConvNeXt-Tiny + Forensic SRM Residuals.

Phases:
  Phase 1 (Epochs 1-3): Backbone Frozen (Linear probe on Forensic Stream & Heads)
  Phase 2 (Epochs 4-10): Unfreeze Stage 3 & 4 with Differential Learning Rates
  Phase 3: Platt Temperature Calibration on validation logits

Engineered for Google Colab GPU execution and local training.
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR

from .network import SignalScopeModel
from .dataset import load_dataset, create_dataset_from_directory


def fit_temperature(model: SignalScopeModel, val_loader, device: str = "cuda") -> float:
    """
    Fits optimal Platt temperature scaling parameter T on validation set logits
    using Negative Log Likelihood (NLL) optimization.
    """
    print("\n[Platt Calibration] Fitting optimal temperature parameter T on validation set...")
    model.eval()
    logits_list = []
    labels_list = []

    with torch.no_grad():
        for images, labels, _ in val_loader:
            images = images.to(device)
            binary_logits, _ = model(images)
            logits_list.append(binary_logits.squeeze(-1).cpu())
            labels_list.append(labels.cpu())

    if not logits_list:
        return 1.15

    logits = torch.cat(logits_list).to(device)
    labels = torch.cat(labels_list).to(device)

    # Optimization parameter T (initialized to 1.0)
    temperature = nn.Parameter(torch.ones(1, device=device))
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.LBFGS([temperature], lr=0.01, max_iter=50)

    def eval_loss():
        optimizer.zero_grad()
        loss = criterion(logits / temperature.clamp(min=0.05), labels)
        loss.backward()
        return loss

    try:
        optimizer.step(eval_loss)
        optimal_temp = float(temperature.item())
        optimal_temp = max(0.1, min(5.0, optimal_temp))
    except Exception as e:
        print(f"Calibration optimizer warning: {e}. Defaulting to T=1.15")
        optimal_temp = 1.15

    print(f"[Platt Calibration] Optimal Temperature T fitted: {optimal_temp:.4f}")
    return optimal_temp


def train_epoch(model, loader, optimizer, criterion_bin, criterion_attr, device, scaler, use_amp):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels, attr_labels in loader:
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)
        attr_labels = attr_labels.to(device, non_blocking=True)

        optimizer.zero_grad()
        with torch.amp.autocast(device_type=device.type, enabled=use_amp):
            bin_logits, attr_logits = model(images)
            # Apply label smoothing (0.05) to targets: [0 -> 0.05, 1 -> 0.95]
            smoothed_labels = labels * 0.90 + 0.05
            loss_bin = criterion_bin(bin_logits.squeeze(-1), smoothed_labels)
            loss_attr = criterion_attr(attr_logits, attr_labels)
            total_loss = loss_bin + 0.25 * loss_attr

        if use_amp:
            scaler.scale(total_loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            total_loss.backward()
            optimizer.step()

        running_loss += total_loss.item() * images.size(0)
        preds = (torch.sigmoid(bin_logits.squeeze(-1)) >= 0.5).float()
        correct += (preds == labels).sum().item()
        total += labels.size(0)

    avg_loss = running_loss / max(1, total)
    acc = correct / max(1, total)
    return avg_loss, acc


def validate(model, loader, criterion_bin, criterion_attr, device, use_amp):
    model.eval()
    val_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels, attr_labels in loader:
            images = images.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)
            attr_labels = attr_labels.to(device, non_blocking=True)

            with torch.amp.autocast(device_type=device.type, enabled=use_amp):
                bin_logits, attr_logits = model(images)
                loss_bin = criterion_bin(bin_logits.squeeze(-1), labels)
                loss_attr = criterion_attr(attr_logits, attr_labels)
                total_loss = loss_bin + 0.25 * loss_attr

            val_loss += total_loss.item() * images.size(0)
            preds = (torch.sigmoid(bin_logits.squeeze(-1)) >= 0.5).float()
            correct += (preds == labels).sum().item()
            total += labels.size(0)

    avg_loss = val_loss / max(1, total)
    acc = correct / max(1, total)
    return avg_loss, acc


def run_training(args):
    device = torch.device("cuda" if torch.cuda.is_available() and args.device == "cuda" else "cpu")
    print("=" * 60)
    print("       SIGNALSCOPE TWO-PHASE FINE-TUNING PIPELINE")
    print("=" * 60)
    print(f"Device: {device} | GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
    print(f"Data Dir: {args.data_dir}")
    print(f"Phase 1 Epochs (Frozen): {args.phase1_epochs} | Phase 2 Epochs (Fine-Tuning): {args.phase2_epochs}")
    print(f"Batch Size: {args.batch_size} | Head LR: {args.lr_head} | Backbone LR: {args.lr_backbone}")
    print("=" * 60)

    save_path = Path(args.save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    # 1. Dataset Loading (Manifest or Directory)
    if not os.path.exists(args.data_dir):
        print(f"Notice: Data directory {args.data_dir} not found. Synthesizing dummy dataset for pipeline verification...")
        dummy_dir = save_path / "dummy_data"
        (dummy_dir / "REAL").mkdir(parents=True, exist_ok=True)
        (dummy_dir / "FAKE").mkdir(parents=True, exist_ok=True)
        from PIL import Image
        for i in range(12):
            Image.new("RGB", (224, 224), (200, 100, 50)).save(dummy_dir / "REAL" / f"real_{i}.jpg")
            Image.new("RGB", (224, 224), (50, 100, 200)).save(dummy_dir / "FAKE" / f"fake_{i}.jpg")
        args.data_dir = str(dummy_dir)

    train_ds, train_loader = load_dataset(args.data_dir, split="train", batch_size=args.batch_size)
    val_ds, val_loader = load_dataset(args.data_dir, split="val" if (Path(args.data_dir)/"dataset_manifest.csv").exists() else "test", batch_size=args.batch_size)

    # Check for held-out unseen test split
    unseen_loader = None
    try:
        if (Path(args.data_dir) / "dataset_manifest.csv").exists():
            unseen_ds, unseen_loader = load_dataset(args.data_dir, split="test_unseen", batch_size=args.batch_size)
            if len(unseen_ds) > 0:
                print(f"Loaded {len(unseen_ds)} held-out UNSEEN generator test samples for real-time generalization tracking.")
            else:
                unseen_loader = None
    except Exception:
        unseen_loader = None

    print(f"Successfully loaded {len(train_ds)} train samples and {len(val_ds)} validation samples.")

    # 2. Build Dual-Stream Model
    model = SignalScopeModel(pretrained=True).to(device)
    criterion_bin = nn.BCEWithLogitsLoss()
    criterion_attr = nn.CrossEntropyLoss()

    use_amp = (device.type == "cuda")
    scaler = torch.amp.GradScaler('cuda', enabled=use_amp)

    best_val_loss = float("inf")
    history = {"phase1_train": [], "phase1_val": [], "phase2_train": [], "phase2_val": [], "unseen_test": []}

    # -------------------------------------------------------------
    # PHASE 1: LINEAR PROBE (Frozen Backbone)
    # -------------------------------------------------------------
    if args.phase1_epochs > 0:
        print("\n>>> STARTING PHASE 1: Linear Probe & Forensic Adaptation (Backbone FROZEN) <<<")
        model.freeze_backbone()
        optimizer_p1 = optim.AdamW(
            filter(lambda p: p.requires_grad, model.parameters()),
            lr=args.lr_head,
            weight_decay=1e-2
        )
        scheduler_p1 = CosineAnnealingLR(optimizer_p1, T_max=args.phase1_epochs, eta_min=1e-5)

        for ep in range(1, args.phase1_epochs + 1):
            t0 = time.time()
            t_loss, t_acc = train_epoch(model, train_loader, optimizer_p1, criterion_bin, criterion_attr, device, scaler, use_amp)
            v_loss, v_acc = validate(model, val_loader, criterion_bin, criterion_attr, device, use_amp)
            
            u_acc_str = ""
            if unseen_loader:
                _, u_acc = validate(model, unseen_loader, criterion_bin, criterion_attr, device, use_amp)
                history["unseen_test"].append({"epoch": ep, "acc": u_acc})
                u_acc_str = f" | Unseen Gen Acc: {u_acc:.3%}"

            scheduler_p1.step()
            el = time.time() - t0

            history["phase1_train"].append({"epoch": ep, "loss": t_loss, "acc": t_acc})
            history["phase1_val"].append({"epoch": ep, "loss": v_loss, "acc": v_acc})
            print(f"[Phase 1] Epoch {ep}/{args.phase1_epochs} ({el:.1f}s) - Train Loss: {t_loss:.4f}, Acc: {t_acc:.3%} | Val Loss: {v_loss:.4f}, Acc: {v_acc:.3%}{u_acc_str}")

            if v_loss < best_val_loss:
                best_val_loss = v_loss
                torch.save({"model_state_dict": model.state_dict(), "epoch": ep, "val_loss": v_loss}, save_path / "signalscope_convnext_tiny.pth")

    # -------------------------------------------------------------
    # PHASE 2: DIFFERENTIAL FINE-TUNING (Unfreeze Stages 3 & 4)
    # -------------------------------------------------------------
    if args.phase2_epochs > 0:
        print("\n>>> STARTING PHASE 2: Differential Stage Fine-Tuning (Stages 3-4 UNFROZEN) <<<")
        model.unfreeze_later_stages()

        # Differential Parameter Groups: Small LR for backbone, standard LR for head
        backbone_params = []
        head_params = []
        for name, param in model.named_parameters():
            if not param.requires_grad:
                continue
            if "features" in name:
                backbone_params.append(param)
            else:
                head_params.append(param)

        param_groups = [
            {"params": backbone_params, "lr": args.lr_backbone},
            {"params": head_params, "lr": args.lr_head * 0.5}
        ]

        optimizer_p2 = optim.AdamW(param_groups, weight_decay=1e-2)
        scheduler_p2 = CosineAnnealingLR(optimizer_p2, T_max=args.phase2_epochs, eta_min=1e-6)

        for ep in range(1, args.phase2_epochs + 1):
            t0 = time.time()
            t_loss, t_acc = train_epoch(model, train_loader, optimizer_p2, criterion_bin, criterion_attr, device, scaler, use_amp)
            v_loss, v_acc = validate(model, val_loader, criterion_bin, criterion_attr, device, use_amp)
            
            u_acc_str = ""
            if unseen_loader:
                _, u_acc = validate(model, unseen_loader, criterion_bin, criterion_attr, device, use_amp)
                history["unseen_test"].append({"epoch": ep, "acc": u_acc})
                u_acc_str = f" | Unseen Gen Acc: {u_acc:.3%}"

            scheduler_p2.step()
            el = time.time() - t0

            history["phase2_train"].append({"epoch": ep, "loss": t_loss, "acc": t_acc})
            history["phase2_val"].append({"epoch": ep, "loss": v_loss, "acc": v_acc})
            print(f"[Phase 2] Epoch {ep}/{args.phase2_epochs} ({el:.1f}s) - Train Loss: {t_loss:.4f}, Acc: {t_acc:.3%} | Val Loss: {v_loss:.4f}, Acc: {v_acc:.3%}{u_acc_str}")

            if v_loss < best_val_loss:
                best_val_loss = v_loss
                torch.save({"model_state_dict": model.state_dict(), "epoch": ep, "val_loss": v_loss}, save_path / "signalscope_convnext_tiny.pth")

    # -------------------------------------------------------------
    # PHASE 3: PLATT TEMPERATURE CALIBRATION
    # -------------------------------------------------------------
    best_weights_path = save_path / "signalscope_convnext_tiny.pth"
    if best_weights_path.exists():
        ckpt = torch.load(best_weights_path, map_location=device)
        model.load_state_dict(ckpt["model_state_dict"])

    optimal_t = fit_temperature(model, val_loader, device=device.type)
    model.set_temperature(optimal_t)

    # Save final deployable model
    torch.save({
        "model_state_dict": model.state_dict(),
        "temperature": optimal_t,
        "backbone": "ConvNeXt-Tiny + Forensic-SRM",
        "best_val_loss": best_val_loss,
        "history": history
    }, save_path / "signalscope_convnext_tiny.pth")

    calib_meta = {
        "model": "SignalScope Dual-Stream ConvNeXt-Tiny",
        "calibration_temperature": round(optimal_t, 4),
        "calibration_method": "Platt Scaling (Temperature Scaling)",
        "best_val_loss": round(best_val_loss, 4),
        "total_parameters": sum(p.numel() for p in model.parameters()),
        "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad)
    }

    with open(save_path / "calibration_config.json", "w") as f:
        json.dump(calib_meta, f, indent=2)

    with open(save_path / "training_history.json", "w") as f:
        json.dump(history, f, indent=2)

    print("\n" + "=" * 60)
    print("       TRAINING & CALIBRATION COMPLETE!")
    print(f"Model Checkpoint: {save_path / 'signalscope_convnext_tiny.pth'}")
    print(f"Calibration Config: {save_path / 'calibration_config.json'}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="SignalScope Two-Phase Model Fine-Tuning")
    parser.add_argument("--data-dir", type=str, default="./data/cifake", help="Path to dataset root")
    parser.add_argument("--save-dir", type=str, default="./repo/model/weights", help="Directory to store checkpoints")
    parser.add_argument("--phase1-epochs", type=int, default=2, help="Epochs for Phase 1 (Frozen backbone)")
    parser.add_argument("--phase2-epochs", type=int, default=3, help="Epochs for Phase 2 (Fine-tuning)")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr-head", type=float, default=1e-3, help="Learning rate for heads and forensic stream")
    parser.add_argument("--lr-backbone", type=float, default=1e-5, help="Learning rate for ConvNeXt backbone")
    parser.add_argument("--device", type=str, default="cuda", choices=["cuda", "cpu"], help="Compute device")
    args = parser.parse_args()
    run_training(args)


if __name__ == "__main__":
    main()
