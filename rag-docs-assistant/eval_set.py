from typing import Literal
from pydantic import BaseModel


Category = Literal["direct", "paraphrased", "multi_doc", "near_miss", "out_of_scope"]


class EvalCase(BaseModel):
    id: str
    question: str
    category: Category
    expected_sources: list[str] = []  # substrings of the source file path
    should_answer: bool
    key_facts: list[str] = []         # facts a correct answer MUST contain


EVAL_QUESTIONS: list[EvalCase] = [
    # ---------- direct ----------
    EvalCase(
        id="q01",
        question="How do I define a path parameter in FastAPI?",
        category="direct",
        expected_sources=["path-params"],
        should_answer=True,
        key_facts=[
            "declared in the path with curly braces, e.g. /items/{item_id}",
            "the function takes an argument with the same name",
            "a type annotation (e.g. int) makes FastAPI convert and validate it",
        ],
    ),
    EvalCase(
        id="q02",
        question="How do I add a dependency using Depends() in FastAPI?",
        category="direct",
        expected_sources=["dependencies"],
        should_answer=True,
        key_facts=[
            "the dependency is a function (a 'dependable') that can take the same parameters as a path operation",
            "it is declared in the path operation's parameters with Depends(the_function)",
            "FastAPI calls the dependency and passes its return value into the path operation",
        ],
    ),
    EvalCase(
        id="q03",
        question="How do I validate a request body using Pydantic models?",
        category="direct",
        expected_sources=["body"],
        should_answer=True,
        key_facts=[
            "define a class that inherits from pydantic BaseModel",
            "declare a path operation parameter typed as that model",
            "invalid data returns a clear error showing where and what was wrong",
        ],
    ),
    EvalCase(
        id="q04",
        question="How do background tasks work in FastAPI?",
        category="direct",
        expected_sources=["background-tasks"],
        should_answer=True,
        key_facts=[
            "declare a parameter of type BackgroundTasks in the path operation",
            "add work with background_tasks.add_task(func, *args)",
            "the task runs after the response is sent",
        ],
    ),
    EvalCase(
        id="q05",
        question="How do I add CORS middleware to a FastAPI app?",
        category="direct",
        expected_sources=["cors"],
        should_answer=True,
        key_facts=[
            "import CORSMiddleware",
            "add it with app.add_middleware(CORSMiddleware, ...)",
            "allow_origins lists the permitted origins",
        ],
    ),
    EvalCase(
        id="q06",
        question="How do I define a response model in FastAPI?",
        category="direct",
        expected_sources=["response-model"],
        should_answer=True,
        key_facts=[
            "use the response_model parameter on the decorator or the function's return type annotation",
            "FastAPI validates and filters the output data to that model",
            "filtering lets you hide fields such as a password from the response",
        ],
    ),
    EvalCase(
        id="q07",
        question="What is FastAPI Cloud?",
        category="direct",
        expected_sources=["cloud"],
        should_answer=True,
        key_facts=[
            "a platform to deploy FastAPI apps with one command, fastapi deploy",
            "built by the same author and team behind FastAPI",
            "handles things like HTTPS and replication with autoscaling",
        ],
    ),
    EvalCase(
        id="q08",
        question="How do I organize a large FastAPI application with multiple files?",
        category="direct",
        expected_sources=["bigger-applications"],
        should_answer=True,
        key_facts=[
            "use APIRouter in separate modules",
            "register routers on the app with app.include_router",
            "include_router can set a prefix, tags and dependencies",
        ],
    ),
    EvalCase(
        id="q09",
        question="How do I implement OAuth2 authentication in FastAPI?",
        category="direct",
        expected_sources=["security"],
        should_answer=True,
        key_facts=[
            "use OAuth2PasswordBearer with a tokenUrl",
            "the scheme is used as a dependency with Depends to get the token",
            "the password flow with Bearer tokens (JWT in the full example)",
        ],
    ),
    EvalCase(
        id="q10",
        question="How do I serve static files in FastAPI?",
        category="direct",
        expected_sources=["static-files"],
        should_answer=True,
        key_facts=[
            "import StaticFiles",
            "mount it with app.mount('/static', StaticFiles(directory='static'), name='static')",
        ],
    ),
    EvalCase(
        id="q11",
        question="How do I handle WebSocket connections in FastAPI?",
        category="direct",
        expected_sources=["websockets"],
        should_answer=True,
        key_facts=[
            "declare the endpoint with @app.websocket('/ws')",
            "call await websocket.accept() first",
            "receive and send in a loop, e.g. receive_text and send_text",
        ],
    ),
    EvalCase(
        id="q12",
        question="How do I write tests for a FastAPI application?",
        category="direct",
        expected_sources=["testing"],
        should_answer=True,
        key_facts=[
            "use TestClient from fastapi.testclient, passing it the app",
            "TestClient needs httpx installed",
            "write normal test functions run with pytest and assert on the response",
        ],
    ),
    EvalCase(
        id="q14",
        question="What's the difference between FastAPI and Flask?",
        category="direct",
        expected_sources=["alternatives"],
        should_answer=True,
        key_facts=[
            "Flask is a microframework without built-in database integrations",
            "FastAPI took Flask's micro-framework, mix-and-match approach and simple routing",
            "FastAPI adds automatic data validation, serialization and OpenAPI docs from Python type hints",
        ],
    ),

    # ---------- paraphrased ----------
    # Was expected_source="dependencies" (FastAPI's Depends page), which was wrong:
    # "add a dependency to my project" means installing a package.
    EvalCase(
        id="q13",
        question="How do I add a dependency to my Python project?",
        category="paraphrased",
        expected_sources=["virtual-environments"],
        should_answer=True,
        key_facts=[
            "the docs recommend uv to manage the project and its dependencies",
            "add a package with uv add, e.g. uv add \"fastapi[standard]\"",
            "uv creates the virtual environment automatically",
        ],
    ),

    # ---------- out_of_scope ----------
    EvalCase(
        id="q15",
        question="What is the capital of France?",
        category="out_of_scope",
        should_answer=False,
    ),
    EvalCase(
        id="q16",
        question="How do I train a machine learning model with PyTorch?",
        category="out_of_scope",
        should_answer=False,
    ),
    EvalCase(
        id="q17",
        question="What's the best recipe for chocolate chip cookies?",
        category="out_of_scope",
        should_answer=False,
    ),

    # ---------- near_miss ----------
    # The alternatives page discusses Django, so retrieval may pull it in,
    # but the docs never explain how to set up Django routing.
    EvalCase(
        id="q18",
        question="How do I set up routing in Django?",
        category="near_miss",
        should_answer=False,
    ),

        # ======== NEW (Oct 6) ========

    # ---------- direct (new topics) ----------
    EvalCase(
        id="q19",
        question="How do I run code when my FastAPI app starts up and shuts down?",
        category="direct",
        expected_sources=["events"],
        should_answer=True,
        key_facts=[
            "define a lifespan function as an async context manager (@asynccontextmanager)",
            "code before yield runs on startup, code after yield runs on shutdown",
            "pass it to the app with FastAPI(lifespan=lifespan)",
        ],
    ),
    EvalCase(
        id="q20",
        question="How do I limit the maximum length of a query parameter?",
        category="direct",
        expected_sources=["query-params-str-validations"],
        should_answer=True,
        key_facts=[
            "use Query with max_length, e.g. Query(max_length=50)",
            "declare it with Annotated, e.g. Annotated[str | None, Query(max_length=50)]",
        ],
    ),

    # ---------- paraphrased (a problem, not the docs' words) ----------
    EvalCase(
        id="q21",
        question="My React app on localhost:3000 gets blocked by the browser when it calls my API on port 8000. How do I fix it?",
        category="paraphrased",
        expected_sources=["cors"],
        should_answer=True,
        key_facts=[
            "this is CORS: different ports count as different origins",
            "add CORSMiddleware with app.add_middleware",
            "put http://localhost:3000 in allow_origins",
        ],
    ),
    EvalCase(
        id="q22",
        question="My user endpoint accidentally returns the password hash. How do I make sure it never goes back to the client?",
        category="paraphrased",
        expected_sources=["response-model", "extra-models"],
        should_answer=True,
        key_facts=[
            "declare an output model without the password field",
            "set it as response_model (or the return type) so FastAPI filters the output",
        ],
    ),
    EvalCase(
        id="q23",
        question="My signup endpoint is slow because it sends a welcome email. Can I respond right away and send the email afterwards?",
        category="paraphrased",
        expected_sources=["background-tasks"],
        should_answer=True,
        key_facts=[
            "use BackgroundTasks as a parameter",
            "call background_tasks.add_task with the email function",
            "the task runs after the response is returned",
        ],
    ),
    EvalCase(
        id="q24",
        question="My main.py has 2,000 lines of routes. How do I split it up?",
        category="paraphrased",
        expected_sources=["bigger-applications"],
        should_answer=True,
        key_facts=[
            "move routes into modules using APIRouter",
            "connect them with app.include_router",
        ],
    ),

    # ---------- multi_doc (needs ALL listed sources) ----------
    EvalCase(
        id="q25",
        question="How do I test an endpoint that uses a database dependency without hitting the real database?",
        category="multi_doc",
        expected_sources=["testing-dependencies", "dependencies"],
        should_answer=True,
        key_facts=[
            "use TestClient to call the endpoint",
            "replace the dependency with app.dependency_overrides[original] = override",
            "clear overrides afterwards (app.dependency_overrides = {})",
        ],
    ),
    EvalCase(
        id="q26",
        question="How do I require authentication on every route in one router?",
        category="multi_doc",
        expected_sources=["bigger-applications", "security"],
        should_answer=True,
        key_facts=[
            "create the auth check as a dependency (e.g. using OAuth2PasswordBearer)",
            "pass it in dependencies=[Depends(...)] on APIRouter or include_router",
        ],
    ),
    EvalCase(
        id="q27",
        question="How do I open a database session per request and make sure it's always closed afterwards?",
        category="multi_doc",
        expected_sources=["dependencies-with-yield", "sql-databases"],
        should_answer=True,
        key_facts=[
            "write a dependency that creates the session and yields it",
            "code after yield (or a finally block) closes the session",
            "inject it into path operations with Depends",
        ],
    ),

    # ---------- near_miss (FastAPI-adjacent, NOT answered by the docs) ----------
    EvalCase(
        id="q28",
        question="How do I configure Celery workers and a Redis broker for my FastAPI app?",
        category="near_miss",   # background-tasks page mentions Celery but doesn't configure it
        should_answer=False,
    ),
    EvalCase(
        id="q29",
        question="How do I deploy FastAPI to AWS Lambda using Mangum?",
        category="near_miss",   # deployment pages say 'follow your provider's guides'
        should_answer=False,
    ),
    EvalCase(
        id="q30",
        question="How do I define models and run migrations with the Django ORM?",
        category="near_miss",   # alternatives page describes Django, not its ORM usage
        should_answer=False,
    ),
]


# Fail fast on duplicate ids
_ids = [c.id for c in EVAL_QUESTIONS]
assert len(_ids) == len(set(_ids)), "duplicate eval ids"