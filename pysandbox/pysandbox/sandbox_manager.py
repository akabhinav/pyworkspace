import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class SandboxInfo:
    sandbox_id: str
    language: str
    timeout_seconds: int
    memory_mb: int
    status: str
    created_at: datetime
    workspace_id: str | None = None


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: int


class SandboxManager:
    def __init__(self) -> None:
        self._sandboxes: dict[str, SandboxInfo] = {}

    def create_sandbox(
        self,
        language: str = "python",
        timeout: int = 300,
        memory: int = 512,
        workspace_id: str | None = None,
    ) -> SandboxInfo:
        sandbox_id = str(uuid.uuid4())
        info = SandboxInfo(
            sandbox_id=sandbox_id,
            language=language,
            timeout_seconds=timeout,
            memory_mb=memory,
            status="running",
            created_at=datetime.now(timezone.utc),
            workspace_id=workspace_id,
        )
        self._sandboxes[sandbox_id] = info
        return info

    def execute_code(self, sandbox_id: str, code: str, stdin: str = "") -> ExecutionResult:
        if sandbox_id not in self._sandboxes:
            raise KeyError(f"Sandbox {sandbox_id} not found")

        start = time.monotonic()

        # Simulate execution based on code content
        if "import time" in code:
            time.sleep(0.1)

        if "raise" in code or "error" in code.lower():
            stderr = "Traceback (most recent call last):\n  Error in user code"
            stdout = ""
            exit_code = 1
        elif "print(" in code:
            # Extract the argument to print()
            try:
                # Handle simple print('...') or print("...")
                idx = code.index("print(")
                rest = code[idx + 6:]
                # Find matching closing paren
                depth = 1
                end = 0
                for i, ch in enumerate(rest):
                    if ch == "(":
                        depth += 1
                    elif ch == ")":
                        depth -= 1
                    if depth == 0:
                        end = i
                        break
                arg = rest[:end].strip()
                # Remove surrounding quotes
                if (arg.startswith("'") and arg.endswith("'")) or (
                    arg.startswith('"') and arg.endswith('"')
                ):
                    arg = arg[1:-1]
                stdout = arg + "\n"
            except (ValueError, IndexError):
                stdout = code + "\n"
            stderr = ""
            exit_code = 0
        else:
            stdout = code + "\n"
            stderr = ""
            exit_code = 0

        elapsed_ms = int((time.monotonic() - start) * 1000)

        return ExecutionResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            execution_time_ms=elapsed_ms,
        )

    def destroy_sandbox(self, sandbox_id: str) -> None:
        if sandbox_id not in self._sandboxes:
            raise KeyError(f"Sandbox {sandbox_id} not found")
        del self._sandboxes[sandbox_id]

    def list_sandboxes(self) -> list[SandboxInfo]:
        return list(self._sandboxes.values())

    def get_sandbox(self, sandbox_id: str) -> SandboxInfo:
        if sandbox_id not in self._sandboxes:
            raise KeyError(f"Sandbox {sandbox_id} not found")
        return self._sandboxes[sandbox_id]

    def destroy_sandboxes_for_workspace(self, workspace_id: str) -> int:
        to_remove = [
            sid for sid, info in self._sandboxes.items()
            if info.workspace_id == workspace_id
        ]
        for sid in to_remove:
            del self._sandboxes[sid]
        return len(to_remove)


# Global singleton
sandbox_manager = SandboxManager()
