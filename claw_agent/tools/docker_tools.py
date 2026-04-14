"""Docker tools — container and compose management."""

from __future__ import annotations

import subprocess
from pathlib import Path


def docker_ps(all_containers: bool = False) -> str:
    """List Docker containers.

    Args:
        all_containers: If True, include stopped containers.
    """
    cmd = ["docker", "ps", "--format", "table {{.ID}}\\t{{.Image}}\\t{{.Status}}\\t{{.Names}}\\t{{.Ports}}"]
    if all_containers:
        cmd.insert(2, "-a")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            return f"Error: {result.stderr.strip()}"
        output = result.stdout.strip()
        if not output or output.count("\n") == 0:
            return "No running containers." if not all_containers else "No containers found."
        return output
    except FileNotFoundError:
        return "Error: Docker not found. Is Docker installed and in PATH?"
    except subprocess.TimeoutExpired:
        return "Error: Docker command timed out."


def docker_build(directory: str = ".", tag: str = "", dockerfile: str = "") -> str:
    """Build a Docker image.

    Args:
        directory: Build context directory.
        tag: Image tag (e.g., 'myapp:latest').
        dockerfile: Path to Dockerfile (default: Dockerfile in directory).
    """
    root = Path(directory).expanduser().resolve()
    if not root.is_dir():
        return f"Error: Not a directory — {directory}"

    df_path = Path(dockerfile) if dockerfile else root / "Dockerfile"
    if not dockerfile:
        df_path = root / "Dockerfile"
        if not df_path.exists():
            df_path = root / "dockerfile"
    if not df_path.exists():
        return f"Error: No Dockerfile found in {root}"

    cmd = ["docker", "build", "."]
    if tag:
        cmd.extend(["-t", tag])
    if dockerfile:
        cmd.extend(["-f", str(df_path)])

    try:
        result = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            # Trim to last 30 lines
            err_lines = result.stderr.strip().splitlines()
            return "Build failed:\n" + "\n".join(err_lines[-30:])
        # Show last 10 lines of output (usually the final steps)
        out_lines = result.stdout.strip().splitlines()
        summary = "\n".join(out_lines[-10:])
        return f"✓ Build succeeded.\n\n{summary}"
    except FileNotFoundError:
        return "Error: Docker not found."
    except subprocess.TimeoutExpired:
        return "Error: Build timed out after 300s."


def docker_compose_up(directory: str = ".", detach: bool = True, services: str = "") -> str:
    """Start Docker Compose services.

    Args:
        directory: Directory containing docker-compose.yml.
        detach: Run in background (default True).
        services: Space-separated service names (blank = all).
    """
    root = Path(directory).expanduser().resolve()
    compose_file = None
    for name in ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]:
        if (root / name).exists():
            compose_file = name
            break
    if not compose_file:
        return f"Error: No docker-compose file found in {root}"

    # Try docker compose (v2) first, fall back to docker-compose (v1)
    for base in [["docker", "compose"], ["docker-compose"]]:
        cmd = base + ["up"]
        if detach:
            cmd.append("-d")
        if services:
            cmd.extend(services.split())

        try:
            result = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                output = (result.stdout or result.stderr).strip()
                return f"✓ Compose services started.\n\n{output[-500:]}"
            if "not found" not in result.stderr.lower() and "unknown" not in result.stderr.lower():
                return f"Error:\n{result.stderr.strip()[-500:]}"
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            return "Error: Compose timed out after 120s."

    return "Error: Neither 'docker compose' nor 'docker-compose' found."


def docker_compose_down(directory: str = ".", remove_volumes: bool = False) -> str:
    """Stop Docker Compose services.

    Args:
        directory: Directory containing docker-compose.yml.
        remove_volumes: Also remove volumes (default False).
    """
    root = Path(directory).expanduser().resolve()

    for base in [["docker", "compose"], ["docker-compose"]]:
        cmd = base + ["down"]
        if remove_volumes:
            cmd.append("-v")
        try:
            result = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return f"✓ Compose services stopped.\n\n{(result.stdout or result.stderr).strip()[-300:]}"
            if "not found" not in result.stderr.lower() and "unknown" not in result.stderr.lower():
                return f"Error:\n{result.stderr.strip()[-300:]}"
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            return "Error: Timed out."

    return "Error: Docker Compose not found."
