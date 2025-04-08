import json
import re

input_path = 'converted_dataset.json'
output_path = 'cleaned_dataset.json'

with open(input_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

seen = set()

def clean_text(text):
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'[^\w\s\u0600-\u06FF]', '', text)
    return text

cleaned = []
for item in data:
    q = clean_text(item['instruction'])
    a = clean_text(item['output'])

    if len(q) < 3 or len(a) < 3:
        continue
    if len(q.split()) < 2 or len(a.split()) < 2:
        continue
    if (q, a) in seen:
        continue

    seen.add((q, a))
    cleaned.append({
        "instruction": q,
        "input": "",
        "output": a
    })

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(cleaned, f, ensure_ascii=False, indent=2)

