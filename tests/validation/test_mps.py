import torch

print(f"PyTorch version: {torch.__version__}")
print(f"MPS available: {torch.backends.mps.is_available()}")
print(f"MPS built: {torch.backends.mps.is_built()}")

if torch.backends.mps.is_available():
    device = torch.device("mps")
    x = torch.randn(100, 100).to(device)
    y = torch.randn(100, 100).to(device)
    z = x @ y
    print("MPS computation successful!")
    print(f"Result shape: {z.shape}")
    print(f"Device: {z.device}")
else:
    print("MPS is not available on this system")
