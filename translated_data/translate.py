

import json
from langchain.chat_models import ChatOllama
from langchain.schema import SystemMessage, HumanMessage
from tqdm import tqdm
import time

model = ChatOllama(
    model="llama3.1",
    temperature=0.6
)

def translate_text(text):
    if not text.strip():
        return text
    try:
        messages = [
            SystemMessage(content="You are a professional Persian translator."),
            HumanMessage(content=f"Translate the following into Persian:\n{text}")
        ]
        response = model.invoke(messages)
        return response.content.strip()
    except Exception as e:
        print(" Error translating:", e)
        return text

with open("C:/python/langchain projects/roshd\data/translated_data/craigslist_formatted.json", "r", encoding="utf-8") as f:
    dataset = json.load(f)

sample_size = max(1, int(len(dataset) * 0.001))
subset = dataset[:sample_size]

translated_dataset = []
for item in tqdm(subset, desc="Translating 0.1% of data..."):
    translated_item = {
        "instruction": translate_text(item.get("instruction", "")),
        "input": item.get("input", ""),
        "output": translate_text(item.get("output", ""))
    }
    translated_dataset.append(translated_item)
    time.sleep(0.5)

with open("translated_sample.json", "w", encoding="utf-8") as f:
    json.dump(translated_dataset, f, ensure_ascii=False, indent=2)

print(" ترجمه 1٪ از دیتا انجام شد و در 'translated_sample.json' ذخیره شد.")
