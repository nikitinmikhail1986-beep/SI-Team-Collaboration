from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol

from .recruitment_runner import RecruitmentResult, RecruitmentRunner, RecruitmentTarget


class HealthAwareAdapter(Protocol):
    def health(self) -> tuple[bool, str]:
        ...


@dataclass(frozen=True)
class RuntimeHealth:
    name: str
    available: bool
    detail: str


@dataclass(frozen=True)
class RuntimeRoute:
    candidate_id: str
    preferred: tuple[str, ...]
    selected: str | None
    reason: str


DEFAULT_INTERNAL_ROUTE = (
    "codex_cli",
    "claude_cli",
    "mcp",
    "a2a",
    "file_queue",
)

DEFAULT_EXTERNAL_ROUTE = (
    "a2a",
    "mcp",
    "codex_cli",
    "claude_cli",
    "file_queue",
)


def adapter_health(name: str, adapter: object) -> RuntimeHealth:
    health = getattr(adapter, "health", None)
    if health is None:
        # A configured adapter without a health() probe is usable only as a fallback.
        return RuntimeHealth(name, True, "configured; no explicit health probe")
    try:
        ok, detail = health()
        return RuntimeHealth(name, bool(ok), str(detail))
    except Exception as exc:
        return RuntimeHealth(name, False, f"{type(exc).__name__}: {exc}")


def health_table(adapters: dict[str, object]) -> list[RuntimeHealth]:
    return [adapter_health(name, adapter) for name, adapter in adapters.items()]


def preferred_transports(target: RecruitmentTarget) -> tuple[str, ...]:
    if target.transport and target.transport != "auto":
        ordered = (target.transport,) + tuple(
            name for name in (DEFAULT_INTERNAL_ROUTE if target.source == "internal" else DEFAULT_EXTERNAL_ROUTE)
            if name != target.transport
        )
        return ordered
    return DEFAULT_INTERNAL_ROUTE if target.source == "internal" else DEFAULT_EXTERNAL_ROUTE


def select_transport(target: RecruitmentTarget, adapters: dict[str, object]) -> RuntimeRoute:
    preferred = preferred_transports(target)
    for name in preferred:
        adapter = adapters.get(name)
        if adapter is None:
            continue
        health = adapter_health(name, adapter)
        if health.available:
            return RuntimeRoute(target.candidate_id, preferred, name, health.detail)
    return RuntimeRoute(target.candidate_id, preferred, None, "no healthy transport available")


class FailoverRecruitmentRunner:
    """Selects a healthy transport and falls back on transport-level failure only."""

    def __init__(
        self,
        adapters: dict[str, object],
        constitution_version: str | None = None,
        persistence: object | None = None,
    ):
        self.adapters = adapters
        self.constitution_version = constitution_version
        self.persistence = persistence

    def run_target(self, target: RecruitmentTarget) -> RecruitmentResult:
        attempts: list[str] = []
        for name in preferred_transports(target):
            adapter = self.adapters.get(name)
            if adapter is None:
                continue
            health = adapter_health(name, adapter)
            if not health.available:
                attempts.append(f"{name}:unhealthy")
                continue

            routed = replace(
                target,
                transport=name,
                response_transport=name,
                runtime=target.runtime or name,
            )
            runner = RecruitmentRunner(
                {name: adapter},
                constitution_version=self.constitution_version,
                persistence=self.persistence,
            )
            try:
                result = runner.run_target(routed)
            except Exception as exc:
                attempts.append(f"{name}:{type(exc).__name__}")
                continue

            # Candidate decisions and completed responses are final; do not route around them.
            if result.state in {
                "registered",
                "declined",
                "needs_conditions",
                "baseline_failed",
                "rejected_response",
                "already_registered",
                "awaiting_response",
            }:
                detail = result.detail
                prefix = f"transport={name}"
                return replace(result, detail=f"{prefix}; {detail}" if detail else prefix)

            attempts.append(f"{name}:{result.state}")

        return RecruitmentResult(
            candidate_id=target.candidate_id,
            source=target.source,
            state="blocked",
            detail="; ".join(attempts) if attempts else "no configured transport",
        )

    def run(self, targets: list[RecruitmentTarget]) -> list[RecruitmentResult]:
        return [self.run_target(target) for target in targets]
