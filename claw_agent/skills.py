"""Skills system for Claw AI - installable capabilities like Claude Code.

Skills are packages that extend Claw's capabilities with:
- Custom tools
- Prompt templates  
- Context providers
- Workflow automation
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Skills directory
SKILLS_DIR = Path.home() / ".claw-agent" / "skills"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)

# Registry of built-in skills
BUILTIN_SKILLS = {
    "web-dev": {
        "name": "web-dev",
        "version": "1.0.0",
        "description": "Web development toolkit - HTML, CSS, JavaScript, React, Vue",
        "tools": ["web_fetch", "write_file", "run_command", "read_file"],
        "prompts": {
            "create-react": "Create a React component with TypeScript",
            "debug-js": "Debug JavaScript/TypeScript code",
            "setup-vite": "Set up Vite project",
        },
    },
    "data-science": {
        "name": "data-science",
        "version": "1.0.0",
        "description": "Data science toolkit - pandas, numpy, matplotlib, ML",
        "tools": ["notebook_run", "run_command", "read_file", "write_file"],
        "prompts": {
            "analyze-data": "Analyze a CSV file and create visualizations",
            "train-model": "Train a machine learning model",
            "eda": "Exploratory data analysis",
        },
    },
    "devops": {
        "name": "devops",
        "version": "1.0.0",
        "description": "DevOps toolkit - Docker, Kubernetes, CI/CD, cloud",
        "tools": ["run_command", "write_file", "read_file"],
        "prompts": {
            "dockerize": "Create Docker setup for a project",
            "ci-cd": "Set up CI/CD pipeline",
            "k8s": "Kubernetes configuration",
        },
    },
    "security": {
        "name": "security",
        "version": "1.0.0",
        "description": "Security toolkit - vulnerability scanning, code review",
        "tools": ["read_file", "grep_search", "run_command"],
        "prompts": {
            "audit": "Security audit of codebase",
            "review": "Security code review",
            "scan": "Vulnerability scan",
        },
    },
    "api-dev": {
        "name": "api-dev",
        "version": "1.0.0",
        "description": "API development - REST, GraphQL, OpenAPI, testing",
        "tools": ["write_file", "read_file", "run_command", "web_fetch"],
        "prompts": {
            "create-api": "Create REST API endpoint",
            "openapi": "Generate OpenAPI spec",
            "test-api": "API integration tests",
        },
    },
}


@dataclass
class SkillInfo:
    """Information about an installed skill."""
    name: str
    version: str
    description: str
    installed_at: str
    tools: list[str] = field(default_factory=list)
    prompts: dict[str, str] = field(default_factory=dict)
    is_builtin: bool = False


def list_skills() -> list[SkillInfo]:
    """List all installed skills."""
    skills = []
    
    # List installed skills
    if SKILLS_DIR.exists():
        for skill_dir in sorted(SKILLS_DIR.iterdir()):
            if skill_dir.is_dir():
                manifest_path = skill_dir / "skill.json"
                if manifest_path.exists():
                    with open(manifest_path, "r") as f:
                        data = json.load(f)
                        skills.append(SkillInfo(
                            name=data["name"],
                            version=data.get("version", "1.0.0"),
                            description=data.get("description", ""),
                            installed_at=data.get("installed_at", "unknown"),
                            tools=data.get("tools", []),
                            prompts=data.get("prompts", {}),
                            is_builtin=False,
                        ))
    
    # Add builtin skills
    for name, info in BUILTIN_SKILLS.items():
        skills.append(SkillInfo(
            name=name,
            version=info["version"],
            description=info["description"],
            installed_at="built-in",
            tools=info.get("tools", []),
            prompts=info.get("prompts", {}),
            is_builtin=True,
        ))
    
    return skills


def install_skill(skill_name: str) -> str:
    """Install a skill by name."""
    # Check if it's a builtin skill
    if skill_name in BUILTIN_SKILLS:
        skill_data = BUILTIN_SKILLS[skill_name].copy()
        skill_data["installed_at"] = datetime.now().isoformat()
        skill_data["name"] = skill_name
        
        # Create skill directory
        skill_dir = SKILLS_DIR / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        # Save manifest
        with open(skill_dir / "skill.json", "w") as f:
            json.dump(skill_data, f, indent=2)
        
        return f"✓ Installed skill: {skill_name} v{skill_data['version']}"
    
    # For external skills, would download from registry
    return f"✗ Skill '{skill_name}' not found. Available: {', '.join(BUILTIN_SKILLS.keys())}"


def uninstall_skill(skill_name: str) -> str:
    """Uninstall a skill by name."""
    import shutil
    
    skill_dir = SKILLS_DIR / skill_name
    
    if not skill_dir.exists():
        return f"✗ Skill '{skill_name}' is not installed"
    
    # Check if builtin
    manifest_path = skill_dir / "skill.json"
    if manifest_path.exists():
        with open(manifest_path, "r") as f:
            data = json.load(f)
            if data.get("is_builtin"):
                return f"✗ Cannot uninstall builtin skill '{skill_name}'"
    
    # Remove skill directory
    shutil.rmtree(skill_dir)
    return f"✓ Uninstalled skill: {skill_name}"


def get_skill_context(skill_name: str) -> str:
    """Get context string for a skill (used in system prompt)."""
    skill_dir = SKILLS_DIR / skill_name
    manifest_path = skill_dir / "skill.json"
    
    if not manifest_path.exists():
        return ""
    
    with open(manifest_path, "r") as f:
        data = json.load(f)
    
    context = f"\n## Active Skill: {data['name']} v{data.get('version', '1.0.0')}\n"
    context += f"{data.get('description', '')}\n"
    
    if data.get("prompts"):
        context += "\nAvailable prompts:\n"
        for name, desc in data["prompts"].items():
            context += f"- {name}: {desc}\n"
    
    return context


def get_all_skills_context() -> str:
    """Get context for all active skills."""
    context = ""
    for skill_info in list_skills():
        if not skill_info.is_builtin:  # Only custom skills add context
            context += get_skill_context(skill_info.name)
    return context


def format_skills_table(skills: list[SkillInfo]) -> str:
    """Format skills as a nice table."""
    if not skills:
        return "No skills installed."
    
    lines = []
    lines.append(f"{'Name':<20} {'Version':<12} {'Type':<10} {'Description'}")
    lines.append("─" * 80)
    
    for skill in skills:
        skill_type = "builtin" if skill.is_builtin else "custom"
        lines.append(f"{skill.name:<20} {skill.version:<12} {skill_type:<10} {skill.description}")
    
    return "\n".join(lines)
