"""Run the full arena test."""
from claw_agent.ai_lab.reasoning_engine import run_full_arena_test
import json

result = run_full_arena_test()

print("=" * 70)
print("ARENA TEST RESULTS")
print("=" * 70)

for part_name, part_data in result["parts"].items():
    verified = part_data.get("verified", "?")
    notes = part_data["notes"]
    print(f"\n--- {part_name} ---")
    print(f"  Verified: {verified}")
    print(f"  Notes: {notes}")

print()
print("=" * 70)
print("FINAL AUDIT")
print("=" * 70)
audit = result["audit"]
print(f"Scores: {json.dumps(audit['scores'], indent=2)}")
print(f"Confidence: {audit['confidence']}%")
print(f"Hardest: {audit['hardest']}")
print(f"Mistakes: {audit['mistakes']}")
print(f"Verdict: {audit['verdict']}")
