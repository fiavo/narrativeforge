from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from config import config
except ImportError:
    from NarrativeForge.Engine.config import config

app = FastAPI(title="NarrativeForge Engine", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=config.host, port=config.port, reload=True)
