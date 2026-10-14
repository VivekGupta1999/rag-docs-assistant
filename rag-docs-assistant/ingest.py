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





# Matches heading lines like:  ## Use CORSMiddleware { #use-corsmiddleware }
#   (#{1,3})            -> 1 to 3 '#' characters            (group 1)
#   (.+?)               -> the heading text                 (group 2)
#   (\s*\{\s*#.*\})?    -> optional { #anchor } tag at the end, kept out of the title
HEADING = re.compile(r"^(#{1,3})\s+(.+?)(\s*\{\s*#.*\})?\s*$")


def split_sections(text):
    # "Split one markdown page into title, sections_text pairs"
    sections = []
    title = ""
    lines = []
    in_code = False

    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code

        match = None if in_code else HEADING.match(line)
        if match:
            if lines:
                sections.append((title,"\n".join(lines).strip()))
            title = match.group(2)
            lines = [line]
        else:
            lines.append(line)

    if lines: 
        sections.append((title, "\n".join(lines).strip()))
    return sections


def split_long(text, max_chars = 1000):
    #if a section is too long, split it at blamk lines, never mid-word  and never inside code.

    if len(text) <= max_chars:
        return [text]


    parts = []
    current = ""
    for para in text.split("\n\n"):
        inside_code = current.count("```") %2 ==1
        too_big = len(current) + len(para) > max_chars
        if current and too_big and not inside_code:
            parts.append(current.strip())
            current = ""
        current += para + "\n\n"

    if current.strip():
        parts.append(current.strip())
    return parts



def chunk_page(text):
    #Turn one page into labelled chunks,: 'Page title > Section Title' + section text.
    sections = split_sections(text)
    page_title = sections[0][0] if sections else " "

    chunks = []
    for title, section in sections:
        if len(section.splitlines()) <=1:
            continue
        if title and title != page_title:
            label = f"{page_title} > {title}"
        else:
            label = page_title
        for part in split_long(section):
            chunks.append(f"{label}\n\n{part}")
    return chunks


def chunk_text(text,chunk_size=1000, overlap = 200):
    chunks = []
    start =0
    while(start<len(text)):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks

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

all_chunks = []

for path in md_files:
    content = path.read_text(encoding="utf-8")
    content = inline_code_includes(content) 
    chunks = chunk_page(content)
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
              "doc_type": ("changelog" if "release-notes.md" in chunk["source"]
                           else "reference" if "/reference/" in chunk["source"]
                           else "guide"),
              } for chunk in all_chunks]

collection.add(
    ids=ids,
    documents=documents,
    metadatas=metadatas,
)

print(f"Collection now has {collection.count()} chunks")