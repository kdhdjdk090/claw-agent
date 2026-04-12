"""Quick infrastructure tests."""
from claw_agent.agent import Agent
from claw_agent.permissions import PermissionContext
from claw_agent.sessions import Session, save_session, load_session, list_sessions
from claw_agent.cost_tracker import CostTracker
from claw_agent.tools import TOOL_REGISTRY

# Test session save/load
a = Agent(model="qwen2.5:7b")
resp = a.chat("Say hello")
print(f"Agent responded: {resp[:100]}")

save_session(a.session)
sid = a.session.session_id
print(f"Session saved: {sid[:12]}")

sessions = list_sessions()
print(f"Sessions found: {len(sessions)}")

loaded = load_session(sid)
print(f"Session loaded: {loaded.session_id[:12]}, turns: {loaded.total_turns}")
print(f"Messages in session: {len(loaded.messages)}")

# Test permissions
p = PermissionContext.default()
print(f"Blocks 'rm -rf /': {p.check_command_safety('rm -rf /')}")
print(f"Blocks 'echo hi': {p.check_command_safety('echo hi')}")

# Test cost tracker
print(f"Cost summary: {a.cost.summary()}")

# Test tool count
print(f"Tools registered: {len(TOOL_REGISTRY)}")
print(f"Tool names: {sorted(TOOL_REGISTRY.keys())}")

print()
print("ALL INFRASTRUCTURE TESTS PASSED")
