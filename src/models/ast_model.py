from __future__ import annotations
"""
AST model wrapper for binary first-crack detection.

Uses Hugging Face Audio Spectrogram Transformer (AST) for audio classification.
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import torch
from transformers import ASTFeatureExtractor, ASTForAudioClassification


DEFAULT_MODEL_NAME = "MIT/ast-finetuned-audioset-10-10-0.4593"


@dataclass
class ModelInitConfig:
    model_name: str = DEFAULT_MODEL_NAME
    num_labels: int = 2
    device: Optional[str] = None  # "mps", "cuda", or "cpu". If None, auto-detect.


class FirstCrackClassifier(torch.nn.Module):
    def __init__(self, config: ModelInitConfig = ModelInitConfig()):
        super().__init__()
        self.feature_extractor = ASTFeatureExtractor.from_pretrained(config.model_name)
        self.model = ASTForAudioClassification.from_pretrained(
            config.model_name,
            num_labels=config.num_labels,
            ignore_mismatched_sizes=True,
        )

        # Device selection
        if config.device:
            device = torch.device(config.device)
        else:
            if torch.backends.mps.is_available():
                device = torch.device("mps")
            elif torch.cuda.is_available():
                device = torch.device("cuda")
            else:
                device = torch.device("cpu")
        self.device = device
        self.to(self.device)

        # Cache common params
        self.sampling_rate = getattr(self.feature_extractor, "sampling_rate", 16000)

    def forward(self, audio_batch: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            audio_batch: Tensor of shape (batch, samples) at self.sampling_rate
        Returns:
            logits: Tensor of shape (batch, num_labels)
        """
        if audio_batch.dim() == 1:
            audio_batch = audio_batch.unsqueeze(0)

        # Move to CPU for feature extraction if necessary (some HF processors run on CPU)
        # Then move features to target device
        audio_list: List[List[float]] = [x.detach().cpu().float().tolist() for x in audio_batch]

        inputs: Dict[str, Any] = self.feature_extractor(
            audio_list,
            sampling_rate=self.sampling_rate,
            return_tensors="pt",
        )

        # ASTFeatureExtractor returns "input_features"
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        outputs = self.model(**inputs)
        return outputs.logits

    @torch.inference_mode()
    def predict_proba(self, audio_batch: torch.Tensor) -> torch.Tensor:
        logits = self.forward(audio_batch)
        return torch.softmax(logits, dim=-1)

    @torch.inference_mode()
    def predict(self, audio_batch: torch.Tensor) -> torch.Tensor:
        probs = self.predict_proba(audio_batch)
        return torch.argmax(probs, dim=-1)
