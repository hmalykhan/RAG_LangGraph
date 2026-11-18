from backend.vector_store import vstore
for d in vstore.similarity_search("Can I return a damaged laptop after 10 days?", k=3):
    print(d.metadata["source"], "|", d.page_content[:100].replace("\n", " "))
