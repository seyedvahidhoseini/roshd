from selenium import webdriver
from selenium.webdriver.common.by import By
import json
import threading
import keyboard  
import time
from selenium.webdriver.common.keys import Keys


USERNAME = "09217395654"
PASSWORD = "asgari@5654"


login_url = "https://www.karlancer.com/login"
messages_url = "https://www.karlancer.com/panel/messages"
#https://parscoders.com/

driver = webdriver.Chrome()
driver.get(login_url)

time.sleep(2)

username_input = driver.find_element(By.NAME, "username")
password_input = driver.find_element(By.NAME, "password")

username_input.send_keys(USERNAME)
password_input.send_keys(PASSWORD)

password_input.send_keys(Keys.RETURN)

time.sleep(2)

driver.get(messages_url)
time.sleep(20)
chat_container = driver.find_element(By.CSS_SELECTOR, 'div[type="chat"]')
all_chats = chat_container.find_elements(By.XPATH, './*')  
print(len(all_chats))
print(all_chats)

print(f"all chats: {len(all_chats)}")

all_chats_data = {}

for index, chat in enumerate(all_chats):
    try:
        chat.click()
        time.sleep(2)

        reflect_div = driver.find_element(By.CSS_SELECTOR, 'div.reflect')
        message_blocks = reflect_div.find_elements(By.CSS_SELECTOR, 'div.fs-13.mb-10.transition-1')

        if message_blocks:
            message_blocks.pop(0)  

        all_messages = []
        for msg_block in message_blocks:
            try:
                msg_text_divs = msg_block.find_elements(By.XPATH, './/div[contains(@class, "p-3")]')
                for div in msg_text_divs:
                    class_attr = div.get_attribute("class")
                    message_only_divs = div.find_elements(By.XPATH, './div[1]')
                    if message_only_divs:
                        text = message_only_divs[0].text.strip()
                        if text:
                            sender = "من" if "bg-default" in class_attr and "text-mobile-white" in class_attr else "مشتری"
                            all_messages.append({
                                "sender": sender,
                                "text": text
                            })
            except Exception as e:
                print(f"⚠️ خطا در استخراج پیام: {e}")

        all_chats_data[f'chat_{index}'] = all_messages

    except Exception as e:
        print(f"Error chat {index + 1}: {e}")

with open("dataset.json", "w", encoding="utf-8") as f:
    json.dump(all_chats_data, f, ensure_ascii=False, indent=2)

print("JSON saved: dataset.json")