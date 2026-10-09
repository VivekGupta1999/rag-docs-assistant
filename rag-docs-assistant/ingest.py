from pathlib import Path
import chromadb
import re 


REPO = Path("fastapi-repo")

INCLUDE_PATTERN = re.compile(r"\{\*\s*(\S*docs_src/\S+).*?\*\}")

def inline_code_includes(text):
    """Replace every {* ../../docs_src/... *} line with the real code."""
    def replace(match):
        path = match.group(1)
        if "docs_src/" not in path:              # 1. not a code include → leave it alone
            return match.group(0)
        rel = path[path.index("docs_src/"):]     # safe now: we know docs_src/ is there
        code_file = REPO / rel
        if not code_file.exists():               # 2. file missing → leave it alone
            return match.group(0)
        code = code_file.read_text()
        return f"```python\n{code}\n```"
   

    return INCLUDE_PATTERN.sub(replace, text)



docs_dir = Path("fastapi-repo/docs/en/docs")
chroma_client = chromadb.PersistentClient(path="./chroma_db")
try:
    chroma_client.delete_collection(name="fastapi_docs")
except Exception :
    pass

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
    content = inline_code_includes(content) 
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
metadatas = [{"source": chunk["source"],
              "doc_type":"changelog" if "release-notes.md" in chunk["source"] else "guide",
              } for chunk in all_chunks]

collection.add(
    ids=ids,
    documents=documents,
    metadatas=metadatas,
)

print(f"Collection now has {collection.count()} chunks")