from dataclasses import dataclass, field
from typing import Any

from NarrativeForge.Engine.ai_providers.base import AIProvider
from NarrativeForge.Engine.agents.base import AgentContext, AgentResult
from NarrativeForge.Engine.agents.director_agent import DirectorAgent
from NarrativeForge.Engine.agents.story_agent import StoryAgent
from NarrativeForge.Engine.agents.dialogue_agent import DialogueAgent
from NarrativeForge.Engine.agents.quest_agent import QuestAgent
from NarrativeForge.Engine.agents.lore_agent import LoreAgent
from NarrativeForge.Engine.agents.consistency_checker import ConsistencyChecker
from NarrativeForge.Engine.models.lore import LoreEntry


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
        self._dialogue = DialogueAgent(provider)
        self._quest = QuestAgent(provider)
        self._lore = LoreAgent(provider)
        self._checker = ConsistencyChecker(provider)

    @property
    def provider(self) -> AIProvider:
        return self._provider

    def _build_agent_context(
        self, context: AgentContext, prev_results: dict[str, Any]
    ) -> AgentContext:
        return AgentContext(
            project=context.project,
            story_bible=context.story_bible,
            graph=context.graph,
            user_request=context.user_request,
            generation_params=context.generation_params,
            previous_results=prev_results,
            locked_elements=context.locked_elements,
        )

    async def run(self, context: AgentContext) -> PipelineResult:
        stages_completed: list[str] = []
        results: list[AgentResult] = []
        prev_results: dict = {}

        # Stage 1: Director
        director_ctx = self._build_agent_context(context, prev_results)
        director_result = await self._director.execute(director_ctx)
        stages_completed.append("Director")
        results.append(director_result)
        prev_results["DirectorAgent"] = director_result.content

        classification = director_result.metadata.get("classification", "story")

        # Stage 2: Route to appropriate agent(s)
        agent_results = await self._route_agents(
            context, classification, prev_results
        )
        for agent_res in agent_results:
            results.append(agent_res)
            stages_completed.append(agent_res.agent_name.replace("Agent", ""))

        prev_results.update({r.agent_name: r.content for r in agent_results})

        # Stage 3: Consistency Checker (always runs last)
        consistency_ctx = self._build_agent_context(context, prev_results)
        consistency_result = await self._checker.execute(consistency_ctx)
        stages_completed.append("Consistency")
        results.append(consistency_result)

        # Apply lore changes to story bible
        lore_added = self._apply_lore_changes(context, results)

        # Determine content from the last non-checker, non-director result
        content = agent_results[-1].content if agent_results else None

        # Build metadata
        metadata: dict[str, Any] = {}
        if consistency_result.metadata:
            metadata["consistency_score"] = consistency_result.metadata.get("score", 0.0)
            metadata["issue_count"] = consistency_result.metadata.get("issue_count", 0)
            metadata["critical_count"] = consistency_result.metadata.get("critical_count", 0)
        metadata["classification"] = classification
        metadata["lore_entries_added"] = lore_added

        return PipelineResult(
            content=content,
            stages_completed=stages_completed,
            results=results,
            metadata=metadata,
        )

    async def _route_agents(
        self,
        context: AgentContext,
        classification: str,
        prev_results: dict[str, Any],
    ) -> list[AgentResult]:
        if classification == "dialogue":
            agent_ctx = self._build_agent_context(context, prev_results)
            return [await self._dialogue.execute(agent_ctx)]

        if classification == "quest":
            agent_ctx = self._build_agent_context(context, prev_results)
            return [await self._quest.execute(agent_ctx)]

        if classification == "lore":
            agent_ctx = self._build_agent_context(context, prev_results)
            return [await self._lore.execute(agent_ctx)]

        if classification == "mixed":
            story_ctx = self._build_agent_context(context, prev_results)
            story_res = await self._story.execute(story_ctx)
            prev_results[story_res.agent_name] = story_res.content
            quest_ctx = self._build_agent_context(context, prev_results)
            quest_res = await self._quest.execute(quest_ctx)
            return [story_res, quest_res]

        # Default: 'story' and any unknown classification
        agent_ctx = self._build_agent_context(context, prev_results)
        return [await self._story.execute(agent_ctx)]

    def _apply_lore_changes(
        self, context: AgentContext, results: list[AgentResult]
    ) -> int:
        if not context.story_bible:
            return 0

        lore_added = 0
        for result in results:
            for change in result.changes:
                lore_data = change.get("lore_entries")
                if not lore_data:
                    continue
                for entry_dict in lore_data.get("new", []):
                    entry = LoreEntry(
                        title=entry_dict.get("title", ""),
                        content=entry_dict.get("content", ""),
                        category=entry_dict.get("category", ""),
                        tags=entry_dict.get("tags", []),
                    )
                    context.story_bible.lore_entries[entry.id] = entry
                    lore_added += 1
        return lore_added
