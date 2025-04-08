import json

input_path = 'dataset.json'
output_path = 'converted_dataset.json'

with open(input_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

converted = []

for chat_id, messages in data.items():
    for i in range(len(messages) - 1):
        q = messages[i]
        a = messages[i + 1]

        if q["sender"] != a["sender"]:
            question = q["text"].strip()
            answer = a["text"].strip()

            converted.append({
                "instruction": question,
                "input": "",
                "output": answer
            })

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(converted, f, ensure_ascii=False, indent=2)

