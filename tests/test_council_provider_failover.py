from __future__ import annotations

import unittest
from unittest.mock import patch

from claw_agent.ll_council import ALIBABA_MODELS, OPENROUTER_MODELS, LLCouncil, CouncilResponse


class CouncilProviderFailoverTests(unittest.TestCase):
    def test_openrouter_is_pruned_when_alibaba_can_answer(self) -> None:
        models = [OPENROUTER_MODELS[0], OPENROUTER_MODELS[1], ALIBABA_MODELS[0]]

        def fake_query(council: LLCouncil, model: str, user_message: str) -> CouncilResponse:
            if model in OPENROUTER_MODELS:
                return CouncilResponse(model=model, content="", error="HTTP 429: temporarily rate-limited upstream")
            return CouncilResponse(model=model, content="hello", token_count=3)

        council = LLCouncil(models=models)
        with patch.object(LLCouncil, "_query_model", autospec=True, side_effect=fake_query):
            result = council.query_council("Reply with exactly one word: hello")

        self.assertEqual(council.models, [ALIBABA_MODELS[0]])
        self.assertEqual(len(result.all_responses), 1)
        self.assertNotIn("Partial council", result.consensus_answer)
        self.assertIn("hello", result.consensus_answer.lower())

    def test_last_remaining_provider_error_is_still_reported(self) -> None:
        council = LLCouncil(models=[OPENROUTER_MODELS[0]])

        def fake_query(council: LLCouncil, model: str, user_message: str) -> CouncilResponse:
            return CouncilResponse(model=model, content="", error="HTTP 429: temporarily rate-limited upstream")

        with patch.object(LLCouncil, "_query_model", autospec=True, side_effect=fake_query):
            result = council.query_council("Reply with exactly one word: hello")

        self.assertIn("All 1 council models failed", result.consensus_answer)
        self.assertEqual(council.models, [OPENROUTER_MODELS[0]])