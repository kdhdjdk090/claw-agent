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
    # 🥇 CORE DEVELOPMENT SKILLS
    "web-dev": {
        "name": "web-dev",
        "version": "1.0.0",
        "description": "Web development toolkit - HTML, CSS, JavaScript, React, Vue, Next.js",
        "tools": ["web_fetch", "write_file", "run_command", "read_file"],
        "prompts": {
            "create-react": "Create a React component with TypeScript",
            "debug-js": "Debug JavaScript/TypeScript code",
            "setup-vite": "Set up Vite project",
            "nextjs": "Create Next.js app with routing",
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
        "description": "DevOps toolkit - Docker, Kubernetes, CI/CD, cloud deployment",
        "tools": ["run_command", "write_file", "read_file"],
        "prompts": {
            "dockerize": "Create Docker setup for a project",
            "ci-cd": "Set up CI/CD pipeline",
            "k8s": "Kubernetes configuration",
            "deploy": "Deploy to cloud (AWS/GCP/Azure)",
        },
    },
    
    # 🥇 SECURITY & CODE QUALITY
    "security": {
        "name": "security",
        "version": "1.0.0",
        "description": "Security toolkit - vulnerability scanning, code review, audits",
        "tools": ["read_file", "grep_search", "run_command"],
        "prompts": {
            "audit": "Security audit of codebase",
            "review": "Security code review",
            "scan": "Vulnerability scan",
            "pentest": "Penetration testing checklist",
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
            "graphql": "Create GraphQL schema",
        },
    },
    
    # 🥈 ADVANCED DEVELOPMENT
    "mobile-dev": {
        "name": "mobile-dev",
        "version": "1.0.0",
        "description": "Mobile development - React Native, Flutter, iOS/Android",
        "tools": ["write_file", "run_command", "read_file"],
        "prompts": {
            "react-native": "Create React Native component",
            "flutter": "Set up Flutter project",
            "debug-mobile": "Debug mobile build issues",
        },
    },
    "ml-ops": {
        "name": "ml-ops",
        "version": "1.0.0",
        "description": "Machine Learning Ops - model training, deployment, monitoring",
        "tools": ["notebook_run", "run_command", "write_file", "web_fetch"],
        "prompts": {
            "train": "Train ML model with best practices",
            "deploy-model": "Deploy ML model to production",
            "monitor": "Set up model monitoring",
        },
    },
    "database": {
        "name": "database",
        "version": "1.0.0",
        "description": "Database toolkit - SQL, NoSQL, migrations, optimization",
        "tools": ["run_command", "read_file", "write_file"],
        "prompts": {
            "design-schema": "Design database schema",
            "optimize": "Optimize slow queries",
            "migrate": "Database migration script",
            "nosql": "NoSQL data modeling",
        },
    },
    
    # 🥉 TESTING & QA
    "testing": {
        "name": "testing",
        "version": "1.0.0",
        "description": "Testing toolkit - unit, integration, e2e, TDD",
        "tools": ["run_command", "read_file", "write_file"],
        "prompts": {
            "unit-test": "Write unit tests",
            "e2e": "End-to-end test setup",
            "tdd": "Test-driven development workflow",
            "coverage": "Check test coverage",
        },
    },
    "code-review": {
        "name": "code-review",
        "version": "1.0.0",
        "description": "Code review toolkit - best practices, refactoring, patterns",
        "tools": ["read_file", "grep_search", "diff_files"],
        "prompts": {
            "review": "Comprehensive code review",
            "refactor": "Refactor code for better structure",
            "patterns": "Apply design patterns",
            "clean-code": "Clean code principles check",
        },
    },
    
    # ⚡ PRODUCTIVITY & WORKFLOW
    "git-workflow": {
        "name": "git-workflow",
        "version": "1.0.0",
        "description": "Git workflow automation - branching, merging, CI integration",
        "tools": ["run_command", "read_file"],
        "prompts": {
            "branch": "Create Git branching strategy",
            "merge": "Resolve merge conflicts",
            "rebase": "Interactive rebase guide",
            "release": "Release management workflow",
        },
    },
    "documentation": {
        "name": "documentation",
        "version": "1.0.0",
        "description": "Documentation toolkit - README, API docs, diagrams",
        "tools": ["read_file", "write_file", "web_fetch"],
        "prompts": {
            "readme": "Generate comprehensive README",
            "api-docs": "Generate API documentation",
            "diagrams": "Create architecture diagrams",
            "changelog": "Generate changelog",
        },
    },
    "blockchain": {
        "name": "blockchain",
        "version": "1.0.0",
        "description": "Blockchain development - Solidity, smart contracts, Web3",
        "tools": ["write_file", "read_file", "run_command"],
        "prompts": {
            "solidity": "Write Solidity smart contract",
            "web3": "Integrate Web3.js",
            "audit-contract": "Smart contract security audit",
        },
    },
    "game-dev": {
        "name": "game-dev",
        "version": "1.0.0",
        "description": "Game development - Unity, Unreal, Godot, web games",
        "tools": ["write_file", "read_file", "run_command"],
        "prompts": {
            "unity": "Unity C# script",
            "godot": "Godot GDScript",
            "web-game": "HTML5/JavaScript game",
        },
    },

    # 🌐 CLOUD & INFRASTRUCTURE
    "cloud": {
        "name": "cloud",
        "version": "1.0.0",
        "description": "Cloud platforms - AWS, GCP, Azure, Terraform, serverless",
        "tools": ["run_command", "write_file", "read_file", "web_fetch"],
        "prompts": {
            "aws": "AWS infrastructure setup",
            "gcp": "Google Cloud configuration",
            "azure": "Azure resource deployment",
            "terraform": "Terraform IaC templates",
            "serverless": "Serverless function deployment",
        },
    },
    "performance": {
        "name": "performance",
        "version": "1.0.0",
        "description": "Performance optimization - profiling, caching, load testing",
        "tools": ["run_command", "read_file", "grep_search", "web_fetch"],
        "prompts": {
            "profile": "Profile application performance",
            "cache": "Implement caching strategy",
            "load-test": "Set up load testing",
            "optimize": "Optimize slow code paths",
        },
    },
    "a11y": {
        "name": "a11y",
        "version": "1.0.0",
        "description": "Accessibility - WCAG compliance, screen readers, ARIA",
        "tools": ["read_file", "grep_search", "write_file", "web_fetch"],
        "prompts": {
            "audit": "Accessibility audit against WCAG",
            "aria": "Add ARIA attributes",
            "contrast": "Check color contrast ratios",
            "screen-reader": "Screen reader compatibility check",
        },
    },
    "embedded": {
        "name": "embedded",
        "version": "1.0.0",
        "description": "Embedded systems - Arduino, ESP32, Raspberry Pi, firmware",
        "tools": ["write_file", "read_file", "run_command"],
        "prompts": {
            "arduino": "Arduino sketch development",
            "esp32": "ESP32 firmware",
            "rpi": "Raspberry Pi project setup",
            "firmware": "Firmware development workflow",
        },
    },
    "sysadmin": {
        "name": "sysadmin",
        "version": "1.0.0",
        "description": "System administration - Linux, networking, monitoring, scripts",
        "tools": ["run_command", "write_file", "read_file", "grep_search"],
        "prompts": {
            "bash": "Shell scripting automation",
            "monitoring": "Set up system monitoring",
            "nginx": "Nginx/Apache configuration",
            "systemd": "Systemd service management",
        },
    },
    "ai-ml": {
        "name": "ai-ml",
        "version": "1.0.0",
        "description": "AI & deep learning - PyTorch, TensorFlow, transformers, LLMs",
        "tools": ["notebook_run", "run_command", "write_file", "read_file", "web_fetch"],
        "prompts": {
            "pytorch": "PyTorch model training",
            "tensorflow": "TensorFlow pipeline",
            "transformers": "Hugging Face transformers",
            "finetune": "Fine-tune language model",
            "rag": "Build RAG pipeline",
        },
    },
    "iot": {
        "name": "iot",
        "version": "1.0.0",
        "description": "IoT development - MQTT, sensors, edge computing, protocols",
        "tools": ["write_file", "read_file", "run_command", "web_fetch"],
        "prompts": {
            "mqtt": "MQTT broker and client setup",
            "edge": "Edge computing pipeline",
            "sensor": "Sensor data processing",
            "protocol": "IoT protocol implementation",
        },
    },
    "ui-ux": {
        "name": "ui-ux",
        "version": "1.0.0",
        "description": "UI/UX design - Tailwind, Figma, animations, design systems",
        "tools": ["write_file", "read_file", "web_fetch"],
        "prompts": {
            "tailwind": "Tailwind CSS component design",
            "animation": "CSS/JS animations",
            "design-system": "Build design system",
            "responsive": "Responsive layout implementation",
        },
    },
    "networking": {
        "name": "networking",
        "version": "1.0.0",
        "description": "Networking - TCP/UDP, WebSocket, gRPC, DNS, load balancing",
        "tools": ["run_command", "write_file", "read_file", "web_fetch"],
        "prompts": {
            "websocket": "WebSocket server/client",
            "grpc": "gRPC service definition",
            "dns": "DNS configuration",
            "load-balance": "Load balancer setup",
        },
    },
    "microservices": {
        "name": "microservices",
        "version": "1.0.0",
        "description": "Microservices - service mesh, event-driven, API gateway, saga",
        "tools": ["write_file", "read_file", "run_command"],
        "prompts": {
            "service": "Create microservice scaffold",
            "gateway": "API gateway configuration",
            "event-driven": "Event-driven architecture",
            "saga": "Saga pattern implementation",
        },
    },
    "rust-dev": {
        "name": "rust-dev",
        "version": "1.0.0",
        "description": "Rust development - Cargo, async, traits, WebAssembly",
        "tools": ["write_file", "read_file", "run_command", "grep_search"],
        "prompts": {
            "cargo": "Cargo project setup",
            "async": "Async Rust with Tokio",
            "wasm": "Rust to WebAssembly",
            "traits": "Trait-based design patterns",
        },
    },
    "python-dev": {
        "name": "python-dev",
        "version": "1.0.0",
        "description": "Python development - FastAPI, Django, async, packaging",
        "tools": ["write_file", "read_file", "run_command", "notebook_run"],
        "prompts": {
            "fastapi": "FastAPI application scaffold",
            "django": "Django project setup",
            "packaging": "Python package with pyproject.toml",
            "async": "Async Python with asyncio",
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
