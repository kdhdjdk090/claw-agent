"""Test script for LL Council functionality."""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from claw_agent.ll_council import LLCouncil, CouncilResponse, DEFAULT_COUNCIL_MODELS

def test_council_initialization():
    """Test that council initializes correctly."""
    print("=" * 60)
    print("TEST 1: Council Initialization")
    print("=" * 60)
    
    council = LLCouncil(
        system_prompt="You are a test assistant.",
        temperature=0.7,
    )
    
    print(f"✓ Council created successfully")
    print(f"  Models: {len(council.models)}")
    print(f"  Models list: {', '.join(council.models[:3])}...")
    print(f"  Temperature: {council.temperature}")
    print()
    
    assert len(council.models) > 0, "Should have models configured"
    assert council.total_calls == 0, "Should have zero calls initially"
    
    print("✅ TEST 1 PASSED\n")
    return True

def test_council_info():
    """Test council info method."""
    print("=" * 60)
    print("TEST 2: Council Info")
    print("=" * 60)
    
    council = LLCouncil(system_prompt="Test")
    info = council.get_council_info()
    
    print(f"✓ Council info:")
    print(f"  Model count: {info['model_count']}")
    print(f"  Threshold: {info['threshold']}")
    print(f"  Total calls: {info['total_calls']}")
    print()
    
    assert 'models' in info
    assert 'model_count' in info
    assert info['model_count'] == len(DEFAULT_COUNCIL_MODELS)
    
    print("✅ TEST 2 PASSED\n")
    return True

def test_response_creation():
    """Test creating council responses."""
    print("=" * 60)
    print("TEST 3: Response Creation")
    print("=" * 60)
    
    response = CouncilResponse(
        model="test-model",
        content="Test response content",
        token_count=100,
        latency_ms=1500.0,
    )
    
    print(f"✓ Response created:")
    print(f"  Model: {response.model}")
    print(f"  Content: {response.content}")
    print(f"  Tokens: {response.token_count}")
    print(f"  Latency: {response.latency_ms:.0f}ms")
    print()
    
    assert response.model == "test-model"
    assert response.token_count == 100
    
    print("✅ TEST 3 PASSED\n")
    return True

def test_similarity():
    """Test content similarity detection."""
    print("=" * 60)
    print("TEST 4: Content Similarity")
    print("=" * 60)
    
    council = LLCouncil(system_prompt="Test")
    
    # Test exact match
    assert council._is_similar("hello world", "hello world")
    print("✓ Exact match detected")
    
    # Test containment
    assert council._is_similar("hello", "say hello world")
    print("✓ Containment detected")
    
    # Test dissimilar
    assert not council._is_similar("completely different text", "xyz abc 123")
    print("✓ Dissimilar content identified")
    
    print()
    print("✅ TEST 4 PASSED\n")
    return True

def test_normalization():
    """Test content normalization."""
    print("=" * 60)
    print("TEST 5: Content Normalization")
    print("=" * 60)
    
    council = LLCouncil(system_prompt="Test")
    
    # Test with code blocks
    content = "```python\nprint('hello')\n```"
    normalized = council._normalize_content(content)
    assert "```" not in normalized
    print(f"✓ Code blocks removed")
    
    # Test case normalization
    content = "Hello World"
    normalized = council._normalize_content(content)
    assert normalized == "hello world"
    print(f"✓ Case normalized")
    
    # Test whitespace
    content = "  hello   world  "
    normalized = council._normalize_content(content)
    assert normalized == "hello world"
    print(f"✓ Whitespace normalized")
    
    print()
    print("✅ TEST 5 PASSED\n")
    return True

def test_aggregation_logic():
    """Test response aggregation without API calls."""
    print("=" * 60)
    print("TEST 6: Response Aggregation Logic")
    print("=" * 60)
    
    council = LLCouncil(system_prompt="Test")
    
    # Create mock responses (all agreeing)
    responses = [
        CouncilResponse(model="model1", content="The answer is 42", token_count=50),
        CouncilResponse(model="model2", content="The answer is 42", token_count=45),
        CouncilResponse(model="model3", content="The answer is 42", token_count=48),
        CouncilResponse(model="model4", content="I think it might be 42", token_count=52),
        CouncilResponse(model="model5", content="The answer is 42", token_count=47),
        CouncilResponse(model="model6", content="42 is correct", token_count=40),
    ]
    
    result = council._aggregate_responses(responses)
    
    print(f"✓ Aggregation completed")
    print(f"  Consensus: {result.consensus_percentage:.0%}")
    print(f"  Total tokens: {result.total_tokens}")
    print(f"  Models agreed: {len(result.votes)}")
    print()
    
    assert result.consensus_percentage > 0.5, "Should have majority consensus"
    assert result.total_tokens == 282, "Should sum all tokens"
    assert "42" in result.consensus_answer, "Should contain the answer"
    
    print("✅ TEST 6 PASSED\n")
    return True

def test_env_configuration():
    """Test environment variable configuration."""
    print("=" * 60)
    print("TEST 7: Environment Configuration")
    print("=" * 60)
    
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    council_models = os.environ.get("COUNCIL_MODELS", "")
    threshold = os.environ.get("COUNCIL_THRESHOLD", "")
    
    print(f"✓ OPENROUTER_API_KEY: {'Set' if api_key else 'NOT SET'}")
    print(f"  Value preview: {api_key[:20]}..." if api_key else "  (empty)")
    print()
    
    print(f"✓ COUNCIL_MODELS: {'Set' if council_models else 'NOT SET'}")
    if council_models:
        models = council_models.split(",")
        print(f"  Count: {len(models)}")
        print(f"  Models: {', '.join(models[:3])}...")
    print()
    
    print(f"✓ COUNCIL_THRESHOLD: {'Set' if threshold else 'NOT SET'}")
    if threshold:
        print(f"  Value: {threshold}")
    print()
    
    # API key should be set for full functionality
    if not api_key:
        print("⚠️  WARNING: OPENROUTER_API_KEY not set!")
        print("   Council queries will fail without an API key.\n")
    else:
        print("✅ API key configured")
    
    print("✅ TEST 7 PASSED\n")
    return True

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🧪 CLAW AI - LL COUNCIL TEST SUITE")
    print("=" * 60 + "\n")
    
    tests = [
        test_council_initialization,
        test_council_info,
        test_response_creation,
        test_similarity,
        test_normalization,
        test_aggregation_logic,
        test_env_configuration,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ TEST FAILED: {e}\n")
            failed += 1
    
    print("=" * 60)
    print(f"📊 TEST RESULTS")
    print("=" * 60)
    print(f"  Passed: {passed}/{len(tests)}")
    print(f"  Failed: {failed}/{len(tests)}")
    print()
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! Council is ready!")
        print("\nNext steps:")
        print("  1. Start Claw AI: python -m claw_agent")
        print("  2. Try chatting - council mode is automatic!")
        print("  3. Read COUNCIL_GUIDE.md for full documentation")
    else:
        print(f"⚠️  {failed} test(s) failed. Please review the errors above.")
    
    print("=" * 60 + "\n")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
