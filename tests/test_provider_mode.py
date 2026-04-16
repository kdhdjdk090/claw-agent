from __future__ import annotations

import unittest
from unittest.mock import patch

import claw_agent.agent as agent


class ProviderModeTests(unittest.TestCase):
    def test_prefers_openrouter_direct_when_council_disabled(self) -> None:
        with patch.object(agent, "OPENROUTER_API_KEY", "or-key"), patch.object(agent, "DEEPSEEK_API_KEY", "ds-key"), patch.dict(
            "os.environ",
            {"DISABLE_COUNCIL": "1"},
            clear=False,
        ):
            self.assertEqual(agent.get_runtime_provider_mode(), "openrouter")

    def test_uses_council_when_openrouter_available_and_not_disabled(self) -> None:
        with patch.object(agent, "OPENROUTER_API_KEY", "or-key"), patch.object(agent, "DEEPSEEK_API_KEY", ""), patch.dict(
            "os.environ",
            {},
            clear=False,
        ):
            self.assertIn(agent.get_runtime_provider_mode(), ("council", "codex"))

    def test_falls_back_to_deepseek_without_openrouter(self) -> None:
        with patch.object(agent, "OPENROUTER_API_KEY", ""), patch.object(agent, "DEEPSEEK_API_KEY", "ds-key"), patch.dict(
            "os.environ",
            {},
            clear=False,
        ):
            self.assertEqual(agent.get_runtime_provider_mode(), "deepseek")


if __name__ == "__main__":
    unittest.main()
