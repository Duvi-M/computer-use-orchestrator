from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ToolGrant(StrEnum):
    BROWSER = "browser"
    SHELL = "shell"
    FILE_SYSTEM = "file_system"
    DESKTOP = "desktop"
    NETWORK = "network"


@dataclass(frozen=True)
class ToolGrantPolicy:
    allowed: frozenset[ToolGrant] = field(default_factory=frozenset)
    denied_reason: str = "Tool grant is not enabled for this session"

    @classmethod
    def local_demo_default(cls) -> ToolGrantPolicy:
        return cls(
            allowed=frozenset(
                {
                    ToolGrant.BROWSER,
                    ToolGrant.DESKTOP,
                    ToolGrant.NETWORK,
                    ToolGrant.FILE_SYSTEM,
                }
            )
        )

    @classmethod
    def locked_down(cls) -> ToolGrantPolicy:
        return cls(allowed=frozenset())

    def allows(self, grant: ToolGrant | str) -> bool:
        return ToolGrant(grant) in self.allowed

    def require(self, grant: ToolGrant | str) -> None:
        if not self.allows(grant):
            raise PermissionError(f"{ToolGrant(grant).value}: {self.denied_reason}")
