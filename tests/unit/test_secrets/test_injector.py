import pytest

from pyworkspace.secrets.injector import SecretInjector


class TestSecretInjector:
    @pytest.mark.asyncio
    async def test_inject_without_vault(self):
        injector = SecretInjector(vault_client=None)
        pod_spec = {"spec": {"containers": [{"name": "pg", "env": []}]}}
        result = await injector.inject_into_pod_spec(pod_spec, "ws-1", "pg1")
        # Should return pod_spec unchanged
        assert result == pod_spec

    @pytest.mark.asyncio
    async def test_build_env_vars(self):
        injector = SecretInjector(vault_client=None)
        services = [
            {"env_vars": {"DB_URL": "postgres://...", "DB_HOST": "pg1"}},
            {"env_vars": {"REDIS_URL": "redis://..."}},
        ]
        env = await injector.build_env_vars("ws-1", services)
        assert env["DB_URL"] == "postgres://..."
        assert env["REDIS_URL"] == "redis://..."
        assert len(env) == 3
