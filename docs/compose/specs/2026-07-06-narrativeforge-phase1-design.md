# NarrativeForge Phase 1: Core Engine — Design Spec

## [S1] Problem Statement

Game developers need a specialized AI-powered narrative tool that maintains deep memory of entire game worlds, enforces story consistency, and produces AAA-quality narrative content. General-purpose AI tools lack the domain-specific intelligence required for large-scale game writing — they forget context, generate contradictions, and cannot manage the complex web of characters, lore, timelines, and quest dependencies that define professional game narratives.

## [S2] Solution Overview

A Windows-first desktop application (WPF) with a Python AI backend (FastAPI) communicating over localhost HTTP. Phase 1 delivers the foundation: a project management system with a Story Bible memory, three specialized AI agents (Story, Director, Consistency Checker), a multi-stage generation pipeline, local LLM support, and an IDE-like dockable UI.

## [S3] Architecture Approach

**Layered Monolith with Clean Boundaries.** Four distinct layers, each independently testable:

| Layer | Technology | Responsibility |
|-------|-----------|----------------|
| Presentation | C# WPF (.NET 8), MVVM | Dockable panels, user interaction, project navigation |
| API Client | C# HttpClient wrappers | REST communication with backend, request/response mapping |
| AI Engine | Python FastAPI | Agent orchestration, generation pipeline, LLM management |
| Data | SQLite + JSON files | Structured queries, project file persistence, graph storage |

## [S4] Directory Structure

```
NarrativeForge/
├── src/
│   ├── NarrativeForge.App/           # WPF application
│   │   ├── Views/                    # XAML windows and panels
│   │   ├── ViewModels/               # MVVM view models
│   │   ├── Services/                 # API client wrappers
│   │   ├── Controls/                 # Custom WPF controls
│   │   └── Resources/               # Styles, themes, icons
│   ├── NarrativeForge.Core/          # Shared C# types (DTOs, enums)
│   │   ├── DTOs/
│   │   └── Enums/
│   └── NarrativeForge.Engine/        # Python FastAPI backend
│       ├── main.py                   # Entry point
│       ├── api/                      # Route handlers
│       ├── agents/                   # AI agents
│       ├── pipeline/                 # Multi-stage generation
│       ├── models/                   # Data models
│       ├── memory/                   # Story Bible + graph
│       ├── storage/                  # SQLite + JSON persistence
│       └── ai_providers/             # LLM abstraction
├── tests/
├── docs/compose/specs/
└── pyproject.toml
```

## [S5] Core Data Models

### Project
- `id` (UUID), `name`, `genre` (enum), `sub_genres`, `target_audience`, `tone`, `themes`
- `story_bible_id` (reference), `settings` (JSON), timestamps

### StoryBible (Central Knowledge Base)
- `characters` (map of Character objects)
- `locations` (map of Location objects)
- `factions` (map of Faction objects)
- `timeline` (ordered list of TimelineEvent)
- `relationships` (list of Relationship — graph edges)
- `lore_entries` (map of LoreEntry)
- `locked_elements` (set of IDs the user has locked against AI modification)

### Character
- Identity: `id`, `name`, `alias`, `role` (protagonist/antagonist/npc/companion)
- Psychology: `personality` (traits, values, fears, desires), `motivation`, `goals`
- Narrative: `backstory`, `arc` (current journey state), `dialogue_style`
- Social: `relationships` (map to other character IDs with relationship type)
- State: `is_alive`, `is_locked`

### Location
- `id`, `name`, `type` (city/dungeon/planet/realm), `description`
- `connected_to` (other location IDs), `inhabitants`, `factions_present`

### TimelineEvent
- `id`, `title`, `description`, `timestamp` (relative or absolute)
- `participants`, `location_id`, `consequences`, `order`

### Relationship (Graph Edge)
- `source_id`, `target_id`, `type` (enemy/ally/parent/child/loves/leads/member_of)
- `strength` (0.0–1.0), `is_bidirectional`

### .nforge Project File Format
JSON archive containing project metadata, story bible, generated content, and version info. Portable and human-readable.

## [S6] AI Agent Architecture

### Agent Interface

All agents implement a common `BaseAgent` ABC:
- `execute(context: AgentContext) → AgentResult` — process input, return structured output
- `build_prompt(context) → str` — construct agent-specific prompt with story bible context

### Three Phase-1 Agents

**DirectorAgent (Orchestrator)**
- Does not generate prose. Receives user requests, classifies them, decomposes into sub-tasks, dispatches to Story Agent, merges results, triggers consistency validation, and updates the Story Bible.

**StoryAgent (Generator)**
- Produces all narrative content: story beats, chapters, side stories, plot twists, endings, cutscene descriptions, dialogue drafts.
- System prompt enforces AAA quality, genre conventions, emotional pacing, and character voice consistency.

**ConsistencyChecker (Validator)**
- Scans generated output against the full Story Bible for: plot holes, timeline contradictions, character behavior violations, lore conflicts, dead-character resurrection, geography errors.
- Returns a structured report with severity levels and specific references.

### Agent Context Object
Every agent receives: `project`, `story_bible`, `narrative_graph`, `user_request`, `generation_params`, `previous_results` (pipeline outputs so far), `locked_elements`.

## [S7] Multi-Stage Generation Pipeline

All content passes through six stages before delivery:

```
Request → Director → [Planner → Writer → Critic → LoreChecker → Editor] → Output
                                        ↑                   ↓
                                  Consistency ← Story Bible Update
```

1. **Planner** — Structural outline. Beats, arcs, pacing. No prose.
2. **Writer** — Fleshes the plan into narrative text using story bible context.
3. **Critic** — Scores output on: coherence, character depth, dialogue quality, emotional impact, pacing, creativity, structural quality.
4. **LoreChecker** — Cross-references against Story Bible for contradictions.
5. **Editor** — Refines based on Critic scores and LoreChecker flags.
6. **Output** — Final formatted result + delta updates to Story Bible.

## [S8] Memory & Story Bible System

### Narrative Graph
Nodes represent characters, events, locations, factions, items. Edges represent relationships. Traversed during consistency checking and context building.

### Story Bible Loading
Before any generation, the pipeline loads relevant slices of the Story Bible into context:
- Characters involved in the request
- Connected locations and factions
- Recent timeline events
- Active quest dependencies

### Locked Elements
Users can lock any entity (character, location, event) to prevent AI modification. The pipeline respects these locks during generation and validation.

### Continuity Enforcement
After each pipeline run, the Story Bible receives delta updates — new characters, changed states, new events. The graph is rebuilt incrementally.

## [S9] Storage Layer

### SQLite (Structured Queries)
- `projects`, `characters`, `locations`, `factions`, `timeline_events`, `relationships`, `lore_entries`
- Full-text search across all text fields
- Relationship queries for graph traversal

### JSON Files (Project Persistence)
- Each `.nforge` file is a self-contained JSON archive
- Contains project + story bible + generated content + metadata
- Enables file-based sharing and backup
- SQLite acts as local cache/index for fast queries

### Graph Storage
- Relationships stored in SQLite `relationships` table
- In-memory `NetworkX` graph for traversal during consistency checks
- Rebuilt from SQLite on project load

## [S10] AI Provider System

### Provider Interface
```python
class AIProvider(ABC):
    async def complete(messages, temperature, max_tokens) -> str
    async def stream(messages, temperature, max_tokens) -> AsyncIterator[str]
```

### Phase-1 Implementations
- **llama_cpp** — Local models via `llama-cpp-python`. Direct GGUF loading.
- **openai_compatible** — Any OpenAI-API-compatible endpoint: Ollama, vLLM, LM Studio, text-generation-webui, DeepSeek API, Mistral API.

This covers LLaMA, Mistral, DeepSeek, and hundreds of open-source models — all runnable locally with no API keys required.

### Provider Selection
Users configure one default provider per project. The Director Agent can optionally route different agents to different providers (e.g., Story Agent on a larger model, Consistency Checker on a faster model).

## [S11] WPF Desktop Application

### UI Framework
- .NET 8, WPF with MVVM pattern
- **AvalonDock** for IDE-like dockable panel layout
- **CommunityToolkit.Mvvm** for MVVM infrastructure
- Custom dark theme (game-dev aesthetic)

### Panel Layout
```
┌──────────┬──────────────────────────┬──────────┐
│ Project  │     Main Workspace       │ Story    │
│ Explorer │  (Content Editor /       │ Bible    │
│ (tree)   │   Generation View)       │ Inspector│
│          │                          │          │
├──────────┤                          ├──────────┤
│ Timeline │                          │ Agent    │
│ View     │                          │ Output   │
│          │                          │ Log      │
└──────────┴──────────────────────────┴──────────┘
                    Status Bar
```

### Core Panels (Phase 1)
1. **Project Explorer** — Tree view of all project entities (characters, locations, quests, etc.)
2. **Main Workspace** — Tabbed editor for viewing/editing generated content
3. **Story Bible Inspector** — Detail panel showing selected entity's full data
4. **Timeline View** — Visual chronological representation of events
5. **Agent Output Log** — Real-time display of pipeline progress and agent messages
6. **AI Generation Panel** — Input area for generation requests with parameter controls

### Key UI Features
- Dockable, resizable, tabbable panels (AvalonDock)
- Auto-save with undo/redo (Ctrl+Z/Ctrl+Y)
- Search across entire project (Ctrl+Shift+F)
- Keyboard shortcuts for all major actions
- Dark theme with accent colors
- Progress indicators during AI generation

## [S12] API Contracts

### Project Endpoints
- `POST /api/projects` — Create project
- `GET /api/projects` — List projects
- `GET /api/projects/{id}` — Get project with story bible
- `PUT /api/projects/{id}` — Update project
- `DELETE /api/projects/{id}` — Delete project

### Story Bible Endpoints
- `GET /api/projects/{id}/characters` — List characters
- `POST /api/projects/{id}/characters` — Create character
- `PUT /api/projects/{id}/characters/{char_id}` — Update character
- Same pattern for locations, factions, timeline, lore

### Generation Endpoints
- `POST /api/generate` — Submit generation request (returns job ID)
- `GET /api/generate/{job_id}` — Poll job status / stream results
- `POST /api/generate/validate` — Run consistency check without generation

### Graph Endpoints
- `GET /api/projects/{id}/graph` — Get full narrative graph
- `GET /api/projects/{id}/graph/character/{id}` — Get character's relationship subgraph

## [S13] Phase 1 Scope Boundaries

### Included
- Project creation and management
- Story Bible with characters, locations, timeline, relationships
- Narrative graph with relationship traversal
- Three AI agents: Story, Director, Consistency Checker
- Six-stage generation pipeline
- Local LLM support (llama-cpp, OpenAI-compatible)
- IDE-like WPF desktop UI
- SQLite + JSON hybrid storage
- .nforge project file format
- Basic export (JSON, Markdown)

### Deferred to Phase 2+
- Full export system (Unity, Unreal, Godot, Ink, Yarn Spinner, Ren'Py)
- Plugin system
- Additional agents (Dialogue, Quest, Lore, World, Timeline, Critic, Rewrite)
- Vector database for semantic search
- Version control / history comparison
- Collaboration features
- Online mode with cloud AI providers

## [S14] Quality Standards

### Code
- C# follows .NET conventions, uses nullable reference types
- Python follows PEP 8, uses type hints throughout
- Both sides have unit tests and integration tests
- API contracts validated via OpenAPI schema

### AI Output
- All generation passes through the full pipeline before delivery
- Consistency Checker must run on every output
- Critic must score below threshold → Editor refinement loop
- Locked elements are never modified by AI

### Performance
- Generation requests stream results to UI in real-time
- Story Bible load time under 2 seconds for projects up to 1000 entities
- Consistency check completes within 30 seconds for full story bible scan
