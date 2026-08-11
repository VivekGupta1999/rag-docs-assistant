import chromadb


chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection(name="fastapi_docs")

results = collection.query(
    query_texts=["What is Fast API cloud?"],
    n_results=3,
    where={"doc_type" : "guide"},
)

print(results)