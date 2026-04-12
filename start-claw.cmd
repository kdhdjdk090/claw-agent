@echo off
REM Start Claw AI CLI
cd /d "C:\Users\Sinwa\Pictures\ClaudeAI\claw-agent"
echo Starting Claw AI...
echo.
python -m claw_agent.cli %*
