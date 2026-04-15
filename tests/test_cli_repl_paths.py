from __future__ import annotations

import unittest
from unittest.mock import patch

from prompt_toolkit.history import FileHistory

import claw_agent.agent as agent_mod
import claw_agent.cli as cli_mod


class _FakeCloudStream:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def raise_for_status(self) -> None:
        return None

    def iter_lines(self):
        yield 'data: {"choices":[{"delta":{"content":"Summary"},"finish_reason":null}]}'
        yield 'data: {"choices":[{"delta":{},"finish_reason":"stop"}],"usage":{"prompt_tokens":3,"completion_tokens":4}}'


class CliReplPathTests(unittest.TestCase):
    def test_build_prompt_session_uses_single_line_history_prompt(self) -> None:
        with patch.object(cli_mod, "PromptSession", return_value=object()) as prompt_session_cls:
            prompt_session = cli_mod._build_prompt_session()

        self.assertIs(prompt_session, prompt_session_cls.return_value)
        self.assertFalse(prompt_session_cls.call_args.kwargs["multiline"])
        self.assertIsInstance(prompt_session_cls.call_args.kwargs["history"], FileHistory)
        self.assertNotIn("key_bindings", prompt_session_cls.call_args.kwargs)

    def test_iteration_limit_summary_uses_cloud_chat_completions_endpoint(self) -> None:
        agent = agent_mod.Agent(model="test-model", base_url="https://openrouter.ai/api/v1")
        agent.is_cloud = True
        agent._max_iterations = 0

        with patch.object(agent.client, "stream", return_value=_FakeCloudStream()) as stream_mock:
            events = list(agent._stream_loop())

        self.assertEqual(
            stream_mock.call_args.args[1],
            "https://openrouter.ai/api/v1/chat/completions",
        )
        self.assertIsInstance(events[-1], agent_mod.AgentDone)
        self.assertEqual(events[-1].final_text, "Summary")


if __name__ == "__main__":
    unittest.main()
