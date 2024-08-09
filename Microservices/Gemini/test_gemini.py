import google.generativeai as genai
import os

genai.configure(api_key="AIzaSyCmorRbRVa7whMTl7utEyQwo0xCXYWfXlo")

model = genai.GenerativeModel('gemini-1.5-flash')

response = model.generate_content("Write a story about an AI and magic in 20 words")
print(response.text)