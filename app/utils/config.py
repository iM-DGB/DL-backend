import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
SOLAR_API_KEY = os.getenv("SOLAR_API_KEY")
