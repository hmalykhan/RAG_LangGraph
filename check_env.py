from dotenv import load_dotenv
import os
load_dotenv()
for k in ["GROQ_API_KEY","GROQ_MODEL","ASTRA_DB_API_ENDPOINT",
          "ASTRA_DB_APPLICATION_TOKEN","ASTRA_DB_COLLECTION",
          "LANGSMITH_API_KEY","LANGSMITH_PROJECT","DATABASE_URL"]:
    print(k, "OK" if os.getenv(k) else "MISSING")
