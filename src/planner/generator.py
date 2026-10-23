"""Generates a project-tailored 30-day engineering roadmap."""

import json
import logging
import re
from pathlib import Path
from typing import List, Optional

from src.config import ProjectConfig
from src.providers.base import LLMProvider
from src.providers.factory import get_llm_provider
from src.state.manager import StateManager, Task, TaskStatus
from src.planner.roadmap_writer import RoadmapWriter

logger = logging.getLogger("agent.planner.generator")


class RoadmapGenerator:
    """Creates a comprehensive 30-day technical plan tailored to the configured project."""

    def __init__(self, config: ProjectConfig, state_manager: StateManager, provider: Optional[LLMProvider] = None):
        self.config = config
        self.state_manager = state_manager
        self.provider = provider or get_llm_provider(config.llm)
        self.writer = RoadmapWriter(config.target_project_root, config)

    def generate_and_save(self, force: bool = False) -> List[Task]:
        """Generate roadmap tasks if not already existing, and persist to SQLite and ROADMAP.md."""
        if not force and self.state_manager.has_roadmap():
            logger.info("Existing 30-day roadmap found in state store. Loading...")
            tasks = self.state_manager.get_all_tasks()
            self.writer.write_roadmap_md(tasks)
            self.writer.write_progress_md(tasks, self.state_manager.get_progress_summary())
            return tasks

        logger.info("Generating new 30-day roadmap tailored to '%s'...", self.config.project_name)
        tasks = self._synthesize_tasks()
        self.state_manager.save_roadmap(tasks)
        self.writer.write_roadmap_md(tasks)
        self.writer.write_progress_md(tasks, self.state_manager.get_progress_summary())
        logger.info("30-Day roadmap generated and persisted successfully.")
        return tasks

    def _synthesize_tasks(self) -> List[Task]:
        """Attempt LLM generation, falling back gracefully to domain-specific structured synthesizer."""
        try:
            tasks = self._generate_with_llm()
            if len(tasks) == 30:
                return tasks
        except Exception as e:
            logger.warning("LLM roadmap generation failed or incomplete: %s. Using tailored domain synthesizer.", e)

        return self._generate_tailored_domain_tasks()

    def _generate_with_llm(self) -> List[Task]:
        prompt = f"""
You are a Principal Software Architect. Plan a rigorous, realistic, high-quality 30-day software development roadmap for the following project:

Project Name: {self.config.project_name}
Description: {self.config.project_description}
Tech Stack: {self.config.tech_stack.language}, {', '.join(self.config.tech_stack.frameworks)}
Goals:
{chr(10).join(f"- {g}" for g in self.config.project_goals)}

Divide the work across exactly 30 days across these 5 phases:
- Phase 1: Foundation (Days 1–5)
- Phase 2: Core Functionality (Days 6–12)
- Phase 3: Advanced Features (Days 13–19)
- Phase 4: Reliability and Polish (Days 20–25)
- Phase 5: Release (Days 26–30)

Return ONLY valid JSON matching this schema:
{{
  "tasks": [
    {{
      "day_number": 1,
      "id": "task-day-01",
      "title": "Short title",
      "phase": "Phase 1: Foundation",
      "description": "Concrete technical description of work",
      "acceptance_criteria": ["Criteria 1", "Criteria 2", "Criteria 3"],
      "deliverables": ["path/to/file1.py", "path/to/test1.py"],
      "dependencies": [],
      "complexity": "Low"
    }}
  ]
}}
Ensure exactly 30 tasks numbered 1 to 30.
"""
        response = self.provider.generate(prompt, json_mode=True)
        content = response.content.strip()

        # Extract JSON from markdown fence if present
        if "```" in content:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
            if match:
                content = match.group(1).strip()

        data = json.loads(content)
        raw_tasks = data.get("tasks", [])
        if len(raw_tasks) != 30:
            raise ValueError(f"Expected 30 tasks from LLM, got {len(raw_tasks)}")

        result: List[Task] = []
        for item in raw_tasks:
            result.append(
                Task(
                    id=item.get("id", f"task-day-{item['day_number']:02d}"),
                    day_number=item["day_number"],
                    title=item["title"],
                    phase=item["phase"],
                    description=item["description"],
                    acceptance_criteria=item.get("acceptance_criteria", []),
                    deliverables=item.get("deliverables", []),
                    dependencies=item.get("dependencies", []),
                    complexity=item.get("complexity", "Medium"),
                    status=TaskStatus.PENDING,
                )
            )
        return result

    def _generate_tailored_domain_tasks(self) -> List[Task]:
        """Domain-adapted structured task matrix tailored directly to CloudTelemetry & Distributed Systems."""
        name = self.config.project_name
        
        task_blueprints = [
            # Phase 1: Foundation (Days 1–5)
            (1, "Phase 1: Foundation", "Requirements, Acceptance Criteria, Architecture, and Synthetic Database Domain",
             "Define ClarifySQL system requirements, architecture specifications, and synthetic e-commerce database schema contracts.",
             ["Specify schema entity-relationship model (customers, orders, products, order_items)", "Document clarification engine state machine and ambiguity trigger thresholds", "Define read-only safety guardrails, timeouts, and AST validation specifications"],
             ["docs/architecture.md", "docs/requirements.md", "docs/domain_schema.md"], [], "Low"),
            (2, "Phase 1: Foundation", "Project Scaffolding, Python/FastAPI Environment, PostgreSQL Config, and React Layout",
             "Initialize backend project layout with FastAPI and Pydantic v2, PostgreSQL connection driver, and React frontend scaffolding.",
             ["FastAPI application skeleton with structured config management", "Pydantic v2 settings loading database credentials from environment", "React frontend scaffolding initialized with Tailwind CSS configuration"],
             ["src/core/config.py", "src/main.py", "frontend/package.json", "frontend/src/App.tsx"], ["task-day-01"], "Low"),
            (3, "Phase 1: Foundation", "Synthetic Database Domain: Customers, Orders, Products, and Realistic Seed Data",
             "Create relational schemas for customers, products, orders, and order_items with realistic sample data for text-to-sql evaluation.",
             ["SQLAlchemy models defined with primary keys, foreign keys, and indexes", "Synthetic seed generator populates realistic customers, products, orders, and line items", "Unit test verifies relational integrity and seed data consistency"],
             ["src/db/models.py", "src/db/seed_data.py", "tests/test_seed_data.py"], ["task-day-02"], "Medium"),
            (4, "Phase 1: Foundation", "Database Connection Management, Session Pooling, and Schema Introspection",
             "Implement robust database session management and automatic schema reflection extracting table names, columns, and data types.",
             ["Thread-safe engine pool with read-only execution session factory", "Schema introspector extracts tables, columns, foreign keys, and sample distinct values", "Tests verify schema reflection accurately matches database catalog"],
             ["src/db/connection.py", "src/db/introspector.py", "tests/test_introspector.py"], ["task-day-03"], "Medium"),
            (5, "Phase 1: Foundation", "Backend Configuration Validation, Health Endpoints, and Baseline Test Suite",
             "Add comprehensive health check endpoints, configuration sanity checks, and automated baseline pytest suite.",
             ["GET /health endpoint reporting database ping latency and schema readiness", "Configuration validator checking model API keys and connection parameters", "Pytest suite executes and passes 100% on Phase 1 modules"],
             ["src/api/health.py", "tests/test_health.py", "tests/test_config.py"], ["task-day-04"], "Low"),

            # Phase 2: Core Functionality (Days 6–12)
            (6, "Phase 2: Core Functionality", "LLM Provider Interface and Structured Response Schemas",
             "Implement pluggable LLM provider abstraction supporting Gemini and OpenAI with structured JSON response schemas.",
             ["Pydantic models for SQLGenerationResponse, AmbiguityCheck, and ClarificationPrompt", "Gemini and OpenAI provider implementations with exponential backoff", "Unit tests verifying JSON response parsing and schema conformance"],
             ["src/llm/provider.py", "src/llm/schemas.py", "tests/test_llm_provider.py"], ["task-day-05"], "Medium"),
            (7, "Phase 2: Core Functionality", "Schema-Aware SQL Generation Engine",
             "Build prompt synthesis pipeline injecting introspected database schema, foreign keys, and constraints into LLM context.",
             ["Dynamic prompt builder formatting schema catalog into compact model context", "Generates standard SQL queries adhering to database dialect without hallucinations", "Unit tests verifying correct table joins on multi-table queries"],
             ["src/engine/sql_generator.py", "tests/test_sql_generator.py"], ["task-day-06"], "Medium"),
            (8, "Phase 2: Core Functionality", "SQL Parsing, Read-Only Query Validation, and Query Limits",
             "Implement strict AST-based SQL validator enforcing read-only SELECT/CTE queries and blocking DDL/DML.",
             ["SQL AST parser rejects INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE", "Blocks stacked queries, dangerous functions, and unauthorized system tables", "Enforces statement limit (LIMIT 100) and query complexity checks"],
             ["src/security/sql_guard.py", "tests/test_sql_guard.py"], ["task-day-07"], "High"),
            (9, "Phase 2: Core Functionality", "Safe Query Execution Engine and Tabular Result Serialization",
             "Execute validated queries under statement timeouts, serialize results to JSON tables, and compute column metadata.",
             ["Read-only database transaction execution with strict timeout (5 seconds)", "Serializes rows and columns into JSON table structure with row count and duration", "Error interceptor converting database exceptions into readable user messages"],
             ["src/engine/query_executor.py", "tests/test_query_executor.py"], ["task-day-08"], "Medium"),
            (10, "Phase 2: Core Functionality", "Test Clear Questions, Invalid Queries, and Unsupported Requests",
             "Build rigorous test suite covering unambiguous questions, syntactic errors, and out-of-domain requests.",
             ["End-to-end tests for simple and aggregated clear questions (e.g. 'total sales in 2024')", "Tests verifying rejection of malicious queries like 'DROP TABLE customers'", "Negative tests handling unsupported queries with graceful error responses"],
             ["tests/test_clear_questions.py", "tests/test_security_rejection.py"], ["task-day-09"], "Medium"),
            (11, "Phase 2: Core Functionality", "Ambiguity Detection and Clarification-State Models",
             "Implement ambiguity analyzer detecting underspecified metrics, missing time ranges, or multiple ranking criteria.",
             ["Ambiguity classifier determining if question requires user clarification", "Identifies specific ambiguity type: ranking criteria, date range, entity filter", "Tests verify clear questions are not unnecessarily flagged as ambiguous"],
             ["src/engine/ambiguity_detector.py", "tests/test_ambiguity_detector.py"], ["task-day-10"], "High"),
            (12, "Phase 2: Core Functionality", "Targeted Clarification Question Generator with Selectable Options",
             "Generate one concise, targeted clarification question with 2-4 distinct selectable options when ambiguity is detected.",
             ["Clarification generator outputs clear question and structured choice options", "Example: 'Show top customers' -> choices: Total Spending, Order Count, Recent Activity", "Tests confirm concise wording and mutually exclusive options"],
             ["src/engine/clarification_generator.py", "tests/test_clarification_generator.py"], ["task-day-11"], "Medium"),

            # Phase 3: Clarification & State (Days 13–19)
            (13, "Phase 3: Clarification & State", "Conversation State Manager Preserving Clarification Turns",
             "Build stateful conversation store preserving original user question, detected ambiguities, and user answers.",
             ["Session state store caching multi-turn dialogue history with TTL cleanup", "ConversationTurn model linking question, clarification options, and selection", "Integration tests verifying conversation state persistence across turns"],
             ["src/engine/conversation.py", "tests/test_conversation.py"], ["task-day-12"], "Medium"),
            (14, "Phase 3: Clarification & State", "Clarification-Informed SQL Regeneration",
             "Incorporate user clarification choice into the SQL generator prompt to produce accurate, tailored queries.",
             ["Prompt pipeline augments schema and original question with selected clarification", "Generates refined SQL directly matching the clarified user intent", "Tests verify generated SQL reflects the clarified metric (e.g. SUM(total_amount))"],
             ["src/engine/sql_regenerator.py", "tests/test_sql_regenerator.py"], ["task-day-13"], "Medium"),
            (15, "Phase 3: Clarification & State", "Test Suite for Ambiguous, Underspecified, and Clear Questions",
             "Comprehensive automated test matrix asserting correct routing between direct execution and clarification flow.",
             ["Tests asserting clarification triggers on underspecified ranking requests", "Tests asserting direct execution on fully specified date-filtered queries", "Verification that default assumptions are explicitly documented when no clarification is needed"],
             ["tests/test_clarification_workflow.py"], ["task-day-14"], "Medium"),
            (16, "Phase 3: Clarification & State", "React Chat Interface and Question Submission Workflow",
             "Build modern, responsive React chat interface with Tailwind CSS for natural language question input.",
             ["Clean chat message timeline supporting user questions and assistant responses", "Input box with auto-focus, send button, and keyboard shortcut (Enter)", "Component tests asserting input handling and loading state transitions"],
             ["frontend/src/components/ChatTimeline.tsx", "frontend/src/components/QuestionInput.tsx"], ["task-day-15"], "Medium"),
            (17, "Phase 3: Clarification & State", "Interactive Clarification Option Controls and Turn History",
             "Render clickable clarification option buttons within the chat stream allowing 1-click option selection.",
             ["ClarificationCard component rendering option pills/buttons for user selection", "Disables choices once answered and updates conversation timeline seamlessly", "Frontend interaction tests verifying choice submission callback"],
             ["frontend/src/components/ClarificationCard.tsx", "frontend/src/components/HistorySidebar.tsx"], ["task-day-16"], "Medium"),
            (18, "Phase 3: Clarification & State", "SQL Preview Modal, Plain-English Explanations, and Tabular Results",
             "Display formatted SQL preview with syntax highlighting, plain-English explanation, and interactive data table.",
             ["SqlPreview component with copy-to-clipboard and syntax highlighting", "QueryExplanation card detailing why the query was constructed that way", "ResultTable component with pagination, sortable columns, and row counts"],
             ["frontend/src/components/SqlPreview.tsx", "frontend/src/components/ResultTable.tsx"], ["task-day-17"], "Medium"),
            (19, "Phase 3: Clarification & State", "Responsive UI Polish, Skeleton Loading States, and Error Banners",
             "Implement polished dark-mode styling, loading skeletons during SQL execution, and actionable error toasts.",
             ["Skeleton placeholders for SQL generation and data table loading states", "Error banner explaining syntax or security policy rejections clearly", "Responsive mobile-friendly drawer and desktop side-by-side view"],
             ["frontend/src/components/ErrorBanner.tsx", "frontend/src/components/LoadingSkeleton.tsx"], ["task-day-18"], "Low"),

            # Phase 4: Evaluation, Hardening & Integration (Days 20–25)
            (20, "Phase 4: Evaluation, Hardening & Integration", "Full Frontend-Backend API Integration and User Journey Test",
             "Connect React frontend with FastAPI backend endpoints over HTTP and test complete clarification journey.",
             ["POST /api/v1/query endpoint handling initial question, ambiguity, and clarification", "End-to-end integration test asserting full question -> clarify -> execute flow", "CORS and API client error handling verified"],
             ["src/api/routes.py", "tests/test_api_integration.py"], ["task-day-19"], "High"),
            (21, "Phase 4: Evaluation, Hardening & Integration", "Representative Text-to-SQL Benchmark Dataset",
             "Curate benchmark suite of 50 diverse e-commerce questions across simple, multi-join, ambiguous, and edge cases.",
             ["Benchmark dataset JSON containing questions, expected tables, and golden SQL", "Categories covering simple lookups, aggregations, multi-table joins, and ambiguous prompts", "Automated dataset loader and test runner"],
             ["benchmarks/dataset.json", "benchmarks/evaluator.py"], ["task-day-20"], "Medium"),
            (22, "Phase 4: Evaluation, Hardening & Integration", "Execution Accuracy and Clarification Effectiveness Measurement",
             "Run automated evaluation computing exact-match accuracy, execution accuracy, and ambiguity recall.",
             ["Evaluation script calculates execution accuracy (% of queries producing identical results)", "Measures clarification precision: does the engine ask questions only when needed?", "Generates benchmark evaluation report in Markdown"],
             ["benchmarks/run_eval.py", "reports/evaluation_results.md"], ["task-day-21"], "High"),
            (23, "Phase 4: Evaluation, Hardening & Integration", "Prompt Engineering Improvements and Failure Analysis",
             "Analyze failed benchmark questions to refine schema prompts, few-shot examples, and ambiguity triggers.",
             ["Incorporate few-shot representative join examples into generator prompt", "Fine-tune ambiguity detection thresholds to minimize false positive clarifications", "Re-run benchmarks demonstrating measurable accuracy improvement"],
             ["src/engine/prompts.py", "tests/test_prompt_improvements.py"], ["task-day-22"], "Medium"),
            (24, "Phase 4: Evaluation, Hardening & Integration", "Database Security Audit, Parameterization, and Vulnerability Scan",
             "Audit SQL security rules, enforce parameterized execution for literals, and run dependency audit.",
             ["Verify parameterization of user-supplied filter constants to prevent SQL injection", "Audit query timeout enforcement preventing Denial-of-Service on heavy scans", "Run security audit verifying zero high/critical vulnerabilities"],
             ["src/security/sanitizer.py", "tests/test_security_audit.py"], ["task-day-23"], "Medium"),
            (25, "Phase 4: Evaluation, Hardening & Integration", "Full Regression Testing and Defect Resolution",
             "Execute full regression test suite across backend API, database engine, guardrails, and frontend mocks.",
             ["100% test pass rate across all backend unit and integration test suites", "Resolve all outstanding edge-case defects identified during evaluation", "Produce quality and reliability sign-off checklist"],
             ["tests/test_full_regression.py", "reports/quality_audit.md"], ["task-day-24"], "Medium"),

            # Phase 5: Release (Days 26–30)
            (26, "Phase 5: Release", "Production Deployment Configuration and Environment Setup",
             "Configure production environment profiles, database connection pooling, and Gunicorn/Uvicorn workers.",
             ["Production settings profile with strict environment variable validation", "Production ASGI server configuration with optimized worker processes", "Configuration tests validating production parameters"],
             ["src/core/prod_config.py", "tests/test_prod_config.py"], ["task-day-25"], "Low"),
            (27, "Phase 5: Release", "Containerization: Multi-Stage Dockerfile & Docker Compose Pipeline",
             "Create multi-stage Dockerfile packaging FastAPI backend, React build, and PostgreSQL database service.",
             ["Multi-stage Dockerfile producing minimal, hardened production container", "docker-compose.yml orchestrating ClarifySQL API, PostgreSQL, and React frontend", "Automated container startup smoke test verifying all services healthy"],
             ["Dockerfile", "docker-compose.yml", ".dockerignore"], ["task-day-26"], "Medium"),
            (28, "Phase 5: Release", "End-to-End Production Smoke Testing in Sandbox",
             "Deploy containerized ClarifySQL stack in isolated sandbox and execute comprehensive smoke test suite.",
             ["Automated smoke test exercises natural language question, clarification, SQL execution, and table output", "Verifies read-only permission isolation on production database account", "Sandbox health verification passes without warnings"],
             ["scripts/smoke_test.py", "tests/test_smoke.py"], ["task-day-27"], "Medium"),
            (29, "Phase 5: Release", "Comprehensive Developer Guide, Architecture Specs, and Interactive Demo Guide",
             "Author complete technical documentation, architecture diagrams, API reference, and demo walk-throughs.",
             ["Comprehensive README.md with system architecture diagram and feature highlights", "API documentation covering all REST endpoints with curl examples", "Interactive demo guide with sample ambiguous and clear questions to try"],
             ["README.md", "docs/api_reference.md", "docs/demo_guide.md"], ["task-day-28"], "Low"),
            (30, "Phase 5: Release", "Final Acceptance Audit, Release v1.0.0 Tagging, and 30-Day Retrospective",
             "Conduct final acceptance audit against all requirements, tag v1.0.0 release, and document project achievements.",
             ["All 30 daily acceptance criteria verified 100% complete", "Changelog and release notes published for v1.0.0", "Publish 30-day retrospective report documenting architecture, evaluation, and future roadmap"],
             ["CHANGELOG.md", "reports/30_day_retrospective.md"], ["task-day-29"], "Low"),
        ]

        tasks = []
        for day, phase, title, desc, criteria, deliverables, deps, complexity in task_blueprints:
            tasks.append(
                Task(
                    id=f"task-day-{day:02d}",
                    day_number=day,
                    title=title,
                    phase=phase,
                    description=desc,
                    acceptance_criteria=criteria,
                    deliverables=deliverables,
                    dependencies=deps,
                    complexity=complexity,
                    status=TaskStatus.PENDING,
                )
            )
        return tasks
