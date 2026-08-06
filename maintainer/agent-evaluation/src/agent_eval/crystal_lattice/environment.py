"""Crystal Lattice implementation of the generic run environment."""

from __future__ import annotations

import hashlib
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator, Mapping

from agent_app import AgentApplication, InMemoryApplicationNotificationStore
from agent_core import AgentCore

from agent_eval.services import RunServices

from .context import CrystalLatticeContext
from .requests import RequestDriver, application_request_driver
from .snapshots import (
    CrystalLatticeSnapshot,
    CrystalSnapshotter,
    application_session_snapshot,
    restore_session,
)


ApplicationFactory = Callable[..., AgentApplication]


class CrystalLatticeEnvironment:
    """Run Crystal Lattice Core/Application in an isolated local lifecycle."""

    def __init__(
        self,
        *,
        config_path: Path,
        env_overrides: Mapping[str, str] | None = None,
        config_env: Mapping[str, str] | None = None,
        core_factory: Callable[[], AgentCore] = AgentCore,
        application_factory: ApplicationFactory = AgentApplication,
        default_agent: str | None = None,
        request_driver: RequestDriver | None = None,
        snapshotter: CrystalSnapshotter = application_session_snapshot,
    ) -> None:
        self.config_path = config_path.expanduser().resolve()
        self.env_overrides = dict(env_overrides or {})
        self.config_env = dict(config_env or {})
        self.core_factory = core_factory
        self.application_factory = application_factory
        self.default_agent = default_agent
        self.request_driver = request_driver or application_request_driver()
        self.snapshotter = snapshotter

    @classmethod
    def from_config(
        cls,
        config_path: str | Path,
        *,
        environment: Mapping[str, str] | None = None,
        config_env: Mapping[str, str] | None = None,
        core_factory: Callable[[], AgentCore] = AgentCore,
        application_factory: ApplicationFactory = AgentApplication,
        default_agent: str | None = None,
        request_driver: RequestDriver | None = None,
        snapshotter: CrystalSnapshotter = application_session_snapshot,
    ) -> "CrystalLatticeEnvironment":
        return cls(
            config_path=Path(config_path),
            env_overrides=environment,
            config_env=config_env,
            core_factory=core_factory,
            application_factory=application_factory,
            default_agent=default_agent,
            request_driver=request_driver,
            snapshotter=snapshotter,
        )

    def fingerprint(self) -> object:
        return {
            "type": "crystal-lattice",
            "schema": 1,
            "config_path": str(self.config_path),
            "config_sha256": hashlib.sha256(
                self.config_path.read_bytes()
            ).hexdigest(),
            "env_overrides": _hashed_mapping(self.env_overrides),
            "config_env": _hashed_mapping(self.config_env),
            "core_factory": _callable_name(self.core_factory),
            "application_factory": _callable_name(self.application_factory),
            "default_agent": self.default_agent,
            "request_driver": _callable_name(self.request_driver),
            "snapshotter": _callable_name(self.snapshotter),
        }

    @contextmanager
    def open(
        self,
        *,
        services: RunServices,
        workspace: Path | None,
        parent_snapshot: object | None,
    ) -> Iterator[CrystalLatticeContext]:
        runtime_root = Path(
            tempfile.mkdtemp(
                prefix=".crystal-lattice-runtime-",
                dir=services.artifact_dir,
            )
        )
        session_root = runtime_root / "sessions"
        application = self.application_factory(
            self.config_path,
            session_root,
            core_factory=self.core_factory,
            env_overrides=self.env_overrides,
            config_env=self.config_env,
            replay_server_settings_on_startup=False,
            application_notification_store=InMemoryApplicationNotificationStore(),
        )
        context = CrystalLatticeContext(
            application=application,
            workspace=workspace,
            services=services,
            default_request_driver=self.request_driver,
        )
        try:
            if parent_snapshot is not None:
                if not isinstance(parent_snapshot, CrystalLatticeSnapshot):
                    raise TypeError(
                        "CrystalLatticeEnvironment requires "
                        "CrystalLatticeSnapshot parent state"
                    )
                restored = restore_session(
                    parent_snapshot,
                    workspace_root=str(workspace) if workspace is not None else None,
                )
                if restored is not None:
                    context.restore_session(restored)
                context.config.update(parent_snapshot.request_defaults)
            elif self.default_agent is not None:
                context.start(self.default_agent)
            yield context
        finally:
            application.close()
            shutil.rmtree(runtime_root, ignore_errors=True)

    def snapshot(
        self,
        context: CrystalLatticeContext,
    ) -> object | None:
        return self.snapshotter(context)

    def finalize(self, context: CrystalLatticeContext) -> object:
        if context.session_or_none is not None:
            context.services.artifacts.write_json(
                "raw/environment/crystal-lattice-session.json",
                context.session.to_dict(),
            )
        context.services.artifacts.write_json(
            "raw/environment/crystal-lattice-observation.json",
            context.observation(),
        )
        return context.observation()

    def serialize_snapshot(self, snapshot: object) -> bytes:
        if not isinstance(snapshot, CrystalLatticeSnapshot):
            raise TypeError(
                "CrystalLatticeEnvironment can only serialize "
                "CrystalLatticeSnapshot"
            )
        return snapshot.to_bytes()

    def deserialize_snapshot(self, data: bytes) -> object:
        return CrystalLatticeSnapshot.from_bytes(data)


def _hashed_mapping(values: Mapping[str, str]) -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "name": key,
            "sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
        }
        for key, value in sorted(values.items())
    )


def _callable_name(value: object) -> str:
    module = getattr(value, "__module__", type(value).__module__)
    qualname = getattr(value, "__qualname__", type(value).__qualname__)
    return f"{module}.{qualname}"