"""Cursor Agent CLI backend — drive the local ``agent`` CLI in headless print mode.

Uses ``agent -p <question> --output-format stream-json --stream-partial-output``:
a newline-delimited JSON event stream (system init, assistant text deltas,
tool_call start/complete, terminal ``result``). We map each event onto a
:class:`SubagentEvent` channel and forward it live so the sidebar shows the
same intermediate steps the user would see in their own terminal.

Auth and config are inherited automatically: the spawned ``agent`` reads the
user's existing Cursor login / ``CURSOR_API_KEY``, so no token is ever
handled here.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from deeptutor.services.subagent.base import OnEvent, SubagentBackend
from deeptutor.services.subagent.config import BackendConfig
from deeptutor.services.subagent.process import (
    compact_field as _compact,
)
from deeptutor.services.subagent.process import (
    probe_version,
    stream_process_lines,
    truncate_field,
)
from deeptutor.services.subagent.types import (
    EVENT_ERROR,
    EVENT_LOG,
    EVENT_TEXT,
    EVENT_TOOL,
    EVENT_TOOL_RESULT,
    ConsultResult,
    DetectResult,
    SubagentEvent,
)

logger = logging.getLogger(__name__)

_TOOL_HEADER_CHARS = 160
# Cursor's --sandbox accepts only these two values.
_CURSOR_SANDBOX = frozenset({"enabled", "disabled"})


class CursorBackend(SubagentBackend):
    kind = "cursor"
    display_name = "Cursor"
    cli_command = "agent"

    async def detect(self) -> DetectResult:
        ok, text = await probe_version([self.cli_command, "--version"])
        return DetectResult(
            kind=self.kind,
            display_name=self.display_name,
            available=ok,
            version=text if ok else "",
            detail="" if ok else (text or "agent CLI not found on PATH"),
        )

    def _build_command(
        self,
        question: str,
        *,
        session_id: str | None,
        fresh_session: bool,
        config: BackendConfig,
        images: list[str] | None = None,
    ) -> list[str]:
        prompt = question
        # No system-prompt flag — prepend once on the session-creating consult
        # (same approach as Kimi); resumed sessions already carry the context.
        if config.system_prompt.strip() and fresh_session:
            prompt = f"{config.system_prompt.strip()}\n\n{question}"
        if images:
            listing = "\n".join(images)
            prompt = (
                f"{prompt}\n\n[The user attached image(s) for this question. View "
                f"them with your file tools before answering:\n{listing}]"
            )
        cmd = [
            self.cli_command,
            "-p",
            prompt,
            "--output-format",
            "stream-json",
            "--stream-partial-output",
            # Headless: trust the workspace without an interactive prompt.
            "--trust",
        ]
        if session_id:
            cmd += ["--resume", session_id]
        if config.auto_approve:
            # Apply file changes / run commands without confirmation.
            cmd.append("--force")
        sandbox = (config.sandbox or "").strip()
        if sandbox in _CURSOR_SANDBOX:
            cmd += ["--sandbox", sandbox]
        if config.model:
            cmd += ["--model", config.model]
        cmd += list(config.extra_args)
        return cmd

    async def consult(
        self,
        question: str,
        *,
        on_event: OnEvent,
        cwd: str | None = None,
        session_id: str | None = None,
        config: BackendConfig | None = None,
        images: list[str] | None = None,
        partner_id: str | None = None,  # noqa: ARG002 — partner-only; ignored here
    ) -> ConsultResult:
        config = config or BackendConfig()
        fresh_session = not session_id
        cmd = self._build_command(
            question,
            session_id=session_id,
            fresh_session=fresh_session,
            config=config,
            images=images,
        )
        result = ConsultResult(session_id=session_id)
        assistant_text: list[str] = []
        # Cumulative streaming text keyed by a stable merge id so the sidebar
        # types the answer out live (only real deltas — see Cursor docs).
        stream: dict[str, Any] = {"acc": "", "merge_id": "cursor:assistant"}

        async def emit(
            kind: str, text: str, raw: dict[str, Any], meta: dict[str, Any] | None = None
        ) -> None:
            result.event_count += 1
            await on_event(SubagentEvent(kind=kind, text=text, raw=raw, meta=meta or {}))

        try:
            async for channel, line in stream_process_lines(cmd, cwd=cwd):
                if channel == "exit":
                    if line != "0" and result.success and not result.final_text:
                        result.success = False
                        result.error = f"agent exited with code {line}"
                        await emit(EVENT_ERROR, result.error, {"returncode": line})
                    continue
                if channel == "stderr":
                    if line.strip():
                        await emit(EVENT_LOG, line, {"stream": "stderr"})
                    continue
                event = _parse_json(line)
                if event is None:
                    if line.strip():
                        await emit(EVENT_LOG, line, {"stream": "stdout"})
                    continue
                await self._handle_event(event, result, assistant_text, stream, emit)
        except Exception as exc:  # pragma: no cover - defensive: surface, don't crash the turn
            logger.warning("cursor consult failed: %s", exc, exc_info=True)
            result.success = False
            result.error = str(exc)
            await emit(EVENT_ERROR, str(exc), {})

        if not result.final_text and assistant_text:
            result.final_text = "\n".join(t for t in assistant_text if t).strip()
        return result

    async def _handle_event(
        self,
        event: dict[str, Any],
        result: ConsultResult,
        assistant_text: list[str],
        stream: dict[str, Any],
        emit: Any,
    ) -> None:
        sid = event.get("session_id")
        if isinstance(sid, str) and sid:
            result.session_id = sid
        etype = str(event.get("type") or "")

        if etype == "system":
            if event.get("subtype") == "init":
                model = str(event.get("model") or "")
                await emit(EVENT_LOG, f"Session started{f' · {model}' if model else ''}", event)
            return

        if etype == "user":
            # Echo of the prompt — noise in the Activity panel.
            return

        if etype == "assistant":
            # With --stream-partial-output, only deltas with timestamp_ms and
            # without model_call_id carry new text; buffered pre-tool flushes
            # and the end-of-turn flush are duplicates and must be skipped.
            has_ts = "timestamp_ms" in event
            has_mc = "model_call_id" in event
            if has_ts and not has_mc:
                piece = _assistant_text(event)
                if piece:
                    stream["acc"] = str(stream.get("acc") or "") + piece
                    text = str(stream["acc"]).strip()
                    if text:
                        await emit(
                            EVENT_TEXT,
                            text,
                            event,
                            {"merge_id": str(stream.get("merge_id") or "cursor:assistant")},
                        )
            return

        if etype == "tool_call":
            subtype = str(event.get("subtype") or "")
            call_id = str(event.get("call_id") or "")
            if subtype == "started":
                await emit(
                    EVENT_TOOL,
                    _render_tool_started(event),
                    event,
                    {"merge_id": f"cursor:tool:{call_id}"} if call_id else None,
                )
            elif subtype == "completed":
                await emit(
                    EVENT_TOOL_RESULT,
                    _render_tool_completed(event),
                    event,
                    {"merge_id": f"cursor:tool:{call_id}"} if call_id else None,
                )
            return

        if etype == "result":
            text = str(event.get("result") or "").strip()
            if text:
                result.final_text = text
            if event.get("is_error") is True:
                result.success = False
            # Answer already streamed as assistant deltas — only surface the
            # result text when nothing was streamed (degenerate run).
            if text and not assistant_text and not stream.get("acc"):
                await emit(EVENT_TEXT, text, event)
            elif stream.get("acc"):
                # Finalize accumulated streaming text as the fallback answer.
                acc = str(stream["acc"]).strip()
                if acc and not result.final_text:
                    result.final_text = acc
                if acc and acc not in assistant_text:
                    assistant_text.append(acc)
            return

        await emit(EVENT_LOG, _compact(event), event)


def _parse_json(line: str) -> dict[str, Any] | None:
    line = line.strip()
    if not line or line[0] not in "{[":
        return None
    try:
        parsed = json.loads(line)
    except (ValueError, TypeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _assistant_text(event: dict[str, Any]) -> str:
    message = event.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text") or ""))
    return "".join(parts)


def _tool_payload(event: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Return (toolName, toolBody) from a Cursor ``tool_call`` object."""
    raw = event.get("tool_call")
    if not isinstance(raw, dict) or not raw:
        return "tool", {}
    # Prefer named *ToolCall keys (readToolCall / writeToolCall / …).
    for key, value in raw.items():
        if not isinstance(value, dict):
            continue
        if key.endswith("ToolCall") or key == "function":
            name = key.removesuffix("ToolCall") if key.endswith("ToolCall") else str(
                value.get("name") or "function"
            )
            return name or "tool", value
    # Fallback: first dict value.
    key, value = next(iter(raw.items()))
    return str(key), value if isinstance(value, dict) else {}


def _render_tool_started(event: dict[str, Any]) -> str:
    name, body = _tool_payload(event)
    args = body.get("args") if isinstance(body.get("args"), dict) else body
    if not isinstance(args, dict):
        return name
    for key in ("command", "path", "file_path", "pattern", "query", "url", "prompt", "description"):
        value = args.get(key)
        if isinstance(value, str) and value.strip():
            return f"{name}({_inline(value)})"
    # function-style: arguments may be a JSON string
    if isinstance(args.get("arguments"), str) and args["arguments"].strip():
        return f"{name}({_inline(args['arguments'])})"
    if args:
        return f"{name}({_inline(_compact(args))})"
    return name


def _render_tool_completed(event: dict[str, Any]) -> str:
    _name, body = _tool_payload(event)
    result = body.get("result")
    if not isinstance(result, dict):
        return truncate_field(_compact(body)) or "(empty result)"
    success = result.get("success")
    if isinstance(success, dict):
        if "content" in success:
            return truncate_field(str(success.get("content") or "")) or "(empty result)"
        if "linesCreated" in success or "fileSize" in success:
            path = str(success.get("path") or body.get("args", {}).get("path") or "")
            lines = success.get("linesCreated", "")
            size = success.get("fileSize", "")
            bits = [b for b in (path, f"{lines} lines" if lines != "" else "", f"{size} B" if size != "" else "") if b]
            return ", ".join(bits) or "ok"
        if "totalLines" in success:
            return f"{success.get('totalLines')} lines"
        return truncate_field(_compact(success)) or "ok"
    if result.get("error"):
        return truncate_field(str(result.get("error"))) or "error"
    return truncate_field(_compact(result)) or "(empty result)"


def _inline(text: str) -> str:
    one_line = " ".join(text.split())
    if len(one_line) > _TOOL_HEADER_CHARS:
        return one_line[:_TOOL_HEADER_CHARS].rstrip() + " …"
    return one_line


__all__ = ["CursorBackend"]
