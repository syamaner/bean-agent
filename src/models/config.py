TRAINING_CONFIG = {
    "batch_size": 8,
    "learning_rate": 5e-5,
    "num_epochs": 20,
    "warmup_steps": 100,
    "weight_decay": 0.01,
    "max_grad_norm": 1.0,
    "device": "mps",
    "seed": 42,
    "sample_rate": 16000,
    "target_length_sec": 10,
    # Cropping strategies for windows longer than target_length_sec
    # train_crop_mode: random crops improve robustness
    # eval_crop_mode: center crop for determinism
    "train_crop_mode": "random",
    "eval_crop_mode": "center",
    # Inference overlap for sliding windows (70% = 3s hop with 10s windows)
    "overlap": 0.7,
}
