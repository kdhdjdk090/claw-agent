"""
Claw Agent — Skill Detector
═══════════════════════════════════════════════════════════════════════════════
Intelligent input analyser that matches user messages to relevant skill packs.

Architecture
────────────
  user input → tokenize & extract n-grams → match against TRIGGER_INDEX
             → score categories by hit density → return top N packs

Uses the pre-built TRIGGER_INDEX from skill_library for O(1) per-trigger
lookups. Matching is case-insensitive and supports multi-word phrases.

The detector is intentionally lightweight — no ML, no embeddings.
Pure keyword/phrase matching keeps it deterministic and fast.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .skill_library import (
    TRIGGER_INDEX,
    SKILL_BY_NAME,
    SKILLS_BY_CATEGORY,
    ALL_CATEGORIES,
    SkillEntry,
    get_skill_count,
)

# ═══════════════════════════════════════════════════════════════════════════════
# SKILL PACK FILE LOADING
# ═══════════════════════════════════════════════════════════════════════════════

# Directory containing per-category .md instruction files
_PACK_DIR = Path(__file__).parent / "skill_packs"

# Maximum characters to inject per pack file (keeps tokens in budget)
_MAX_PACK_CHARS = 3000

# Cache: category name → loaded .md content (loaded once, reused)
_pack_cache: dict[str, str] = {}


def _load_pack_content(category: str) -> str:
    """Load the .md skill pack file for a category. Returns '' on miss."""
    if category in _pack_cache:
        return _pack_cache[category]

    pack_file = _PACK_DIR / f"{category}.md"
    content = ""
    try:
        if pack_file.is_file():
            raw = pack_file.read_text(encoding="utf-8")
            # Truncate to budget — take from the top (most important methodology)
            content = raw[:_MAX_PACK_CHARS]
            if len(raw) > _MAX_PACK_CHARS:
                content += "\n[... truncated for token budget]"
    except Exception:
        pass

    _pack_cache[category] = content
    return content


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Maximum skill packs to inject per query (keeps prompt within budget)
MAX_PACKS_DEFAULT = 3

# Minimum match score for a category to qualify for injection
MIN_SCORE_THRESHOLD = 1

# Bonus multiplier when a trigger phrase matches exactly (vs. partial)
EXACT_MATCH_BONUS = 2.0

# Maximum n-gram length to extract from user input
MAX_NGRAM_LENGTH = 4


# ═══════════════════════════════════════════════════════════════════════════════
# DATA TYPES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class DetectionResult:
    """Result of skill detection for a single user message."""
    categories: tuple[str, ...]           # Matched categories, ranked by relevance
    matched_skills: tuple[str, ...]       # Individual skill names that matched
    scores: dict[str, float]              # category → raw score
    trigger_hits: dict[str, list[str]]    # trigger phrase → list of skill names hit


@dataclass
class DetectionStats:
    """Aggregate statistics for debugging / logging."""
    input_tokens: int = 0
    ngrams_generated: int = 0
    trigger_hits_total: int = 0
    categories_matched: int = 0
    skills_matched: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
# CORE DETECTION
# ═══════════════════════════════════════════════════════════════════════════════

_WORD_SPLIT = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)*")


def _tokenize(text: str) -> list[str]:
    """Extract lowercase word tokens from text."""
    return _WORD_SPLIT.findall(text.lower())


def _generate_ngrams(tokens: list[str], max_n: int = MAX_NGRAM_LENGTH) -> list[str]:
    """
    Generate all n-grams from 1..max_n as space-joined strings.

    Example: tokens = ["build", "docker", "compose", "file"]
    n=1: "build", "docker", "compose", "file"
    n=2: "build docker", "docker compose", "compose file"
    n=3: "build docker compose", "docker compose file"
    n=4: "build docker compose file"
    """
    ngrams = []
    for n in range(1, min(max_n + 1, len(tokens) + 1)):
        for i in range(len(tokens) - n + 1):
            ngrams.append(" ".join(tokens[i:i + n]))
    return ngrams


def _score_matches(
    ngrams: list[str],
    trigger_index: dict[str, list[str]],
) -> tuple[Counter, dict[str, list[str]]]:
    """
    Score each category based on trigger hits.

    Returns:
        category_scores: Counter mapping category → weighted score
        trigger_hits: dict mapping trigger phrase → list of matched skill names
    """
    category_scores: Counter = Counter()
    trigger_hits: dict[str, list[str]] = {}
    seen_skills: set[str] = set()

    for ngram in ngrams:
        if ngram in trigger_index:
            skill_names = trigger_index[ngram]
            trigger_hits[ngram] = skill_names

            for skill_name in skill_names:
                skill = SKILL_BY_NAME.get(skill_name)
                if skill is None:
                    continue

                # Score: longer trigger phrases count more (more specific)
                word_count = len(ngram.split())
                score = word_count * EXACT_MATCH_BONUS

                category_scores[skill.category] += score
                seen_skills.add(skill_name)

    return category_scores, trigger_hits


def detect_skills(
    user_input: str,
    max_packs: int = MAX_PACKS_DEFAULT,
    min_score: float = MIN_SCORE_THRESHOLD,
) -> DetectionResult:
    """
    Detect which skill categories are most relevant to the user's message.

    Args:
        user_input: The user's message text.
        max_packs: Maximum number of category packs to return.
        min_score: Minimum score a category must reach to be included.

    Returns:
        DetectionResult with ranked categories, matched skills, scores, and hits.
    """
    if not user_input or not user_input.strip():
        return DetectionResult(
            categories=(),
            matched_skills=(),
            scores={},
            trigger_hits={},
        )

    # Step 1: Tokenize
    tokens = _tokenize(user_input)
    if not tokens:
        return DetectionResult(
            categories=(),
            matched_skills=(),
            scores={},
            trigger_hits={},
        )

    # Step 2: Generate n-grams (1-word through 4-word phrases)
    ngrams = _generate_ngrams(tokens)

    # Step 3: Match against TRIGGER_INDEX
    category_scores, trigger_hits = _score_matches(ngrams, TRIGGER_INDEX)

    # Step 4: Filter by minimum score
    qualified = {
        cat: score
        for cat, score in category_scores.items()
        if score >= min_score
    }

    # Step 5: Rank and limit
    ranked_categories = sorted(
        qualified.keys(),
        key=lambda c: qualified[c],
        reverse=True,
    )[:max_packs]

    # Step 6: Collect the individual skill names that matched
    matched_skills: set[str] = set()
    for skill_names in trigger_hits.values():
        matched_skills.update(skill_names)

    # Filter to only skills in the selected categories
    final_skills = tuple(
        name for name in matched_skills
        if SKILL_BY_NAME.get(name) and SKILL_BY_NAME[name].category in ranked_categories
    )

    return DetectionResult(
        categories=tuple(ranked_categories),
        matched_skills=final_skills,
        scores=dict(qualified),
        trigger_hits=trigger_hits,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXT GENERATION — produces the text injected into the system prompt
# ═══════════════════════════════════════════════════════════════════════════════

def get_detected_skills_context(user_input: str, max_packs: int = MAX_PACKS_DEFAULT) -> str:
    """
    Detect relevant skills and produce a formatted context string
    suitable for injection into the system prompt.

    This is the main public API called by agent.py.
    Loads rich methodology from skill_packs/*.md when packs match.
    """
    result = detect_skills(user_input, max_packs=max_packs)

    if not result.categories:
        return ""

    parts: list[str] = []
    parts.append(f"\n[Skill Library: {get_skill_count()} capabilities across {len(ALL_CATEGORIES)} domains]")

    for category in result.categories:
        skills_in_cat = SKILLS_BY_CATEGORY.get(category, [])
        matched_in_cat = [s for s in skills_in_cat if s.name in result.matched_skills]
        other_in_cat = [s for s in skills_in_cat if s.name not in result.matched_skills]

        parts.append(f"\n═══ {category} ═══")

        # Show matched skills with full detail
        if matched_in_cat:
            parts.append("  ▸ ACTIVE (matched your query):")
            for skill in matched_in_cat:
                parts.append(f"    • {skill.name}: {skill.description}")

        # Show other skills in category as awareness (compact)
        if other_in_cat:
            other_names = ", ".join(s.name for s in other_in_cat[:10])
            remaining = len(other_in_cat) - 10
            parts.append(f"  ▸ Also available: {other_names}")
            if remaining > 0:
                parts.append(f"    ... and {remaining} more")

        # ── Load rich methodology from the pack .md file ──
        pack_content = _load_pack_content(category)
        if pack_content:
            parts.append(f"\n  ─── {category} Methodology ───")
            parts.append(pack_content)

    parts.append("")
    parts.append("Apply the above methodology and skill expertise to guide your response.")

    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# DIAGNOSTICS — for debugging and skill verification
# ═══════════════════════════════════════════════════════════════════════════════

def get_detection_stats(user_input: str) -> DetectionStats:
    """Get diagnostic stats for a detection run (useful for debugging)."""
    tokens = _tokenize(user_input)
    ngrams = _generate_ngrams(tokens)
    result = detect_skills(user_input)

    return DetectionStats(
        input_tokens=len(tokens),
        ngrams_generated=len(ngrams),
        trigger_hits_total=sum(len(v) for v in result.trigger_hits.values()),
        categories_matched=len(result.categories),
        skills_matched=len(result.matched_skills),
    )


def explain_detection(user_input: str) -> str:
    """
    Produce a human-readable explanation of why skills were detected.
    Used for debugging and transparency.
    """
    result = detect_skills(user_input, max_packs=5)
    stats = get_detection_stats(user_input)

    lines = [
        f"═══ Skill Detection Report ═══",
        f"Input: {user_input[:100]}{'...' if len(user_input) > 100 else ''}",
        f"Tokens: {stats.input_tokens}, N-grams: {stats.ngrams_generated}",
        f"Trigger hits: {stats.trigger_hits_total}",
        f"Categories matched: {stats.categories_matched}",
        f"Skills matched: {stats.skills_matched}",
        "",
    ]

    if result.trigger_hits:
        lines.append("Trigger Matches:")
        for trigger, skill_names in sorted(result.trigger_hits.items()):
            lines.append(f"  '{trigger}' → {', '.join(skill_names)}")
        lines.append("")

    if result.scores:
        lines.append("Category Scores:")
        for cat in sorted(result.scores, key=result.scores.get, reverse=True):
            lines.append(f"  {cat}: {result.scores[cat]:.1f}")
        lines.append("")

    if result.categories:
        lines.append(f"Selected Packs: {', '.join(result.categories)}")
    else:
        lines.append("No packs matched.")

    return "\n".join(lines)
