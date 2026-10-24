
import os
from dotenv import load_dotenv
from google import genai

# Load the API key from the .env file
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY was not found in the .env file.")
else:
    try:
        client = genai.Client(api_key=api_key)

        print("Connecting to Gemini AI...")

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents="Explain artificial intelligence in two simple sentences."
        )

        print("\nGemini responded successfully!")
        print(response.text)

    except Exception as error:
         print("\nGemini connection failed.")
         print("Error type:", type(error).__name__)
         print("Error details:", str(error))
