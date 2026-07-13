# NarrativeForge

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-343%20passing-brightgreen)](https://github.com/fiavo/narrativeforge)
[![.NET](https://img.shields.io/badge/.NET-9.0-purple.svg)](https://dotnet.microsoft.com/)
[![Version](https://img.shields.io/badge/version-1.0.0-orange.svg)](https://github.com/fiavo/narrativeforge/releases/tag/v1.0.0)

**AI-Powered Story Generation and Narrative Design Platform for Game Developers**

A professional-grade AI-powered narrative engine capable of managing AAA-scale game worlds, generating consistent stories, quests, and dialogue, and acting as a co-writer and narrative designer.

## Features

### AI-Powered Narrative Generation
- **10 Specialized AI Agents**: Story, Director, Dialogue, Quest, Lore, World, Timeline, Critic, Rewrite, Consistency Checker
- **Multi-Stage Pipeline**: Director → Writer → Critic → Lore Checker → Editor
- **Smart Routing**: Director classifies requests and routes to the appropriate agent

### Visual Graph Editor
- **Dialogue Trees**: Create branching dialogue with player choices
- **Quest Graphs**: Design dynamic quest chains with multiple paths
- **Auto-Layout**: Hierarchical and force-directed algorithms
- **Drag & Drop**: Intuitive node connection and positioning

### Story Bible Manager
- **Characters**: Full personality profiles, backstories, relationships
- **Locations**: World geography with connections and inhabitants
- **Factions**: Organizations with goals, allies, and enemies
- **Timeline**: Historical events and chronology
- **Lore**: World history, religions, economies, cultures

### Export System (9 Formats)
- **Dialogue**: Ink, Yarn Spinner, Ren'Py, Twine
- **Project**: JSON, Markdown
- **Game Engines**: Unity, Unreal Engine, Godot

### Import System
- Import existing Ink and Yarn Spinner scripts
- Auto-detect format from file extension
- Drag-and-drop onto graph editor

### Version Control
- Snapshot-based version history
- Side-by-side diff comparison
- One-click restore to any previous version
- Auto-save with configurable intervals

### Plugin System
- Extend with custom AI agents
- Add new AI providers
- Create custom export formats
- Dual discovery: pip packages + file-based

## Requirements

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 8GB minimum, 16GB recommended
- **GPU**: 4GB VRAM recommended for AI generation
- **Python**: 3.11+ (for AI engine)
- **.NET**: 9.0 (for desktop app)

## Installation

### From Release
1. Download the latest release from [Releases](https://github.com/fiavo/narrativeforge/releases/tag/v1.0.0)
2. Extract the ZIP file
3. Run `NarrativeForge.bat`

### From Source
```bash
# Clone the repository
git clone https://github.com/narrativeforge/narrativeforge.git
cd narrativeforge

# Install Python dependencies
cd src/NarrativeForge/Engine
pip install -r requirements.txt

# Build the WPF app
cd ../..
dotnet build -c Release src/NarrativeForge/NarrativeForge.App/NarrativeForge.App.csproj

# Start the AI engine
cd src/NarrativeForge/Engine
python -m uvicorn main:app --host 127.0.0.1 --port 8000

# In a separate terminal, run the WPF app
src/NarrativeForge/NarrativeForge.App/bin/Release/net9.0-windows/NarrativeForge.App.exe
```

## Usage

1. **Start the AI Engine**: Run `narrativeforge-engine.exe` or use `python -m uvicorn main:app`
2. **Connect**: Click "Connect" in the desktop app
3. **Create a Project**: Click "New" in the Project Explorer
4. **Generate Content**: Type a request and click "Generate"
5. **Build Dialogues**: Use the Graph Editor tab to create branching dialogues
6. **Manage World**: Use the Story Bible tab to edit characters, locations, and lore
7. **Export**: Use File > Export to save in your preferred format

## Example Prompts

```
Write a prologue for a dark fantasy RPG
Create a dialogue between a hero and a mysterious stranger
Design a quest to rescue a kidnapped villager
Generate the history of an ancient dragon war
Create a branching dialogue with 3 choices for the player
```

## Architecture

- **Frontend**: C# WPF (.NET 9) with MVVM pattern
- **Backend AI**: Python FastAPI with multi-agent architecture
- **Storage**: SQLite + JSON hybrid
- **Communication**: Local HTTP API

## Project Structure

```
NarrativeForge/
├── src/
│   ├── NarrativeForge/           # C# Solution
│   │   ├── NarrativeForge.App/   # WPF Desktop App
│   │   └── NarrativeForge.Core/  # Shared DTOs
│   └── NarrativeForge/Engine/    # Python AI Backend
│       ├── agents/               # 10 AI agents
│       ├── pipeline/             # Generation pipeline
│       ├── scripting/            # Ink/Yarn parsers
│       ├── storage/              # SQLite database
│       └── api/                  # REST endpoints
├── docs/                         # Documentation
└── tests/                        # Test suites
```

## API Documentation

The API documentation is auto-generated by FastAPI and available at:
```
http://127.0.0.1:8000/docs
```

## Testing

```bash
# Run Python tests
cd src/NarrativeForge/Engine
python -m pytest tests/ -v

# Run C# tests
dotnet test src/NarrativeForge/NarrativeForge.Tests/
```

## Building Release

```bash
# Build Python backend as standalone executable
pip install pyinstaller
pyinstaller narrativeforge-engine.spec --clean

# Build WPF app
dotnet build -c Release src/NarrativeForge/NarrativeForge.App/NarrativeForge.App.csproj

# Create release package
python build_release.py
```

## License

FSAL License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) first.

## Support

- **Issues**: [GitHub Issues](https://github.com/narrativeforge/narrativeforge/issues)
- **Documentation**: [docs/](docs/)
- **API Reference**: http://127.0.0.1:8000/docs (when running)

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Desktop app powered by [WPF](https://docs.microsoft.com/en-us/dotnet/desktop/wpf/)
- AI agents using [Pydantic](https://docs.pydantic.dev/)
- Graph editor with custom WPF Canvas
