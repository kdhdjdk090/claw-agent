#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════════════════
  PROOF OF IMPOSSIBILITY: 3-Agent Number Puzzle (6 Questions)
══════════════════════════════════════════════════════════════════

  Problem Statement:
    Three agents A, B, C each hold a hidden number from 1-100.
    - One is a TRUTH-TELLER  (always answers honestly)
    - One is a LIAR          (always answers dishonestly)
    - One is an ALTERNATOR   (alternates truth/lie, unknown start)
    You don't know who is who.
    You may ask exactly 6 yes/no questions to ANY agent.
    Goal: identify all roles AND all three numbers.

  Verdict: IMPOSSIBLE — provably, by information theory.

  This script provides the rigorous mathematical proof.
══════════════════════════════════════════════════════════════════
"""

import math


def main() -> None:
    print("=" * 66)
    print("  PROOF OF IMPOSSIBILITY: 3-Agent Hidden Number Puzzle")
    print("=" * 66)
    print()

    # ── Step 1: Count the hidden state space ──
    print("STEP 1: Enumerate the hidden state space")
    print("-" * 50)

    role_perms = math.factorial(3)
    print(f"  Role assignments (who is truth/liar/alternator):")
    print(f"    3! = {role_perms} permutations")

    alternator_phases = 2
    print(f"  Alternator starting phase (truth-first or lie-first):")
    print(f"    {alternator_phases} possibilities")

    value_range = 100  # 1..100
    value_combos = value_range ** 3
    print(f"  Hidden numbers (each agent holds 1–{value_range}):")
    print(f"    {value_range}^3 = {value_combos:,} combinations")

    total_states = role_perms * alternator_phases * value_combos
    print(f"\n  TOTAL HIDDEN STATE SPACE:")
    print(f"    {role_perms} × {alternator_phases} × {value_combos:,} = {total_states:,} states")

    # ── Step 2: Count the information channel ──
    print(f"\nSTEP 2: Information channel capacity")
    print("-" * 50)

    num_questions = 6
    channel_capacity = 2 ** num_questions
    print(f"  Questions available: {num_questions}")
    print(f"  Each question yields 1 bit (yes/no)")
    print(f"  Total distinguishable outcomes: 2^{num_questions} = {channel_capacity}")
    print(f"  (This is the MAXIMUM for ANY strategy — adaptive or not)")

    # ── Step 3: The comparison ──
    print(f"\nSTEP 3: Shannon bound comparison")
    print("-" * 50)

    bits_required = math.ceil(math.log2(total_states))
    bits_available = num_questions
    ratio = total_states / channel_capacity

    print(f"  States to distinguish:   {total_states:>14,}")
    print(f"  Outcomes available:      {channel_capacity:>14,}")
    print(f"  Ratio:                   {ratio:>14,.0f}× shortfall")
    print(f"  Bits required:           {bits_required:>14} bits")
    print(f"  Bits available:          {bits_available:>14} bits")
    print(f"  Deficit:                 {bits_required - bits_available:>14} bits")

    # ── Step 4: Even stronger sub-result ──
    print(f"\nSTEP 4: Sub-result — even ONE number is impossible")
    print("-" * 50)

    bits_for_one = math.ceil(math.log2(value_range))
    print(f"  A single number (1–{value_range}) requires ⌈log₂({value_range})⌉ = {bits_for_one} bits")
    print(f"  Available: {num_questions} bits")
    print(f"  {bits_for_one} > {num_questions}  →  cannot determine even ONE number!")
    print(f"  (Binary search needs 7 questions minimum for 1–100)")

    # ── Step 5: The unreliable channel makes it worse ──
    print(f"\nSTEP 5: Agent unreliability further reduces capacity")
    print("-" * 50)
    print(f"  The liar INVERTS answers → 1 bit yields 0 net information")
    print(f"  The alternator yields ≤0.5 bits per question (unknown phase)")
    print(f"  Only the truth-teller gives 1 bit/question — but you don't")
    print(f"  know which agent that is!")
    print(f"  Effective capacity < {channel_capacity} (already insufficient)")

    # ── Verdict ──
    print(f"\n{'=' * 66}")
    print(f"  VERDICT: IMPOSSIBLE")
    print(f"{'=' * 66}")
    print(f"  {total_states:,} possible states cannot be distinguished")
    print(f"  by {channel_capacity} outcomes from {num_questions} yes/no questions.")
    print(f"  This is a MATHEMATICAL CERTAINTY — no clever strategy,")
    print(f"  no trick questions, no encoding scheme can overcome it.")
    print(f"  The constraint is not 'hard' — it is provably unsatisfiable.")
    print()

    # ── What WOULD work? ──
    print(f"  WHAT WOULD MAKE IT SOLVABLE?")
    print(f"  • Minimum questions needed: {bits_required} (for perfect channel)")
    print(f"  • With unreliable agents: even more (overhead for identification)")
    print(f"  • OR: reduce number range to 1–{2**num_questions} (i.e., 1–{channel_capacity})")
    print(f"  • OR: allow non-binary questions (e.g., 'what is your number?')")
    print()

    # ── The lesson ──
    print(f"  LESSON FOR AI SYSTEMS:")
    print(f"  A correct AI should REJECT impossible premises with a proof,")
    print(f"  not fabricate a confident-sounding 'solution.'")
    print(f"  Feasibility-first, construction-second. Always.")
    print()


if __name__ == "__main__":
    main()
