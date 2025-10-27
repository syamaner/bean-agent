#!/usr/bin/env python3
"""
Quick test for AST model loading and forward pass on MPS (if available).
"""

import torch

from ast_model import FirstCrackClassifier, ModelInitConfig


def main():
    print("🚀 Testing AST model loading and forward pass")
    device = (
        "mps" if torch.backends.mps.is_available() else
        ("cuda" if torch.cuda.is_available() else "cpu")
    )
    print(f"Device: {device}")

    # Init model
    clf = FirstCrackClassifier(ModelInitConfig(device=device))
    print("✅ Model initialized")

    # Create dummy audio batch (batch=2, 10s at 16kHz)
    sr = clf.sampling_rate
    samples = sr * 10
    dummy = torch.randn(2, samples)

    # Forward
    with torch.inference_mode():
        logits = clf(dummy)
        probs = torch.softmax(logits, dim=-1)
    print(f"Logits shape: {logits.shape}")
    print(f"Probs: {probs}")

    print("\n✅ Forward pass successful")


if __name__ == "__main__":
    main()
