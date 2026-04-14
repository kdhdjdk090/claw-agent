from __future__ import annotations

import unittest
from unittest.mock import Mock

import claw_agent.agent as agent_mod


class CouncilStreamingTests(unittest.TestCase):
    def test_stream_chat_uses_council_when_available(self) -> None:
        agent = agent_mod.Agent(model="test", base_url="http://localhost:11434")
        agent.council = Mock()
        agent.council.query_council.return_value = type("CouncilResult", (), {"consensus_answer": "Council answer"})()

        events = list(agent.stream_chat("hello"))

        agent.council.query_council.assert_called_once_with("hello")
        self.assertIsInstance(events[-1], agent_mod.AgentDone)
        self.assertEqual(events[-1].final_text, "Council answer")


if __name__ == "__main__":
    unittest.main()
