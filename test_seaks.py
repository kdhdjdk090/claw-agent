"""Full SEAKS integration test."""
import json
from claw_agent.ai_lab.seaks import SEAKS

print("=" * 70)
print("SEAKS — Self-Evolving AI Kernel System")
print("=" * 70)

# Initialize
seaks = SEAKS()
print(f"\nKernel v{seaks.kernel.version} loaded")
print(f"Difficulty: {seaks.kernel.rules.difficulty_level}")
print(f"Judge strictness: {seaks.kernel.rules.judge_strictness:.0%}")

# Run full test suite first
print("\n" + "=" * 70)
print("PHASE 1: Full Test Suite")
print("=" * 70)
suite = seaks.run_full_suite()
for r in suite["results"]:
    grade_icon = {"ELITE": "✅", "PASS": "✅", "MEDIUM": "⚠️", "FAIL": "❌"}.get(r["grade"], "?")
    print(f"  {grade_icon} {r['task_type']}: {r['grade']} (score: {r['score']:.2f})")
print(f"\n  Overall: {suite['overall_grade']}")
print(f"  Fitness: {suite['metrics']['fitness']:.3f}")
print(f"  Accuracy: {suite['metrics']['accuracy']:.3f}")
print(f"  Hallucination rate: {suite['metrics']['hallucination_rate']:.3f}")

# Run evolution cycles
print("\n" + "=" * 70)
print("PHASE 2: Evolution (20 cycles)")
print("=" * 70)
evo = seaks.run_full_evolution(cycles=20)
print(f"  Cycles run: {evo['cycles_run']}")
print(f"  Version: v{evo['initial_version']} → v{evo['final_version']}")
print(f"  Final fitness: {evo['final_fitness']:.3f}")
print(f"  Accuracy: {evo['accuracy']:.3f}")
print(f"  Hallucination rate: {evo['hallucination_rate']:.3f}")
print(f"  Consistency: {evo['consistency']:.3f}")
print(f"  Passes: {evo['total_passes']}/{evo['total_passes'] + evo['total_fails']}")
print(f"  Difficulty level: {evo['difficulty_level']}")

# Audit for drift
print("\n" + "=" * 70)
print("PHASE 3: Anti-Drift Audit")
print("=" * 70)
audit = seaks.audit()
drift = audit["drift_status"]
print(f"  Drifting: {drift['drifting']}")
print(f"  Status: {drift['reason']}")
print(f"  Current fitness: {audit['current_fitness']:.3f}")
print(f"  Saved versions: {audit['saved_versions']}")
print(f"  Kernel version: v{audit['current_version']}")

# Show evolved rules
rules = audit["current_rules"]
print(f"\n  Evolved rules:")
print(f"    Judge strictness: {rules['judge_strictness']:.0%}")
print(f"    Difficulty level: {rules['difficulty_level']}")
print(f"    Hallucination gate: {rules['hallucination_gate']}")
print(f"    Min confidence: {rules['min_confidence_to_assert']:.0%}")
print(f"    Step-by-step: {rules['require_step_by_step']}")
print(f"    Verification: {rules['require_verification']}")

# System prompt patch
print("\n" + "=" * 70)
print("SYSTEM PROMPT PATCH (injected into Claw)")
print("=" * 70)
print(seaks.get_system_prompt_patch())

# Final arena test
print("\n" + "=" * 70)
print("PHASE 4: Post-Evolution Arena Test")
print("=" * 70)
from claw_agent.ai_lab.reasoning_engine import run_full_arena_test
arena = run_full_arena_test()
for part, data in arena["parts"].items():
    v = "✅" if data.get("verified") else "⚠️"
    print(f"  {v} {part}: {data['notes'][:60]}")
print(f"\n  VERDICT: {arena['audit']['verdict']}")
print(f"  Confidence: {arena['audit']['confidence']}%")
