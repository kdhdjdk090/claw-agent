"""Test SEAKS at higher difficulty levels."""
from claw_agent.ai_lab.seaks import SEAKS, Kernel, KernelRules

# Start at difficulty 5
rules = KernelRules(difficulty_level=5)
kernel = Kernel(rules=rules)
seaks = SEAKS(kernel=kernel)

print("Testing difficulty 5 suite:")
suite = seaks.run_full_suite()
for r in suite["results"]:
    icon = {"ELITE": "V", "PASS": "V", "MEDIUM": "~", "FAIL": "X"}[r["grade"]]
    ttype = r["task_type"]
    grade = r["grade"]
    score = r["score"]
    print(f"  [{icon}] {ttype}: {grade} ({score:.2f})")
print(f"Overall: {suite['overall_grade']}")
print(f"Fitness: {suite['metrics']['fitness']:.3f}")

# Now difficulty 8
print()
print("Testing difficulty 8 suite:")
rules8 = KernelRules(difficulty_level=8, include_missing_variables=True)
kernel8 = Kernel(rules=rules8)
seaks8 = SEAKS(kernel=kernel8)
suite8 = seaks8.run_full_suite()
for r in suite8["results"]:
    icon = {"ELITE": "V", "PASS": "V", "MEDIUM": "~", "FAIL": "X"}[r["grade"]]
    ttype = r["task_type"]
    grade = r["grade"]
    score = r["score"]
    print(f"  [{icon}] {ttype}: {grade} ({score:.2f})")
print(f"Overall (difficulty 8): {suite8['overall_grade']}")
print(f"Fitness: {suite8['metrics']['fitness']:.3f}")
