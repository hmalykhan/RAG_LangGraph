from dotenv import load_dotenv
import os
load_dotenv()
from groq import Groq
for m in sorted(Groq().models.list().data, key=lambda m: m.id):
    print(m.id)
