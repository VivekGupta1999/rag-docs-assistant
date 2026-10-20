from generate import collection, expand, format_context, client , model


TOOLS = [
    {
        "name":"search_docs",
        "description":"Search the Fast API documentation. Returns the most relevant sections with there source page. "
                        "Use Short Specific Queries. Call it more than once if the question has several parts.",
        "input_schema":{
            "type":"object",
            "properties":{
                "query":{"type":"string","description":"What to search for, e.g. 'APIRouter dependencies'"}
            
            },
            "required":["query"]
        },
    },

    {
        "name":"read_page",
        "description":"Read a full documentation page by its source path, as returned by search_docs. "
                        "Use only when the search results are cutoff or missing code",
        "input_schema":{
            "type":"object",
            "properties":{
                "source":{"type":"string","description":"The exact source path from a search resutl"}\
                
            },
            "required":["source"]
        },
    },
]


def search_docs(query):
    result = collection.query(query_texts=[query], n_results=5,where={"doc_type":"guide"})
    documents,sources = expand(result["ids"][0])
    return format_context(documents,sources), sources


MAX_PAGE_CHARS = 6000



def read_page(source):
    data = collection.get(where={"source":source},include=["documents"])
    if not data["ids"]:
        return f"No page found with source:'{source}' .",[]
    chunks=sorted(zip(data["ids"],data["documents"]), key=lambda p:int(p[0].split("_")[1]))
    text = "\n\n".join(doc for _, doc in chunks)
    if len(text) > MAX_PAGE_CHARS:
        text = text[:MAX_PAGE_CHARS] + "\n\n[page truncated]"
    return f"[Source:{source}]\n{text}",[source]



TOOL_FUNCTIONS = {
    "search_docs": lambda args:search_docs(args["query"]),
    "read_page": lambda args:read_page(args["source"])

}


def run_tool(name,args):
    if name not in TOOL_FUNCTIONS:
        return f"Unknown Tool:{name}",[]

    try:
        return TOOL_FUNCTIONS[name](args)
    except Exception as e:
        return f"Tool {name} failed: {type(e).__name__}: {e}", []

SYSTEM = """You answer questions about FastAPI using only its documentation, which you can search with your tools.

Rules:
1. If the question has nothing to do with programming, reply with exactly: I don't know. Never answer it from your own knowledge.
2. Otherwise, always search before answering. If the question has several parts, search for each part separately.
3. If your searches find nothing relevant, start your answer with exactly: I don't know.
4. Answer only from the tool results. Cite the source page for each claim. Only use code that appears in the tool results; do not invent code, parameters or values."""

MAX_STEPS = 5

def ask_agent(question):
    messages = [{"role":"user","content":question}]
    sources, trace,seen = [], [] , []

    for step in range(MAX_STEPS):
        response = client.messages.create(
            model=model, max_tokens=1500,system=SYSTEM,tools=TOOLS,temperature=0, messages= messages,
            tool_choice={"type": "any"} if step == 0 else {"type": "auto"},
        )

        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text"), sources, trace, "\n\n".join(seen)

        messages.append({"role":"assistant","content":response.content})

        results = []
        for block in response.content:
            if block.type == "tool_use":
                text,srcs = run_tool(block.name,block.input)
                print (f" step {step+1} : {block.name} ({block.input}) -> {srcs}")
                trace.append({"step": step + 1, "tool": block.name, "input": block.input})
                for s in srcs:
                    if s not in sources:
                        sources.append(s)
                results.append({"type":"tool_result","tool_use_id":block.id,"content":text})
                seen.append(text)
        messages.append({"role":"user","content":results})

    return "I could'nt finish within the step limit.",sources,trace ,"\n\n".join(seen)


    

if __name__ == "__main__":
    for q in ["How do I require authentication on every route in one router?",
              "What is the capital of France?"]:
        answer, sources, trace, context = ask_agent(q)
        print("\nQ:", q)
        print("tool calls:", len(trace), "| sources:", sources, "| context chars:", len(context))
        print("ANSWER:", answer[:120])