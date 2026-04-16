from __future__ import annotations

import importlib
import os
import unittest
from unittest import mock


class CouncilReportingTests(unittest.TestCase):
    def _reload_modules(self):
        import claw_agent.agent as agent_mod
        import claw_agent.cli as cli_mod
        import claw_agent.ll_council as council_mod
        import claw_agent.ll_council_advanced as advanced_mod

        agent_mod = importlib.reload(agent_mod)
        council_mod = importlib.reload(council_mod)
        advanced_mod = importlib.reload(advanced_mod)
        cli_mod = importlib.reload(cli_mod)
        agent_mod = importlib.reload(agent_mod)
        cli_mod = importlib.reload(cli_mod)
        return agent_mod, cli_mod, council_mod, advanced_mod

    def test_runtime_mode_detail_uses_live_council_roster(self) -> None:
        env = {
            "OPENROUTER_API_KEY": "test-openrouter-key",
            "DASHSCOPE_API_KEY": "test-dashscope-key",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            os.environ.pop("COMETAPI_KEY", None)
            os.environ.pop("COUNCIL_MODELS", None)
            _, cli_mod, council_mod, _ = self._reload_modules()

            mode = cli_mod._get_runtime_mode()
            detail = mode["detail"]

            if mode["kind"] == "codex":
                from claw_agent.codex_runtime import _detect_provider, FREE_ROLE_MODELS
                provider = _detect_provider()
                role_models = FREE_ROLE_MODELS.get(provider, {})
                self.assertEqual(
                    detail,
                    f"{len(role_models)} roles via {provider.title()}",
                )
            else:
                self.assertEqual(
                    detail,
                    f"{len(council_mod.DEFAULT_COUNCIL_MODELS)} models via Alibaba + OpenRouter",
                )

    def test_advanced_council_uses_same_default_roster_as_base_council(self) -> None:
        env = {
            "OPENROUTER_API_KEY": "test-openrouter-key",
            "DASHSCOPE_API_KEY": "test-dashscope-key",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            os.environ.pop("COMETAPI_KEY", None)
            os.environ.pop("COUNCIL_MODELS", None)
            _, _, council_mod, advanced_mod = self._reload_modules()

            self.assertEqual(
                advanced_mod.DEFAULT_COUNCIL_MODELS,
                council_mod.DEFAULT_COUNCIL_MODELS,
            )


if __name__ == "__main__":
    unittest.main()