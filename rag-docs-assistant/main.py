from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from generate import answer_question

from fastapi import Request
from slowapi import Limiter,_rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

def get_real_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"))

limiter = Limiter(key_func=get_real_client_ip)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded,_rate_limit_exceeded_handler)
class QueryRequest(BaseModel):
    question: str



@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.get("/resume.pdf")
def resume():
    return FileResponse("readme_assets/Resume.pdf", media_type="application/pdf")


@app.post("/query")
@limiter.limit("5/minute")
def query(request:Request,body:QueryRequest):
    answer,sources = answer_question(body.question)
    return {"answer": answer,"source":sources}