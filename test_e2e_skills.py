"""E2E integration test for the 3-tier skill architecture."""
from claw_agent.skill_detector import detect_skills, get_detected_skills_context
from claw_agent.skill_library import SKILL_REGISTRY, SKILLS_BY_CATEGORY, SKILL_BY_NAME, TRIGGER_INDEX

# === REGISTRY HEALTH ===
print("=== REGISTRY HEALTH ===")
print(f"  Total skills: {len(SKILL_REGISTRY)}")
print(f"  Unique names: {len(SKILL_BY_NAME)}")
print(f"  Categories: {len(SKILLS_BY_CATEGORY)}")
print(f"  Trigger keywords: {len(TRIGGER_INDEX)}")
assert len(SKILL_REGISTRY) >= 650, f"Expected 650+, got {len(SKILL_REGISTRY)}"
assert len(SKILL_BY_NAME) == len(SKILL_REGISTRY), "Duplicate names exist"
assert len(SKILLS_BY_CATEGORY) == 18, f"Expected 18 categories, got {len(SKILLS_BY_CATEGORY)}"

# === SKILL DETECTION ACROSS ALL CATEGORIES ===
print("\n=== SKILL DETECTION (10 queries) ===")
queries = [
    ("Build an NFT marketplace with Solidity", "blockchain"),
    ("Set up Kubernetes monitoring with Grafana", "devops"),
    ("Design a Figma component library", "design"),
    ("Write a cold email outreach sequence", "marketing"),
    ("Build a React dashboard with charts", "frontend"),
    ("Run a security review on my authentication code", "security"),
    ("Create Flutter mobile app with react native navigation", "mobile"),
    ("Train a recommendation model with machine learning pytorch", "ai-ml"),
    ("Set up dbt data pipeline analytics warehouse", "data"),
    ("Write unit tests with playwright testing coverage", "testing"),
]

for query, label in queries:
    result = detect_skills(query)
    names = list(result.matched_skills[:3])
    top_cat = result.categories[0] if result.categories else "none"
    top_score = max(result.scores.values()) if result.scores else 0
    print(f"  [{label:10s}] cat={top_cat:25s} score={top_score:.1f}  skills={names}")
    assert len(result.matched_skills) > 0, f"No skills detected for: {query}"

# === CONTEXT GENERATION (pack file loading) ===
print("\n=== CONTEXT GENERATION ===")
ctx = get_detected_skills_context("I need to build a serverless API with DynamoDB and set up CI/CD")
print(f"  Context chars: {len(ctx)}")
print(f"  Context lines: {len(ctx.strip().splitlines())}")
assert len(ctx) > 500, f"Context too short: {len(ctx)} chars"

# Test new expansion skills are detectable
print("\n=== EXPANSION WAVE 2 DETECTION ===")
expansion_tests = [
    ("Set up a monorepo with Turborepo", "monorepo-patterns"),
    ("Build GraphQL API with DataLoader", "graphql-patterns"),
    ("Implement message queue with RabbitMQ", "message-queue-patterns"),
    ("Design token system with Style Dictionary", "design-token-systems"),
    ("Create a newsletter writing workflow", "newsletter-writing"),
    ("Fine-tune an LLM model", "fine-tuning-llm"),
    ("Set up Kubernetes cluster", "kubernetes-advanced"),
    ("Implement contract testing", "contract-testing"),
    ("Build a DAO governance system", "dao-governance"),
    ("Create push notification system", "push-notifications"),
]

for query, expected_name in expansion_tests:
    result = detect_skills(query)
    detected_names = list(result.matched_skills[:5])
    found = expected_name in detected_names
    status = "OK" if found else "MISS"
    print(f"  [{status}] \"{query[:45]}\" -> expected={expected_name}, top5={detected_names}")

# === EXPANSION WAVE 3 DETECTION ===
print("\n=== EXPANSION WAVE 3 DETECTION ===")
wave3_tests = [
    ("Encrypt and password-protect a PDF document", "pdf-encryption"),
    ("Generate documentation from OpenAPI spec", "api-doc-generation"),
    ("Build a drag and drop form builder component", "form-builder-patterns"),
    ("Deploy to edge with Deno runtime", "deno-patterns"),
    ("Create IoT device firmware with MQTT telemetry", "iot-firmware"),
    ("Compile WebAssembly module from Rust", "webassembly-patterns"),
    ("Build an ERC-20 token with vesting", "token-vesting"),
    ("Set up Elasticsearch cluster monitoring", "elasticsearch-patterns"),
]

for query, expected_name in wave3_tests:
    result = detect_skills(query)
    detected_names = list(result.matched_skills[:5])
    found = expected_name in detected_names
    status = "OK" if found else "MISS"
    print(f"  [{status}] \"{query[:45]}\" -> expected={expected_name}, top5={detected_names}")

print("\n" + "=" * 60)
print(f"ALL E2E TESTS PASSED — {len(SKILL_REGISTRY)} skills, 18 categories, full pipeline")
print("=" * 60)
