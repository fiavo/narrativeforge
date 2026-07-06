from dataclasses import dataclass, field

from NarrativeForge.Engine.ai_providers.base import AIProvider
from NarrativeForge.Engine.agents.base import AgentContext, AgentResult
from NarrativeForge.Engine.agents.director_agent import DirectorAgent
from NarrativeForge.Engine.agents.story_agent import StoryAgent
from NarrativeForge.Engine.agents.consistency_checker import ConsistencyChecker


@dataclass
class PipelineResult:
    content: dict | list | str | None = None
    stages_completed: list[str] = field(default_factory=list)
    results: list[AgentResult] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class PipelineOrchestrator:
    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider
        self._director = DirectorAgent(provider)
        self._story = StoryAgent(provider)
        self._checker = ConsistencyChecker(provider)

    async def run(self, context: AgentContext) -> PipelineResult:
        stages_completed: list[str] = []
        results: list[AgentResult] = []
        prev_results: dict = {}

        # Stage 1: Director
        director_ctx = AgentContext(
            project=context.project,
            story_bible=context.story_bible,
            graph=context.graph,
            user_request=context.user_request,
            generation_params=context.generation_params,
            previous_results=prev_results,
            locked_elements=context.locked_elements,
        )
        director_result = await self._director.execute(director_ctx)
        stages_completed.append("Director")
        results.append(director_result)
        prev_results["DirectorAgent"] = director_result.content

        # Stage 2: Story
        story_ctx = AgentContext(
            project=context.project,
            story_bible=context.story_bible,
            graph=context.graph,
            user_request=context.user_request,
            generation_params=context.generation_params,
            previous_results=prev_results,
            locked_elements=context.locked_elements,
        )
        story_result = await self._story.execute(story_ctx)
        stages_completed.append("Story")
        results.append(story_result)
        prev_results["StoryAgent"] = story_result.content

        # Stage 3: Consistency Checker
        consistency_ctx = AgentContext(
            project=context.project,
            story_bible=context.story_bible,
            graph=context.graph,
            user_request=context.user_request,
            generation_params=context.generation_params,
            previous_results=prev_results,
            locked_elements=context.locked_elements,
        )
        consistency_result = await self._checker.execute(consistency_ctx)
        stages_completed.append("Consistency")
        results.append(consistency_result)

        # Build metadata
        metadata = {}
        if consistency_result.metadata:
            metadata["consistency_score"] = consistency_result.metadata.get("score", 0.0)
            metadata["issue_count"] = consistency_result.metadata.get("issue_count", 0)
            metadata["critical_count"] = consistency_result.metadata.get("critical_count", 0)

        return PipelineResult(
            content=story_result.content,
            stages_completed=stages_completed,
            results=results,
            metadata=metadata,
        )
