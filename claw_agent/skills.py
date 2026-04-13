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

# Registry of built-in skills - CLAUDE AI TOP SKILLS INSTALLED
BUILTIN_SKILLS = {
    # Core capabilities — Claude-style
    "code": {
        "name": "code",
        "version": "1.0.0",
        "description": "Generate, edit & debug code in any language",
        "tools": ["write_file", "read_file", "run_command", "grep_search"],
        "prompts": {
            "generate": "Generate code from a description",
            "edit": "Edit existing code to add a feature",
            "fix": "Fix a bug in the provided code",
        },
    },
    "analyze": {
        "name": "analyze",
        "version": "1.0.0",
        "description": "Research & data analysis",
        "tools": ["read_file", "notebook_run", "web_fetch", "grep_search"],
        "prompts": {
            "data": "Analyze a dataset and surface insights",
            "research": "Research a topic with sources",
            "compare": "Compare options with pros and cons",
        },
    },
    "write": {
        "name": "write",
        "version": "1.0.0",
        "description": "Essays, emails, reports & creative writing",
        "tools": ["write_file", "read_file"],
        "prompts": {
            "essay": "Write a structured essay",
            "email": "Draft a professional email",
            "report": "Create a detailed report",
        },
    },
    "summarize": {
        "name": "summarize",
        "version": "1.0.0",
        "description": "Condense documents & articles",
        "tools": ["read_file", "web_fetch"],
        "prompts": {
            "document": "Summarize a long document",
            "article": "Summarize a web article",
            "key-points": "Extract key takeaways",
        },
    },
    "translate": {
        "name": "translate",
        "version": "1.0.0",
        "description": "Translate between any language pair",
        "tools": ["read_file", "write_file"],
        "prompts": {
            "text": "Translate text to a target language",
            "file": "Translate an entire file",
            "localize": "Localize content for a region",
        },
    },
    "math": {
        "name": "math",
        "version": "1.0.0",
        "description": "Calculations, equations & mathematical reasoning",
        "tools": ["notebook_run", "run_command"],
        "prompts": {
            "solve": "Solve a math problem step by step",
            "proof": "Write a mathematical proof",
            "compute": "Perform a numerical computation",
        },
    },
    "reason": {
        "name": "reason",
        "version": "1.0.0",
        "description": "Logic, critical thinking & problem solving",
        "tools": ["read_file", "web_fetch"],
        "prompts": {
            "logic": "Solve a logic puzzle",
            "decision": "Decision analysis with trade-offs",
            "debug-logic": "Find the flaw in an argument",
        },
    },
    "brainstorm": {
        "name": "brainstorm",
        "version": "1.0.0",
        "description": "Ideation & creative thinking",
        "tools": ["write_file", "web_fetch"],
        "prompts": {
            "ideas": "Brainstorm ideas for a project",
            "names": "Generate names or titles",
            "strategy": "Strategic planning session",
        },
    },
    "explain": {
        "name": "explain",
        "version": "1.0.0",
        "description": "Simplify complex topics",
        "tools": ["read_file", "web_fetch"],
        "prompts": {
            "concept": "Explain a concept simply",
            "eli5": "Explain like I'm five",
            "deep-dive": "In-depth technical explanation",
        },
    },
    "extract": {
        "name": "extract",
        "version": "1.0.0",
        "description": "Structure data from unstructured text",
        "tools": ["read_file", "write_file", "grep_search"],
        "prompts": {
            "json": "Extract data into JSON format",
            "table": "Extract data into a table",
            "entities": "Extract named entities from text",
        },
    },
    "vision": {
        "name": "vision",
        "version": "1.0.0",
        "description": "Describe & analyze images and diagrams",
        "tools": ["read_file", "web_fetch"],
        "prompts": {
            "describe": "Describe what's in an image",
            "diagram": "Interpret a diagram or chart",
            "ocr": "Extract text from an image",
        },
    },
    "debug": {
        "name": "debug",
        "version": "1.0.0",
        "description": "Find & fix bugs in code",
        "tools": ["read_file", "grep_search", "run_command", "diff_files"],
        "prompts": {
            "error": "Debug an error message",
            "trace": "Trace the root cause of a bug",
            "fix": "Fix a failing test",
        },
    },
    "refactor": {
        "name": "refactor",
        "version": "1.0.0",
        "description": "Improve code quality & structure",
        "tools": ["read_file", "write_file", "grep_search", "diff_files"],
        "prompts": {
            "clean": "Clean up messy code",
            "patterns": "Apply design patterns",
            "performance": "Optimize for performance",
        },
    },
    "review": {
        "name": "review",
        "version": "1.0.0",
        "description": "Code review & feedback",
        "tools": ["read_file", "grep_search", "diff_files"],
        "prompts": {
            "pr": "Review a pull request",
            "security": "Security-focused code review",
            "best-practices": "Check against best practices",
        },
    },
    "test": {
        "name": "test",
        "version": "1.0.0",
        "description": "Write tests & QA",
        "tools": ["write_file", "read_file", "run_command"],
        "prompts": {
            "unit": "Write unit tests",
            "integration": "Write integration tests",
            "coverage": "Improve test coverage",
        },
    },
    "docs": {
        "name": "docs",
        "version": "1.0.0",
        "description": "Generate documentation",
        "tools": ["read_file", "write_file"],
        "prompts": {
            "readme": "Generate a README",
            "api": "Generate API documentation",
            "comments": "Add inline documentation",
        },
    },
    "design": {
        "name": "design",
        "version": "1.0.0",
        "description": "System architecture & technical design",
        "tools": ["read_file", "write_file", "web_fetch"],
        "prompts": {
            "architecture": "Design system architecture",
            "schema": "Design a database schema",
            "api-design": "Design an API interface",
        },
    },
    "search": {
        "name": "search",
        "version": "1.0.0",
        "description": "Web research & information lookup",
        "tools": ["web_fetch", "web_search", "read_file"],
        "prompts": {
            "web": "Search the web for information",
            "docs": "Find documentation for a library",
            "answer": "Research and answer a question",
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
