import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # Loads your .env file

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

models = client.models.list()
print("Available Models:")
for model in models.data:
    print("•", model.id)
