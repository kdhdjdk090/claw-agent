from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import httpx

import claw_agent.agent as agent_mod
import claw_agent.cli as cli_mod
from claw_agent.sessions import Session


class CouncilStreamingTests(unittest.TestCase):
    def test_make_agent_resolves_council_to_real_model(self) -> None:
        import claw_agent.cli as cli_mod

        agent = cli_mod.make_agent("council")

        self.assertNotEqual(agent.model, "council")
        self.assertEqual(agent.session.model, agent.model)

    def test_stream_chat_uses_council_when_available(self) -> None:
        agent = agent_mod.Agent(model="test", base_url="http://localhost:11434")
        agent.council = Mock()
        agent.council.query_council.return_value = type("CouncilResult", (), {"consensus_answer": "Council answer"})()

        events = list(agent.stream_chat("hello"))

        agent.council.query_council.assert_called_once_with("hello")
        self.assertIsInstance(events[-1], agent_mod.AgentDone)
        self.assertEqual(events[-1].final_text, "Council answer")

    def test_stream_chat_bypasses_council_for_live_tool_query(self) -> None:
        agent = agent_mod.Agent(model="test", base_url="http://localhost:11434")
        agent.council = Mock()

        def fake_stream_loop():
            yield agent_mod.TextDelta("Fetched answer")
            yield agent_mod.AgentDone("Fetched answer")

        agent._stream_loop = fake_stream_loop

        events = list(agent.stream_chat("search web about todays stock market"))

        agent.council.query_council.assert_not_called()
        self.assertEqual(events[-1].final_text, "Fetched answer")

    def test_stream_chat_bypasses_council_for_real_world_question_and_injects_grounding(self) -> None:
        agent = agent_mod.Agent(model="test", base_url="http://localhost:11434")
        agent.council = Mock()

        def fake_stream_loop():
            self.assertEqual(agent.messages[-2]["role"], "user")
            self.assertEqual(agent.messages[-2]["content"], "find all info about US Iran war")
            self.assertIn("GROUNDING REQUIRED FOR THIS REQUEST", agent.messages[-1]["content"])
            self.assertIn("web_search first", agent.messages[-1]["content"])
            self.assertIn("Summary, What is verified, What is uncertain, Sources", agent.messages[-1]["content"])
            self.assertIn("US Iran war", agent.messages[-1]["content"])
            yield agent_mod.TextDelta("Grounded answer")
            yield agent_mod.AgentDone("Grounded answer")

        agent._stream_loop = fake_stream_loop

        events = list(agent.stream_chat("find all info about US Iran war"))

        agent.council.query_council.assert_not_called()
        self.assertEqual(events[-1].final_text, "Grounded answer")
        self.assertEqual(agent.session.messages[-1]["content"], "find all info about US Iran war")

    def test_chat_bypasses_council_for_live_tool_query(self) -> None:
        agent = agent_mod.Agent(model="test", base_url="http://localhost:11434")
        agent.council = Mock()

        with patch.object(
            agent_mod.Agent,
            "stream_chat",
            return_value=iter([agent_mod.AgentDone("Tool answer")]),
        ) as stream_chat:
            result = agent.chat("what is date and time now")

        agent.council.query_council.assert_not_called()
        stream_chat.assert_called_once_with("what is date and time now")
        self.assertEqual(result, "Tool answer")

    def test_cli_does_not_render_council_answer_twice(self) -> None:
        council_text = "[Council Vote - No consensus (33%)]\n\nMajority: test"

        class FakeAgent:
            def stream_chat(self, _user_input):
                yield agent_mod.TextDelta(council_text)
                yield agent_mod.AgentDone(council_text)

        with patch.object(cli_mod, "_render_markdown_response") as render_mock, patch.object(cli_mod.console, "print") as print_mock:
            cli_mod.stream_response_enhanced(FakeAgent(), "hello")

        render_mock.assert_called_once_with(council_text)
        duplicated = [call for call in print_mock.call_args_list if council_text in " ".join(str(arg) for arg in call.args)]
        self.assertEqual(duplicated, [])

    def test_stream_chat_syncs_session_even_when_interrupted(self) -> None:
        agent = agent_mod.Agent(model="test", base_url="http://localhost:11434")
        agent.council = None

        def fake_stream_loop():
            raise KeyboardInterrupt()
            yield

        agent._stream_loop = fake_stream_loop

        with self.assertRaises(KeyboardInterrupt):
            list(agent.stream_chat("hello"))

        self.assertEqual(agent.session.total_turns, 1)
        self.assertEqual(agent.session.messages[-1]["content"], "hello")

    def test_make_agent_from_session_preserves_system_prompt_and_session_state(self) -> None:
        session = Session(
            session_id="abc123def456",
            model="council",
            messages=[{"role": "user", "content": "resume me"}],
            total_turns=1,
        )

        agent = cli_mod._make_agent_from_session(session)

        self.assertIs(agent.session, session)
        self.assertEqual(agent.session.model, agent.model)
        self.assertEqual(agent.messages[0]["role"], "system")
        self.assertEqual(agent.messages[1:], session.messages)

    def test_stream_chat_persists_api_errors_into_session_history(self) -> None:
        agent = agent_mod.Agent(model="test", base_url="https://openrouter.ai/api/v1")
        agent.council = None
        agent.is_cloud = True

        class FailingStream:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def raise_for_status(self):
                request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
                response = httpx.Response(404, request=request)
                raise httpx.HTTPStatusError("boom", request=request, response=response)

            def iter_lines(self):
                return iter(())

        with patch.object(agent.client, "stream", return_value=FailingStream()):
            events = list(agent.stream_chat("hello"))

        self.assertEqual(events[-1].final_text, "[API Error: HTTP 404: Not Found]")
        self.assertEqual(agent.session.messages[-1]["content"], "[API Error: HTTP 404: Not Found]")

    def test_stream_chat_answers_simple_time_question_without_provider_call(self) -> None:
        agent = agent_mod.Agent(model="test", base_url="https://openrouter.ai/api/v1")
        agent.council = None
        agent.is_cloud = True

        local_now = datetime(2026, 4, 15, 21, 34, 56)
        utc_now = datetime(2026, 4, 15, 16, 4, 56, tzinfo=timezone.utc)

        def fake_now(tz=None):
            return utc_now if tz is not None else local_now

        with patch.object(agent_mod, "datetime") as mock_datetime, \
             patch.object(agent.client, "stream") as stream_mock:
            mock_datetime.now.side_effect = fake_now
            events = list(agent.stream_chat("what is the time now"))

        stream_mock.assert_not_called()
        self.assertEqual(
            events[-1].final_text,
            "Local time: 21:34:56\nLocal date: Wednesday, 15 April 2026\nUTC: 16:04:56 UTC",
        )
        self.assertEqual(agent.session.messages[-1]["content"], events[-1].final_text)

    def test_stream_chat_answers_ambiguous_now_question_without_provider_call(self) -> None:
        agent = agent_mod.Agent(model="test", base_url="https://openrouter.ai/api/v1")
        agent.council = None
        agent.is_cloud = True

        local_now = datetime(2026, 4, 15, 21, 34, 56)
        utc_now = datetime(2026, 4, 15, 16, 4, 56, tzinfo=timezone.utc)

        def fake_now(tz=None):
            return utc_now if tz is not None else local_now

        with patch.object(agent_mod, "datetime") as mock_datetime, \
             patch.object(agent.client, "stream") as stream_mock:
            mock_datetime.now.side_effect = fake_now
            events = list(agent.stream_chat("what is it now"))

        stream_mock.assert_not_called()
        self.assertEqual(
            events[-1].final_text,
            "Today's date: Wednesday, 15 April 2026\nLocal time: 21:34:56\nUTC: 2026-04-15 16:04:56 UTC",
        )
        self.assertEqual(agent.session.messages[-1]["content"], events[-1].final_text)

    def test_stream_chat_preserves_cloud_tool_contract_after_missing_tool_args(self) -> None:
        agent = agent_mod.Agent(model="test", base_url="https://openrouter.ai/api/v1")
        agent.council = None
        agent.is_cloud = True

        class ToolCallStream:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def raise_for_status(self):
                return None

            def iter_lines(self):
                yield 'data: {"choices":[{"delta":{"tool_calls":[{"id":"call_search_1","type":"function","function":{"name":"web_search","arguments":"{}"}}]}}]}'
                yield 'data: {"choices":[{"delta":{},"finish_reason":"stop"}],"usage":{"prompt_tokens":1,"completion_tokens":1}}'

        class FinalAnswerStream:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def raise_for_status(self):
                return None

            def iter_lines(self):
                yield 'data: {"choices":[{"delta":{"content":"Recovered answer"},"finish_reason":"stop"}],"usage":{"prompt_tokens":1,"completion_tokens":1}}'

        call_count = {"value": 0}

        def stream_side_effect(_method, _url, json=None, headers=None, timeout=None):
            call_count["value"] += 1
            if call_count["value"] == 1:
                return ToolCallStream()

            self.assertIsNotNone(json)
            messages = json["messages"]
            assistant_tool_message = next(
                message for message in reversed(messages)
                if message.get("role") == "assistant" and message.get("tool_calls")
            )
            self.assertEqual(assistant_tool_message["tool_calls"][0]["id"], "call_search_1")
            self.assertEqual(assistant_tool_message["tool_calls"][0]["type"], "function")
            self.assertEqual(assistant_tool_message["tool_calls"][0]["function"]["name"], "web_search")
            self.assertEqual(assistant_tool_message["tool_calls"][0]["function"]["arguments"], "{}")
            self.assertEqual(messages[-1]["role"], "tool")
            self.assertEqual(messages[-1]["tool_call_id"], "call_search_1")
            self.assertIn("missing required argument(s) for tool 'web_search': query", messages[-1]["content"])
            return FinalAnswerStream()

        with patch.object(agent.client, "stream", side_effect=stream_side_effect):
            events = list(agent.stream_chat("what is US Iran situation today"))

        self.assertEqual(events[-1].final_text, "Recovered answer")
        self.assertEqual(call_count["value"], 2)

    def test_stream_chat_retries_openrouter_model_after_model_404(self) -> None:
        agent = agent_mod.Agent(model="missing/model", base_url="https://openrouter.ai/api/v1")
        agent.council = None
        agent.is_cloud = True

        class FailingStream:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def raise_for_status(self):
                request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
                response = httpx.Response(
                    404,
                    request=request,
                    json={"error": {"message": "model not found"}},
                )
                raise httpx.HTTPStatusError("boom", request=request, response=response)

            def iter_lines(self):
                return iter(())

        class SuccessStream:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def raise_for_status(self):
                return None

            def iter_lines(self):
                yield 'data: {"choices":[{"delta":{"content":"Recovered"},"finish_reason":"stop"}],"usage":{"prompt_tokens":1,"completion_tokens":1}}'

        def stream_side_effect(_method, _url, json=None, headers=None, timeout=None):
            if json and json.get("model") == "missing/model":
                return FailingStream()
            return SuccessStream()

        with patch.object(agent_mod, "_get_openrouter_direct_models", return_value=["missing/model", "working/model"]), \
             patch.object(agent.client, "stream", side_effect=stream_side_effect):
            events = list(agent.stream_chat("hello"))

        self.assertEqual(events[-1].final_text, "Recovered")
        self.assertEqual(agent.model, "working/model")
        self.assertEqual(agent.session.model, "working/model")

    def test_stream_chat_retries_openrouter_model_after_rate_limit_429(self) -> None:
        agent = agent_mod.Agent(model="rate-limited/model", base_url="https://openrouter.ai/api/v1")
        agent.council = None
        agent.is_cloud = True

        class FailingStream:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def raise_for_status(self):
                request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
                response = httpx.Response(
                    429,
                    request=request,
                    json={"error": {"message": "Too Many Requests"}},
                )
                raise httpx.HTTPStatusError("boom", request=request, response=response)

            def iter_lines(self):
                return iter(())

        class SuccessStream:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def raise_for_status(self):
                return None

            def iter_lines(self):
                yield 'data: {"choices":[{"delta":{"content":"Recovered after retry"},"finish_reason":"stop"}],"usage":{"prompt_tokens":1,"completion_tokens":1}}'

        def stream_side_effect(_method, _url, json=None, headers=None, timeout=None):
            if json and json.get("model") == "rate-limited/model":
                return FailingStream()
            return SuccessStream()

        with patch.object(agent_mod, "_get_openrouter_direct_models", return_value=["rate-limited/model", "working/model"]), \
             patch.object(agent.client, "stream", side_effect=stream_side_effect):
            events = list(agent.stream_chat("hello"))

        self.assertEqual(events[-1].final_text, "Recovered after retry")
        self.assertEqual(agent.model, "working/model")
        self.assertEqual(agent.session.model, "working/model")


if __name__ == "__main__":
    unittest.main()
