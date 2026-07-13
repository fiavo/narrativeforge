"""Tests for AI pipeline and orchestration."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from NarrativeForge.Engine.pipeline.orchestrator import PipelineOrchestrator
from NarrativeForge.Engine.agents.base import AgentContext
from NarrativeForge.Engine.models import Project, GameGenre


@pytest.mark.unit
class TestPipelineOrchestrator:
    """Test pipeline orchestration."""

    def test_orchestrator_initialization(self, mock_ai_provider):
        """Test that orchestrator initializes all agents."""
        orchestrator = PipelineOrchestrator(mock_ai_provider)
        
        assert orchestrator.provider is mock_ai_provider
        assert orchestrator._director is not None
        assert orchestrator._story is not None
        assert orchestrator._dialogue is not None
        assert orchestrator._quest is not None
        assert orchestrator._lore is not None
        assert orchestrator._checker is not None

    @pytest.mark.asyncio
    async def test_pipeline_run_story_classification(self, mock_ai_provider):
        """Test pipeline routes correctly for story requests."""
        orchestrator = PipelineOrchestrator(mock_ai_provider)
        
        orchestrator._director.execute = AsyncMock()
        orchestrator._director.execute.return_value = MagicMock(
            content={"story": "Once upon a time..."},
            metadata={"classification": "story"},
            agent_name="DirectorAgent",
            changes=[],
        )
        
        orchestrator._story.execute = AsyncMock()
        orchestrator._story.execute.return_value = MagicMock(
            content="Once upon a time...",
            metadata={},
            agent_name="StoryAgent",
            changes=[],
        )
        
        orchestrator._checker.execute = AsyncMock()
        orchestrator._checker.execute.return_value = MagicMock(
            content={},
            metadata={"score": 0.95, "issue_count": 0, "critical_count": 0},
            agent_name="ConsistencyChecker",
            changes=[],
        )
        
        project = Project(
            id=uuid4(),
            name="Test",
            genre=GameGenre.Fantasy,
            sub_genres=[],
            target_audience="Adult",
            tone="Epic",
            themes=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        context = AgentContext(
            project=project,
            story_bible=None,
            graph=None,
            user_request="Write a fantasy story",
            generation_params={},
            previous_results={},
            locked_elements=[],
        )
        
        result = await orchestrator.run(context)
        
        assert result.content == "Once upon a time..."
        assert "Director" in result.stages_completed
        assert "Story" in result.stages_completed
        assert "Consistency" in result.stages_completed
        assert result.metadata["consistency_score"] == 0.95
