from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import auth, documents, review
from app.services.rate_limit import limiter


app = FastAPI(title="CaseMatch AI")

app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)

app.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

app.include_router(
    documents.router,
    prefix="/documents",
    tags=["Documents"],
)

app.include_router(
    review.router,
    prefix="/review",
    tags=["Review"],
)


@app.get("/health")
def health():
    return {"status": "ok"}
