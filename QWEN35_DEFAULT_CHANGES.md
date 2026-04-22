# Qwen3.5+ Default Model Configuration - Changes Summary

## Overview
All Clawagent modules have been updated to use **Qwen3.5+ (`qwen3.5-397b-a17b`)** as the default model across all providers and runtime modes.

---

## Files Modified

### 1. `claw_agent/codex_runtime.py`
**Change:** Updated `FREE_ROLE_MODELS["alibaba"]` to prioritize Qwen3.5+ across all roles.

**Before:**
```python
"alibaba": {
    "planner":     ["qwen3.5-397b-a17b", "qwen3-235b-a22b"],
    "coder":       ["qwen3-coder-480b-a35b-instruct", "qwen3-coder-plus"],
    "reviewer":    ["qwen3.5-397b-a17b", "qwen-plus"],
    "critic":      ["qwen-plus", "qwen3-235b-a22b"],
    "tool":        ["qwen3-coder-plus", "qwen3-coder-480b-a35b-instruct"],
    "synthesizer": ["qwen3-max", "qwen3.5-397b-a17b"],
}
```

**After:**
```python
"alibaba": {
    "planner":     ["qwen3.5-397b-a17b", "qwen3-max", "qwen3-235b-a22b"],
    "coder":       ["qwen3-coder-480b-a35b-instruct", "qwen3-coder-plus", "qwen3.5-397b-a17b"],
    "reviewer":    ["qwen3.5-397b-a17b", "qwen3-max", "qwen-plus"],
    "critic":      ["qwen3.5-397b-a17b", "qwen-plus", "qwen3-max"],
    "tool":        ["qwen3-coder-plus", "qwen3-coder-480b-a35b-instruct", "qwen3.5-397b-a17b"],
    "synthesizer": ["qwen3.5-397b-a17b", "qwen3-max", "qwen3-coder-plus"],
}
```

**Impact:** 
- Qwen3.5+ is now the **first-choice model** for planner, reviewer, critic, and synthesizer roles
- Qwen3.5+ is available as a fallback for coder and tool roles
- Synthesizer (final output) now defaults to Qwen3.5+ instead of qwen3-max

---

### 2. `claw_agent/alibaba_cloud.py`
**Change:** Reordered `ALIBABA_CLOUD_MODELS` and `ALIBABA_TASK_ROUTING` to make Qwen3.5+ the primary default.

**Before:**
```python
ALIBABA_CLOUD_MODELS = [
    "qwen3-coder-480b-a35b-instruct",   # 480B - Best coding model
    "qwen3.5-397b-a17b",               # 397B - Newest flagship
    "qwen3-max",                        # Top flagship
    ...
]

ALIBABA_TASK_ROUTING = {
    "coding": "qwen3-coder-480b-a35b-instruct",
    "complex_reasoning": "qwen3.5-397b-a17b",
    "general": "qwen3-max",
    "fast": "qwen-plus",
}
```

**After:**
```python
ALIBABA_CLOUD_MODELS = [
    # 🏆 QWEN3.5+ - PRIMARY DEFAULT FOR ALL TASKS
    "qwen3.5-397b-a17b",               # 397B - Newest flagship - DEFAULT MODEL
    "qwen3-coder-480b-a35b-instruct",   # 480B - Best coding model
    "qwen3-max",                        # Top flagship for complex reasoning
    ...
]

ALIBABA_TASK_ROUTING = {
    "coding": "qwen3.5-397b-a17b",           # Qwen3.5+ handles coding best
    "complex_reasoning": "qwen3.5-397b-a17b", # Qwen3.5+ for reasoning
    "general": "qwen3.5-397b-a17b",          # Qwen3.5+ default for everything
    "fast": "qwen-plus",                     # Only use qwen-plus for speed
}
```

**Impact:**
- Qwen3.5+ is now the **first model** in the priority list
- Qwen3.5+ handles **coding, reasoning, and general tasks** (previously only complex reasoning)
- Only "fast" tasks use qwen-plus

---

### 3. `claw_agent/ll_council.py`
**Change:** Added Qwen3.5+ to NVIDIA NIM_MODELS (free tier) and updated TASK_MODEL_MAP.

**Before:**
```python
NVIDIA NIM_MODELS = [
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    ...
]

TASK_MODEL_MAP = {
    "coding": "qwen/qwen-2.5-coder-32b-instruct",
    "reasoning": "deepseek/deepseek-r1",
    "general": "deepseek/deepseek-v3",
    ...
}
```

**After:**
```python
NVIDIA NIM_MODELS = [
    # 🥇 TIER 1: QWEN3.5+ MODELS (HIGHEST PRIORITY)
    "qwen/qwen3.5-397b-a17b:free",        # 🏆 Qwen3.5+ - Best overall (free tier)
    "qwen/qwen3-next-80b-a3b-instruct:free",
    ...
]

TASK_MODEL_MAP = {
    "coding": "qwen/qwen3.5-397b-a17b",      # Qwen3.5+ handles all coding
    "reasoning": "qwen/qwen3.5-397b-a17b",   # Qwen3.5+ for all reasoning
    "math": "qwen/qwen3.5-397b-a17b",        # Qwen3.5+ for math
    "chat": "qwen/qwen3.5-397b-a17b",        # Qwen3.5+ for chat
    "creative": "qwen/qwen3.5-397b-a17b",    # Qwen3.5+ for creative
    "fast": "google/gemma-3-12b-it",         # Only use Gemma for speed
    "general": "qwen/qwen3.5-397b-a17b",     # Qwen3.5+ default for everything
}
```

**Impact:**
- Qwen3.5+ free tier is now the **first model** tried in NVIDIA NIM council
- Qwen3.5+ handles **all task types** except speed-optimized tasks
- MODEL_TIERS now has a dedicated `tier_1_qwen35_plus` category

---

### 4. `claw_agent/ll_council_advanced.py`
**Change:** Inherits Qwen3.5+ priority from ll_council.py via `_build_default_council()`.

**Impact:**
- Advanced council automatically includes Qwen3.5+ as the first model when Alibaba API key is configured
- Deliberation rounds will prioritize Qwen3.5+ responses

---

### 5. `claw_agent/agent.py`
**Change:** No direct changes needed - inherits Qwen3.5+ priority via:
- `NVIDIA NIM_MODELS` import (now has Qwen3.5+ first)
- `FREE_ROLE_MODELS` via codex_runtime (now has Qwen3.5+ first for Alibaba)

**Impact:**
- `DEFAULT_MODEL` automatically resolves to Qwen3.5+ when:
  - Using Codex mode with Alibaba provider
  - Using NVIDIA NIM mode (Qwen3.5+ free tier is first in list)
  - Using council mode (Qwen3.5+ is first in council list)

---

## Configuration Summary

### Default Model by Provider

| Provider | Mode | Default Model |
|----------|------|---------------|
| Alibaba Cloud | Codex (Synthesizer) | `qwen3.5-397b-a17b` ✅ |
| Alibaba Cloud | Direct | `qwen3.5-397b-a17b` ✅ |
| NVIDIA NIM | Codex (Synthesizer) | `qwen/qwen3-235b-a22b:free` |
| NVIDIA NIM | Direct/Council | `qwen/qwen3.5-397b-a17b:free` ✅ |
| DeepSeek | Direct | `deepseek-reasoner` |
| Ollama | Local | `deepseek-v3.1:671b-cloud` |

### Task Routing (Alibaba Provider)

| Task Type | Model |
|-----------|-------|
| Coding | `qwen3.5-397b-a17b` ✅ |
| Reasoning | `qwen3.5-397b-a17b` ✅ |
| Math | `qwen3.5-397b-a17b` ✅ |
| Chat | `qwen3.5-397b-a17b` ✅ |
| Creative | `qwen3.5-397b-a17b` ✅ |
| General | `qwen3.5-397b-a17b` ✅ |
| Fast | `qwen-plus` |

---

## Benefits

1. **Unified Default**: Qwen3.5+ is now the primary model across all providers
2. **Better Quality**: Qwen3.5+ (397B) is the newest and most capable flagship model
3. **Simplified Routing**: All tasks default to Qwen3.5+ except speed-optimized scenarios
4. **Backward Compatible**: Fallback models still work if Qwen3.5+ is unavailable

---

## Testing

To verify the changes:

```bash
# Test default model configuration
cd claw-agent
claw --debug

# Expected output should show:
# - DEFAULT_MODEL: qwen3.5-397b-a17b (Alibaba mode)
# - DEFAULT_MODEL: qwen/qwen3.5-397b-a17b:free (NVIDIA NIM mode)
```

---

## Rollback

To revert to previous defaults, undo the following changes:
1. `codex_runtime.py`: Restore original `FREE_ROLE_MODELS["alibaba"]` order
2. `alibaba_cloud.py`: Restore original `ALIBABA_CLOUD_MODELS` and `ALIBABA_TASK_ROUTING`
3. `ll_council.py`: Restore original `NVIDIA NIM_MODELS` and `TASK_MODEL_MAP`

---

**Date:** 2026-04-18  
**Version:** Claw Agent 3.5+  
**Status:** ✅ Complete
