from fastapi import FastAPI

app = FastAPI(title="CaseMatch AI")


@app.get("/health")
def health():
    return {"status": "ok"}
