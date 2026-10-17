import re
import chromadb
from rank_bm25 import BM25Okapi

#connect to the database

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection(name="fastapi_docs")

#tokenizer

TOKEN = re.compile(r"[a-z0-9_]+")

STOPWORDS = {
    "how", "do", "i", "a", "an", "the", "to", "in", "of", "my", "and", "or", "is",
    "it", "for", "on", "with", "can", "what", "when", "use", "using",
    "fastapi", "app", "api",
}


def tokenize(text):
    return [t for t in TOKEN.findall(text.lower()) if t not in STOPWORDS]


#load all guide chunk once and build the BM25 index

data = collection.get(where={"doc_type":"guide"}, include =["documents","metadatas"])

IDS = data["ids"]
DOCS = data["documents"]
SOURCES = [m["source"] for m in data["metadatas"]]


ID_TO_INDEX = {doc_id:i for i , doc_id in enumerate(IDS)}


bm25 = BM25Okapi([tokenize(doc) for doc in DOCS])

#keyword search: top n chunk ids from chromaDB
def bm25_search(question,n=20):
    scores = bm25.get_scores(tokenize(question))
    top = sorted(range(len(scores)),key=lambda i:scores[i],reverse=True)[:n]
    return [IDS[i] for i in top]

# --- meaning search: top n chunk ids from ChromaDB ---
def vector_search(question, n=20):
    results = collection.query(query_texts=[question], n_results=n, where={"doc_type": "guide"})
    return results["ids"][0]

def rrf(rankings, weights, k=60):
    scores = {}
    for ranking, weight in zip(rankings, weights):
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0) + weight / (k + rank)
    return sorted(scores, key=scores.get, reverse=True)


BM25_WEIGHT = 0.5


def hybrid_search(question, n=5):
    fused = rrf([vector_search(question), bm25_search(question)], weights=[1.0, BM25_WEIGHT])
    return [(DOCS[ID_TO_INDEX[i]], SOURCES[ID_TO_INDEX[i]]) for i in fused[:n]]

# --- quick test: only runs when you do `python hybrid.py` ---
if __name__ == "__main__":
    q = "How do I use lifespan events to run code on startup and shutdown?"
    for doc, source in hybrid_search(q):
        print(source, "|", doc[:80].replace("\n", " "))