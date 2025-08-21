import os
from transformers import AutoTokenizer, AutoModelForTokenClassification

MODEL_NAME = "yashpwr/resume-ner-bert-v2"
SAVE_PATH = "models"

os.makedirs(SAVE_PATH, exist_ok=True)

print(f"Downloading model '{MODEL_NAME}' to '{SAVE_PATH}'...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.save_pretrained(SAVE_PATH)

model = AutoModelForTokenClassification.from_pretrained(MODEL_NAME)
model.save_pretrained(SAVE_PATH)

print("Download complete. Model files are now in the 'models' folder.")