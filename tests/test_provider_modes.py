from __future__ import annotations

import importlib
import os
import unittest
from unittest import mock


class ProviderModeTests(unittest.TestCase):
    def _reload_modules(self):
        import claw_agent.agent as agent_mod
        import claw_agent.cli as cli_mod

        agent_mod = importlib.reload(agent_mod)
        cli_mod = importlib.reload(cli_mod)
        return agent_mod, cli_mod

    def test_openrouter_direct_mode_lists_cloud_models_when_council_disabled(self) -> None:
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key", "DISABLE_COUNCIL": "1"}, clear=False):
            os.environ.pop("DEEPSEEK_API_KEY", None)
            agent_mod, cli_mod = self._reload_modules()
            models = cli_mod.list_models()
            self.assertIn(agent_mod.DEFAULT_MODEL, models)

    def test_council_mode_keeps_combined_provider_models_visible(self) -> None:
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}, clear=False):
            agent_mod, cli_mod = self._reload_modules()
            models = cli_mod.list_models()
            self.assertGreaterEqual(len(models), len(set(models)))
            if getattr(agent_mod, "USE_CODEX", False):
                from claw_agent.codex_runtime import _detect_provider, FREE_ROLE_MODELS
                provider = _detect_provider()
                role_models = FREE_ROLE_MODELS.get(provider, {})
                unique = {m for mlist in role_models.values() for m in mlist}
                self.assertGreaterEqual(len(models), len(unique))
            else:
                self.assertGreaterEqual(len(models), len(getattr(importlib.import_module("claw_agent.ll_council"), "DEFAULT_COUNCIL_MODELS")))


if __name__ == "__main__":
    unittest.main()
