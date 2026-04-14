"""Debug which test cases fail."""
from claw_agent.ai_lab.reasoning_engine import predict_next_number, deep_pattern_analysis

test_cases = [
    ([1, 2, 4, 8, 15, 16], "ambiguous"),
    ([2, 4, 6, 8], 10),
    ([1, 2, 4, 8, 16], 32),
    ([1, 4, 9, 16, 25], 36),
    ([], "ambiguous"),
    ([5], "ambiguous"),
]

for seq, expected in test_cases:
    actual = predict_next_number(seq)
    status = "PASS" if actual == expected else "FAIL"
    print(f"  {status}: input={seq}, expected={expected}, got={actual}")
    if status == "FAIL":
        analysis = deep_pattern_analysis([float(x) for x in seq] if seq else [])
        print(f"    Analysis: conclusion={analysis['conclusion']}, predicted={analysis['predicted_next']}")
        for h in analysis.get("hypotheses", []):
            print(f"    Hypothesis: {h.name} -> {h.predicted_next} (confidence={h.confidence}, fits_all={h.fits_all})")
