"""Complete Skill Library for Claw AI — Claude-level coverage.

This module contains the FULL registry of ~660 skills organized by category,
each with name, description, trigger keywords, and category assignment.
The skill_detector uses this registry to match user input to relevant skills,
and the skill_packs provide the detailed instructions for each category.

Architecture:
  skill_library.py  →  Registry of ALL skills (this file)
  skill_detector.py →  Matches user input → skill names + categories
  skill_packs/      →  Detailed instructions per category (injected on-demand)
  skills.py         →  Integration layer (loads packs into system prompt)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class SkillEntry:
    """Single skill in the library."""
    name: str
    category: str
    description: str
    triggers: tuple[str, ...]  # Keywords that activate this skill


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

CAT_ENGINEERING_CORE = "engineering-core"
CAT_FRONTEND = "frontend"
CAT_BACKEND = "backend"
CAT_DEVOPS = "devops-infra"
CAT_SECURITY = "security"
CAT_TESTING = "testing-qa"
CAT_DATA = "data-analytics"
CAT_DESIGN_UI = "design-ui"
CAT_MOBILE = "mobile"
CAT_MARKETING = "marketing-growth"
CAT_BUSINESS = "business-strategy"
CAT_GAME_DEV = "game-dev"
CAT_WRITING = "writing-content"
CAT_PRODUCTIVITY = "productivity"
CAT_SPECIALIZED = "specialized-domains"
CAT_DOCUMENT = "document-processing"
CAT_AI_ML = "ai-ml"
CAT_BLOCKCHAIN = "blockchain-web3"

ALL_CATEGORIES = (
    CAT_ENGINEERING_CORE, CAT_FRONTEND, CAT_BACKEND, CAT_DEVOPS,
    CAT_SECURITY, CAT_TESTING, CAT_DATA, CAT_DESIGN_UI, CAT_MOBILE,
    CAT_MARKETING, CAT_BUSINESS, CAT_GAME_DEV, CAT_WRITING,
    CAT_PRODUCTIVITY, CAT_SPECIALIZED, CAT_DOCUMENT, CAT_AI_ML,
    CAT_BLOCKCHAIN,
)


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLETE SKILL REGISTRY — 660+ skills, every single one Claude has
# ═══════════════════════════════════════════════════════════════════════════════

SKILL_REGISTRY: tuple[SkillEntry, ...] = (

    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  ENGINEERING CORE — coding standards, architecture, git, patterns   ║
    # ╚═══════════════════════════════════════════════════════════════════════╝

    SkillEntry("coding-standards", CAT_ENGINEERING_CORE,
        "Cross-project coding conventions for naming, readability, immutability, and code-quality review",
        ("coding standards", "naming conventions", "code quality", "readability", "clean code", "immutability")),

    SkillEntry("git-workflow", CAT_ENGINEERING_CORE,
        "Git branching strategies, commit conventions, merge vs rebase, conflict resolution",
        ("git", "branching", "commit", "merge", "rebase", "conflict", "cherry-pick", "git workflow", "conventional commits")),

    SkillEntry("architecture-decision-records", CAT_ENGINEERING_CORE,
        "Capture architectural decisions as structured ADRs with context, alternatives, rationale",
        ("adr", "architecture decision", "decision record", "technical decision", "design decision")),

    SkillEntry("hexagonal-architecture", CAT_ENGINEERING_CORE,
        "Ports & Adapters pattern with clear domain boundaries, dependency inversion",
        ("hexagonal", "ports and adapters", "clean architecture", "domain driven", "ddd", "dependency inversion")),

    SkillEntry("api-design", CAT_ENGINEERING_CORE,
        "REST API design patterns — resource naming, status codes, pagination, filtering, error responses",
        ("api design", "rest api", "api patterns", "pagination", "filtering", "error response", "resource naming")),

    SkillEntry("database-migrations", CAT_ENGINEERING_CORE,
        "Database migration best practices for schema changes, data migrations, rollbacks",
        ("database migration", "schema change", "migration rollback", "prisma migrate", "drizzle", "django migration")),

    SkillEntry("deployment-patterns", CAT_ENGINEERING_CORE,
        "Deployment workflows, CI/CD, Docker containerization, health checks, rollback strategies",
        ("deployment", "ci/cd", "docker", "health check", "rollback", "blue green", "canary")),

    SkillEntry("codebase-onboarding", CAT_ENGINEERING_CORE,
        "Analyze unfamiliar codebase and generate structured onboarding guide",
        ("codebase onboarding", "new project", "unfamiliar code", "onboarding guide", "architecture map")),

    SkillEntry("code-tour", CAT_ENGINEERING_CORE,
        "Create CodeTour .tour files — step-by-step walkthroughs with real file and line anchors",
        ("code tour", "walkthrough", "onboarding tour", "architecture tour", "codetour")),

    SkillEntry("blueprint", CAT_ENGINEERING_CORE,
        "Turn a one-line objective into a step-by-step construction plan for multi-session projects",
        ("blueprint", "construction plan", "multi-session", "project plan", "roadmap")),

    SkillEntry("verification-loop", CAT_ENGINEERING_CORE,
        "Comprehensive verification system — lint, test, coverage, security scan before completion",
        ("verification", "verify", "check everything", "lint", "pre-commit", "pre-merge")),

    SkillEntry("continuous-learning", CAT_ENGINEERING_CORE,
        "Extract reusable patterns from sessions and save as learned skills",
        ("continuous learning", "learn from session", "extract pattern", "self-improving")),

    SkillEntry("strategic-compact", CAT_ENGINEERING_CORE,
        "Manual context compaction at logical intervals to preserve context through task phases",
        ("compact", "context compaction", "context budget", "token budget")),

    SkillEntry("pr-review-expert", CAT_ENGINEERING_CORE,
        "Review pull requests, analyze code changes, check for security issues in PRs",
        ("pr review", "pull request", "code review", "review changes", "diff review")),

    SkillEntry("changelog-generator", CAT_ENGINEERING_CORE,
        "Create user-facing changelogs from git commits, categorize changes automatically",
        ("changelog", "release notes", "what changed", "version history")),

    SkillEntry("spec-driven-workflow", CAT_ENGINEERING_CORE,
        "Write specs before code, define acceptance criteria, plan features before implementation",
        ("spec driven", "specification", "acceptance criteria", "spec first", "requirements")),

    SkillEntry("tech-debt-tracker", CAT_ENGINEERING_CORE,
        "Scan codebases for technical debt, score severity, generate remediation plans",
        ("tech debt", "technical debt", "code smell", "cleanup", "refactoring priority")),

    SkillEntry("monorepo-navigator", CAT_ENGINEERING_CORE,
        "Navigate, manage, and understand monorepo architectures",
        ("monorepo", "workspace", "turborepo", "nx", "lerna", "pnpm workspace")),

    SkillEntry("release-manager", CAT_ENGINEERING_CORE,
        "Plan releases, manage changelogs, coordinate deployments, automate versioning",
        ("release", "version", "semver", "release branch", "release candidate")),

    SkillEntry("env-secrets-manager", CAT_ENGINEERING_CORE,
        "Manage environment variables, secrets, and configuration safely",
        ("env", "secrets", "environment variables", ".env", "vault", "secret management")),

    SkillEntry("dependency-auditor", CAT_ENGINEERING_CORE,
        "Audit project dependencies for vulnerabilities, outdated packages, and license issues",
        ("dependency audit", "npm audit", "outdated packages", "license check", "vulnerability")),

    SkillEntry("mcp-server-patterns", CAT_ENGINEERING_CORE,
        "Build MCP servers with Node/TypeScript SDK — tools, resources, prompts, validation",
        ("mcp server", "model context protocol", "mcp tools", "mcp resources")),

    SkillEntry("focused-fix", CAT_ENGINEERING_CORE,
        "Systematic deep-dive repair across all files and dependencies for a specific feature",
        ("focused fix", "make it work", "fix the feature", "deep fix", "end to end fix")),

    SkillEntry("karpathy-coder", CAT_ENGINEERING_CORE,
        "Enforce Karpathy's 4 coding principles — surface assumptions, keep it simple, surgical changes",
        ("karpathy", "simple code", "surgical change", "overcoding", "before i commit")),

    SkillEntry("self-eval", CAT_ENGINEERING_CORE,
        "Honestly evaluate AI work quality using two-axis scoring system",
        ("self eval", "evaluate work", "quality score", "honest assessment")),


    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  FRONTEND — React, Next.js, Vue, Svelte, CSS, design systems       ║
    # ╚═══════════════════════════════════════════════════════════════════════╝

    SkillEntry("frontend-patterns", CAT_FRONTEND,
        "Frontend patterns for React, Next.js, state management, performance optimization",
        ("react", "next.js", "nextjs", "frontend", "component", "state management", "hooks", "ssr", "ssg")),

    SkillEntry("frontend-design", CAT_FRONTEND,
        "Create distinctive production-grade frontend interfaces with high design quality",
        ("frontend design", "ui design", "interface", "landing page", "web design", "beautiful ui")),

    SkillEntry("frontend-slides", CAT_FRONTEND,
        "Create stunning animation-rich HTML presentations from scratch or by converting PowerPoint",
        ("slides", "presentation", "pptx to html", "reveal.js", "html slides")),

    SkillEntry("design-system", CAT_FRONTEND,
        "Generate or audit design systems, check visual consistency, review styling PRs",
        ("design system", "design tokens", "component library", "visual consistency", "theme")),

    SkillEntry("nextjs-turbopack", CAT_FRONTEND,
        "Next.js 16+ and Turbopack — incremental bundling, FS caching, dev speed",
        ("turbopack", "next.js 16", "bundler", "webpack alternative")),

    SkillEntry("nuxt4-patterns", CAT_FRONTEND,
        "Nuxt 4 app patterns for hydration safety, performance, route rules, lazy loading",
        ("nuxt", "vue", "nuxt 4", "vue 3", "hydration", "usefetch", "useasyncdata")),

    SkillEntry("bun-runtime", CAT_FRONTEND,
        "Bun as runtime, package manager, bundler, and test runner",
        ("bun", "bun runtime", "bun test", "bun install", "bun build")),

    SkillEntry("epic-design", CAT_FRONTEND,
        "Immersive cinematic 2.5D interactive websites with scroll storytelling, parallax",
        ("cinematic", "scroll animation", "parallax", "immersive", "storytelling", "apple style")),

    SkillEntry("remotion-video", CAT_FRONTEND,
        "Video creation in React using Remotion — 3D, animations, audio, captions, transitions",
        ("remotion", "react video", "programmatic video")),

    SkillEntry("web-artifacts-builder", CAT_FRONTEND,
        "Create elaborate multi-component React artifacts with state management and routing",
        ("web artifact", "react app", "multi-component", "complex ui")),

    SkillEntry("d3js-visualization", CAT_FRONTEND,
        "Interactive data visualizations using d3.js — charts, graphs, network diagrams, geographic",
        ("d3", "d3.js", "data visualization", "svg chart", "interactive chart")),

    SkillEntry("algorithmic-art", CAT_FRONTEND,
        "Create algorithmic art using p5.js with seeded randomness and interactive parameters",
        ("algorithmic art", "generative art", "p5.js", "creative coding", "flow field")),

    SkillEntry("canvas-design", CAT_FRONTEND,
        "Create beautiful visual art in .png and .pdf using design philosophy",
        ("canvas", "poster", "visual art", "png design", "pdf art")),

    SkillEntry("accessibility-audit", CAT_FRONTEND,
        "WCAG 2.2 Level A/AA compliance scanning, fixing, and verification",
        ("accessibility", "a11y", "wcag", "aria", "screen reader", "color contrast")),

    SkillEntry("ui-ux-pro-max", CAT_FRONTEND,
        "UI/UX design intelligence — 50+ styles, 161 color palettes, 57 font pairings, 99 UX guidelines",
        ("ui ux", "color palette", "font pairing", "ux guideline", "glassmorphism", "neumorphism")),

    SkillEntry("email-template-builder", CAT_FRONTEND,
        "Build responsive email templates compatible with all email clients",
        ("email template", "html email", "responsive email", "email design")),

    SkillEntry("landing-page-generator", CAT_FRONTEND,
        "Generate high-converting landing pages as Next.js/React components with Tailwind",
        ("landing page", "marketing page", "lead capture", "conversion page")),


    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  BACKEND — API, databases, Django, Laravel, NestJS, Spring Boot     ║
    # ╚═══════════════════════════════════════════════════════════════════════╝

    SkillEntry("backend-patterns", CAT_BACKEND,
        "Backend architecture, API design, database optimization for Node.js, Express, Next.js",
        ("backend", "express", "node.js", "api route", "server side")),

    SkillEntry("django-patterns", CAT_BACKEND,
        "Django architecture, REST API with DRF, ORM, caching, signals, middleware",
        ("django", "drf", "django rest", "django orm", "django model")),

    SkillEntry("django-security", CAT_BACKEND,
        "Django security — authentication, CSRF, SQL injection prevention, XSS prevention",
        ("django security", "django csrf", "django auth")),

    SkillEntry("django-tdd", CAT_BACKEND,
        "Django testing with pytest-django, TDD, factory_boy, mocking, coverage",
        ("django test", "pytest-django", "django tdd", "factory_boy")),

    SkillEntry("laravel-patterns", CAT_BACKEND,
        "Laravel architecture, routing, Eloquent ORM, service layers, queues, events",
        ("laravel", "eloquent", "artisan", "blade", "laravel queue")),

    SkillEntry("laravel-security", CAT_BACKEND,
        "Laravel security — validation, CSRF, mass assignment, file uploads, secrets",
        ("laravel security", "laravel validation", "laravel auth")),

    SkillEntry("laravel-tdd", CAT_BACKEND,
        "TDD for Laravel with PHPUnit and Pest, factories, database testing",
        ("laravel test", "phpunit", "pest php", "laravel tdd")),

    SkillEntry("nestjs-patterns", CAT_BACKEND,
        "NestJS architecture — modules, controllers, providers, DTO validation, guards",
        ("nestjs", "nest.js", "nestjs module", "nestjs guard", "nestjs interceptor")),

    SkillEntry("springboot-patterns", CAT_BACKEND,
        "Spring Boot architecture, REST API, layered services, data access, caching",
        ("spring boot", "spring", "java spring", "spring rest", "@RestController")),

    SkillEntry("springboot-security", CAT_BACKEND,
        "Spring Security — authn/authz, validation, CSRF, secrets, headers, rate limiting",
        ("spring security", "spring auth", "spring jwt")),

    SkillEntry("springboot-tdd", CAT_BACKEND,
        "TDD for Spring Boot using JUnit 5, Mockito, MockMvc, Testcontainers",
        ("spring test", "junit 5", "mockito", "testcontainers", "spring tdd")),

    SkillEntry("golang-patterns", CAT_BACKEND,
        "Idiomatic Go patterns, error handling, concurrency, interfaces",
        ("go", "golang", "goroutine", "go pattern", "go module")),

    SkillEntry("golang-testing", CAT_BACKEND,
        "Go testing — table-driven tests, subtests, benchmarks, fuzzing, coverage",
        ("go test", "golang test", "go benchmark", "go fuzz")),

    SkillEntry("rust-patterns", CAT_BACKEND,
        "Idiomatic Rust — ownership, error handling, traits, concurrency",
        ("rust", "cargo", "ownership", "borrow checker", "rust trait")),

    SkillEntry("rust-testing", CAT_BACKEND,
        "Rust testing — unit tests, integration tests, async testing, property-based",
        ("rust test", "cargo test", "rust async test")),

    SkillEntry("python-patterns", CAT_BACKEND,
        "Pythonic idioms, PEP 8, type hints, best practices for Python",
        ("python", "pep 8", "type hints", "pythonic", "python pattern")),

    SkillEntry("python-testing", CAT_BACKEND,
        "Python testing with pytest, TDD, fixtures, mocking, parametrization",
        ("pytest", "python test", "unittest", "python mock", "python tdd")),

    SkillEntry("kotlin-patterns", CAT_BACKEND,
        "Idiomatic Kotlin — coroutines, null safety, DSL builders",
        ("kotlin", "kotlin pattern", "kotlin coroutine", "kotlin dsl")),

    SkillEntry("kotlin-ktor-patterns", CAT_BACKEND,
        "Ktor server — routing DSL, plugins, authentication, Koin DI, kotlinx.serialization",
        ("ktor", "ktor server", "kotlin server")),

    SkillEntry("kotlin-exposed-patterns", CAT_BACKEND,
        "JetBrains Exposed ORM — DSL queries, DAO pattern, transactions, HikariCP",
        ("exposed", "kotlin orm", "kotlin database")),

    SkillEntry("java-coding-standards", CAT_BACKEND,
        "Java coding standards for Spring Boot — naming, immutability, Optional, streams",
        ("java", "java coding", "java standard", "java naming")),

    SkillEntry("jpa-patterns", CAT_BACKEND,
        "JPA/Hibernate — entity design, relationships, query optimization, transactions",
        ("jpa", "hibernate", "entity", "jpql", "spring data")),

    SkillEntry("perl-patterns", CAT_BACKEND,
        "Modern Perl 5.36+ idioms and best practices",
        ("perl", "perl 5", "cpan")),

    SkillEntry("cpp-coding-standards", CAT_BACKEND,
        "C++ coding standards based on C++ Core Guidelines",
        ("c++", "cpp", "c++ standard", "core guidelines")),

    SkillEntry("dotnet-patterns", CAT_BACKEND,
        "Idiomatic C# and .NET — DI, async/await, best practices",
        (".net", "c#", "csharp", "dotnet", "asp.net")),

    SkillEntry("postgres-patterns", CAT_BACKEND,
        "PostgreSQL query optimization, schema design, indexing, security",
        ("postgres", "postgresql", "sql optimization", "pg", "supabase")),

    SkillEntry("clickhouse-patterns", CAT_BACKEND,
        "ClickHouse analytics, query optimization, data engineering for OLAP workloads",
        ("clickhouse", "olap", "analytics database")),

    SkillEntry("sql-database-assistant", CAT_BACKEND,
        "Write SQL queries, optimize performance, generate migrations, work with ORMs",
        ("sql", "orm", "prisma", "drizzle", "typeorm", "sqlalchemy", "database query")),

    SkillEntry("database-designer", CAT_BACKEND,
        "Design database schemas, plan data migrations, choose between SQL and NoSQL",
        ("database design", "schema design", "er diagram", "nosql vs sql")),

    SkillEntry("stripe-integration", CAT_BACKEND,
        "Stripe integration — Checkout Sessions, PaymentIntents, Connect, billing, webhooks",
        ("stripe", "payment", "checkout", "subscription billing", "stripe webhook")),


    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  DEVOPS & INFRASTRUCTURE — Docker, Terraform, CI/CD, Cloud          ║
    # ╚═══════════════════════════════════════════════════════════════════════╝

    SkillEntry("docker-patterns", CAT_DEVOPS,
        "Docker and Docker Compose — local dev, container security, networking, volumes",
        ("docker", "dockerfile", "docker-compose", "container", "docker network")),

    SkillEntry("docker-development", CAT_DEVOPS,
        "Dockerfile optimization, multi-stage builds, container security hardening",
        ("multi-stage", "docker optimization", "docker security", "image size")),

    SkillEntry("terraform-patterns", CAT_DEVOPS,
        "Terraform IaC — module design, state management, provider configuration, CI/CD",
        ("terraform", "opentofu", "infrastructure as code", "iac", "terraform module")),

    SkillEntry("helm-chart-builder", CAT_DEVOPS,
        "Helm chart development — scaffolding, values design, template patterns, security",
        ("helm", "helm chart", "kubernetes chart", "helm template")),

    SkillEntry("aws-solution-architect", CAT_DEVOPS,
        "AWS architecture for startups — serverless, CloudFormation, Lambda, cost optimization",
        ("aws", "lambda", "cloudformation", "s3", "ec2", "dynamodb", "api gateway")),

    SkillEntry("azure-cloud-architect", CAT_DEVOPS,
        "Azure architecture — Bicep/ARM templates, AKS, App Service, Azure Functions, Cosmos DB",
        ("azure", "bicep", "aks", "azure functions", "cosmos db", "azure devops")),

    SkillEntry("gcp-cloud-architect", CAT_DEVOPS,
        "GCP architecture — Cloud Run, GKE, Cloud Functions, BigQuery, cost optimization",
        ("gcp", "google cloud", "cloud run", "gke", "bigquery", "cloud functions")),

    SkillEntry("ci-cd-pipeline-builder", CAT_DEVOPS,
        "Build CI/CD pipelines for GitHub Actions, GitLab CI, and other platforms",
        ("ci/cd", "github actions", "gitlab ci", "pipeline", "continuous integration")),

    SkillEntry("observability-designer", CAT_DEVOPS,
        "Design observability stacks — logging, metrics, tracing, alerting",
        ("observability", "logging", "metrics", "tracing", "grafana", "prometheus", "datadog")),

    SkillEntry("dashboard-builder", CAT_DEVOPS,
        "Build monitoring dashboards for Grafana, SigNoz, and similar platforms",
        ("dashboard", "grafana", "monitoring", "signoz", "kibana")),

    SkillEntry("incident-commander", CAT_DEVOPS,
        "Incident response command — classify severity, coordinate teams, run post-mortems",
        ("incident", "outage", "postmortem", "on-call", "sev1", "incident response")),

    SkillEntry("runbook-generator", CAT_DEVOPS,
        "Generate operational runbooks for common and emergency scenarios",
        ("runbook", "playbook", "operational guide", "emergency procedure")),

    SkillEntry("cloudflare-workers", CAT_DEVOPS,
        "Cloudflare Workers code, Wrangler CLI, Durable Objects, D1, R2, KV",
        ("cloudflare", "workers", "wrangler", "durable objects", "cloudflare d1")),

    SkillEntry("cloudflare-agents-sdk", CAT_DEVOPS,
        "Build AI agents on Cloudflare Workers using the Agents SDK",
        ("cloudflare agent", "agents sdk", "cloudflare ai")),

    SkillEntry("senior-devops", CAT_DEVOPS,
        "Comprehensive DevOps — CI/CD, infrastructure automation, containerization, cloud platforms",
        ("devops", "infrastructure", "deploy", "provision", "orchestration")),


    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  SECURITY — audits, pen testing, compliance, threat detection       ║
    # ╚═══════════════════════════════════════════════════════════════════════╝

    SkillEntry("security-review", CAT_SECURITY,
        "Security checklist for auth, user input, secrets, API endpoints, sensitive features",
        ("security review", "security checklist", "auth security", "input validation")),

    SkillEntry("security-scan", CAT_SECURITY,
        "Scan configurations for security vulnerabilities and misconfigurations",
        ("security scan", "vulnerability scan", "config audit")),

    SkillEntry("security-pen-testing", CAT_SECURITY,
        "Penetration testing, OWASP Top 10 checks, offensive security assessments",
        ("pen test", "penetration test", "owasp", "offensive security", "vulnerability assessment")),

    SkillEntry("security-bounty-hunter", CAT_SECURITY,
        "Hunt for exploitable bounty-worthy security issues in repositories",
        ("bug bounty", "bounty", "exploit", "security hunt")),

    SkillEntry("cloud-security", CAT_SECURITY,
        "Cloud infrastructure security — IAM, S3, security groups, IaC security",
        ("cloud security", "iam", "s3 public", "security group", "cloud posture")),

    SkillEntry("ai-security", CAT_SECURITY,
        "AI/ML security — prompt injection, jailbreak, model inversion, data poisoning",
        ("ai security", "prompt injection", "jailbreak", "adversarial", "ai safety")),

    SkillEntry("red-team", CAT_SECURITY,
        "Red team — MITRE ATT&CK kill-chain, attack path analysis, offensive simulations",
        ("red team", "mitre att&ck", "attack path", "offensive")),

    SkillEntry("threat-detection", CAT_SECURITY,
        "Threat hunting — IOC analysis, behavioral anomalies, z-score anomaly detection",
        ("threat hunting", "ioc", "threat detection", "anomaly", "siem")),

    SkillEntry("incident-response", CAT_SECURITY,
        "Security incident classification, triage, escalation, forensic evidence collection",
        ("incident response", "security incident", "forensics", "breach")),

    SkillEntry("senior-secops", CAT_SECURITY,
        "Application security, vulnerability management, compliance (SOC2, PCI-DSS, HIPAA, GDPR)",
        ("secops", "compliance", "soc2", "pci-dss", "gdpr", "cve remediation")),

    SkillEntry("hipaa-compliance", CAT_SECURITY,
        "HIPAA privacy and security for healthcare — PHI handling, covered entities, BAAs",
        ("hipaa", "phi", "healthcare compliance", "covered entity")),

    SkillEntry("soc2-compliance", CAT_SECURITY,
        "SOC 2 audit preparation — Trust Service Criteria, control matrices, evidence collection",
        ("soc 2", "soc2", "trust service criteria", "audit evidence")),

    SkillEntry("gdpr-dsgvo-expert", CAT_SECURITY,
        "GDPR and German DSGVO compliance — DPIA, data subject rights, privacy audits",
        ("gdpr", "dsgvo", "data protection", "privacy", "dpia")),

    SkillEntry("iso27001-isms", CAT_SECURITY,
        "ISO 27001 ISMS implementation, security risk assessment, control implementation",
        ("iso 27001", "isms", "information security", "iso27001")),

    SkillEntry("defi-amm-security", CAT_SECURITY,
        "Solidity AMM security — reentrancy, CEI ordering, oracle manipulation, slippage",
        ("defi security", "amm", "reentrancy", "solidity security")),


    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  TESTING & QA — TDD, E2E, unit, integration, Playwright, Jest      ║
    # ╚═══════════════════════════════════════════════════════════════════════╝

    SkillEntry("tdd-workflow", CAT_TESTING,
        "Test-driven development with 80%+ coverage — unit, integration, E2E",
        ("tdd", "test driven", "red green refactor", "test first")),

    SkillEntry("e2e-testing", CAT_TESTING,
        "Playwright E2E testing — Page Object Model, configuration, CI/CD, flaky test strategies",
        ("e2e", "playwright", "end to end", "browser test")),

    SkillEntry("playwright-pro", CAT_TESTING,
        "Production-grade Playwright toolkit — generate tests, fix flaky, migrate from Cypress",
        ("playwright", "flaky test", "cypress migrate", "browser automation")),

    SkillEntry("senior-qa", CAT_TESTING,
        "Generate unit/integration/E2E tests for React/Next.js — Jest, RTL, Playwright, MSW",
        ("jest", "react testing library", "msw", "test coverage", "test stub")),

    SkillEntry("tdd-guide", CAT_TESTING,
        "TDD skill for writing unit tests, generating fixtures and mocks across frameworks",
        ("unit test", "mock", "fixture", "test framework", "vitest")),

    SkillEntry("api-test-suite-builder", CAT_TESTING,
        "Generate API tests, create integration test suites, build contract tests",
        ("api test", "integration test", "contract test", "api testing")),

    SkillEntry("csharp-testing", CAT_TESTING,
        "C# testing with xUnit, FluentAssertions, mocking, integration tests",
        ("xunit", "csharp test", "fluent assertions", ".net test")),

    SkillEntry("cpp-testing", CAT_TESTING,
        "C++ testing with GoogleTest/CTest, sanitizers, coverage",
        ("gtest", "googletest", "ctest", "c++ test")),

    SkillEntry("kotlin-testing", CAT_TESTING,
        "Kotlin testing with Kotest, MockK, coroutine testing, property-based",
        ("kotest", "mockk", "kotlin test")),

    SkillEntry("perl-testing", CAT_TESTING,
        "Perl testing — Test2::V0, Test::More, prove, mocking, Devel::Cover",
        ("perl test", "prove", "test::more")),

    SkillEntry("browser-qa", CAT_TESTING,
        "Automated visual testing and UI interaction verification after deploying features",
        ("visual test", "browser qa", "ui verification", "screenshot test")),

    SkillEntry("webapp-testing", CAT_TESTING,
        "Interact with and test local web applications using Playwright",
        ("webapp test", "local test", "test webapp", "browser test local")),

    SkillEntry("pypict-combinatorial", CAT_TESTING,
        "Design comprehensive test cases using PICT pairwise combinatorial testing",
        ("pict", "pairwise", "combinatorial testing", "test case generation")),

    SkillEntry("benchmark", CAT_TESTING,
        "Measure performance baselines, detect regressions before/after PRs",
        ("benchmark", "performance test", "regression test", "perf baseline")),

    SkillEntry("canary-watch", CAT_TESTING,
        "Monitor a deployed URL for regressions after deploys, merges, or dependency upgrades",
        ("canary", "smoke test", "deploy monitor", "regression watch")),

    SkillEntry("test-fixing", CAT_TESTING,
        "Run tests and systematically fix all failing tests using smart error grouping",
        ("fix tests", "failing tests", "test failures", "make tests pass")),


    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  DATA & ANALYTICS — data engineering, ML, analytics, visualization  ║
    # ╚═══════════════════════════════════════════════════════════════════════╝

    SkillEntry("senior-data-engineer", CAT_DATA,
        "Data pipelines, ETL/ELT, Spark, Airflow, dbt, Kafka, modern data stack",
        ("data pipeline", "etl", "elt", "spark", "airflow", "dbt", "kafka", "data engineering")),

    SkillEntry("senior-data-scientist", CAT_DATA,
        "Statistical modeling, A/B testing, causal inference, predictive analytics",
        ("data science", "a/b test", "statistical", "causal inference", "predictive")),

    SkillEntry("pytorch-patterns", CAT_DATA,
        "PyTorch deep learning — training pipelines, model architectures, data loading",
        ("pytorch", "deep learning", "neural network", "training loop")),

    SkillEntry("csv-data-summarizer", CAT_DATA,
        "Analyze CSV files, generate summary stats, plot visualizations with pandas",
        ("csv", "pandas", "data summary", "data analysis")),

    SkillEntry("data-quality-auditor", CAT_DATA,
        "Audit datasets for completeness, consistency, accuracy, detect anomalies",
        ("data quality", "data audit", "anomaly detection", "data completeness")),

    SkillEntry("statistical-analyst", CAT_DATA,
        "Hypothesis tests, A/B experiment results, sample sizes, statistical significance",
        ("hypothesis test", "statistical significance", "sample size", "p-value", "effect size")),

    SkillEntry("product-analytics", CAT_DATA,
        "Product KPIs, metric dashboards, cohort analysis, retention, feature adoption",
        ("product analytics", "cohort", "retention", "feature adoption", "kpi")),

    SkillEntry("campaign-analytics", CAT_DATA,
        "Campaign performance, multi-touch attribution, funnel analysis, ROI calculation",
        ("campaign analytics", "attribution", "funnel", "roas", "marketing roi")),

    SkillEntry("snowflake-development", CAT_DATA,
        "Snowflake SQL, Dynamic Tables, Streams/Tasks, Cortex AI, Snowpark Python, dbt",
        ("snowflake", "snowpark", "cortex ai", "snowflake sql")),

    SkillEntry("ga4-bigquery-schema", CAT_DATA,
        "GA4 BigQuery Export Schema — field reference, nested structures, query patterns",
        ("ga4 bigquery", "ga4 schema", "bigquery export")),

    SkillEntry("ga4-events", CAT_DATA,
        "GA4 event implementation — event taxonomy, parameter lists, gtag.js, GTM, Measurement Protocol",
        ("ga4 event", "google analytics", "gtag", "measurement protocol")),


    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  AI & ML — LLM APIs, prompt engineering, RAG, agent systems         ║
    # ╚═══════════════════════════════════════════════════════════════════════╝

    SkillEntry("claude-api", CAT_AI_ML,
        "Anthropic Claude API — Messages API, streaming, tool use, vision, extended thinking, batches",
        ("claude api", "anthropic", "anthropic sdk", "claude sdk", "messages api")),

    SkillEntry("senior-prompt-engineer", CAT_AI_ML,
        "Optimize prompts, design prompt templates, evaluate LLM outputs, agent architectures",
        ("prompt engineer", "prompt optimization", "prompt template", "few-shot", "chain of thought")),

    SkillEntry("rag-architect", CAT_AI_ML,
        "Design RAG pipelines, optimize retrieval, choose embedding models, vector search",
        ("rag", "retrieval augmented", "embedding", "vector search", "knowledge retrieval")),

    SkillEntry("senior-ml-engineer", CAT_AI_ML,
        "Productionize models, build MLOps pipelines, integrate LLMs — MLflow, Kubeflow",
        ("mlops", "model deployment", "ml pipeline", "model serving", "mlflow")),

    SkillEntry("senior-computer-vision", CAT_AI_ML,
        "Object detection, image segmentation, YOLO, SAM, Vision Transformers, ONNX/TensorRT",
        ("computer vision", "object detection", "yolo", "segmentation", "sam", "vision transformer")),

    SkillEntry("llm-cost-optimizer", CAT_AI_ML,
        "Reduce LLM API spend, control token usage, model routing, prompt caching",
        ("llm cost", "token usage", "model routing", "prompt caching", "api cost")),

    SkillEntry("prompt-governance", CAT_AI_ML,
        "Manage prompts in production — versioning, A/B testing, registries, eval pipelines",
        ("prompt versioning", "prompt registry", "prompt a/b test", "prompt regression")),

    SkillEntry("agent-designer", CAT_AI_ML,
        "Design multi-agent systems, agent communication patterns, autonomous workflows",
        ("multi-agent", "agent architecture", "agent communication", "autonomous agent")),

    SkillEntry("agent-workflow-designer", CAT_AI_ML,
        "Design agent workflows with tool calling, state machines, and evaluation",
        ("agent workflow", "tool calling", "state machine", "agent eval")),

    SkillEntry("cost-aware-llm-pipeline", CAT_AI_ML,
        "Cost optimization for LLM APIs — model routing, budget tracking, retry logic",
        ("llm pipeline", "cost aware", "budget tracking", "model cost")),

    SkillEntry("eval-harness", CAT_AI_ML,
        "Formal evaluation framework implementing eval-driven development principles",
        ("eval", "evaluation", "eval harness", "eval driven")),

    SkillEntry("fal-ai-media", CAT_AI_ML,
        "Media generation via fal.ai — image, video, audio (Seedance, Kling, Veo 3)",
        ("fal.ai", "image generation", "video generation", "text to image", "text to video")),

    SkillEntry("imagen", CAT_AI_ML,
        "Generate images using Google Gemini's image generation capabilities",
        ("imagen", "gemini image", "generate image", "ai image")),

    SkillEntry("nano-banana-image", CAT_AI_ML,
        "Generate images using Nano Banana Pro (Gemini 3 Pro Preview)",
        ("nano banana", "gemini 3", "ai art generation")),


    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  DESIGN & UI — UI/UX, design systems, accessibility, styling       ║
    # ╚═══════════════════════════════════════════════════════════════════════╝

    SkillEntry("ui-design-system", CAT_DESIGN_UI,
        "Design system toolkit — design tokens, component docs, responsive design, dev handoff",
        ("design system", "design tokens", "component docs", "dev handoff")),

    SkillEntry("ux-researcher-designer", CAT_DESIGN_UI,
        "UX research — personas, journey mapping, usability testing, research synthesis",
        ("ux research", "persona", "journey map", "usability test", "user interview")),

    SkillEntry("apple-hig-expert", CAT_DESIGN_UI,
        "Apple Human Interface Guidelines — iOS, macOS, visionOS, Liquid Glass",
        ("apple hig", "ios design", "macos design", "visionos", "human interface")),

    SkillEntry("brand-guidelines", CAT_DESIGN_UI,
        "Apply brand colors, typography, visual identity, and style guidelines",
        ("brand guideline", "brand color", "typography", "visual identity", "style guide")),

    SkillEntry("theme-factory", CAT_DESIGN_UI,
        "Style artifacts with themes — 10 pre-set themes with colors and fonts",
        ("theme", "theming", "color theme", "dark mode", "light mode")),

    SkillEntry("image-enhancer", CAT_DESIGN_UI,
        "Improve image quality — enhance resolution, sharpness, clarity for screenshots",
        ("enhance image", "image quality", "sharpen", "upscale", "screenshot enhance")),

    SkillEntry("banner-design", CAT_DESIGN_UI,
        "Design banners for social media, ads, website heroes with AI-generated visuals",
        ("banner", "hero image", "social banner", "ad banner")),

    SkillEntry("icon-design", CAT_DESIGN_UI,
        "Design icons in 15+ styles as SVG using AI generation",
        ("icon", "svg icon", "icon design", "app icon")),

    SkillEntry("slack-gif-creator", CAT_DESIGN_UI,
        "Create animated GIFs optimized for Slack with constraints and validation",
        ("gif", "slack gif", "animated gif")),


    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  MOBILE — SwiftUI, Flutter, React Native, Android, iOS              ║
    # ╚═══════════════════════════════════════════════════════════════════════╝

    SkillEntry("swiftui-patterns", CAT_MOBILE,
        "SwiftUI architecture, @Observable state management, navigation, performance, iOS/macOS",
        ("swiftui", "swift", "ios", "macos", "@Observable", "swift ui")),

    SkillEntry("swift-concurrency", CAT_MOBILE,
        "Swift 6.2 Approachable Concurrency — single-threaded default, @concurrent, isolated conformances",
        ("swift concurrency", "swift async", "swift 6", "@concurrent")),

    SkillEntry("swift-actor-persistence", CAT_MOBILE,
        "Thread-safe data persistence in Swift using actors — in-memory cache with file-backed storage",
        ("swift actor", "swift persistence", "swift thread safety")),

    SkillEntry("swift-protocol-di-testing", CAT_MOBILE,
        "Protocol-based dependency injection for testable Swift — mock file system, network, APIs",
        ("swift protocol", "swift di", "swift testing", "swift mock")),

    SkillEntry("foundation-models-on-device", CAT_MOBILE,
        "Apple FoundationModels framework for on-device LLM — guided generation, tool calling, iOS 26+",
        ("foundation models", "on-device llm", "apple ai", "ios 26")),

    SkillEntry("liquid-glass-design", CAT_MOBILE,
        "iOS 26 Liquid Glass design system — dynamic glass material with blur, reflection, morphing",
        ("liquid glass", "ios 26 design", "glass material")),

    SkillEntry("dart-flutter-patterns", CAT_MOBILE,
        "Dart and Flutter — null safety, state management (BLoC, Riverpod), GoRouter, Dio, Freezed",
        ("flutter", "dart", "bloc", "riverpod", "flutter state")),

    SkillEntry("flutter-dart-code-review", CAT_MOBILE,
        "Flutter/Dart code review — widgets, state management, performance, accessibility, security",
        ("flutter review", "dart review", "flutter code quality")),

    SkillEntry("compose-multiplatform-patterns", CAT_MOBILE,
        "Compose Multiplatform and Jetpack Compose — state, navigation, theming, platform-specific UI",
        ("compose", "jetpack compose", "compose multiplatform", "kmp")),

    SkillEntry("android-clean-architecture", CAT_MOBILE,
        "Clean Architecture for Android/KMP — module structure, dependency rules, UseCases, Repositories",
        ("android", "android architecture", "kmp", "kotlin multiplatform")),

    SkillEntry("kotlin-coroutines-flows", CAT_MOBILE,
        "Kotlin Coroutines and Flow — structured concurrency, StateFlow, error handling, testing",
        ("coroutines", "flow", "stateflow", "kotlin flow")),


    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  MARKETING & GROWTH — SEO, content, ads, email, social, CRO        ║
    # ╚═══════════════════════════════════════════════════════════════════════╝

    SkillEntry("seo-audit", CAT_MARKETING,
        "Audit technical SEO, on-page SEO, meta tags, core web vitals, indexing issues",
        ("seo", "seo audit", "technical seo", "meta tags", "ranking", "not ranking")),

    SkillEntry("ai-seo", CAT_MARKETING,
        "Optimize content for AI search engines — ChatGPT, Perplexity, Google AI Overviews",
        ("ai seo", "aeo", "geo", "ai overviews", "perplexity", "ai citations")),

    SkillEntry("content-strategy", CAT_MARKETING,
        "Plan content strategy, decide what to create, topic clusters, editorial calendar",
        ("content strategy", "blog strategy", "topic cluster", "content planning", "editorial calendar")),

    SkillEntry("content-production", CAT_MARKETING,
        "Full content production pipeline — take a topic from blank page to published-ready",
        ("write blog", "article", "blog post", "content production", "write content")),

    SkillEntry("content-humanizer", CAT_MARKETING,
        "Make AI-generated content sound genuinely human — not just cleaned up, but alive",
        ("humanize", "sounds like ai", "make it human", "ai writing", "generic content")),

    SkillEntry("copywriting", CAT_MARKETING,
        "Write marketing copy for homepage, landing pages, pricing pages, feature pages",
        ("copywriting", "marketing copy", "headline", "cta", "value proposition", "tagline")),

    SkillEntry("copy-editing", CAT_MARKETING,
        "Edit, review, improve existing marketing copy — systematic multi-pass editing",
        ("copy editing", "edit copy", "proofread", "polish", "tighten")),

    SkillEntry("cold-email", CAT_MARKETING,
        "Write B2B cold emails and follow-up sequences that get replies",
        ("cold email", "cold outreach", "prospecting", "sdr email", "sales email")),

    SkillEntry("email-sequence", CAT_MARKETING,
        "Create email sequences, drip campaigns, automated flows, lifecycle email programs",
        ("email sequence", "drip campaign", "nurture", "welcome sequence", "email automation")),

    SkillEntry("social-content", CAT_MARKETING,
        "Create social media content for LinkedIn, Twitter/X, Instagram, TikTok",
        ("social media", "linkedin post", "twitter thread", "content calendar", "social post")),

    SkillEntry("paid-ads", CAT_MARKETING,
        "Paid advertising campaigns — Google Ads, Meta, LinkedIn, targeting, ROAS",
        ("paid ads", "ppc", "google ads", "facebook ads", "meta ads", "roas", "cpa")),

    SkillEntry("ad-creative", CAT_MARKETING,
        "Generate ad copy variations — headlines, descriptions, RSA, bulk creative",
        ("ad copy", "ad creative", "headlines", "rsa", "ad variations")),

    SkillEntry("page-cro", CAT_MARKETING,
        "Conversion rate optimization for marketing pages — homepage, landing, pricing",
        ("cro", "conversion rate", "page optimization", "not converting", "bounce rate")),

    SkillEntry("signup-flow-cro", CAT_MARKETING,
        "Optimize signup, registration, account creation, trial activation flows",
        ("signup", "registration", "signup flow", "trial signup", "account creation")),

    SkillEntry("onboarding-cro", CAT_MARKETING,
        "Optimize post-signup onboarding, user activation, first-run experience",
        ("onboarding", "activation rate", "first-run", "aha moment", "time to value")),

    SkillEntry("ab-test-setup", CAT_MARKETING,
        "Plan, design, implement A/B tests and experiments, statistical significance",
        ("a/b test", "split test", "experiment", "variant", "hypothesis")),

    SkillEntry("analytics-tracking", CAT_MARKETING,
        "Set up GA4, GTM, conversion tracking, event tracking, UTM parameters",
        ("analytics", "ga4", "gtm", "google tag manager", "tracking", "utm")),

    SkillEntry("pricing-strategy", CAT_MARKETING,
        "Design SaaS pricing — tiers, value metrics, pricing pages, price increase strategy",
        ("pricing", "pricing tiers", "freemium", "pricing page", "monetization")),

    SkillEntry("launch-strategy", CAT_MARKETING,
        "Plan product launches, feature announcements, Product Hunt, GTM",
        ("launch", "product hunt", "go-to-market", "gtm", "beta launch", "waitlist")),

    SkillEntry("referral-program", CAT_MARKETING,
        "Design referral and affiliate programs — mechanics, incentives, optimization",
        ("referral", "affiliate", "word of mouth", "ambassador", "refer a friend")),

    SkillEntry("churn-prevention", CAT_MARKETING,
        "Reduce churn — cancel flows, save offers, dunning, win-back, exit surveys",
        ("churn", "cancel flow", "dunning", "retention", "save offer", "win-back")),

    SkillEntry("programmatic-seo", CAT_MARKETING,
        "Create SEO-driven pages at scale using templates and data",
        ("programmatic seo", "template pages", "pages at scale", "directory pages")),

    SkillEntry("schema-markup", CAT_MARKETING,
        "Implement structured data (JSON-LD) for rich snippets in Google Search",
        ("schema markup", "json-ld", "structured data", "rich snippets", "schema.org")),

    SkillEntry("site-architecture", CAT_MARKETING,
        "Plan website structure, URL hierarchy, navigation, internal linking",
        ("site architecture", "url structure", "internal linking", "navigation design")),

    SkillEntry("customer-research", CAT_MARKETING,
        "Conduct, analyze, synthesize customer research — interviews, surveys, reviews",
        ("customer research", "icp", "personas", "jtbd", "voice of customer")),

    SkillEntry("competitor-alternatives", CAT_MARKETING,
        "Create competitor comparison pages and vs pages for SEO and sales enablement",
        ("competitor", "vs page", "alternative page", "comparison page")),

    SkillEntry("marketing-psychology", CAT_MARKETING,
        "Apply psychological principles and mental models to marketing",
        ("psychology", "cognitive bias", "persuasion", "nudge", "social proof")),

    SkillEntry("community-marketing", CAT_MARKETING,
        "Build online communities — Discord, Slack, forums — for product growth",
        ("community", "discord", "slack community", "community-led growth")),

    SkillEntry("video-content-strategist", CAT_MARKETING,
        "Plan video content, write scripts, optimize YouTube, short-form video",
        ("youtube", "video strategy", "video script", "short form video", "reels", "tiktok")),

    SkillEntry("x-twitter-growth", CAT_MARKETING,
        "X/Twitter growth — algorithm mechanics, thread engineering, profile optimization",
        ("twitter", "x growth", "tweet", "thread", "twitter algorithm")),

    SkillEntry("form-cro", CAT_MARKETING,
        "Optimize lead capture, contact, demo request, and application forms",
        ("form optimization", "lead form", "contact form", "form friction")),

    SkillEntry("popup-cro", CAT_MARKETING,
        "Create/optimize popups, modals, exit intent overlays for conversions",
        ("popup", "modal", "exit intent", "overlay", "slide-in")),

    SkillEntry("paywall-upgrade-cro", CAT_MARKETING,
        "In-app paywalls, upgrade screens, upsell modals, feature gates",
        ("paywall", "upgrade screen", "upsell", "feature gate", "freemium conversion")),

    SkillEntry("free-tool-strategy", CAT_MARKETING,
        "Build free tools for marketing — calculators, generators, graders for lead gen",
        ("free tool", "calculator", "generator", "engineering as marketing", "lead gen tool")),

    SkillEntry("lead-magnets", CAT_MARKETING,
        "Create lead magnets — ebooks, checklists, templates for email capture",
        ("lead magnet", "ebook", "checklist", "template download", "gated content")),

    SkillEntry("sales-enablement", CAT_MARKETING,
        "Create sales collateral — pitch decks, one-pagers, objection handling, demo scripts",
        ("sales deck", "pitch deck", "one-pager", "objection handling", "demo script")),

    SkillEntry("revops", CAT_MARKETING,
        "Revenue operations, lead lifecycle, marketing-to-sales handoff, CRM automation",
        ("revops", "lead scoring", "lead routing", "mql", "sql", "pipeline")),

    SkillEntry("aso-audit", CAT_MARKETING,
        "App Store and Google Play listing optimization",
        ("aso", "app store optimization", "app listing", "app ranking")),


    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  BUSINESS & C-SUITE — CEO, CFO, CTO, CMO advisors, strategy        ║
    # ╚═══════════════════════════════════════════════════════════════════════╝

    SkillEntry("ceo-advisor", CAT_BUSINESS,
        "Executive leadership — strategic decisions, organizational development, stakeholder mgmt",
        ("ceo", "strategic planning", "board meeting", "investor", "organizational leadership")),

    SkillEntry("cfo-advisor", CAT_BUSINESS,
        "Financial leadership — modeling, unit economics, fundraising, cash management",
        ("cfo", "financial model", "burn rate", "runway", "fundraising", "unit economics", "ltv", "cac")),

    SkillEntry("cto-advisor", CAT_BUSINESS,
        "Technical leadership — engineering teams, architecture decisions, tech strategy, DORA metrics",
        ("cto", "tech debt", "team scaling", "architecture decision", "dora metrics")),

    SkillEntry("cmo-advisor", CAT_BUSINESS,
        "Marketing leadership — brand positioning, growth model design, marketing budget allocation",
        ("cmo", "brand strategy", "growth model", "channel mix", "marketing roi")),

    SkillEntry("coo-advisor", CAT_BUSINESS,
        "Operations leadership — process design, OKR execution, operational cadence, scaling",
        ("coo", "operations", "okr", "process improvement", "scaling", "operational efficiency")),

    SkillEntry("cpo-advisor", CAT_BUSINESS,
        "Product leadership — product vision, portfolio strategy, product-market fit",
        ("cpo", "product strategy", "product-market fit", "portfolio prioritization")),

    SkillEntry("cro-advisor", CAT_BUSINESS,
        "Revenue leadership — forecasting, sales model design, pricing, NRR, sales team scaling",
        ("cro", "revenue strategy", "arr growth", "nrr", "expansion revenue", "sales capacity")),

    SkillEntry("chro-advisor", CAT_BUSINESS,
        "People leadership — hiring strategy, compensation design, org structure, retention",
        ("chro", "hr", "hiring", "compensation", "org design", "retention")),

    SkillEntry("ciso-advisor", CAT_BUSINESS,
        "Security leadership — risk quantification, compliance roadmap, incident response",
        ("ciso", "security strategy", "compliance roadmap", "zero trust")),

    SkillEntry("founder-coach", CAT_BUSINESS,
        "Personal leadership for founders — delegation, energy management, imposter syndrome",
        ("founder", "delegation", "burnout", "imposter syndrome", "leadership development")),

    SkillEntry("executive-mentor", CAT_BUSINESS,
        "Adversarial thinking partner — stress-tests plans, finds holes, forces honest post-mortems",
        ("executive mentor", "stress test", "devil's advocate", "post-mortem")),

    SkillEntry("board-meeting", CAT_BUSINESS,
        "Multi-agent board meeting protocol for strategic decisions with 6-phase deliberation",
        ("board meeting", "board deliberation", "strategic decision")),

    SkillEntry("board-deck-builder", CAT_BUSINESS,
        "Assemble board and investor update decks with multi-role perspectives",
        ("board deck", "investor update", "quarterly review")),

    SkillEntry("competitive-intel", CAT_BUSINESS,
        "Systematic competitor tracking — positioning, battlecards, market positioning",
        ("competitive intelligence", "competitor analysis", "battlecard", "win/loss")),

    SkillEntry("company-os", CAT_BUSINESS,
        "Operating system selection — EOS, Scaling Up, OKR-native, accountability charts",
        ("company os", "eos", "scaling up", "l10 meeting", "rocks", "scorecard")),

    SkillEntry("culture-architect", CAT_BUSINESS,
        "Build, measure, evolve company culture — values, behaviors, rituals",
        ("culture", "values", "culture code", "culture health")),

    SkillEntry("change-management", CAT_BUSINESS,
        "Roll out organizational changes — ADKAR model, communication, resistance patterns",
        ("change management", "reorg", "pivot", "org change")),

    SkillEntry("internal-narrative", CAT_BUSINESS,
        "Build coherent company story across all audiences — employees, investors, customers",
        ("internal narrative", "company story", "all-hands", "crisis communication")),

    SkillEntry("strategic-alignment", CAT_BUSINESS,
        "Cascade strategy from boardroom to individual contributor, detect misalignment",
        ("alignment", "strategy cascade", "silo", "conflicting okrs")),

    SkillEntry("scenario-war-room", CAT_BUSINESS,
        "Cross-functional what-if modeling for cascading multi-variable scenarios",
        ("scenario planning", "war room", "what if", "stress scenario")),

    SkillEntry("org-health-diagnostic", CAT_BUSINESS,
        "Cross-functional organizational health check — 8 dimensions with traffic-light scoring",
        ("org health", "health check", "health dashboard")),

    SkillEntry("intl-expansion", CAT_BUSINESS,
        "International market expansion — market selection, entry modes, localization, regulatory",
        ("international", "expansion", "localization", "new market")),

    SkillEntry("ma-playbook", CAT_BUSINESS,
        "M&A strategy — due diligence, valuation, integration, deal structure",
        ("m&a", "acquisition", "merger", "due diligence", "deal structure")),

    SkillEntry("investor-materials", CAT_BUSINESS,
        "Create pitch decks, investor memos, financial models, fundraising materials",
        ("pitch deck", "investor memo", "fundraising", "financial model")),

    SkillEntry("investor-outreach", CAT_BUSINESS,
        "Draft cold emails, warm intros, follow-ups for fundraising",
        ("investor outreach", "angel", "vc", "fundraising email")),

    SkillEntry("saas-metrics-coach", CAT_BUSINESS,
        "SaaS financial health — ARR, MRR, churn, LTV, CAC, NRR analysis",
        ("saas metrics", "arr", "mrr", "churn rate", "ltv cac")),

    SkillEntry("financial-analyst", CAT_BUSINESS,
        "Financial ratio analysis, DCF valuation, budget variance analysis, rolling forecasts",
        ("financial analysis", "dcf", "valuation", "budget variance", "forecast")),

    SkillEntry("business-investment-advisor", CAT_BUSINESS,
        "Business investment analysis — ROI, IRR, NPV, payback period, build vs buy",
        ("investment", "roi", "irr", "npv", "payback period", "build vs buy")),

    SkillEntry("revenue-operations", CAT_BUSINESS,
        "Sales pipeline health, revenue forecasting, go-to-market efficiency metrics",
        ("revenue operations", "pipeline coverage", "forecast accuracy", "gtm efficiency")),

    SkillEntry("customer-success-manager", CAT_BUSINESS,
        "Customer health monitoring, churn prediction, expansion opportunities",
        ("customer success", "health score", "churn prediction", "expansion revenue")),

    SkillEntry("sales-engineer", CAT_BUSINESS,
        "RFP/RFI responses, competitive feature matrices, proof-of-concept planning",
        ("sales engineer", "rfp", "rfi", "poc", "demo", "pre-sales")),

    SkillEntry("contract-proposal-writer", CAT_BUSINESS,
        "Write proposals, contracts, SOWs, and business agreements",
        ("contract", "proposal", "sow", "agreement", "rfp response")),


    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  GAME DEVELOPMENT — design, level design, narrative, QA, engines    ║
    # ╚═══════════════════════════════════════════════════════════════════════╝

    SkillEntry("game-brainstorm", CAT_GAME_DEV,
        "Guided game concept ideation — from zero to structured game concept document",
        ("game concept", "game idea", "game brainstorm", "game jam")),

    SkillEntry("game-design-system", CAT_GAME_DEV,
        "Guided section-by-section GDD authoring for a single game system",
        ("gdd", "game design document", "game system", "game mechanics")),

    SkillEntry("game-map-systems", CAT_GAME_DEV,
        "Decompose a game concept into individual systems, map dependencies, prioritize",
        ("game systems", "systems index", "system dependencies")),

    SkillEntry("game-architecture", CAT_GAME_DEV,
        "Master architecture document for the game — reads all GDDs, existing ADRs, engine reference",
        ("game architecture", "engine architecture", "technical design")),

    SkillEntry("game-balance-check", CAT_GAME_DEV,
        "Analyze game balance data — outliers, broken progressions, degenerate strategies",
        ("game balance", "balance check", "progression", "economy balance")),

    SkillEntry("game-level-design", CAT_GAME_DEV,
        "Spatial designs, encounter layouts, pacing plans, environmental storytelling",
        ("level design", "encounter", "pacing", "spatial puzzle")),

    SkillEntry("game-narrative", CAT_GAME_DEV,
        "Story architecture, world-building, character design, dialogue strategy",
        ("narrative", "story arc", "world building", "character design", "dialogue")),

    SkillEntry("game-sprint-plan", CAT_GAME_DEV,
        "Generate sprint plans based on milestone, completed work, and available capacity",
        ("sprint plan", "game sprint", "milestone", "backlog")),

    SkillEntry("game-qa-plan", CAT_GAME_DEV,
        "Generate QA test plans for a sprint or feature — automated, manual, smoke test",
        ("game qa", "test plan", "smoke test", "playtest")),

    SkillEntry("game-bug-report", CAT_GAME_DEV,
        "Create structured bug reports with full reproduction steps and severity assessment",
        ("bug report", "game bug", "reproduction steps", "severity")),

    SkillEntry("game-perf-profile", CAT_GAME_DEV,
        "Structured performance profiling — bottlenecks, budgets, optimization recommendations",
        ("game performance", "fps", "frame time", "profiling", "optimization")),

    SkillEntry("game-launch-checklist", CAT_GAME_DEV,
        "Complete launch readiness — code, content, store, marketing, infrastructure, legal",
        ("launch checklist", "release checklist", "certification", "store submission")),

    SkillEntry("game-prototype", CAT_GAME_DEV,
        "Rapid prototyping to validate game concepts — throwaway code with structured reports",
        ("prototype", "vertical slice", "mechanics test", "concept validation")),

    SkillEntry("game-localize", CAT_GAME_DEV,
        "Full localization pipeline — string extraction, translation, cultural review, RTL",
        ("localization", "i18n", "translate game", "string table")),

    SkillEntry("godot-specialist", CAT_GAME_DEV,
        "Godot engine patterns, GDScript, C#, GDExtension, node/scene architecture",
        ("godot", "gdscript", "godot 4", "godot engine")),

    SkillEntry("unity-specialist", CAT_GAME_DEV,
        "Unity engine patterns, MonoBehaviour, DOTS/ECS, Addressables, UI Toolkit",
        ("unity", "unity engine", "monobehaviour", "dots", "ecs")),

    SkillEntry("unreal-specialist", CAT_GAME_DEV,
        "Unreal Engine patterns — Blueprint vs C++, GAS, Niagara, Enhanced Input",
        ("unreal", "unreal engine", "ue5", "blueprint", "niagara")),


    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  WRITING & CONTENT — copywriting, editing, articles, documentation  ║
    # ╚═══════════════════════════════════════════════════════════════════════╝

    SkillEntry("article-writing", CAT_WRITING,
        "Write articles, guides, blog posts, tutorials in a distinctive derived voice",
        ("article", "guide", "blog post", "tutorial", "newsletter")),

    SkillEntry("content-research-writer", CAT_WRITING,
        "Research-backed writing — citations, hooks, iterating outlines, real-time feedback",
        ("research writing", "citations", "content research", "write with sources")),

    SkillEntry("brand-voice", CAT_WRITING,
        "Build source-derived writing style profile from real posts, essays, launch notes",
        ("brand voice", "writing style", "voice consistency", "tone of voice")),

    SkillEntry("avoid-ai-writing", CAT_WRITING,
        "Audit and rewrite content to remove AI writing patterns (AI-isms)",
        ("ai-isms", "remove ai writing", "sounds like ai", "ai tells")),

    SkillEntry("doc-coauthoring", CAT_WRITING,
        "Co-author documentation — structured workflow for proposals, specs, decision docs",
        ("co-author", "documentation", "proposal", "technical spec")),

    SkillEntry("internal-comms", CAT_WRITING,
        "Write internal communications — status reports, newsletters, FAQs, incident reports",
        ("internal comms", "status report", "newsletter", "faq", "3p update")),

    SkillEntry("academic-paper", CAT_WRITING,
        "12-agent academic paper writing pipeline — full/plan/outline/revision/abstract/lit-review",
        ("academic paper", "research paper", "thesis", "academic writing")),

    SkillEntry("academic-paper-reviewer", CAT_WRITING,
        "Multi-perspective academic paper review with 5 independent reviewer personas",
        ("paper review", "peer review", "manuscript review", "referee report")),

    SkillEntry("meeting-insights-analyzer", CAT_WRITING,
        "Analyze meeting transcripts for behavioral patterns, communication insights",
        ("meeting transcript", "meeting analysis", "communication insights")),


    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  PRODUCTIVITY — project management, Jira, Linear, meetings, plans   ║
    # ╚═══════════════════════════════════════════════════════════════════════╝

    SkillEntry("product-manager-toolkit", CAT_PRODUCTIVITY,
        "RICE prioritization, customer interview analysis, PRD templates, discovery frameworks",
        ("product manager", "rice", "prd", "prioritization", "discovery")),

    SkillEntry("product-strategist", CAT_PRODUCTIVITY,
        "OKR cascade, quarterly planning, competitive landscape, product vision",
        ("product strategy", "okr", "quarterly planning", "product vision")),

    SkillEntry("product-discovery", CAT_PRODUCTIVITY,
        "Validate product opportunities, map assumptions, plan discovery sprints",
        ("product discovery", "assumption mapping", "discovery sprint")),

    SkillEntry("roadmap-communicator", CAT_PRODUCTIVITY,
        "Prepare roadmap narratives, release notes, changelogs, stakeholder updates",
        ("roadmap", "release notes", "stakeholder update")),

    SkillEntry("experiment-designer", CAT_PRODUCTIVITY,
        "Plan product experiments, write hypotheses, estimate sample size, prioritize tests",
        ("experiment", "hypothesis", "sample size", "experiment design")),

    SkillEntry("agile-product-owner", CAT_PRODUCTIVITY,
        "Agile product ownership — user stories, acceptance criteria, sprint planning, velocity",
        ("agile", "scrum", "user story", "acceptance criteria", "sprint planning", "velocity")),

    SkillEntry("scrum-sage", CAT_PRODUCTIVITY,
        "Scrum Master and Enterprise Agility Coach — sprint analysis, impediment removal",
        ("scrum master", "retrospective", "standup", "impediment", "agile coaching")),

    SkillEntry("senior-pm", CAT_PRODUCTIVITY,
        "Senior PM for enterprise — portfolio management, risk analysis, resource optimization",
        ("project manager", "portfolio", "risk analysis", "resource allocation")),

    SkillEntry("jira-expert", CAT_PRODUCTIVITY,
        "Jira project setup, JQL queries, workflows, custom fields, automation, reporting",
        ("jira", "jql", "jira workflow", "jira automation")),

    SkillEntry("confluence-expert", CAT_PRODUCTIVITY,
        "Confluence spaces, knowledge bases, documentation, page templates with macros",
        ("confluence", "knowledge base", "wiki", "confluence template")),

    SkillEntry("linear-skill", CAT_PRODUCTIVITY,
        "Manage Linear issues, projects, teams — create issues, update status, query projects",
        ("linear", "linear issue", "linear project")),

    SkillEntry("github-ops", CAT_PRODUCTIVITY,
        "GitHub operations — issue triage, PR management, CI/CD status, release management",
        ("github", "github issue", "github pr", "github actions")),

    SkillEntry("prd-to-issues", CAT_PRODUCTIVITY,
        "Break a PRD into independently-grabbable GitHub issues using vertical slices",
        ("prd to issues", "break down prd", "implementation tickets")),

    SkillEntry("prd-to-plan", CAT_PRODUCTIVITY,
        "Turn a PRD into a multi-phase implementation plan using tracer-bullet vertical slices",
        ("prd to plan", "implementation plan", "tracer bullet")),

    SkillEntry("write-a-prd", CAT_PRODUCTIVITY,
        "Create a PRD through user interview, codebase exploration, and module design",
        ("write prd", "product requirements", "feature spec")),

    SkillEntry("code-to-prd", CAT_PRODUCTIVITY,
        "Reverse-engineer a codebase into a complete Product Requirements Document",
        ("reverse engineer", "code to prd", "extract requirements")),

    SkillEntry("competitive-teardown", CAT_PRODUCTIVITY,
        "Analyze competitor products — feature comparison, SWOT, positioning maps, UX audits",
        ("competitive teardown", "product comparison", "competitor product")),

    SkillEntry("file-organizer", CAT_PRODUCTIVITY,
        "Intelligently organize files and folders — find duplicates, suggest better structures",
        ("organize files", "file cleanup", "folder structure", "duplicates")),

    SkillEntry("invoice-organizer", CAT_PRODUCTIVITY,
        "Organize invoices and receipts for tax preparation — extract info, rename, sort",
        ("invoice", "receipt", "tax preparation", "bookkeeping")),

    SkillEntry("raffle-winner-picker", CAT_PRODUCTIVITY,
        "Pick random winners from lists or spreadsheets for giveaways and raffles",
        ("raffle", "giveaway", "random winner", "contest")),

    SkillEntry("unblock-action", CAT_PRODUCTIVITY,
        "Help unblock vague or stuck action items — clarify output, scope to today, find next action",
        ("unblock", "stuck", "can't start", "vague task")),

    SkillEntry("session-log", CAT_PRODUCTIVITY,
        "Summarize current session and append to weekly agent-log",
        ("session log", "log this", "summarize session")),


    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  DOCUMENT PROCESSING — PDF, DOCX, PPTX, XLSX, images               ║
    # ╚═══════════════════════════════════════════════════════════════════════╝

    SkillEntry("pdf-processing", CAT_DOCUMENT,
        "Read, merge, split, rotate, watermark, encrypt, OCR, fill forms in PDFs",
        ("pdf", "merge pdf", "split pdf", "ocr", "fill form", "pdf watermark")),

    SkillEntry("docx-processing", CAT_DOCUMENT,
        "Create, read, edit Word documents — tables of contents, headings, formatting",
        ("docx", "word document", "word doc", ".docx")),

    SkillEntry("pptx-processing", CAT_DOCUMENT,
        "Create, read, edit PowerPoint presentations — slides, notes, templates",
        ("pptx", "powerpoint", "slides", "presentation", "deck")),

    SkillEntry("xlsx-processing", CAT_DOCUMENT,
        "Open, read, edit, create spreadsheets — formulas, charts, formatting",
        ("xlsx", "excel", "spreadsheet", "csv", "tabular data")),

    SkillEntry("article-extractor", CAT_DOCUMENT,
        "Extract clean article content from URLs — sans ads, navigation, clutter",
        ("extract article", "clean article", "remove ads", "article content")),

    SkillEntry("youtube-transcript", CAT_DOCUMENT,
        "Download YouTube video transcripts, captions, subtitles",
        ("youtube transcript", "youtube caption", "video transcript")),

    SkillEntry("video-downloader", CAT_DOCUMENT,
        "Download YouTube videos with customizable quality and format options",
        ("download video", "youtube download", "save video")),

    SkillEntry("nutrient-document", CAT_DOCUMENT,
        "Process, convert, OCR, extract, redact, sign documents via Nutrient DWS API",
        ("nutrient", "document processing", "redact", "sign document")),

    SkillEntry("visa-doc-translate", CAT_DOCUMENT,
        "Translate visa application documents to English and create bilingual PDF",
        ("visa document", "document translation", "bilingual pdf")),


    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  SPECIALIZED DOMAINS — healthcare, logistics, finance, academic     ║
    # ╚═══════════════════════════════════════════════════════════════════════╝

    SkillEntry("healthcare-emr-patterns", CAT_SPECIALIZED,
        "EMR/EHR development — clinical safety, encounter workflows, prescription generation",
        ("emr", "ehr", "electronic medical record", "clinical", "healthcare app")),

    SkillEntry("healthcare-cdss-patterns", CAT_SPECIALIZED,
        "Clinical Decision Support — drug interactions, dose validation, clinical scoring",
        ("cdss", "drug interaction", "clinical decision", "news2", "qsofa")),

    SkillEntry("healthcare-phi-compliance", CAT_SPECIALIZED,
        "PHI and PII compliance for healthcare — data classification, access control, audit trails",
        ("phi", "pii", "healthcare compliance", "hipaa data")),

    SkillEntry("iso13485-qms", CAT_SPECIALIZED,
        "ISO 13485 Quality Management System for medical devices",
        ("iso 13485", "qms", "medical device quality", "iso13485")),

    SkillEntry("mdr-745-specialist", CAT_SPECIALIZED,
        "EU MDR 2017/745 compliance — medical device classification, technical documentation",
        ("mdr", "eu mdr", "medical device regulation", "ce marking")),

    SkillEntry("risk-management-iso14971", CAT_SPECIALIZED,
        "ISO 14971 medical device risk management — FMEA, fault tree analysis, risk matrix",
        ("iso 14971", "fmea", "risk management", "hazard identification")),

    SkillEntry("fda-consultant", CAT_SPECIALIZED,
        "FDA regulatory — 510(k), PMA, De Novo, QSR (21 CFR 820), device cybersecurity",
        ("fda", "510k", "pma", "de novo", "qsr")),

    SkillEntry("logistics-exception-mgmt", CAT_SPECIALIZED,
        "Freight exceptions, shipment delays, damages, carrier disputes, claims",
        ("logistics", "freight", "shipment delay", "carrier dispute", "freight claim")),

    SkillEntry("carrier-relationship-mgmt", CAT_SPECIALIZED,
        "Carrier portfolios, freight rate negotiation, performance scorecarding",
        ("carrier", "freight rate", "carrier performance", "rfp freight")),

    SkillEntry("customs-trade-compliance", CAT_SPECIALIZED,
        "Customs documentation, tariff classification, duty optimization, HS codes",
        ("customs", "tariff", "hs code", "incoterms", "trade compliance")),

    SkillEntry("inventory-demand-planning", CAT_SPECIALIZED,
        "Demand forecasting, safety stock, replenishment planning, ABC/XYZ analysis",
        ("demand planning", "safety stock", "inventory", "replenishment", "abc analysis")),

    SkillEntry("production-scheduling", CAT_SPECIALIZED,
        "Production scheduling, job sequencing, line balancing, changeover optimization",
        ("production scheduling", "job sequencing", "line balancing", "oee")),

    SkillEntry("quality-nonconformance", CAT_SPECIALIZED,
        "Quality control, non-conformance investigation, root cause analysis, CAPA",
        ("non-conformance", "ncr", "capa", "root cause analysis", "spc")),

    SkillEntry("returns-reverse-logistics", CAT_SPECIALIZED,
        "Returns authorization, inspection, disposition, refund processing, fraud detection",
        ("returns", "reverse logistics", "refund", "return fraud")),

    SkillEntry("energy-procurement", CAT_SPECIALIZED,
        "Electricity and gas procurement, tariff optimization, renewable PPA evaluation",
        ("energy procurement", "tariff", "ppa", "demand charge")),

    SkillEntry("family-history-research", CAT_SPECIALIZED,
        "Plan family history and genealogy research projects",
        ("genealogy", "family history", "ancestry", "family tree")),

    SkillEntry("deep-research", CAT_SPECIALIZED,
        "Multi-source deep research using web search — synthesize findings with citations",
        ("deep research", "research report", "cited research", "multi-source research")),

    SkillEntry("market-research", CAT_SPECIALIZED,
        "Market research, competitive analysis, investor due diligence, industry intelligence",
        ("market research", "market sizing", "competitive analysis", "industry report")),

    SkillEntry("move-code-quality", CAT_SPECIALIZED,
        "Analyze Move language packages against the Move Book Code Quality Checklist",
        ("move language", "move code", "sui move")),

    SkillEntry("learn-this", CAT_SPECIALIZED,
        "Extract content and create action plans from YouTube videos, articles, PDFs",
        ("learn this", "extract and plan", "make actionable", "weave")),

    SkillEntry("ship-learn-next", CAT_SPECIALIZED,
        "Transform learning content into actionable implementation plans",
        ("ship learn", "action plan", "learning quest")),


    # ╔═══════════════════════════════════════════════════════════════════════╗
    # ║  BLOCKCHAIN & WEB3 — Solidity, DeFi, EVM, token standards           ║
    # ╚═══════════════════════════════════════════════════════════════════════╝

    SkillEntry("evm-token-decimals", CAT_BLOCKCHAIN,
        "Prevent decimal mismatch bugs across EVM chains — runtime lookup, chain-aware caching",
        ("evm", "token decimals", "erc20", "decimal mismatch")),

    SkillEntry("nodejs-keccak256", CAT_BLOCKCHAIN,
        "Prevent Ethereum hashing bugs — Node sha3-256 vs Keccak-256 distinction",
        ("keccak", "sha3", "ethereum hash", "solidity hash")),

    SkillEntry("llm-trading-agent-security", CAT_BLOCKCHAIN,
        "Security for autonomous trading agents — spend limits, pre-send simulation, MEV protection",
        ("trading agent", "trading bot", "mev", "wallet security")),

    SkillEntry("agent-payment-x402", CAT_BLOCKCHAIN,
        "Add x402 payment execution to AI agents — per-task budgets, spending controls",
        ("x402", "agent payment", "non-custodial", "per-task budget")),

    # ═════════════════════════════════════════════════════════════════════════
    # EXPANSION WAVE 2 — Additional skills to reach 500+ coverage
    # ═════════════════════════════════════════════════════════════════════════

    # ── BLOCKCHAIN & WEB3 (+16) ─────────────────────────────────────────────
    SkillEntry("nft-marketplace", CAT_BLOCKCHAIN,
        "Build NFT marketplace contracts — ERC-721/ERC-1155 minting, royalties, marketplace logic",
        ("nft", "erc-721", "erc-1155", "nft marketplace", "minting", "royalties")),
    SkillEntry("dao-governance", CAT_BLOCKCHAIN,
        "DAO governance contracts with voting, proposals, timelock, and treasury management",
        ("dao", "governance", "voting", "timelock", "proposal", "treasury")),
    SkillEntry("cross-chain-bridge", CAT_BLOCKCHAIN,
        "Cross-chain bridge patterns — message passing, token wrapping, relay verification",
        ("cross chain", "bridge", "chain bridge", "message passing", "token wrap")),
    SkillEntry("zk-proof-patterns", CAT_BLOCKCHAIN,
        "Zero-knowledge proof circuits — zk-SNARK, zk-STARK, circom, plonk verification",
        ("zero knowledge", "zk-snark", "zk-stark", "circom", "zk proof")),
    SkillEntry("layer2-scaling", CAT_BLOCKCHAIN,
        "Layer 2 scaling solutions — rollups, optimistic rollups, zk-rollups, state channels",
        ("layer 2", "rollup", "optimistic rollup", "zk rollup", "state channel")),
    SkillEntry("defi-lending", CAT_BLOCKCHAIN,
        "DeFi lending protocol patterns — collateralization, liquidation, interest rate models",
        ("defi lending", "collateral", "liquidation", "interest rate", "lending protocol")),
    SkillEntry("token-economics", CAT_BLOCKCHAIN,
        "Tokenomics design — supply curves, vesting schedules, staking mechanics, incentive alignment",
        ("tokenomics", "token economics", "vesting", "staking", "supply curve")),
    SkillEntry("wallet-integration", CAT_BLOCKCHAIN,
        "Web3 wallet integration — MetaMask, WalletConnect, account abstraction, EIP-4337",
        ("wallet connect", "metamask", "account abstraction", "eip-4337", "web3 wallet")),
    SkillEntry("blockchain-indexing", CAT_BLOCKCHAIN,
        "Blockchain data indexing — The Graph, subgraphs, event indexing, RPC optimization",
        ("the graph", "subgraph", "blockchain indexing", "event indexing", "rpc")),
    SkillEntry("solana-patterns", CAT_BLOCKCHAIN,
        "Solana development — Anchor framework, PDAs, CPIs, token programs, Solana best practices",
        ("solana", "anchor", "pda", "cpi", "solana program", "spl token")),
    SkillEntry("smart-contract-audit", CAT_BLOCKCHAIN,
        "Smart contract security audit — vulnerability patterns, static analysis, formal verification",
        ("smart contract audit", "contract audit", "solidity audit", "formal verification")),
    SkillEntry("ipfs-arweave-storage", CAT_BLOCKCHAIN,
        "Decentralized storage — IPFS pinning, Arweave permanent storage, content addressing",
        ("ipfs", "arweave", "decentralized storage", "content addressing", "pinning")),
    SkillEntry("stablecoin-mechanisms", CAT_BLOCKCHAIN,
        "Stablecoin design — algorithmic, collateralized, hybrid peg mechanisms and risk",
        ("stablecoin", "algorithmic stable", "peg mechanism", "collateralized stable")),
    SkillEntry("web3-auth-patterns", CAT_BLOCKCHAIN,
        "Web3 authentication — Sign-In with Ethereum (SIWE), session tokens, ENS resolution",
        ("siwe", "sign in with ethereum", "web3 auth", "ens resolution")),
    SkillEntry("evm-gas-optimization", CAT_BLOCKCHAIN,
        "EVM gas optimization — storage packing, calldata optimization, assembly tricks",
        ("gas optimization", "gas efficient", "storage packing", "calldata", "assembly")),
    SkillEntry("defi-yield-strategies", CAT_BLOCKCHAIN,
        "DeFi yield strategies — farming, auto-compounding, vault patterns, risk-adjusted returns",
        ("yield farming", "yield strategy", "auto compound", "vault pattern", "defi yield")),

    # ── DESIGN & UI (+16) ──────────────────────────────────────────────────
    SkillEntry("figma-to-code", CAT_DESIGN_UI,
        "Convert Figma designs to production code — tokens, components, responsive layouts",
        ("figma", "figma to code", "design to code", "design handoff", "figma export")),
    SkillEntry("motion-design", CAT_DESIGN_UI,
        "Motion design principles — easing, spring physics, choreography, micro-interactions",
        ("motion design", "animation principles", "easing", "spring animation", "micro interaction")),
    SkillEntry("color-theory", CAT_DESIGN_UI,
        "Color theory for digital products — palettes, contrast ratios, color spaces, dark mode",
        ("color theory", "color palette", "contrast ratio", "color space", "dark mode")),
    SkillEntry("typography-systems", CAT_DESIGN_UI,
        "Typography systems — type scale, fluid typography, font pairing, line height, measure",
        ("typography", "type scale", "font pairing", "line height", "fluid type")),
    SkillEntry("icon-system-design", CAT_DESIGN_UI,
        "Icon design systems — SVG optimization, icon grids, consistency, icon font creation",
        ("icon system", "icon grid", "icon font", "svg optimization")),
    SkillEntry("design-token-systems", CAT_DESIGN_UI,
        "Design token architecture — primitive/semantic/component tokens, Style Dictionary, W3C format",
        ("design tokens", "style dictionary", "semantic tokens", "component tokens")),
    SkillEntry("responsive-layout", CAT_DESIGN_UI,
        "Responsive layout patterns — fluid grids, container queries, breakpoint strategy",
        ("responsive layout", "container query", "fluid grid", "breakpoint", "responsive design")),
    SkillEntry("data-visualization-design", CAT_DESIGN_UI,
        "Data visualization design — chart selection, data-ink ratio, accessibility in charts",
        ("data visualization", "chart design", "data ink", "visualization design")),
    SkillEntry("ux-research-methods", CAT_DESIGN_UI,
        "UX research methods — usability testing, card sorting, heuristic evaluation, A/B tests",
        ("ux research", "usability testing", "card sorting", "heuristic evaluation")),
    SkillEntry("design-ops", CAT_DESIGN_UI,
        "DesignOps — design process optimization, tooling, handoff workflows, design QA",
        ("design ops", "designops", "design process", "design qa", "design handoff")),
    SkillEntry("prototyping-tools", CAT_DESIGN_UI,
        "Rapid prototyping with Framer, Principle, ProtoPie for interactive high-fidelity proofs",
        ("prototyping", "framer", "protopie", "interactive prototype", "hi-fi prototype")),
    SkillEntry("illustration-patterns", CAT_DESIGN_UI,
        "Product illustration style guides — character design, spot illustrations, empty states",
        ("illustration", "character design", "spot illustration", "empty state illustration")),
    SkillEntry("glassmorphism-effects", CAT_DESIGN_UI,
        "Modern visual effects — glassmorphism, neumorphism, claymorphism, gradient meshes",
        ("glassmorphism", "neumorphism", "claymorphism", "gradient mesh", "glass effect")),
    SkillEntry("design-critique", CAT_DESIGN_UI,
        "Structured design critique process — feedback frameworks, visual QA, design review checklists",
        ("design critique", "design review", "design feedback", "visual qa")),
    SkillEntry("whitespace-layout", CAT_DESIGN_UI,
        "Whitespace and layout principles — visual hierarchy, proximity, alignment, Gestalt",
        ("whitespace", "visual hierarchy", "proximity", "alignment", "gestalt")),
    SkillEntry("brand-identity-design", CAT_DESIGN_UI,
        "Brand identity design — logo systems, brand marks, usage guidelines, brand architecture",
        ("brand identity", "logo design", "brand mark", "brand architecture", "logo system")),

    # ── WRITING & CONTENT (+16) ────────────────────────────────────────────
    SkillEntry("technical-writing", CAT_WRITING,
        "Technical writing — API docs, README patterns, developer guides, reference documentation",
        ("technical writing", "api docs", "developer guide", "readme", "developer documentation")),
    SkillEntry("blog-writing", CAT_WRITING,
        "Blog post writing — hooks, structure, SEO, storytelling, audience engagement",
        ("blog post", "blog writing", "write a post", "article writing", "blog content")),
    SkillEntry("microcopy-ux-writing", CAT_WRITING,
        "UX microcopy — error messages, tooltips, empty states, button labels, confirmation dialogs",
        ("microcopy", "ux writing", "error message", "tooltip text", "empty state copy")),
    SkillEntry("email-copywriting", CAT_WRITING,
        "Email copywriting — subject lines, preview text, body structure, CTAs, segmented messaging",
        ("email copy", "subject line", "email writing", "email body", "email cta")),
    SkillEntry("script-writing", CAT_WRITING,
        "Script writing for video/audio — YouTube scripts, podcast outlines, voiceover scripts",
        ("script writing", "video script", "youtube script", "podcast outline", "voiceover")),
    SkillEntry("press-release", CAT_WRITING,
        "Press release writing — news angle, quotes, boilerplate, distribution strategy",
        ("press release", "news release", "media release", "pr writing")),
    SkillEntry("case-study-writing", CAT_WRITING,
        "Customer case study writing — problem/solution/results framework, quotes, metrics",
        ("case study", "customer story", "success story", "testimonial writing")),
    SkillEntry("grant-proposal-writing", CAT_WRITING,
        "Grant proposal writing — problem statement, methodology, budget justification, impact",
        ("grant proposal", "grant writing", "research proposal", "funding proposal")),
    SkillEntry("newsletter-writing", CAT_WRITING,
        "Newsletter writing — curation, format consistency, engagement patterns, growth tactics",
        ("newsletter", "newsletter writing", "email newsletter", "substack", "curated newsletter")),
    SkillEntry("seo-content-writing", CAT_WRITING,
        "SEO-optimized content writing — keyword integration, search intent, E-E-A-T compliance",
        ("seo writing", "seo content", "keyword optimization", "search intent", "eeat")),
    SkillEntry("social-media-writing", CAT_WRITING,
        "Social media writing — platform-specific formats, hooks, hashtags, engagement tactics",
        ("social media writing", "tweet writing", "linkedin post", "social copy", "caption")),
    SkillEntry("whitepaper-writing", CAT_WRITING,
        "Whitepaper writing — B2B thought leadership, technical depth, lead generation content",
        ("whitepaper", "white paper", "thought leadership", "b2b content")),
    SkillEntry("documentation-style", CAT_WRITING,
        "Documentation style guides — voice/tone, formatting conventions, content governance",
        ("documentation style", "style guide", "content governance", "voice and tone")),
    SkillEntry("localization-writing", CAT_WRITING,
        "Content localization — translation management, cultural adaptation, i18n-friendly writing",
        ("localization", "translation", "cultural adaptation", "i18n writing", "multilingual")),
    SkillEntry("landing-page-copy", CAT_WRITING,
        "Landing page copy — hero messaging, value propositions, social proof, CTA optimization",
        ("landing page copy", "hero copy", "value proposition", "landing page")),
    SkillEntry("content-repurposing", CAT_WRITING,
        "Content repurposing — transform one piece across blog, social, email, video, carousel",
        ("content repurpose", "repurposing", "content recycling", "cross platform content")),

    # ── DOCUMENT PROCESSING (+11) ──────────────────────────────────────────
    SkillEntry("pdf-form-filling", CAT_DOCUMENT,
        "PDF form filling automation — AcroForm, XFA forms, batch filling, digital signatures",
        ("pdf form", "form filling", "acroform", "digital signature", "pdf sign")),
    SkillEntry("document-ocr", CAT_DOCUMENT,
        "Document OCR pipelines — Tesseract, cloud OCR APIs, post-processing, accuracy tuning",
        ("ocr", "optical character recognition", "tesseract", "document scanning")),
    SkillEntry("spreadsheet-automation", CAT_DOCUMENT,
        "Spreadsheet automation — formula generation, pivot tables, VBA macros, Google Sheets scripts",
        ("spreadsheet", "pivot table", "vba macro", "google sheets script", "excel formula")),
    SkillEntry("presentation-builder", CAT_DOCUMENT,
        "Automated presentation building — slide generation, templating, data-driven slides",
        ("presentation", "slide deck", "pptx generation", "slide template", "keynote")),
    SkillEntry("markdown-processing", CAT_DOCUMENT,
        "Markdown processing — MDX, Markdoc, markdown-it plugins, AST manipulation, rendering",
        ("markdown", "mdx", "markdoc", "markdown processing", "markdown ast")),
    SkillEntry("document-comparison", CAT_DOCUMENT,
        "Document diff and comparison — version tracking, redlining, change detection",
        ("document diff", "document comparison", "redline", "version comparison")),
    SkillEntry("data-extraction-parsing", CAT_DOCUMENT,
        "Structured data extraction from unstructured documents — tables, entities, key-value pairs",
        ("data extraction", "table extraction", "entity extraction", "document parsing")),
    SkillEntry("ebook-publishing", CAT_DOCUMENT,
        "E-book creation — EPUB generation, formatting, metadata, Kindle conversion, validation",
        ("epub", "ebook", "kindle", "ebook publishing", "epub generation")),
    SkillEntry("invoice-receipt-processing", CAT_DOCUMENT,
        "Invoice/receipt processing — extraction, categorization, tax preparation, bookkeeping",
        ("invoice", "receipt", "invoice processing", "tax preparation", "bookkeeping")),
    SkillEntry("template-engine", CAT_DOCUMENT,
        "Document template engines — mail merge, Jinja2, Handlebars, dynamic document generation",
        ("template engine", "mail merge", "jinja2", "handlebars", "document template")),
    SkillEntry("archive-management", CAT_DOCUMENT,
        "File archive management — zip, tar, compression, batch operations, file organization",
        ("archive", "zip", "tar", "compression", "file organization", "batch rename")),

    # ── DATA & ANALYTICS (+14) ─────────────────────────────────────────────
    SkillEntry("dbt-analytics", CAT_DATA,
        "dbt analytics engineering — models, tests, documentation, macros, incremental strategies",
        ("dbt", "dbt model", "analytics engineering", "dbt test", "dbt macro")),
    SkillEntry("apache-spark-patterns", CAT_DATA,
        "Apache Spark patterns — DataFrames, RDDs, Spark SQL, performance tuning, cluster config",
        ("spark", "pyspark", "spark sql", "spark dataframe", "spark tuning")),
    SkillEntry("etl-pipeline-design", CAT_DATA,
        "ETL/ELT pipeline design — orchestration, idempotency, schema evolution, data quality gates",
        ("etl", "elt", "data pipeline", "pipeline design", "data orchestration")),
    SkillEntry("streaming-data", CAT_DATA,
        "Streaming data processing — Kafka, Flink, Kinesis, event sourcing, exactly-once semantics",
        ("streaming data", "kafka", "flink", "kinesis", "event sourcing", "stream processing")),
    SkillEntry("data-warehouse-design", CAT_DATA,
        "Data warehouse design — star/snowflake schema, dimensional modeling, SCD patterns",
        ("data warehouse", "star schema", "snowflake schema", "dimensional modeling", "scd")),
    SkillEntry("data-quality-framework", CAT_DATA,
        "Data quality frameworks — validation rules, anomaly detection, data contracts, SLAs",
        ("data quality", "data validation", "anomaly detection", "data contract", "data sla")),
    SkillEntry("ab-testing-analysis", CAT_DATA,
        "A/B testing statistical analysis — sample sizing, significance, Bayesian methods, MDE",
        ("ab testing", "a/b test", "statistical significance", "sample size", "bayesian ab")),
    SkillEntry("business-intelligence", CAT_DATA,
        "BI dashboards and reporting — Looker, Tableau, Metabase, Power BI, metric trees",
        ("bi dashboard", "tableau", "looker", "metabase", "power bi", "business intelligence")),
    SkillEntry("feature-engineering", CAT_DATA,
        "Feature engineering — encoding, scaling, feature selection, automated feature generation",
        ("feature engineering", "feature selection", "encoding", "feature store", "feature pipeline")),
    SkillEntry("geospatial-analysis", CAT_DATA,
        "Geospatial data analysis — PostGIS, GeoPandas, coordinate systems, spatial indexing",
        ("geospatial", "postgis", "geopandas", "spatial analysis", "coordinate system")),
    SkillEntry("time-series-analysis", CAT_DATA,
        "Time series analysis — forecasting, seasonality, ARIMA, Prophet, anomaly detection",
        ("time series", "forecasting", "arima", "prophet", "seasonality", "time series analysis")),
    SkillEntry("graph-databases", CAT_DATA,
        "Graph database patterns — Neo4j, Cypher, knowledge graphs, graph algorithms",
        ("graph database", "neo4j", "cypher", "knowledge graph", "graph algorithm")),
    SkillEntry("data-governance", CAT_DATA,
        "Data governance — cataloging, lineage tracking, PII detection, access control, retention",
        ("data governance", "data catalog", "data lineage", "pii detection", "data retention")),
    SkillEntry("vector-database-ops", CAT_DATA,
        "Vector database operations — Pinecone, Weaviate, Qdrant, pgvector, similarity search",
        ("vector database", "pinecone", "weaviate", "qdrant", "pgvector", "similarity search")),

    # ── MOBILE (+14) ───────────────────────────────────────────────────────
    SkillEntry("ios-core-data", CAT_MOBILE,
        "Core Data patterns — managed object context, fetch requests, migrations, CloudKit sync",
        ("core data", "managed object", "cloudkit sync", "core data migration")),
    SkillEntry("android-jetpack", CAT_MOBILE,
        "Android Jetpack components — ViewModel, LiveData, Room, Navigation, WorkManager",
        ("jetpack", "viewmodel", "livedata", "room database", "workmanager")),
    SkillEntry("expo-patterns", CAT_MOBILE,
        "Expo development patterns — managed workflow, EAS Build, OTA updates, native modules",
        ("expo", "eas build", "expo router", "ota update", "expo managed")),
    SkillEntry("mobile-testing", CAT_MOBILE,
        "Mobile testing — Detox, Appium, XCTest, Espresso, snapshot testing, device farms",
        ("mobile testing", "detox", "appium", "xctest", "espresso", "device farm")),
    SkillEntry("push-notifications", CAT_MOBILE,
        "Push notification systems — APNs, FCM, notification channels, deep linking, rich notifications",
        ("push notification", "apns", "fcm", "notification channel", "deep link")),
    SkillEntry("mobile-performance", CAT_MOBILE,
        "Mobile performance optimization — startup time, memory, battery, network efficiency",
        ("mobile performance", "startup time", "battery optimization", "memory leak", "jank")),
    SkillEntry("mobile-ci-cd", CAT_MOBILE,
        "Mobile CI/CD — Fastlane, Bitrise, App Store Connect API, Play Console API, code signing",
        ("fastlane", "bitrise", "code signing", "app store connect", "mobile ci")),
    SkillEntry("mobile-analytics", CAT_MOBILE,
        "Mobile analytics — Firebase Analytics, Amplitude, Mixpanel, crash reporting, funnels",
        ("mobile analytics", "firebase analytics", "amplitude", "mixpanel", "crash reporting")),
    SkillEntry("mobile-security", CAT_MOBILE,
        "Mobile security — certificate pinning, secure storage, jailbreak detection, obfuscation",
        ("certificate pinning", "secure storage", "jailbreak detection", "mobile security")),
    SkillEntry("widget-development", CAT_MOBILE,
        "Widget development — iOS WidgetKit, Android widgets, app clips, instant apps",
        ("widget", "widgetkit", "app clip", "instant app", "ios widget", "android widget")),
    SkillEntry("wearable-development", CAT_MOBILE,
        "Wearable development — watchOS, Wear OS, health sensors, complications, watch faces",
        ("watchos", "wear os", "wearable", "health sensor", "apple watch", "watch face")),
    SkillEntry("mobile-accessibility", CAT_MOBILE,
        "Mobile accessibility — VoiceOver, TalkBack, dynamic type, haptics, assistive tech",
        ("voiceover", "talkback", "dynamic type", "mobile accessibility", "assistive")),
    SkillEntry("ar-vr-mobile", CAT_MOBILE,
        "AR/VR mobile — ARKit, ARCore, RealityKit, spatial computing, 3D model rendering",
        ("arkit", "arcore", "realitykit", "spatial computing", "ar mobile", "vr mobile")),
    SkillEntry("offline-first-mobile", CAT_MOBILE,
        "Offline-first mobile patterns — local database, sync strategies, conflict resolution",
        ("offline first", "offline mobile", "sync strategy", "conflict resolution", "local database")),

    # ── AI & ML (+16) ──────────────────────────────────────────────────────
    SkillEntry("prompt-engineering-advanced", CAT_AI_ML,
        "Advanced prompt engineering — chain-of-thought, self-consistency, tree-of-thought, meta-prompting",
        ("prompt engineering", "chain of thought", "few shot", "tree of thought", "meta prompt")),
    SkillEntry("fine-tuning-llm", CAT_AI_ML,
        "LLM fine-tuning — LoRA, QLoRA, PEFT, dataset preparation, evaluation, deployment",
        ("fine tuning", "lora", "qlora", "peft", "fine tune", "training data")),
    SkillEntry("embedding-models", CAT_AI_ML,
        "Embedding models — text/image/code embeddings, dimensionality reduction, similarity metrics",
        ("embedding", "text embedding", "sentence transformer", "embedding model", "cosine similarity")),
    SkillEntry("ml-model-deployment", CAT_AI_ML,
        "ML model deployment — ONNX, TensorRT, quantization, serving infrastructure, A/B testing",
        ("model deployment", "onnx", "tensorrt", "model serving", "quantization", "ml deployment")),
    SkillEntry("computer-vision-advanced", CAT_AI_ML,
        "Computer vision — object detection, segmentation, OCR, image generation, diffusion models",
        ("computer vision", "object detection", "image segmentation", "diffusion model", "yolo")),
    SkillEntry("nlp-text-processing", CAT_AI_ML,
        "NLP text processing — tokenization, NER, sentiment analysis, text classification, summarization",
        ("nlp", "text classification", "named entity", "sentiment analysis", "text processing")),
    SkillEntry("ml-experiment-tracking", CAT_AI_ML,
        "ML experiment tracking — MLflow, Weights & Biases, experiment comparison, model registry",
        ("mlflow", "weights and biases", "wandb", "experiment tracking", "model registry")),
    SkillEntry("ai-safety-alignment", CAT_AI_ML,
        "AI safety and alignment — guardrails, content filtering, bias detection, red teaming",
        ("ai safety", "alignment", "guardrails", "content filtering", "bias detection", "red teaming")),
    SkillEntry("multi-agent-systems", CAT_AI_ML,
        "Multi-agent AI systems — agent orchestration, communication protocols, tool use coordination",
        ("multi agent", "agent orchestration", "agent communication", "swarm", "crew ai")),
    SkillEntry("speech-audio-ai", CAT_AI_ML,
        "Speech and audio AI — TTS, ASR, Whisper, voice cloning, audio classification",
        ("text to speech", "speech recognition", "whisper", "voice cloning", "tts", "asr")),
    SkillEntry("recommendation-systems", CAT_AI_ML,
        "Recommendation systems — collaborative filtering, content-based, hybrid, real-time serving",
        ("recommendation", "collaborative filtering", "content based filtering", "recommender")),
    SkillEntry("llm-evaluation", CAT_AI_ML,
        "LLM evaluation — benchmarks, evals, human evaluation, RLHF, quality metrics",
        ("llm evaluation", "benchmark", "eval", "rlhf", "model evaluation", "human eval")),
    SkillEntry("knowledge-graph-ai", CAT_AI_ML,
        "Knowledge graph construction with AI — entity extraction, relation mapping, graph RAG",
        ("knowledge graph", "entity extraction", "relation extraction", "graph rag")),
    SkillEntry("synthetic-data-generation", CAT_AI_ML,
        "Synthetic data generation — data augmentation, privacy-preserving datasets, evaluation",
        ("synthetic data", "data augmentation", "synthetic generation", "privacy preserving")),
    SkillEntry("edge-ai-deployment", CAT_AI_ML,
        "Edge AI deployment — TFLite, Core ML, ONNX Mobile, model compression, on-device inference",
        ("edge ai", "tflite", "core ml", "on device", "model compression", "edge deployment")),
    SkillEntry("ai-code-generation", CAT_AI_ML,
        "AI code generation patterns — copilot integration, code review AI, automated testing generation",
        ("code generation", "copilot", "code review ai", "automated testing", "ai coder")),

    # ── DEVOPS & INFRA (+13) ───────────────────────────────────────────────
    SkillEntry("kubernetes-advanced", CAT_DEVOPS,
        "Advanced Kubernetes — operators, CRDs, service mesh, multi-cluster, GitOps with Flux/Argo",
        ("kubernetes operator", "crd", "service mesh", "gitops", "flux", "argocd")),
    SkillEntry("infrastructure-monitoring", CAT_DEVOPS,
        "Infrastructure monitoring — Prometheus, Grafana, alerting rules, SLO/SLI definition",
        ("prometheus", "grafana", "alerting", "slo", "sli", "monitoring stack")),
    SkillEntry("cloud-cost-optimization", CAT_DEVOPS,
        "Cloud cost optimization — reserved instances, spot/preemptible, rightsizing, FinOps",
        ("cloud cost", "finops", "reserved instance", "spot instance", "rightsizing")),
    SkillEntry("log-management", CAT_DEVOPS,
        "Log management — ELK stack, Loki, structured logging, log aggregation, correlation",
        ("elk stack", "loki", "structured logging", "log aggregation", "kibana", "fluentd")),
    SkillEntry("dns-cdn-patterns", CAT_DEVOPS,
        "DNS and CDN patterns — Route 53, Cloudflare, caching strategy, edge functions",
        ("dns", "cdn", "route 53", "cloudflare", "edge function", "caching strategy")),
    SkillEntry("serverless-patterns", CAT_DEVOPS,
        "Serverless architecture — Lambda, Cloud Functions, cold starts, event-driven patterns",
        ("serverless", "lambda", "cloud functions", "cold start", "event driven")),
    SkillEntry("database-administration", CAT_DEVOPS,
        "Database administration — backup strategies, replication, failover, connection pooling",
        ("database admin", "backup strategy", "replication", "failover", "connection pooling")),
    SkillEntry("network-security-infra", CAT_DEVOPS,
        "Network security infrastructure — VPNs, firewalls, WAF, DDoS protection, zero trust",
        ("vpn", "firewall", "waf", "ddos protection", "zero trust network")),
    SkillEntry("immutable-infrastructure", CAT_DEVOPS,
        "Immutable infrastructure — Packer, AMI pipelines, blue-green/canary deployments",
        ("immutable infrastructure", "packer", "ami", "blue green", "canary deployment")),
    SkillEntry("observability-tracing", CAT_DEVOPS,
        "Distributed tracing — OpenTelemetry, Jaeger, Zipkin, trace-based testing, SigNoz",
        ("opentelemetry", "jaeger", "zipkin", "distributed tracing", "signoz")),
    SkillEntry("chaos-engineering", CAT_DEVOPS,
        "Chaos engineering — fault injection, game days, resilience testing, Chaos Monkey patterns",
        ("chaos engineering", "fault injection", "game day", "chaos monkey", "resilience testing")),
    SkillEntry("secrets-rotation", CAT_DEVOPS,
        "Secrets rotation and management — Vault, AWS Secrets Manager, rotation policies",
        ("secrets rotation", "vault", "secrets manager", "rotation policy", "key rotation")),
    SkillEntry("ci-pipeline-optimization", CAT_DEVOPS,
        "CI pipeline optimization — caching, parallelism, incremental builds, monorepo CI",
        ("ci optimization", "pipeline caching", "parallel builds", "incremental build", "monorepo ci")),

    # ── SECURITY (+13) ─────────────────────────────────────────────────────
    SkillEntry("oauth-oidc-patterns", CAT_SECURITY,
        "OAuth 2.0 and OIDC patterns — authorization code flow, PKCE, token management, SSO",
        ("oauth", "oidc", "authorization code", "pkce", "sso", "openid connect")),
    SkillEntry("supply-chain-security", CAT_SECURITY,
        "Software supply chain security — SBOM, dependency scanning, provenance, SLSA levels",
        ("supply chain", "sbom", "dependency scanning", "provenance", "slsa")),
    SkillEntry("container-security", CAT_SECURITY,
        "Container security — image scanning, runtime protection, rootless containers, seccomp",
        ("container security", "image scan", "rootless container", "seccomp", "container hardening")),
    SkillEntry("api-security-patterns", CAT_SECURITY,
        "API security — rate limiting, input validation, JWT best practices, API gateway patterns",
        ("api security", "rate limiting", "jwt security", "api gateway", "input validation")),
    SkillEntry("incident-response-plan", CAT_SECURITY,
        "Incident response planning — playbooks, communication templates, post-mortems, war rooms",
        ("incident response", "incident playbook", "post mortem", "war room", "security incident")),
    SkillEntry("compliance-frameworks", CAT_SECURITY,
        "Compliance frameworks — SOC 2, ISO 27001, GDPR, HIPAA, PCI-DSS audit preparation",
        ("soc 2", "iso 27001", "gdpr", "hipaa", "pci dss", "compliance audit")),
    SkillEntry("zero-trust-architecture", CAT_SECURITY,
        "Zero trust architecture — identity verification, micro-segmentation, BeyondCorp model",
        ("zero trust", "micro segmentation", "beyondcorp", "identity verification")),
    SkillEntry("bug-bounty-patterns", CAT_SECURITY,
        "Bug bounty program design — scope definition, severity classification, reward tiers",
        ("bug bounty", "vulnerability disclosure", "severity classification", "reward tier")),
    SkillEntry("encryption-key-management", CAT_SECURITY,
        "Encryption and key management — KMS, envelope encryption, key rotation, HSM patterns",
        ("kms", "envelope encryption", "key management", "hsm", "key rotation")),
    SkillEntry("sast-dast-scanning", CAT_SECURITY,
        "SAST/DAST scanning — Semgrep, Snyk, OWASP ZAP, CodeQL, scanner pipeline integration",
        ("sast", "dast", "semgrep", "snyk", "owasp zap", "codeql")),
    SkillEntry("identity-access-management", CAT_SECURITY,
        "IAM patterns — RBAC, ABAC, PBAC, permission models, least privilege, role hierarchies",
        ("iam", "rbac", "abac", "access control", "permission model", "least privilege")),
    SkillEntry("web-application-firewall", CAT_SECURITY,
        "WAF configuration — rule tuning, false positive management, bot detection, OWASP CRS",
        ("waf", "web application firewall", "bot detection", "owasp crs", "waf rules")),
    SkillEntry("devsecops-pipeline", CAT_SECURITY,
        "DevSecOps pipeline integration — shift-left security, policy-as-code, security gates",
        ("devsecops", "shift left", "policy as code", "security gate", "security pipeline")),

    # ── TESTING & QA (+12) ─────────────────────────────────────────────────
    SkillEntry("contract-testing", CAT_TESTING,
        "Contract testing — Pact, consumer-driven contracts, provider verification, CI integration",
        ("contract testing", "pact", "consumer driven", "provider verification")),
    SkillEntry("visual-regression-testing", CAT_TESTING,
        "Visual regression testing — Percy, Chromatic, screenshot comparison, pixel diffing",
        ("visual regression", "percy", "chromatic", "screenshot testing", "pixel diff")),
    SkillEntry("performance-testing", CAT_TESTING,
        "Performance testing — k6, Locust, JMeter, load profiles, stress testing, benchmarks",
        ("performance testing", "k6", "locust", "jmeter", "load testing", "stress test")),
    SkillEntry("api-testing-patterns", CAT_TESTING,
        "API testing — REST/GraphQL testing, response validation, schema testing, API mocking",
        ("api testing", "rest testing", "graphql testing", "schema testing", "api mock")),
    SkillEntry("mutation-testing", CAT_TESTING,
        "Mutation testing — Stryker, PIT, mutation operators, test suite quality assessment",
        ("mutation testing", "stryker", "pit", "test quality", "mutation score")),
    SkillEntry("accessibility-testing", CAT_TESTING,
        "Accessibility testing — axe-core, Lighthouse a11y, WAVE, automated a11y CI checks",
        ("accessibility testing", "axe core", "lighthouse a11y", "wave", "a11y testing")),
    SkillEntry("chaos-test-patterns", CAT_TESTING,
        "Chaos testing patterns — network partitions, clock skew, resource exhaustion, fault injection",
        ("chaos test", "network partition", "fault injection", "resource exhaustion")),
    SkillEntry("test-data-management", CAT_TESTING,
        "Test data management — factories, fixtures, seeding, data masking, synthetic test data",
        ("test data", "test factory", "fixture", "data seeding", "test fixture")),
    SkillEntry("mobile-ui-testing", CAT_TESTING,
        "Mobile UI testing — Detox, Maestro, XCUITest, snapshot tests, device matrix",
        ("mobile ui test", "detox", "maestro", "xcuitest", "device matrix")),
    SkillEntry("security-testing", CAT_TESTING,
        "Security testing — OWASP testing guide, penetration testing methodology, vulnerability scan",
        ("security testing", "penetration testing", "vuln scan", "owasp testing")),
    SkillEntry("test-architecture", CAT_TESTING,
        "Test architecture — test pyramid, testing trophy, test strategies, test organization",
        ("test architecture", "test pyramid", "testing trophy", "test strategy")),
    SkillEntry("flaky-test-remediation", CAT_TESTING,
        "Flaky test remediation — root cause analysis, quarantine, retry strategies, determinism",
        ("flaky test", "flaky", "test quarantine", "test retry", "deterministic test")),

    # ── FRONTEND (+11) ─────────────────────────────────────────────────────
    SkillEntry("svelte-patterns", CAT_FRONTEND,
        "Svelte/SvelteKit patterns — reactivity, stores, SSR, server routes, transitions",
        ("svelte", "sveltekit", "svelte store", "svelte component", "svelte transition")),
    SkillEntry("vue-patterns", CAT_FRONTEND,
        "Vue 3 patterns — Composition API, Pinia, Vue Router, composables, teleport",
        ("vue", "vue 3", "pinia", "vue router", "composable", "composition api")),
    SkillEntry("angular-patterns", CAT_FRONTEND,
        "Angular patterns — signals, standalone components, NgRx, RxJS, lazy loading",
        ("angular", "angular signal", "ngrx", "rxjs", "standalone component")),
    SkillEntry("web-components", CAT_FRONTEND,
        "Web Components — custom elements, Shadow DOM, lit, Stencil, framework-agnostic UI",
        ("web component", "custom element", "shadow dom", "lit", "stencil")),
    SkillEntry("css-architecture", CAT_FRONTEND,
        "CSS architecture — BEM, CSS Modules, CSS-in-JS, Tailwind patterns, utility-first design",
        ("css architecture", "bem", "css modules", "css in js", "tailwind patterns")),
    SkillEntry("web-performance", CAT_FRONTEND,
        "Web performance — Core Web Vitals, bundle analysis, lazy loading, prefetching, caching",
        ("web performance", "core web vitals", "bundle size", "lazy loading", "prefetch")),
    SkillEntry("pwa-patterns", CAT_FRONTEND,
        "Progressive Web App patterns — service workers, caching strategies, offline-first",
        ("pwa", "progressive web app", "service worker", "cache strategy", "offline first")),
    SkillEntry("state-machine-ui", CAT_FRONTEND,
        "State machines in UI — XState, finite state machines, statecharts for complex flows",
        ("xstate", "state machine", "statechart", "finite state", "state machine ui")),
    SkillEntry("micro-frontend", CAT_FRONTEND,
        "Micro-frontend architecture — Module Federation, single-spa, independent deployment",
        ("micro frontend", "module federation", "single spa", "micro frontend architecture")),
    SkillEntry("animation-libraries", CAT_FRONTEND,
        "Animation libraries — Framer Motion, GSAP, Lottie, CSS animations, scroll-driven",
        ("framer motion", "gsap", "lottie", "css animation", "scroll animation")),
    SkillEntry("webgl-threejs", CAT_FRONTEND,
        "WebGL and Three.js — 3D rendering, shaders, React Three Fiber, immersive web experiences",
        ("webgl", "three.js", "threejs", "react three fiber", "3d rendering", "shader")),

    # ── GAME DEV (+8) ──────────────────────────────────────────────────────
    SkillEntry("procedural-generation", CAT_GAME_DEV,
        "Procedural generation — terrain, dungeons, loot tables, noise functions, wave function collapse",
        ("procedural generation", "terrain generation", "dungeon generation", "wave function collapse")),
    SkillEntry("game-ai-behavior", CAT_GAME_DEV,
        "Game AI behavior — behavior trees, GOAP, utility AI, flocking, pathfinding algorithms",
        ("behavior tree", "goap", "utility ai", "flocking", "pathfinding algorithm")),
    SkillEntry("shader-programming", CAT_GAME_DEV,
        "Shader programming — HLSL, GLSL, compute shaders, post-processing effects, PBR",
        ("shader", "hlsl", "glsl", "compute shader", "pbr", "post processing")),
    SkillEntry("game-networking", CAT_GAME_DEV,
        "Game networking — client prediction, server reconciliation, snapshot interpolation, netcode",
        ("game networking", "client prediction", "server reconciliation", "netcode", "snapshot")),
    SkillEntry("game-economy-design", CAT_GAME_DEV,
        "Game economy design — sink/faucet analysis, loot tables, gacha mechanics, virtual currencies",
        ("game economy", "loot table", "gacha", "virtual currency", "sink faucet")),
    SkillEntry("level-design-tools", CAT_GAME_DEV,
        "Level design tools — tile maps, procedural layouts, spatial hashing, world streaming",
        ("level design", "tile map", "procedural layout", "spatial hashing", "world streaming")),
    SkillEntry("game-physics", CAT_GAME_DEV,
        "Game physics — collision detection, rigid bodies, raycasting, physics engines, constraints",
        ("game physics", "collision detection", "rigid body", "raycasting", "physics engine")),
    SkillEntry("game-analytics-telemetry", CAT_GAME_DEV,
        "Game analytics and telemetry — player tracking, heatmaps, funnel analysis, retention metrics",
        ("game analytics", "game telemetry", "player tracking", "heatmap", "retention metric")),

    # ── SPECIALIZED DOMAINS (+9) ───────────────────────────────────────────
    SkillEntry("legal-tech-patterns", CAT_SPECIALIZED,
        "Legal tech patterns — contract analysis, clause extraction, document automation, compliance",
        ("legal tech", "contract analysis", "clause extraction", "legal document")),
    SkillEntry("education-tech", CAT_SPECIALIZED,
        "EdTech patterns — LMS integration, adaptive learning, assessment engines, SCORM/xAPI",
        ("edtech", "lms", "adaptive learning", "assessment engine", "scorm", "xapi")),
    SkillEntry("real-estate-tech", CAT_SPECIALIZED,
        "Real estate tech — property search, MLS integration, mortgage calculators, virtual tours",
        ("real estate", "mls", "property search", "mortgage calculator", "virtual tour")),
    SkillEntry("agriculture-tech", CAT_SPECIALIZED,
        "AgriTech patterns — precision agriculture, IoT sensors, crop monitoring, yield prediction",
        ("agritech", "precision agriculture", "crop monitoring", "yield prediction", "iot farm")),
    SkillEntry("automotive-adas", CAT_SPECIALIZED,
        "Automotive ADAS patterns — sensor fusion, object tracking, path planning, safety standards",
        ("adas", "sensor fusion", "path planning", "automotive safety", "object tracking")),
    SkillEntry("telecom-patterns", CAT_SPECIALIZED,
        "Telecom engineering patterns — network protocols, QoS, 5G patterns, CDR processing",
        ("telecom", "network protocol", "qos", "5g", "cdr processing")),
    SkillEntry("construction-bim", CAT_SPECIALIZED,
        "Construction BIM patterns — IFC models, clash detection, 4D scheduling, quantity takeoff",
        ("bim", "ifc model", "clash detection", "4d scheduling", "quantity takeoff")),
    SkillEntry("insurance-actuarial", CAT_SPECIALIZED,
        "Insurance actuarial patterns — risk modeling, claims processing, underwriting automation",
        ("actuarial", "risk modeling", "claims processing", "underwriting", "insurance")),
    SkillEntry("environmental-monitoring", CAT_SPECIALIZED,
        "Environmental monitoring — air/water quality sensors, satellite data, compliance reporting",
        ("environmental monitoring", "air quality", "water quality", "satellite data")),

    # ── PRODUCTIVITY (+8) ──────────────────────────────────────────────────
    SkillEntry("obsidian-knowledge", CAT_PRODUCTIVITY,
        "Obsidian knowledge management — vault structure, plugins, Dataview, linking strategies",
        ("obsidian", "obsidian vault", "dataview", "knowledge base", "zettelkasten")),
    SkillEntry("automation-workflows", CAT_PRODUCTIVITY,
        "Automation workflows — Zapier, Make, n8n, GitHub Actions, cron jobs, webhook orchestration",
        ("automation", "zapier", "make", "n8n", "webhook", "cron job")),
    SkillEntry("time-management", CAT_PRODUCTIVITY,
        "Time management systems — timeboxing, Pomodoro, deep work blocks, calendar optimization",
        ("time management", "timeboxing", "pomodoro", "deep work", "calendar optimization")),
    SkillEntry("meeting-facilitation", CAT_PRODUCTIVITY,
        "Meeting facilitation — agendas, decision logs, async standups, retrospective formats",
        ("meeting facilitation", "agenda", "decision log", "async standup", "retrospective")),
    SkillEntry("onboarding-playbook", CAT_PRODUCTIVITY,
        "Developer onboarding — codebase walkthroughs, environment setup, mentoring frameworks",
        ("onboarding", "developer onboarding", "codebase walkthrough", "mentoring")),
    SkillEntry("decision-frameworks", CAT_PRODUCTIVITY,
        "Decision frameworks — DACI, RFC process, decision matrices, one-way vs two-way doors",
        ("decision framework", "daci", "rfc process", "decision matrix", "two way door")),
    SkillEntry("personal-crm", CAT_PRODUCTIVITY,
        "Personal CRM — contact management, follow-up tracking, networking strategy, outreach",
        ("personal crm", "contact management", "follow up tracking", "networking")),
    SkillEntry("sprint-ceremonies", CAT_PRODUCTIVITY,
        "Sprint ceremonies — planning, daily standup, review, retro facilitation, velocity tracking",
        ("sprint ceremony", "sprint planning", "daily standup", "sprint review", "velocity")),

    # ── ENGINEERING CORE (+10) ─────────────────────────────────────────────
    SkillEntry("monorepo-patterns", CAT_ENGINEERING_CORE,
        "Monorepo patterns — Turborepo, Nx, Lerna, workspace dependencies, incremental builds",
        ("monorepo", "turborepo", "nx", "lerna", "workspace dependency")),
    SkillEntry("graphql-patterns", CAT_ENGINEERING_CORE,
        "GraphQL patterns — schema design, resolvers, DataLoader, subscriptions, code generation",
        ("graphql", "graphql schema", "resolver", "dataloader", "subscription", "graphql codegen")),
    SkillEntry("grpc-patterns", CAT_ENGINEERING_CORE,
        "gRPC patterns — protobuf design, streaming, interceptors, load balancing, health checks",
        ("grpc", "protobuf", "grpc streaming", "grpc interceptor", "grpc health check")),
    SkillEntry("event-driven-architecture", CAT_ENGINEERING_CORE,
        "Event-driven architecture — event sourcing, CQRS, saga orchestration, eventual consistency",
        ("event driven", "event sourcing", "cqrs", "saga pattern", "eventual consistency")),
    SkillEntry("api-versioning", CAT_ENGINEERING_CORE,
        "API versioning strategies — URL versioning, header versioning, deprecation, migration paths",
        ("api versioning", "api deprecation", "api migration", "breaking change")),
    SkillEntry("dependency-injection", CAT_ENGINEERING_CORE,
        "Dependency injection patterns — IoC containers, service locator, constructor injection",
        ("dependency injection", "ioc", "service locator", "constructor injection", "di container")),
    SkillEntry("error-handling-patterns", CAT_ENGINEERING_CORE,
        "Error handling patterns — Result types, error boundaries, retry strategies, circuit breakers",
        ("error handling", "result type", "error boundary", "retry strategy", "circuit breaker")),
    SkillEntry("caching-patterns", CAT_ENGINEERING_CORE,
        "Caching patterns — Redis, Memcached, CDN caching, cache invalidation, TTL strategies",
        ("caching", "redis", "memcached", "cache invalidation", "ttl", "cache aside")),
    SkillEntry("websocket-realtime", CAT_ENGINEERING_CORE,
        "WebSocket and real-time patterns — Socket.io, SSE, long polling, presence, rooms",
        ("websocket", "socket.io", "sse", "real time", "long polling", "server sent events")),
    SkillEntry("code-generation-tools", CAT_ENGINEERING_CORE,
        "Code generation tools — AST manipulation, template-based codegen, macro systems, metaprogramming",
        ("code generation", "ast", "codegen", "metaprogramming", "macro system")),

    # ── BACKEND (+8) ───────────────────────────────────────────────────────
    SkillEntry("message-queue-patterns", CAT_BACKEND,
        "Message queue patterns — RabbitMQ, SQS, NATS, dead letter queues, exactly-once delivery",
        ("message queue", "rabbitmq", "sqs", "nats", "dead letter queue")),
    SkillEntry("search-engine-patterns", CAT_BACKEND,
        "Search engine integration — Elasticsearch, Meilisearch, Typesense, full-text search, facets",
        ("elasticsearch", "meilisearch", "typesense", "full text search", "faceted search")),
    SkillEntry("file-upload-patterns", CAT_BACKEND,
        "File upload patterns — multipart, presigned URLs, chunked uploads, virus scanning, S3",
        ("file upload", "multipart", "presigned url", "chunked upload", "s3 upload")),
    SkillEntry("background-job-patterns", CAT_BACKEND,
        "Background job patterns — Sidekiq, Bull, Celery, job scheduling, retry policies, priorities",
        ("background job", "sidekiq", "bull", "celery", "job scheduler", "job queue")),
    SkillEntry("rate-limiting-patterns", CAT_BACKEND,
        "Rate limiting — token bucket, sliding window, fixed window, distributed rate limiting",
        ("rate limit", "token bucket", "sliding window", "throttle", "api rate")),
    SkillEntry("multi-tenancy-patterns", CAT_BACKEND,
        "Multi-tenancy — schema-per-tenant, row-level security, tenant isolation, data partitioning",
        ("multi tenant", "tenant isolation", "row level security", "schema per tenant")),
    SkillEntry("webhook-patterns", CAT_BACKEND,
        "Webhook patterns — delivery guarantees, signature verification, retry logic, idempotency",
        ("webhook", "webhook delivery", "signature verification", "webhook retry")),
    SkillEntry("session-management", CAT_BACKEND,
        "Session management — stateless JWTs, server sessions, Redis sessions, session security",
        ("session management", "jwt session", "redis session", "session security", "cookie session")),

    # ── BUSINESS STRATEGY (+6) ─────────────────────────────────────────────
    SkillEntry("okr-framework", CAT_BUSINESS,
        "OKR framework — objective writing, key results measurability, cascade alignment, scoring",
        ("okr", "objectives key results", "okr framework", "key result", "okr scoring")),
    SkillEntry("pitch-deck-design", CAT_BUSINESS,
        "Pitch deck design — narrative arc, slide structure, data visualization, investor psychology",
        ("pitch deck", "investor deck", "fundraising deck", "pitch presentation")),
    SkillEntry("customer-journey-mapping", CAT_BUSINESS,
        "Customer journey mapping — touchpoints, pain points, moments of truth, service blueprinting",
        ("customer journey", "journey map", "touchpoint", "service blueprint")),
    SkillEntry("agile-transformation", CAT_BUSINESS,
        "Agile transformation — SAFe, LeSS, adoption roadmaps, change management, scaling patterns",
        ("agile transformation", "safe", "less", "agile scaling", "change management")),
    SkillEntry("market-sizing", CAT_BUSINESS,
        "Market sizing — TAM/SAM/SOM analysis, bottom-up/top-down estimation, market mapping",
        ("market sizing", "tam", "sam", "som", "market analysis", "market map")),
    SkillEntry("partnership-strategy", CAT_BUSINESS,
        "Partnership strategy — co-marketing, channel partnerships, revenue share, API partnerships",
        ("partnership", "co marketing", "channel partner", "revenue share", "api partnership")),

    # ── MARKETING & GROWTH (+4) ────────────────────────────────────────────
    SkillEntry("influencer-marketing", CAT_MARKETING,
        "Influencer marketing — creator outreach, campaign management, ROI tracking, micro-influencers",
        ("influencer", "creator marketing", "micro influencer", "influencer campaign")),
    SkillEntry("growth-hacking-loops", CAT_MARKETING,
        "Growth loops — viral loops, content loops, paid loops, compound growth mechanisms",
        ("growth loop", "viral loop", "growth hacking", "compound growth")),
    SkillEntry("podcast-marketing", CAT_MARKETING,
        "Podcast marketing — guest strategy, show notes, distribution, monetization, audience growth",
        ("podcast", "podcast marketing", "podcast guest", "show notes", "podcast growth")),
    SkillEntry("event-marketing", CAT_MARKETING,
        "Event marketing — webinars, conferences, virtual events, speaker strategy, lead capture",
        ("event marketing", "webinar", "conference", "virtual event", "speaker strategy")),

)


# ═══════════════════════════════════════════════════════════════════════════════
# INDEX STRUCTURES — built at import time for O(1) lookups
# ═══════════════════════════════════════════════════════════════════════════════

# name → SkillEntry
SKILL_BY_NAME: dict[str, SkillEntry] = {s.name: s for s in SKILL_REGISTRY}

# category → list[SkillEntry]
SKILLS_BY_CATEGORY: dict[str, list[SkillEntry]] = {}
for _s in SKILL_REGISTRY:
    SKILLS_BY_CATEGORY.setdefault(_s.category, []).append(_s)

# Flat trigger → skill name mapping (for fast keyword matching)
TRIGGER_INDEX: dict[str, list[str]] = {}
for _s in SKILL_REGISTRY:
    for _t in _s.triggers:
        TRIGGER_INDEX.setdefault(_t.lower(), []).append(_s.name)


def get_skill_count() -> int:
    """Total number of skills in the library."""
    return len(SKILL_REGISTRY)


def get_category_counts() -> dict[str, int]:
    """Skills per category."""
    return {cat: len(skills) for cat, skills in SKILLS_BY_CATEGORY.items()}


def get_skill(name: str) -> Optional[SkillEntry]:
    """Look up a skill by name."""
    return SKILL_BY_NAME.get(name)


def get_skills_in_category(category: str) -> list[SkillEntry]:
    """Get all skills in a category."""
    return SKILLS_BY_CATEGORY.get(category, [])


def search_skills(query: str) -> list[SkillEntry]:
    """Search skills by name or description substring."""
    q = query.lower()
    results = []
    for s in SKILL_REGISTRY:
        if q in s.name.lower() or q in s.description.lower():
            results.append(s)
    return results
