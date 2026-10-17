import chromadb
from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic

RETRIEVAL = "vector"  # "hybrid" or "vector" (rollback switch)
client = Anthropic()
model = "claude-haiku-4-5-20251001"

chroma_client = chromadb.PersistentClient(path="./chroma_db")

collection = chroma_client.get_collection(name="fastapi_docs")



# result = collection.query(
#     query_texts=["What is a Fast API cloud?"],
#     n_results=3,
#     where={"doc_type":"guide"}
# )

# documents = result["documents"][0]
# metadatas = result["metadatas"][0]



SYSTEM_PROMPT = """
You are an expert in Fast API who will be answering any queries about Fast API using only the context provided below.
If you are not able the find the answer in the context you should say I don't know.
Also any answer provided should have citations saying which file the information came from.
Only use code that appears in the context. You may shorten it, but do not invent new code, parameters or example values.
"""


def get_context(question):
    if RETRIEVAL == "hybrid":
     
        from hybrid import hybrid_search
        results = hybrid_search(question, n=5)
        results = hybrid_search(question, n=5)
        documents = [doc for doc, _ in results]
        sources = [source for _, source in results]
    else:
        result = collection.query(
            query_texts=[question],
            n_results=5,
            where={"doc_type": "guide"}
        )
        documents = result["documents"][0]
        sources = [meta["source"] for meta in result["metadatas"][0]]

    context = format_context(documents, sources)
    return context, sources


def format_context(documents, sources):
    parts = []
    for doc, source in zip(documents, sources):
        info = f"[Source : {source},\n document text: {doc}]"
        parts.append(info)
    return "\n\n".join(parts)
# print(get_context("What is a Fast API cloud?"))


def answer_question(question):
    context,sources = get_context(question)

    message = client.messages.create(
        model=model,
        max_tokens = 1000,
        system=SYSTEM_PROMPT,
        temperature=0,
        messages=[
            {"role":"user","content":f"Context: \n{context} \n\n Question: \n{question}"}
        ],
    )

    return message.content[0].text,sources

if __name__ == "__main__":
    print(answer_question("What is the capital of France?")[0])