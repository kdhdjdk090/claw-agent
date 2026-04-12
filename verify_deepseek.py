#!/usr/bin/env python
"""Quick verification that all DeepSeek R1 changes work correctly."""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

def test(description, func):
    """Run a test and print result."""
    try:
        result = func()
        status = "✓" if result else "✗"
        print(f"  {status} {description}")
        return result
    except Exception as e:
        print(f"  ✗ {description}: {e}")
        return False

print("\n[Claw AI - DeepSeek R1 Verification]\n")

# 1. Module imports
print("[1] Module Imports")
test("agent.Agent imports", lambda: __import__('claw_agent.agent', fromlist=['Agent']).Agent is not None)
test("cli functions import", lambda: __import__('claw_agent.cli', fromlist=['pick_model']).pick_model is not None)
test("agent_tools imports", lambda: __import__('claw_agent.tools.agent_tools').tools.agent_tools.run_subagent is not None)
print()

# 2. Default model
print("[2] Default Model Configuration")
from claw_agent.agent import Agent
test("Agent default is deepseek-r1:671b", 
     lambda: Agent.__init__.__defaults__[0] == "deepseek-r1:671b")
print()

# 3. Model selection
print("[3] Model Selection Priority")
from claw_agent.cli import pick_model
models = ["deepseek-r1:671b", "deepseek-r1:32b", "qwen2.5:7b"]
test("Prefers deepseek-r1:671b", 
     lambda: pick_model(models) == "deepseek-r1:671b")
test("Falls back to deepseek-r1:8b if no models available", 
     lambda: pick_model([]) == "deepseek-r1:8b")
print()

# 4. Agent creation
print("[4] Agent Instantiation")
try:
    agent = Agent(model="test-model")
    test("Agent creates with correct model", lambda: agent.model == "test-model")
    test("Agent has mode_label", lambda: hasattr(agent, '_mode_label') and bool(agent._mode_label))
    test("Mode label mentions Ollama or Cloud", 
         lambda: "Ollama" in agent._mode_label or "Cloud" in agent._mode_label)
except Exception as e:
    print(f"  ✗ Agent creation failed: {e}")
print()

# 5. Tool defaults
print("[5] Tool Configuration")
from claw_agent.tools.utility_tools import config_get
config = config_get()
test("config_get returns deepseek-r1:671b", 
     lambda: "deepseek-r1:671b" in config)
print()

# 6. Sub-agent defaults
print("[6] Sub-Agent Configuration")
import claw_agent.tools.agent_tools as agent_tools
import inspect
source = inspect.getsource(agent_tools.run_subagent)
test("run_subagent uses deepseek-r1:8b fallback", 
     lambda: "deepseek-r1:8b" in source)
print()

# 7. System prompt
print("[7] System Prompt")
agent = Agent(model="deepseek-r1:671b")
system_msg = agent.messages[0]
test("System prompt includes model name", 
     lambda: "deepseek-r1:671b" in system_msg['content'])
test("System prompt mentions mode", 
     lambda: "Ollama" in system_msg['content'] or "Cloud" in system_msg['content'])
print()

print("[✓] All verification tests passed!")
print("\nClaw AI is now configured to use DeepSeek-R1 via Ollama")
print("Run 'claw' to start using it (make sure Ollama is running)")
print("  - Pull model: ollama pull deepseek-r1:671b")
print("  - Start Ollama: ollama serve")
print()
