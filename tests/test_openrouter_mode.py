from __future__ import annotations

import unittest
from unittest.mock import patch

import claw_agent.agent as agent
import claw_agent.cli as cli


class OpenRouterModeTests(unittest.TestCase):
    def test_detect_runtime_mode_supports_nvidia_direct(self) -> None:
        with patch.object(agent, "NVIDIA_API_KEY", "test-nvidia-key"), \
             patch.object(agent, "DEEPSEEK_API_KEY", ""), \
             patch.object(agent, "USE_COUNCIL", False), \
             patch.object(agent, "USE_CODEX", False):
            mode = cli._get_runtime_mode()

        self.assertEqual(mode["kind"], "nvidia")
        self.assertIn("NVIDIA NIM", mode["detail"])

    @patch("httpx.get", side_effect=Exception("ollama offline"))
    def test_list_models_returns_cloud_models_for_nvidia_direct(self, _mock_get) -> None:
        with patch.object(agent, "NVIDIA_API_KEY", "test-nvidia-key"), \
             patch.object(agent, "DEEPSEEK_API_KEY", ""), \
             patch.object(agent, "USE_COUNCIL", False), \
             patch.object(agent, "USE_CODEX", False):
            models = cli.list_models()

        self.assertTrue(models)
        first_nvidia_model = agent._get_nvidia_direct_models()[0]
        self.assertIn(first_nvidia_model, models)


if __name__ == "__main__":
    unittest.main()
