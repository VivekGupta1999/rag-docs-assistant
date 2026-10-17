# Experiment (not used in production). Needs: pip install rank-bm25 fastembed
import re
import chromadb
from rank_bm25 import BM25Okapi
from fastembed.rerank.cross_encoder import TextCrossEncoder

#connect to the database

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection(name="fastapi_docs")

#tokenizer

TOKEN = re.compile(r"[a-z0-9_]+")



def tokenize(text):
    return TOKEN.findall(text.lower())


#load all guide chunk once and build the BM25 index

data = collection.get(where={"doc_type":"guide"}, include =["documents","metadatas"])

IDS = data["ids"]
DOCS = data["documents"]
SOURCES = [m["source"] for m in data["metadatas"]]


ID_TO_INDEX = {doc_id:i for i , doc_id in enumerate(IDS)}


bm25 = BM25Okapi([tokenize(doc) for doc in DOCS])

reranker = TextCrossEncoder(model_name="Xenova/ms-marco-MiniLM-L-12-v2")
#keyword search: top n chunk ids from chromaDB
def bm25_search(question,n=20):
    scores = bm25.get_scores(tokenize(question))
    top = sorted(range(len(scores)),key=lambda i:scores[i],reverse=True)[:n]
    return [IDS[i] for i in top]

# --- meaning search: top n chunk ids from ChromaDB ---
def vector_search(question, n=20):
    results = collection.query(query_texts=[question], n_results=n, where={"doc_type": "guide"})
    return results["ids"][0]




def candidates(question, n_vector=20, n_bm25=10):
    seen = []
    for doc_id in vector_search(question, n_vector) + bm25_search(question, n_bm25):
        if doc_id not in seen:
            seen.append(doc_id)
    return seen

def cap_per_source(ranked, max_per_source=3):
    counts = {}
    kept = []
    for doc_id, score in ranked:
        source = SOURCES[ID_TO_INDEX[doc_id]]
        if counts.get(source, 0) < max_per_source:
            kept.append((doc_id, score))
            counts[source] = counts.get(source, 0) + 1
    return kept



BM25_WEIGHT = 0.5




def hybrid_search(question, n=5):
    ids = candidates(question)
    texts = [DOCS[ID_TO_INDEX[i]] for i in ids]
    scores = list(reranker.rerank(question, texts))
    ranked = sorted(zip(ids, scores), key=lambda p: p[1], reverse=True)
    top = cap_per_source(ranked)[:n]
    return [(DOCS[ID_TO_INDEX[i]], SOURCES[ID_TO_INDEX[i]]) for i, _ in top]



if __name__ == "__main__":
    q = "How do I run code when my FastAPI app starts up and shuts down?"
    for doc, source in hybrid_search(q):
        print(source, "|", doc.split("\n")[0][:60])