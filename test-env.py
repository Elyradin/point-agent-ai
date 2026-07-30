import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print("✅ API Key ditemukan!")
    print(f"📌 Key: {api_key[:10]}...{api_key[-5:]}")
else:
    print("❌ API Key tidak ditemukan. Cek file .env")