from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from NarrativeForge.Engine.config import config
from NarrativeForge.Engine.storage.database import Database
from NarrativeForge.Engine.ai_providers import OpenAICompatibleProvider
from NarrativeForge.Engine.pipeline.orchestrator import PipelineOrchestrator
from NarrativeForge.Engine.api import projects_router, generation_router, init_projects, init_generation

db = Database(config.database_url)
provider = OpenAICompatibleProvider(base_url="http://127.0.0.1:11434", model=config.default_model)
orchestrator = PipelineOrchestrator(provider)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init()
    init_projects(db)
    init_generation(db, orchestrator)
    yield
    await db.close()


app = FastAPI(title="NarrativeForge Engine", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router)
app.include_router(generation_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=config.host, port=config.port, reload=True)
