import json
import re

with open('C:/python/langchain projects/roshd\data/translated_data/translated_sample.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

def keep_before_newline(text):
    return re.split(r'\n', text, maxsplit=1)[0] if isinstance(text, str) else text

for item in data:
    for key in ['instruction', 'input', 'output']:
        if key in item:
            item[key] = keep_before_newline(item[key])

with open('test_cleaned.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
