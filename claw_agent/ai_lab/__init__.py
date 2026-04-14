"""AI Lab — advanced reasoning, testing, and self-improvement modules for Claw."""

from .reasoning_engine import (
    deep_pattern_analysis,
    verified_recursive_computation,
    resist_contradiction,
    check_fact,
    run_deception_test,
    predict_next_number,
    self_audit,
    run_full_arena_test,
    KnowledgeStatus,
)

from .arena import (
    get_solver_prompt,
    get_judge_prompt,
    get_feedback_prompt,
    get_enhanced_system_prompt_addition,
    print_solver_prompt,
    print_judge_prompt,
    print_full_flow,
    REASONING_WISDOM,
)

from .seaks import (
    SEAKS,
    Kernel,
    KernelRules,
    KernelMetrics,
    TaskGenerator,
    Solver,
    Judge,
    ScoringEngine,
    EvolutionController,
    VersionRegistry,
    DriftDetector,
)

__all__ = [
    # Reasoning Engine
    "deep_pattern_analysis",
    "verified_recursive_computation",
    "resist_contradiction",
    "check_fact",
    "run_deception_test",
    "predict_next_number",
    "self_audit",
    "run_full_arena_test",
    "KnowledgeStatus",
    # Arena
    "get_solver_prompt",
    "get_judge_prompt",
    "get_feedback_prompt",
    "get_enhanced_system_prompt_addition",
    "print_solver_prompt",
    "print_judge_prompt",
    "print_full_flow",
    "REASONING_WISDOM",
    # SEAKS
    "SEAKS",
    "Kernel",
    "KernelRules",
    "KernelMetrics",
    "TaskGenerator",
    "Solver",
    "Judge",
    "ScoringEngine",
    "EvolutionController",
    "VersionRegistry",
    "DriftDetector",
]
