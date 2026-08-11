from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from generate import answer_question
app = FastAPI()

class QueryRequest(BaseModel):
    question: str


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.post("/query")
def query(request:QueryRequest):
    answer,sources = answer_question(request.question)
    return {"answer": answer,"source":sources}