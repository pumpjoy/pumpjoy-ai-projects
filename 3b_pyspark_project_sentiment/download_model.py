# download_model.py
from transformers import pipeline

print("Downloading model... this may take a minute.")
# This caches the model in ~/.cache/huggingface
model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
print("Model downloaded successfully!")