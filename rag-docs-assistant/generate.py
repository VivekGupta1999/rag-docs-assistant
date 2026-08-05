import chromadb
from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic

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
"""


def get_context(question):
    result = collection.query(
        query_texts=[question],
        n_results= 3,
        where={"doc_type":"guide"}
    )

    return format_context(result["documents"][0], result["metadatas"][0])

def format_context(documents,metadatas):
    parts = []
    for doc,meta in zip(documents,metadatas):
        info = F"[Source : {meta['source']},\n document text: {doc}]"
        parts.append(info)
    return "\n\n".join(parts)


# print(get_context("What is a Fast API cloud?"))


def answer_question(question):
    context = get_context(question)

    message = client.messages.create(
        model=model,
        max_tokens = 1000,
        system=SYSTEM_PROMPT,
        messages=[
            {"role":"user","content":f"Context: \n{context} \\n Question: \n{question}"}
        ],
    )

    return message.content[0].text

question = "What is  Fast API cloud?"
print(answer_question("What is the capital of France?"))