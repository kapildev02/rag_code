import torch
from sentence_transformers import SentenceTransformer, CrossEncoder

print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Device Name: {torch.cuda.get_device_name(0)}")
    print(f"Device Count: {torch.cuda.device_count()}")

# Test models on GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"\nLoading models on {device.upper()}...")

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device=device)
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", device=device)

print("✅ Models loaded successfully on GPU!")