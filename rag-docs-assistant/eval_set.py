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


# Key-fact rule: list only what a correct answer cannot leave out.
# Every fact below was checked against the FastAPI docs page it comes from.

EVAL_QUESTIONS: list[EvalCase] = [
    # ---------- direct ----------
    EvalCase(
        id="q01",
        question="How do I define a path parameter in FastAPI?",
        category="direct",
        expected_sources=["path-params"],
        should_answer=True,
        key_facts=[
            "declare it in the path with curly braces, e.g. /items/{item_id}",
            "the path operation function takes an argument with the same name",
        ],
    ),
    EvalCase(
        id="q02",
        question="How do I add a dependency using Depends() in FastAPI?",
        category="direct",
        expected_sources=["dependencies"],
        should_answer=True,
        key_facts=[
            "declare a path operation parameter using Depends(the_dependency), passing the function or class itself",
            "FastAPI calls the dependency and passes its result into the path operation",
        ],
    ),
    EvalCase(
        id="q03",
        question="How do I validate a request body using Pydantic models?",
        category="direct",
        expected_sources=["body"],
        should_answer=True,
        key_facts=[
            "define a model class that inherits from Pydantic's BaseModel",
            "declare a path operation parameter with that model as its type",
            "FastAPI validates the body automatically and returns an error if the data is invalid",
        ],
    ),
    EvalCase(
        id="q04",
        question="How do background tasks work in FastAPI?",
        category="direct",
        expected_sources=["background-tasks"],
        should_answer=True,
        key_facts=[
            "add a parameter of type BackgroundTasks to the path operation (or a dependency)",
            "schedule work with background_tasks.add_task(...)",
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
            "use CORSMiddleware, added to the app with app.add_middleware",
            "allow_origins lists the origins that are permitted",
        ],
    ),
    EvalCase(
        id="q06",
        question="How do I define a response model in FastAPI?",
        category="direct",
        expected_sources=["response-model"],
        should_answer=True,
        key_facts=[
            "declare it with the function's return type annotation or the response_model parameter",
            "FastAPI validates the returned data and filters it to the model's fields",
        ],
    ),
    EvalCase(
        id="q07",
        question="What is FastAPI Cloud?",
        category="direct",
        expected_sources=["cloud"],
        should_answer=True,
        key_facts=[
            "a platform for deploying FastAPI apps, built by the team behind FastAPI",
            "you deploy with a single command, fastapi deploy",
        ],
    ),
    EvalCase(
        id="q08",
        question="How do I organize a large FastAPI application with multiple files?",
        category="direct",
        expected_sources=["bigger-applications"],
        should_answer=True,
        key_facts=[
            "split routes into separate modules using APIRouter",
            "register each router on the main app with app.include_router",
        ],
    ),
    EvalCase(
        id="q09",
        question="How do I implement OAuth2 authentication in FastAPI?",
        category="direct",
        expected_sources=["security"],
        should_answer=True,
        key_facts=[
            "create an OAuth2PasswordBearer scheme with a tokenUrl",
            "use the scheme as a dependency (Depends) to get the bearer token in the path operation",
        ],
    ),
    EvalCase(
        id="q10",
        question="How do I serve static files in FastAPI?",
        category="direct",
        expected_sources=["static-files"],
        should_answer=True,
        key_facts=[
            "use the StaticFiles class",
            "mount it on the app, e.g. app.mount('/static', StaticFiles(directory='static'), name='static')",
        ],
    ),
    EvalCase(
        id="q11",
        question="How do I handle WebSocket connections in FastAPI?",
        category="direct",
        expected_sources=["websockets"],
        should_answer=True,
        key_facts=[
            "declare the endpoint with the @app.websocket(...) decorator",
            "accept the connection with await websocket.accept()",
            "receive and send messages, e.g. receive_text and send_text, typically in a loop",
        ],
    ),
    EvalCase(
        id="q12",
        question="How do I write tests for a FastAPI application?",
        category="direct",
        expected_sources=["testing"],
        should_answer=True,
        key_facts=[
            "create a TestClient by passing it the FastAPI app",
            "write test functions (run with pytest) that call the client and assert on the response",
        ],
    ),
    EvalCase(
        id="q14",
        question="What's the difference between FastAPI and Flask?",
        category="direct",
        expected_sources=["alternatives"],
        should_answer=True,
        key_facts=[
            "Flask is a microframework that leaves out built-ins such as database integration",
            "FastAPI adds automatic data validation, serialization and API docs based on Python type hints",
        ],
    ),
    EvalCase(
        id="q19",
        question="How do I run code when my FastAPI app starts up and shuts down?",
        category="direct",
        expected_sources=["events"],
        should_answer=True,
        key_facts=[
            "use a lifespan function (an @asynccontextmanager) passed to FastAPI(lifespan=...)",
            "code before yield runs at startup and code after yield runs at shutdown",
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
            "FastAPI validates the value and returns a clear error if it is too long",
        ],
    ),

    # ---------- paraphrased (a problem, not the docs' words) ----------
    EvalCase(
        id="q13",
        question="How do I add a dependency to my Python project?",
        category="paraphrased",
        expected_sources=["virtual-environments"],
        should_answer=True,
        key_facts=[
            "the docs recommend uv to manage the project and its dependencies",
            "add a package with uv add, e.g. uv add \"fastapi[standard]\"",
        ],
    ),
    EvalCase(
        id="q21",
        question="My React app on localhost:3000 gets blocked by the browser when it calls my API on port 8000. How do I fix it?",
        category="paraphrased",
        expected_sources=["cors"],
        should_answer=True,
        key_facts=[
            "this is a CORS issue: a different port is a different origin",
            "add CORSMiddleware with http://localhost:3000 in allow_origins",
        ],
    ),
    EvalCase(
        id="q22",
        question="My user endpoint accidentally returns the password hash. How do I make sure it never goes back to the client?",
        category="paraphrased",
        expected_sources=["response-model", "extra-models"],
        should_answer=True,
        key_facts=[
            "use a separate output model that does not include the password field",
            "set it as the response_model (or return type) so FastAPI filters the output",
        ],
    ),
    EvalCase(
        id="q23",
        question="My signup endpoint is slow because it sends a welcome email. Can I respond right away and send the email afterwards?",
        category="paraphrased",
        expected_sources=["background-tasks"],
        should_answer=True,
        key_facts=[
            "use BackgroundTasks and add the email-sending function with add_task",
            "the task runs after the response is returned, so the client does not wait",
        ],
    ),
    EvalCase(
        id="q24",
        question="My main.py has 2,000 lines of routes. How do I split it up?",
        category="paraphrased",
        expected_sources=["bigger-applications"],
        should_answer=True,
        key_facts=[
            "move routes into separate modules using APIRouter",
            "connect them to the main app with app.include_router",
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
            "override the dependency with app.dependency_overrides[original] = override",
            "call the endpoint with TestClient so the override runs instead of the real database",
        ],
    ),
    EvalCase(
        id="q26",
        question="How do I require authentication on every route in one router?",
        category="multi_doc",
        expected_sources=["bigger-applications", "security"],
        should_answer=True,
        key_facts=[
            "make the auth check a dependency (e.g. based on OAuth2PasswordBearer)",
            "add it with dependencies=[Depends(...)] on the APIRouter or in app.include_router, so it applies to every route",
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
            "code after yield (ideally in a finally block) closes the session after the request",
            "inject the session into path operations with Depends",
        ],
    ),

    # ---------- out_of_scope ----------
    EvalCase(id="q15", question="What is the capital of France?",
             category="out_of_scope", should_answer=False),
    EvalCase(id="q16", question="How do I train a machine learning model with PyTorch?",
             category="out_of_scope", should_answer=False),
    EvalCase(id="q17", question="What's the best recipe for chocolate chip cookies?",
             category="out_of_scope", should_answer=False),

    # ---------- near_miss (FastAPI-adjacent, NOT answered by the docs) ----------
    # The alternatives page describes Django but never explains Django routing.
    EvalCase(id="q18", question="How do I set up routing in Django?",
             category="near_miss", should_answer=False),
    # The background-tasks page recommends Celery for heavy work but never configures it.
    EvalCase(id="q28", question="How do I configure Celery workers and a Redis broker for my FastAPI app?",
             category="near_miss", should_answer=False),
    # No FastAPI docs page covers AWS Lambda or Mangum.
    EvalCase(id="q29", question="How do I deploy FastAPI to AWS Lambda using Mangum?",
             category="near_miss", should_answer=False),
    # The SQL tutorial covers SQLModel and Alembic, not the Django ORM.
    EvalCase(id="q30", question="How do I define models and run migrations with the Django ORM?",
             category="near_miss", should_answer=False),
]


# Fail fast on duplicate ids
_ids = [c.id for c in EVAL_QUESTIONS]
assert len(_ids) == len(set(_ids)), "duplicate eval ids"