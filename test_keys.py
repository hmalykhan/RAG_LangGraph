from dotenv import load_dotenv
import os
load_dotenv()

# Groq
from langchain_groq import ChatGroq
r = ChatGroq(model=os.getenv("GROQ_MODEL")).invoke("Say hi in 3 words")
print("GROQ OK:", r.content)

# Astra DB
from astrapy import DataAPIClient
db = DataAPIClient(os.getenv("ASTRA_DB_APPLICATION_TOKEN")).get_database(
    os.getenv("ASTRA_DB_API_ENDPOINT"))
print("ASTRA OK:", db.list_collection_names())

# LangSmith
from langsmith import Client
print("LANGSMITH OK:", len(list(Client().list_projects(limit=1))) >= 0)
