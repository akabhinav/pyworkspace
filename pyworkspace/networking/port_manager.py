"""Port allocation for workspace services."""
from __future__ import annotations
import structlog
from pyworkspace.config.settings import get_settings

logger = structlog.get_logger()

class PortManager:
    """Allocates unique external ports for workspace services."""

    def __init__(self):
        settings = get_settings()
        self._range_start = settings.PORT_RANGE_START
        self._range_end = settings.PORT_RANGE_END
        self._allocated: dict[str, int] = {}  # "workspace_id:service_name" -> port
        self._used_ports: set[int] = set()

    def allocate(self, workspace_id: str, service_name: str) -> int:
        key = f"{workspace_id}:{service_name}"
        if key in self._allocated:
            return self._allocated[key]

        for port in range(self._range_start, self._range_end):
            if port not in self._used_ports:
                self._used_ports.add(port)
                self._allocated[key] = port
                logger.info("port_allocated", workspace_id=workspace_id, service=service_name, port=port)
                return port

        raise RuntimeError("No available ports in configured range")

    def release(self, workspace_id: str, service_name: str) -> None:
        key = f"{workspace_id}:{service_name}"
        port = self._allocated.pop(key, None)
        if port is not None:
            self._used_ports.discard(port)
            logger.info("port_released", workspace_id=workspace_id, service=service_name, port=port)

    def release_workspace(self, workspace_id: str) -> None:
        prefix = f"{workspace_id}:"
        to_remove = [k for k in self._allocated if k.startswith(prefix)]
        for key in to_remove:
            port = self._allocated.pop(key)
            self._used_ports.discard(port)
        if to_remove:
            logger.info("ports_released_for_workspace", workspace_id=workspace_id, count=len(to_remove))

    def get_port(self, workspace_id: str, service_name: str) -> int | None:
        return self._allocated.get(f"{workspace_id}:{service_name}")
