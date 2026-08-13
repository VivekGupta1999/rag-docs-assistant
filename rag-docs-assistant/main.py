from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from generate import answer_question

from fastapi import Request
from slowapi import Limiter,_rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded,_rate_limit_exceeded_handler)
class QueryRequest(BaseModel):
    question: str


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.post("/query")
@limiter.limit("5/minute")
def query(request:Request,body:QueryRequest):
    answer,sources = answer_question(body.question)
    return {"answer": answer,"source":sources}