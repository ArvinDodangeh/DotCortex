"""Coach tool: pin an existing mastery path when the learner aims at it."""

from __future__ import annotations

from typing import Any

from deeptutor.core.tool_protocol import (
    BaseTool,
    ToolDefinition,
    ToolParameter,
    ToolPromptHints,
    ToolResult,
)


class PinMasteryPathTool(BaseTool):
    """Pin a DeepTutor mastery path onto the DotCortex overview map."""

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="pin_mastery_path",
            description=(
                "Pin an existing mastery path when the learner is clearly trying "
                "to master that topic. Makes it active for chat and shows it on "
                "the map. Do not invent path ids — use a real path_id from "
                "mastery tools or the user's path list."
            ),
            parameters=[
                ToolParameter(
                    name="path_id",
                    type="string",
                    description="Existing mastery path id to pin.",
                ),
                ToolParameter(
                    name="make_active",
                    type="boolean",
                    description="If true (default), also set this path as the active chat focus.",
                    required=False,
                    default=True,
                ),
            ],
        )

    def get_prompt_hints(self, language: str = "en") -> ToolPromptHints:
        return ToolPromptHints(
            short_description="Pin a mastery path to the map and chat focus.",
            when_to_use=(
                "When the learner clearly wants to work toward mastering a topic "
                "that already has a mastery path."
            ),
            input_format='path_id (required), make_active (optional bool)',
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        path_id = str(kwargs.get("path_id") or "").strip()
        if not path_id:
            return ToolResult(content="path_id is required", success=False)
        make_active = kwargs.get("make_active", True)
        if isinstance(make_active, str):
            make_active = make_active.strip().lower() not in ("0", "false", "no")
        try:
            from deeptutor.learning.storage import LearningStore
            from dotcortex.pins import pin_path

            if not LearningStore().exists(path_id):
                return ToolResult(
                    content=f"No mastery path with id {path_id!r}. List paths first.",
                    success=False,
                )
            state = pin_path(path_id, source="agent", make_active=bool(make_active))
        except Exception as exc:
            return ToolResult(content=f"Could not pin path: {exc}", success=False)
        active = state.get("active_path_id")
        return ToolResult(
            content=(
                f"Pinned mastery path {path_id}. "
                f"Active path: {active or 'none'}. "
                "It appears on the DotCortex map."
            ),
            metadata={"path_id": path_id, "active_path_id": active, "source": "agent"},
        )


def register_pin_tool() -> None:
    from deeptutor.runtime.registry.tool_registry import get_tool_registry

    registry = get_tool_registry()
    if registry.get("pin_mastery_path") is None:
        registry.register(PinMasteryPathTool())
