# Claw Agent Feature Audit: CLI vs Vercel

## Status Summary
✅ **Repo**: All changes committed  
✅ **Vercel**: Deployed with DeepSeek API  
⚠️ **Feature Parity**: ~10% complete

---

## CLI Features (LOCAL - FULL IMPLEMENTATION)

### Core Capabilities
✅ 22 slash commands (/help, /model, /cost, /save, /sessions, /resume, /diff, /status, etc.)
✅ 26 tools across 12 categories:
   - File tools (read, write, list, find)
   - Edit tools (replace, multi-edit, insert, diff)
   - Shell tools (run_command, powershell)
   - Search tools (grep_search, web_search, web_fetch)
   - Task tools (task_create, task_update, task_list)
   - Notebook tools (run cells)
   - Context tools (git_diff, git_log, get_workspace_context)
   - Agent tools (run_subagent, plan_and_execute)
   - Advanced editing (advanced_edit_tools)
   - Utility tools (sleep, config operations)

✅ Session Management (save, resume, list, delete sessions)
✅ Cost Tracking (token counts, timing, turn tracking)
✅ Hook System (plugins, lifecycle hooks)
✅ Permission System (gated tools, allow/block list)
✅ Streaming Responses with Rich formatting
✅ Python 3.10+ support
✅ Local Ollama integration (no cloud dependencies)

### Extensions
✅ VS Code Extension with bridge
✅ Chrome Extension with page context
✅ Git workspace integration

---

## Vercel Features (WEB API - MINIMAL IMPLEMENTATION)

### Current Capabilities
✅ Basic chat endpoint (/api/chat)
✅ DeepSeek API integration
✅ Token usage tracking (prompt + completion)
✅ Error handling with helpful messages
✅ CORS enabled
✅ Environment variable support (DEEPSEEK_API_KEY)

### Missing Features
❌ No slash commands support
❌ No tool execution (all 26 tools missing)
❌ No session management
❌ No conversation history persistence
❌ No file/workspace access
❌ No git integration
❌ No streaming responses
❌ No permission system
❌ No cost tracking per session
❌ No context window management
❌ No multi-turn conversation state
❌ No markdown rendering
❌ No conversational state caching

---

## Implementation Roadmap

### Phase 1: Core API (High Priority)
- [ ] Session API endpoint (/api/sessions/{id})
- [ ] Conversation history endpoint
- [ ] Cost tracking per session
- [ ] Multi-turn message handling (store conversation history)
- [ ] System prompt with project context loading

### Phase 2: Command System (Medium Priority)
- [ ] Slash command handler (/help, /status, /cost, /sessions, etc.)
- [ ] Dedicated endpoints for each command
- [ ] Command routing and validation

### Phase 3: Tool Execution (Medium Priority)
- [ ] File tools via filesystem (need sandboxing)
- [ ] Shell execution endpoint (limited/safe)
- [ ] Search tools (grep, web_search)
- [ ] Git integration endpoint
- [ ] Task management endpoint

### Phase 4: Advanced Features (Lower Priority)
- [ ] Streaming responses (Server-Sent Events)
- [ ] Hook system integration
- [ ] Permission checking
- [ ] Context window auto-compaction
- [ ] Conversation compression
- [ ] Integration with VS Code Extension
- [ ] Integration with Chrome Extension

---

## Critical Gaps

1. **Stateless Design**: Current Vercel API is stateless. Need persistent session storage (Vercel KV/Firebase).
2. **Tool Access**: Cannot access filesystem from Vercel without significant infrastructure.
3. **Streaming**: Currently using non-streaming (full response at end). Should use Server-Sent Events.
4. **Project Context**: No way to access MEMORY.md, SOUL.md, .claw project files.
5. **Git Integration**: Cannot run git commands from Vercel without cloned repo access.
6. **Workspace**: No workspace awareness - just chat, no file operations.

---

## Recommendation

### For MVP (Minimum Viable Product):
1. Add session persistence (store conversation history)
2. Add basic slash commands (/help, /status, /cost, /sessions)
3. Add streaming responses
4. Deploy these changes to Vercel

### For Full Parity:
Would require:
- Vercel KV or external database for sessions
- Signed file access APIs or GitHub integration
- Rate limiting and usage quotas
- Sandbox environment for tool execution
- Estimated effort: 40-60 hours

---

## Command Files Updated
- ✅ commands.txt - CLI reference (no changes needed)
- ✅ agent.py - Core agent loop (local only)
- ✅ cli.py - CLI interface (local only)
- ⭕ api/chat.js - Needs extensions for full feature set
- ⭕ index.html - UI needs command palette
- ⭕ need new: api/sessions.js, api/commands.js, api/tools.js

