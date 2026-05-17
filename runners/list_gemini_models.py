import os

from google import genai
from dotenv import load_dotenv

# =========================================================
# LOAD ENV VARIABLES
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

# =========================================================
# INIT CLIENT
# =========================================================

client = genai.Client(api_key=GEMINI_API_KEY)

# =========================================================
# LIST AVAILABLE MODELS
# =========================================================

print("\nAvailable Gemini Models:\n")

try:

    models = client.models.list()

    for model in models:

        print("=" * 80)

        print(f"Model Name: {model.name}")

        if hasattr(model, "display_name"):
            print(f"Display Name: {model.display_name}")

        if hasattr(model, "description"):
            print(f"Description: {model.description}")

        if hasattr(model, "supported_actions"):
            print(f"Supported Actions: {model.supported_actions}")

        print()

except Exception as e:

    print("ERROR:")
    print(str(e))