from fastapi import FastAPI

app = FastAPI(title="CodeVV OS Backend")


@app.get("/health")
async def health():
    return {"status": "healthy"}
