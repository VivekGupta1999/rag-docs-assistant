from pathlib import Path
import chromadb

docs_dir = Path("fastapi-repo/docs/en/docs")
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="fastapi_docs")
md_files = list(docs_dir.rglob("*.md"))

print(f"Found {len(md_files)} markdown files")

total_chars = 0

longest_file = None
longest_length = 0

shortest_file = None
shortest_length = float("inf")


for path in md_files:
    content = path.read_text(encoding="utf-8")
    length = len(content)
    total_chars += length

    if length > longest_length:
        longest_length = length
        longest_file = path

    if length < shortest_length:
        shortest_length = length
        shortest_file = path



def chunk_text(text,chunk_size=1000, overlap = 200):
    chunks = []
    start =0
    while(start<len(text)):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks


all_chunks = []

for path in md_files:
    content = path.read_text(encoding="utf-8")
    chunks = chunk_text(content)
    for chunk in chunks:
        all_chunks.append({"text":chunk,"source":str(path)})


print(f"Total Characters: {total_chars}")
print(f"Longest File: {longest_file} ({longest_length} chars)")
print(f"Shortest File: {shortest_file} ({shortest_length} chars)")
print(f"Total chunks created: {len(all_chunks)}")


# print("\n--- Sample chunk ---")
# print(all_chunks[500]["source"])
# print(all_chunks[500]["text"])

ids = [f"chunk_{i}" for i in range(len(all_chunks))]
documents = [chunk["text"] for chunk in all_chunks]
metadatas = [{"source": chunk["source"]} for chunk in all_chunks]

collection.add(
    ids=ids,
    documents=documents,
    metadatas=metadatas,
)

print(f"Collection now has {collection.count()} chunks")