import uuid
import json
import os
import openai
from datetime import datetime

OPENAI_API_KEY = "api"  
openai.api_key = OPENAI_API_KEY

SAVE_PATH = "dataset/final_dataset.jsonl"

def generate_negotiation_example(topic="خرید دوچرخه"):
    prompt = f"""

موضوع: {topic}

خریدار: سلام، هنوز {topic} موجوده؟
فروشنده:"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=512
    )

    conversation = response['choices'][0]['message']['content'].strip()
    lines = [line.strip() for line in conversation.split("\n") if line.strip()]

    if len(lines) < 2:
        return None  

    instruction_line = lines[-2] if "خریدار:" in lines[-2] else "خریدار: " + lines[-2]
    output_line = lines[-1] if "فروشنده:" in lines[-1] else "فروشنده: " + lines[-1]

    instruction = instruction_line.split("خریدار:")[-1].strip()
    output = output_line.split("فروشنده:")[-1].strip()

    return {
        "instruction": instruction,
        "input": "",
        "output": output
    }

def save_to_jsonl(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

def generate_batch(n=10):
    for _ in range(n):
        sample = generate_negotiation_example()
        if sample:
            save_to_jsonl(sample, SAVE_PATH)

if __name__ == "__main__":
    generate_batch(n=10)
