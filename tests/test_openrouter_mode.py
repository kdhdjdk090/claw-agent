from __future__ import annotations

import unittest
from unittest.mock import patch

import claw_agent.agent as agent
import claw_agent.cli as cli


class OpenRouterModeTests(unittest.TestCase):
    def test_detect_runtime_mode_supports_openrouter_direct(self) -> None:
        with patch.object(agent, "OPENROUTER_API_KEY", "test-openrouter-key"), \
             patch.object(agent, "DEEPSEEK_API_KEY", ""), \
             patch.object(agent, "USE_COUNCIL", False):
            mode = cli._get_runtime_mode()

        self.assertEqual(mode["kind"], "openrouter")
        self.assertIn("OpenRouter", mode["detail"])

    @patch("httpx.get", side_effect=Exception("ollama offline"))
    def test_list_models_returns_cloud_models_for_openrouter_direct(self, _mock_get) -> None:
        with patch.object(agent, "OPENROUTER_API_KEY", "test-openrouter-key"), \
             patch.object(agent, "DEEPSEEK_API_KEY", ""), \
             patch.object(agent, "USE_COUNCIL", False):
            models = cli.list_models()

        self.assertTrue(models)
        self.assertEqual(agent.DEFAULT_MODEL, agent._get_openrouter_direct_models()[0])
        self.assertIn(agent.DEFAULT_MODEL, models)


if __name__ == "__main__":
    unittest.main()
