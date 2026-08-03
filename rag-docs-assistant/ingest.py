from pathlib import Path

docs_dir = Path("fastapi-repo/docs/en/docs")

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


print(f"Total Characters: {total_chars}")
print(f"Longest File: {longest_file} ({longest_length} chars)")
print(f"Shortest File: {shortest_file} ({shortest_length} chars)")

