from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from NarrativeForge.Engine.config import config
from NarrativeForge.Engine.storage.database import Database
from NarrativeForge.Engine.ai_providers import OpenAICompatibleProvider
from NarrativeForge.Engine.pipeline.orchestrator import PipelineOrchestrator
from NarrativeForge.Engine.plugins.plugin_manager import PluginManager
from NarrativeForge.Engine.versioning import VersionManager
from NarrativeForge.Engine.api import (
    projects_router,
    generation_router,
    dialogues_router,
    quests_router,
    versions_router,
    init_projects,
    init_generation,
    init_dialogues,
    init_quests,
    init_versions,
)

db = Database(config.database_url)
provider = OpenAICompatibleProvider(base_url="http://127.0.0.1:11434", model=config.default_model)
orchestrator = PipelineOrchestrator(provider)
plugin_manager = PluginManager()
version_manager = VersionManager("versions_data")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init()
    init_projects(db)
    init_generation(db, orchestrator, plugin_manager)
    init_dialogues(db)
    init_quests(db)
    init_versions(db, version_manager)
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
app.include_router(dialogues_router)
app.include_router(quests_router)
app.include_router(versions_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=config.host, port=config.port, reload=True)
