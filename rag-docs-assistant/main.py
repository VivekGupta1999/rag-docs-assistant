from fastapi import FastAPI
from pydantic import BaseModel
from generate import answer_question
app = FastAPI()

class QueryRequest(BaseModel):
    question: str


@app.post("/query")
def query(request:QueryRequest):
    answer = answer_question(request.question)
    return {"answer": answer}