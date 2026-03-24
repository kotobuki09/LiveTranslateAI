"""Diagnostic: check which Gemini models support the Live API."""
import os
os.environ.pop("GOOGLE_API_KEY", None)   # force-remove system key before SDK loads

from dotenv import load_dotenv
load_dotenv()

from google import genai

api_key = os.getenv("GEMINI_API_KEY", "")
print(f"Using key: {api_key[:8]}...{api_key[-4:]}")

client = genai.Client(api_key=api_key)

print("\nAll available models (filtering for 'flash' / 'live' / 'exp'):\n")
for m in client.models.list():
    name = m.name
    if any(k in name.lower() for k in ("flash", "live", "exp", "2.0", "gemini")):
        methods = getattr(m, "supported_generation_methods", [])
        print(f"  {name}")
        if methods:
            print(f"    supported methods: {methods}")
