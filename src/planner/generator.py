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
            logger.info("Existing roadmap found in state store. Checking for extensions...")
            existing_tasks = self.state_manager.get_all_tasks()
            domain_tasks = self._generate_tailored_domain_tasks()
            if len(domain_tasks) > len(existing_tasks):
                logger.info("Extending roadmap with %d additional milestone(s)...", len(domain_tasks) - len(existing_tasks))
                self.state_manager.save_roadmap(domain_tasks)
                tasks = self.state_manager.get_all_tasks()
            else:
                tasks = existing_tasks
            self.writer.write_roadmap_md(tasks)
            self.writer.write_progress_md(tasks, self.state_manager.get_progress_summary())
            return tasks

        logger.info("Generating new roadmap tailored to '%s'...", self.config.project_name)
        tasks = self._synthesize_tasks()
        self.state_manager.save_roadmap(tasks)
        self.writer.write_roadmap_md(tasks)
        self.writer.write_progress_md(tasks, self.state_manager.get_progress_summary())
        logger.info("Roadmap generated and persisted successfully.")
        return tasks

    def _synthesize_tasks(self) -> List[Task]:
        """Attempt LLM generation, falling back gracefully to domain-specific structured synthesizer."""
        try:
            tasks = self._generate_with_llm()
            if len(tasks) == self.config.project_duration_days:
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

            # Phase 6: Multi-Dialect Support & Advanced Analytics (Days 31–45)
            (31, "Phase 6: Multi-Dialect Support & Advanced Analytics", "SQLite and DuckDB Dialect Adapters and Schema Normalization",
             "Implement pluggable dialect adapter interface supporting SQLite and DuckDB alongside PostgreSQL with schema type normalization.",
             ["Abstract DialectAdapter base class with type translation matrices", "SQLite and DuckDB adapter implementations tested against sample schemas", "Unit tests verifying dialect auto-detection from connection strings"],
             ["src/dialects/base.py", "src/dialects/sqlite_adapter.py", "src/dialects/duckdb_adapter.py", "tests/test_dialects.py"], ["task-day-30"], "Medium"),
            (32, "Phase 6: Multi-Dialect Support & Advanced Analytics", "MySQL Dialect Specialization and Dialect-Specific AST Validation",
             "Add MySQL 8.0+ dialect support and configure sqlglot parser rules for dialect-specific syntax quirks and reserved words.",
             ["MySQL dialect adapter handling backtick identifiers and MySQL date functions", "AST guardrail validator adapted to check statements across all target dialects", "Tests asserting dialect-aware AST validation for PostgreSQL, MySQL, and SQLite"],
             ["src/dialects/mysql_adapter.py", "src/security/dialect_guard.py", "tests/test_dialect_guard.py"], ["task-day-31"], "Medium"),
            (33, "Phase 6: Multi-Dialect Support & Advanced Analytics", "Multi-Database Connection Router and Dynamic Pool Manager",
             "Build connection router allowing queries to execute across configured SQLite, PostgreSQL, or MySQL data sources dynamically.",
             ["Connection registry managing active pools per configured database target", "Header/payload parameter routing queries to specific registered database", "Integration tests asserting dynamic routing between SQLite and PostgreSQL"],
             ["src/db/router.py", "tests/test_db_router.py"], ["task-day-32"], "Medium"),
            (34, "Phase 6: Multi-Dialect Support & Advanced Analytics", "Analytical Window Functions and Ranking SQL Generation",
             "Extend SQL generation prompt and few-shot examples to support window functions: ROW_NUMBER, RANK, DENSE_RANK, and OVER clauses.",
             ["Few-shot window function prompt templates for ranking and partition queries", "Validator rules ensuring window functions execute safely without unbounded memory", "Tests verifying natural queries like 'rank top products by category' generate valid SQL"],
             ["src/engine/window_functions.py", "tests/test_window_functions.py"], ["task-day-33"], "High"),
            (35, "Phase 6: Multi-Dialect Support & Advanced Analytics", "Temporal Analytics: Rolling Averages, Date Truncation, and Intervals",
             "Support natural-language temporal queries generating moving averages, date truncations (DATE_TRUNC), and period-over-period comparisons.",
             ["Temporal prompt module mapping colloquial timeframes ('last quarter', 'year-to-date', '30-day moving average')", "Dialect-aware date arithmetic generator for SQLite, Postgres, and MySQL", "Tests verifying correct date bounds generated for relative time queries"],
             ["src/engine/temporal.py", "tests/test_temporal.py"], ["task-day-34"], "Medium"),
            (36, "Phase 6: Multi-Dialect Support & Advanced Analytics", "Query Cost Estimation and EXPLAIN Plan Complexity Analyzer",
             "Run EXPLAIN queries prior to execution to estimate cost, detect unindexed full table scans, and reject dangerous runaway plans.",
             ["EXPLAIN query planner extracting cost metrics, rows examined, and plan depth", "Cost threshold guardrail rejecting queries exceeding configurable cost limit", "Tests verifying high-cost Cartesian product queries are blocked"],
             ["src/security/explain_analyzer.py", "tests/test_explain_analyzer.py"], ["task-day-35"], "High"),
            (37, "Phase 6: Multi-Dialect Support & Advanced Analytics", "Semantic Schema Tagging and Domain Jargon Synonym Dictionary",
             "Implement synonym dictionary mapping business terminology ('GMV', 'churned', 'top tier') to actual database columns and formulas.",
             ["YAML/JSON-driven domain vocabulary registry mapping business concepts to SQL expressions", "Preprocessor injecting business jargon definitions into LLM prompt context", "Tests asserting 'top GMV customers' maps correctly to SUM(orders.total_amount)"],
             ["src/engine/synonyms.py", "config/business_synonyms.yaml", "tests/test_synonyms.py"], ["task-day-36"], "Medium"),
            (38, "Phase 6: Multi-Dialect Support & Advanced Analytics", "Automated Indexing Advisor Based on Query Workloads",
             "Analyze generated query workloads to detect missing indexes on frequently filtered or joined columns and provide DDL recommendations.",
             ["Workload tracker aggregating WHERE filter and JOIN columns across queries", "Index recommendation engine suggesting single and composite B-tree indexes", "Tests verifying index suggestions generated for slow unindexed filter columns"],
             ["src/engine/index_advisor.py", "tests/test_index_advisor.py"], ["task-day-37"], "Medium"),
            (39, "Phase 6: Multi-Dialect Support & Advanced Analytics", "Query Result Caching Layer with LRU and Schema Invalidation",
             "Implement high-performance query result caching with SHA-256 query hashing, configurable TTL, and cache bypass options.",
             ["In-memory and Redis-compatible cache store with cache hit/miss telemetry", "SHA-256 query hash normalizer ignoring whitespace and casing differences", "Tests asserting second identical query executes with sub-millisecond cache latency"],
             ["src/cache/query_cache.py", "tests/test_query_cache.py"], ["task-day-38"], "Medium"),
            (40, "Phase 6: Multi-Dialect Support & Advanced Analytics", "Streaming Data Exporters: CSV, JSON, and Formatted Excel",
             "Build memory-efficient streaming data export endpoints outputting query results to CSV, JSON Lines, and Excel spreadsheets.",
             ["Streaming response generator yielding chunks to minimize backend memory footprint", "Excel workbook exporter with styled headers and automatic column width sizing", "Unit tests verifying data fidelity across exported CSV, JSON, and Excel outputs"],
             ["src/export/data_exporter.py", "tests/test_data_exporter.py"], ["task-day-39"], "Low"),
            (41, "Phase 6: Multi-Dialect Support & Advanced Analytics", "Natural Language Question Auto-Completion and Suggestions Engine",
             "Implement question suggestion engine providing schema-relevant prompt completions and sample questions based on active database tables.",
             ["Prefix trie and schema-driven query suggestion generator", "GET /api/v1/suggestions endpoint returning recommended query prompts for database schema", "Tests asserting relevant query prompts returned for customer and order entities"],
             ["src/api/suggestions.py", "tests/test_suggestions.py"], ["task-day-40"], "Medium"),
            (42, "Phase 6: Multi-Dialect Support & Advanced Analytics", "Few-Shot Query Memory Bank with Semantic Similarity Search",
             "Store verified, successful query pairs (question -> validated SQL) and retrieve the most relevant few-shot examples dynamically.",
             ["Vector/TF-IDF similarity matcher scoring semantic proximity to user query", "Dynamic few-shot prompt injection ranking top 3 most relevant golden queries", "Tests asserting relevant few-shot examples injected into prompt context"],
             ["src/engine/memory_bank.py", "tests/test_memory_bank.py"], ["task-day-41"], "High"),
            (43, "Phase 6: Multi-Dialect Support & Advanced Analytics", "SQL Query Formatter, Syntax Linter, and Code Beautifier",
             "Integrate SQL formatting and linting utilities producing standardized, indented, readable SQL queries with keyword capitalization.",
             ["SQL formatter wrapping lines, indenting subqueries, and capitalizing keywords (SELECT, FROM, WHERE)", "Linter flagging redundant joins, missing aliases, or unoptimized predicates", "Tests verifying ugly unformatted queries are cleaned and beautified"],
             ["src/engine/sql_formatter.py", "tests/test_sql_formatter.py"], ["task-day-42"], "Low"),
            (44, "Phase 6: Multi-Dialect Support & Advanced Analytics", "Comprehensive Multi-Dialect Integration Test Suite",
             "Run automated end-to-end test suite asserting query generation and execution across PostgreSQL, SQLite, and DuckDB databases.",
             ["End-to-end integration test executing 20 standard business queries across all three dialects", "Assure identical tabular datasets returned across dialects for isomorphic schemas", "Phase 6 integration test pass rate achieves 100%"],
             ["tests/test_multi_dialect_e2e.py"], ["task-day-43"], "Medium"),
            (45, "Phase 6: Multi-Dialect Support & Advanced Analytics", "Phase 6 Milestone Audit and Dialect Architecture Benchmark",
             "Benchmark dialect execution latency, evaluate memory footprint, and publish Phase 6 architecture performance report.",
             ["Benchmark report recording latencies across SQLite, DuckDB, and PostgreSQL engines", "Audit code quality, test coverage, and static type conformance", "Publish Phase 6 milestone documentation and update technical specifications"],
             ["benchmarks/dialect_benchmark.py", "reports/phase_6_audit.md"], ["task-day-44"], "Low"),

            # Phase 7: Enterprise Governance & Security (Days 46–60)
            (46, "Phase 7: Enterprise Governance & Security", "Role-Based Access Control (RBAC) and Table Permissions",
             "Implement fine-grained RBAC restricting which tables and views each user role (admin, analyst, viewer) can query.",
             ["Role permission mapping table defining allowed tables per role", "Security interceptor rejecting queries touching forbidden tables before SQL execution", "Tests asserting analyst role cannot query restricted payroll or credential tables"],
             ["src/security/rbac.py", "tests/test_rbac.py"], ["task-day-45"], "Medium"),
            (47, "Phase 7: Enterprise Governance & Security", "Dynamic Column-Level Data Masking for Sensitive PII",
             "Enforce runtime data masking on sensitive columns (emails, phone numbers, credit cards) based on user role and permissions.",
             ["Data masking policy engine supporting full redaction, email masking, and partial digits (***-**-1234)", "Result transformer applying masks to query result rows dynamically", "Tests asserting unprivileged users receive masked PII values"],
             ["src/security/masking.py", "tests/test_masking.py"], ["task-day-46"], "Medium"),
            (48, "Phase 7: Enterprise Governance & Security", "Row-Level Security (RLS) Filter Injection for Multi-Tenancy",
             "Automatically inject tenant-isolation WHERE clauses (e.g., `tenant_id = ?`) into generated ASTs to prevent multi-tenant data leakage.",
             ["AST rewriter appending mandatory tenant filter conditions to every table in query", "Handles joins, subqueries, and CTEs without bypassing tenant isolation", "Tests verifying tenant filter cannot be bypassed by tricky phrasing"],
             ["src/security/rls_injector.py", "tests/test_rls_injector.py"], ["task-day-47"], "High"),
            (49, "Phase 7: Enterprise Governance & Security", "Immutable Audit Logging for Natural Queries and Executed SQL",
             "Implement structured, append-only security audit log recording every user prompt, generated SQL, execution latency, and actor identity.",
             ["Audit log schema with cryptographic SHA-256 chaining to prevent tampering", "Structured JSON audit event logger with log rotation and retention policies", "Tests verifying audit record written for every accepted and rejected query"],
             ["src/security/audit_logger.py", "tests/test_audit_logger.py"], ["task-day-48"], "Medium"),
            (50, "Phase 7: Enterprise Governance & Security", "Query Anomaly Detection on Latency and Result Volumes",
             "Build anomaly detector identifying suspicious spikes in row volume or abnormal query frequencies indicating data scraping.",
             ["Statistical baseline tracker measuring moving average of row counts and execution duration", "Alert trigger flagging queries returning 10x normal volume", "Tests asserting data egress alert triggers on bulk export queries"],
             ["src/security/anomaly_detector.py", "tests/test_anomaly_detector.py"], ["task-day-49"], "Medium"),
            (51, "Phase 7: Enterprise Governance & Security", "API Rate Limiting and Token Bucket Request Throttling",
             "Add token bucket rate limiter to protect API endpoints against denial-of-service and abusive automated traffic.",
             ["Token bucket rate limiter with sliding window tracking per IP and API key", "HTTP 429 response with Retry-After header and descriptive error payload", "Tests asserting rate limit enforcement under simulated burst traffic"],
             ["src/api/rate_limiter.py", "tests/test_rate_limiter.py"], ["task-day-50"], "Low"),
            (52, "Phase 7: Enterprise Governance & Security", "OAuth2 and JWT Authentication Middleware Integration",
             "Integrate JWT authentication middleware validating bearer tokens, extracting user claims, and establishing request security context.",
             ["JWT validator checking signature, expiration, and issuer claims", "FastAPI dependency injecting AuthenticatedUser into route handlers", "Tests asserting protected endpoints reject unauthenticated or expired tokens"],
             ["src/auth/jwt_handler.py", "src/auth/middleware.py", "tests/test_auth.py"], ["task-day-51"], "Medium"),
            (53, "Phase 7: Enterprise Governance & Security", "Read-Only Database Replica Load Balancing and Health Probes",
             "Implement round-robin connection load balancer across read-only database replicas with automatic unhealthy replica eviction.",
             ["Replica pool manager routing read queries across multiple read replicas", "Periodic background health probe detecting connection lag or network partitions", "Tests asserting queries route to healthy replicas when one node goes offline"],
             ["src/db/replica_pool.py", "tests/test_replica_pool.py"], ["task-day-52"], "Medium"),
            (54, "Phase 7: Enterprise Governance & Security", "Query Complexity Scoring and Maximum Join/Subquery Depth Limits",
             "Calculate static query complexity score based on join count, subquery nesting depth, and aggregation complexity to prevent heavy queries.",
             ["Complexity evaluator inspecting SQL AST and assigning weighted score", "Rejection threshold blocking queries exceeding maximum allowable complexity", "Tests asserting queries with 10+ nested joins are safely rejected with actionable guidance"],
             ["src/security/complexity_scorer.py", "tests/test_complexity_scorer.py"], ["task-day-53"], "Medium"),
            (55, "Phase 7: Enterprise Governance & Security", "Data Lineage Graph: Mapping SQL Columns to Base Schema Tables",
             "Analyze SQL queries to build column-level lineage graph mapping output attributes back to physical source tables and expressions.",
             ["Lineage extractor tracing alias chains and transformations back to root database columns", "Generates JSON data lineage graph indicating source dependencies", "Tests asserting correct source column attribution on multi-table joined queries"],
             ["src/engine/lineage_tracker.py", "tests/test_lineage_tracker.py"], ["task-day-54"], "High"),
            (56, "Phase 7: Enterprise Governance & Security", "Compliance Audit Export Engine (GDPR/HIPAA Data Access Logs)",
             "Provide automated export tools generating audit-ready compliance reports detailing who accessed which tables and sensitive fields.",
             ["Compliance report generator outputting standardized access logs for specified time windows", "Filters logs by user ID, table, or sensitive classification tag", "Tests verifying audit report accuracy against simulated query logs"],
             ["src/export/compliance_exporter.py", "tests/test_compliance_exporter.py"], ["task-day-55"], "Low"),
            (57, "Phase 7: Enterprise Governance & Security", "Secrets Rotation and Environment Credential Isolation",
             "Implement zero-downtime secrets rotation for database passwords, API tokens, and JWT signing keys without service restart.",
             ["Dual-key verification mechanism supporting overlapping key rotation periods", "Secrets reload watcher detecting updated credentials safely", "Tests asserting queries succeed continuously during credential rotation"],
             ["src/core/secrets_manager.py", "tests/test_secrets_manager.py"], ["task-day-56"], "Medium"),
            (58, "Phase 7: Enterprise Governance & Security", "Automated SQL Injection and Security Penetration Test Suite",
             "Execute automated penetration test suite executing 50+ adversarial SQL injection and prompt injection payloads.",
             ["Penetration test suite containing tautology injection, union-based extraction, and stacked statements", "Prompt injection battery attempting system prompt overrides and jailbreaks", "100% of injection attempts safely blocked by guardrails without execution"],
             ["tests/test_penetration_suite.py", "tests/test_prompt_injection.py"], ["task-day-57"], "High"),
            (59, "Phase 7: Enterprise Governance & Security", "Security Regression Benchmark and Vulnerability Assessment Report",
             "Run automated security regression benchmark, verify zero open vulnerabilities, and generate security assessment report.",
             ["Automated security audit generating comprehensive markdown report", "Documents threat modeling, risk mitigations, and penetration test evidence", "Produce security compliance checklist signed off for enterprise deployment"],
             ["reports/security_audit_report.md", "scripts/run_security_benchmark.py"], ["task-day-58"], "Low"),
            (60, "Phase 7: Enterprise Governance & Security", "Phase 7 Milestone Audit and Enterprise Security Certification",
             "Conduct complete Phase 7 milestone audit, verify RBAC, masking, and audit logging, and tag enterprise security milestone.",
             ["Verification that all 15 Phase 7 security criteria pass cleanly", "Audit log retention and masking benchmarks verified", "Publish Phase 7 release notes and update project architecture documentation"],
             ["reports/phase_7_audit.md", "docs/security_architecture.md"], ["task-day-59"], "Low"),

            # Phase 8: Frontend Intelligence & Visualizations (Days 61–75)
            (61, "Phase 8: Frontend Intelligence & Visualizations", "Automatic Chart Recommendation Engine Based on Result Schema",
             "Analyze query result tabular schema, data types, and row cardinalities to recommend the optimal visualization type.",
             ["Heuristic classifier choosing between Bar, Line, Area, Pie, or Table display", "Categorizes columns into dimensions (categorical/temporal) and measures (numeric/aggregations)", "Unit tests verifying time-series data maps to Line charts and category sums to Bar charts"],
             ["frontend/src/utils/chartRecommender.ts", "frontend/src/tests/test_chart_recommender.test.ts"], ["task-day-60"], "Medium"),
            (62, "Phase 8: Frontend Intelligence & Visualizations", "Interactive Recharts Data Visualizations (Bar, Line, Area, Pie)",
             "Build interactive React visualization components using Recharts with tooltips, legends, and responsive auto-sizing.",
             ["ChartContainer component dynamically rendering recommended chart type", "Interactive hover tooltips formatting currency, percentages, and large numbers cleanly", "Component tests verifying chart rendering and legend toggles"],
             ["frontend/src/components/ChartContainer.tsx", "frontend/src/components/MetricCard.tsx"], ["task-day-61"], "Medium"),
            (63, "Phase 8: Frontend Intelligence & Visualizations", "Chart Image and Document Exporter (PNG, SVG, and PDF Reports)",
             "Implement client-side export allowing users to download generated charts as high-resolution PNG, SVG, or printable PDF reports.",
             ["Canvas export utility rendering SVG charts to 300 DPI PNG images", "Download report generator assembling question, SQL preview, chart, and data table into PDF", "Frontend interaction tests verifying export triggers file download without error"],
             ["frontend/src/utils/chartExporter.ts", "frontend/src/components/ExportModal.tsx"], ["task-day-62"], "Low"),
            (64, "Phase 8: Frontend Intelligence & Visualizations", "SQL Query Diff Viewer Highlighting Clarification Impact",
             "Build visual diff viewer comparing original preliminary SQL against refined SQL following user clarification selection.",
             ["Side-by-side or inline diff component highlighting added/modified SQL clauses in green/yellow", "Displays summary explanation of how clarification altered query semantics", "Component tests asserting diff highlights added WHERE or JOIN clauses"],
             ["frontend/src/components/SqlDiffViewer.tsx"], ["task-day-63"], "Medium"),
            (65, "Phase 8: Frontend Intelligence & Visualizations", "Conversational Breadcrumbs and Multi-Branch Exploration UI",
             "Allow users to branch conversations by exploring alternative clarification options without losing prior chat history.",
             ["Conversation tree visualizer allowing rollback or branching from any past turn", "State management storing branched chat turns cleanly in local storage / session", "Tests verifying switching between branches restores respective SQL previews and charts"],
             ["frontend/src/components/BranchExplorer.tsx", "frontend/src/state/conversationStore.ts"], ["task-day-64"], "High"),
            (66, "Phase 8: Frontend Intelligence & Visualizations", "Natural Language Executive Summary Generator for Query Results",
             "Generate automated natural language insights and executive takeaways summarizing query result patterns in plain English.",
             ["Summary engine analyzing tabular results for trends, peaks, anomalies, and top contributors", "Generates concise bulleted executive highlights displayed alongside charts", "Tests asserting correct statistical highlights generated for sales summary queries"],
             ["src/engine/result_summarizer.py", "tests/test_result_summarizer.py"], ["task-day-65"], "Medium"),
            (67, "Phase 8: Frontend Intelligence & Visualizations", "Customizable Analytics Dashboard with Pin-to-Board Widgets",
             "Enable users to pin query cards, charts, and metric counters to a customizable grid dashboard with drag-and-drop layout.",
             ["Dashboard grid component supporting drag-and-drop reordering and resizing", "Persistent dashboard state saving pinned widgets and query configurations", "Component tests verifying adding, removing, and reordering dashboard widgets"],
             ["frontend/src/components/DashboardView.tsx", "frontend/src/components/DashboardWidget.tsx"], ["task-day-66"], "High"),
            (68, "Phase 8: Frontend Intelligence & Visualizations", "Accessible Theme Switcher: Dark/Light Mode and WCAG Contrast",
             "Implement accessible theme manager supporting system preference detection, smooth dark/light transitions, and WCAG AA contrast.",
             ["Tailwind CSS dark mode integration with high-contrast color tokens for data visualizations", "Accessible focus indicators and ARIA roles across all interactive controls", "Accessibility test suite validating WCAG 2.1 AA compliance across UI components"],
             ["frontend/src/theme/ThemeProvider.tsx", "frontend/src/components/ThemeToggle.tsx"], ["task-day-67"], "Low"),
            (69, "Phase 8: Frontend Intelligence & Visualizations", "Power-User Keyboard Navigation and Command Palette (Ctrl+K)",
             "Build fast command palette allowing power users to search query history, switch databases, run common queries, and navigate via keyboard.",
             ["Command palette modal triggered via Ctrl+K / Cmd+K with fuzzy search", "Keyboard navigation supporting Arrow keys, Enter selection, and Escape dismissal", "Component tests verifying quick actions execute correctly from command palette"],
             ["frontend/src/components/CommandPalette.tsx"], ["task-day-68"], "Medium"),
            (70, "Phase 8: Frontend Intelligence & Visualizations", "Shareable Query Snapshots with Encrypted URL State Tokens",
             "Generate shareable URL links containing compressed, encrypted query states allowing colleagues to view identical SQL and results.",
             ["Base64 URL-safe compressor encoding query parameters, selected options, and chart types", "Shared view mode rendering read-only snapshot view for external viewers", "Tests asserting encoded URL faithfully reconstructs complete query context"],
             ["frontend/src/utils/shareableUrl.ts", "frontend/src/components/SharedSnapshotView.tsx"], ["task-day-69"], "Medium"),
            (71, "Phase 8: Frontend Intelligence & Visualizations", "Query Latency Waterfall and Execution Performance Profiler UI",
             "Display visual breakdown of query latency showing time spent in LLM generation, AST validation, database execution, and rendering.",
             ["Waterfall timing bar component visualizing duration of each execution stage", "Highlights bottlenecks (e.g. slow database scan vs LLM token generation latency)", "Component tests asserting correct latency segmentation display"],
             ["frontend/src/components/LatencyProfiler.tsx"], ["task-day-70"], "Low"),
            (72, "Phase 8: Frontend Intelligence & Visualizations", "Streaming Query Execution Progress with Server-Sent Events (SSE)",
             "Stream real-time execution phases (Validating -> Generating -> Executing -> Profiling) to frontend via SSE stream.",
             ["FastAPI SSE endpoint streaming lifecycle event payloads to client", "React hook consuming event stream and updating step progress indicator smoothly", "Tests verifying client receives lifecycle events in proper sequence"],
             ["src/api/streaming.py", "frontend/src/hooks/useExecutionStream.ts", "tests/test_streaming.py"], ["task-day-71"], "Medium"),
            (73, "Phase 8: Frontend Intelligence & Visualizations", "Frontend Component Integration and Automated User Journey Tests",
             "Build comprehensive frontend interaction test suite simulating natural query input, clarification selection, and chart toggles.",
             ["Test suite exercising full user journey from empty state to interactive chart visualization", "Verifies error state recovery when server returns 500 or validation errors", "100% test pass rate across all frontend component tests"],
             ["frontend/src/tests/userJourney.test.tsx"], ["task-day-72"], "Medium"),
            (74, "Phase 8: Frontend Intelligence & Visualizations", "Virtualized Table Rendering for High-Volume Datasets (10k+ Rows)",
             "Integrate virtual scrolling for data tables rendering tens of thousands of rows smoothly at 60 FPS without DOM bloat.",
             ["Windowing virtualization component rendering only visible DOM nodes", "Smooth scroll performance with fixed header and resizable column widths", "Performance test asserting sub-16ms frame render times on 10,000 row dataset"],
             ["frontend/src/components/VirtualizedTable.tsx"], ["task-day-73"], "Medium"),
            (75, "Phase 8: Frontend Intelligence & Visualizations", "Phase 8 Milestone Audit and Frontend Usability Evaluation",
             "Conduct Phase 8 audit reviewing UI responsiveness, visualization fidelity, and accessibility compliance benchmarks.",
             ["Lighthouse performance audit achieving 95+ score across Performance, Accessibility, and Best Practices", "Documentation of visualization components, props, and theme guidelines", "Publish Phase 8 milestone sign-off and retrospective"],
             ["reports/phase_8_audit.md", "docs/frontend_design_system.md"], ["task-day-74"], "Low"),

            # Phase 9: Production Scalability, MLOps & Autonomous Reliability (Days 76–90)
            (76, "Phase 9: Production Scalability & Autonomous Reliability", "Multi-LLM Dynamic Routing and Latency-Based Failover",
             "Implement dynamic LLM provider router falling back across Gemini, Anthropic, and OpenAI based on health and latency probes.",
             ["Provider router maintaining active circuit state and rolling latency percentiles", "Automatic fallback to secondary provider when primary returns 429, 503, or times out", "Tests asserting graceful fallback execution when primary provider mock simulates downtime"],
             ["src/llm/dynamic_router.py", "tests/test_dynamic_router.py"], ["task-day-75"], "High"),
            (77, "Phase 9: Production Scalability & Autonomous Reliability", "Prompt Drift Detection and Output Conformance Telemetry",
             "Monitor model output syntax and adherence over time to detect LLM prompt drift or unexpected degradation in SQL validity.",
             ["Drift telemetry collector tracking syntax error rate and retry counts per model version", "Automated alert triggered when error rate exceeds 5% statistical threshold", "Tests asserting drift alert fires under elevated synthetic error conditions"],
             ["src/monitoring/drift_detector.py", "tests/test_drift_detector.py"], ["task-day-76"], "Medium"),
            (78, "Phase 9: Production Scalability & Autonomous Reliability", "Prometheus Metrics Exporter for System and Query Telemetry",
             "Expose Prometheus metrics endpoint (`/metrics`) instrumenting query throughput, latencies, cache ratios, and error counts.",
             ["Prometheus counter, histogram, and gauge metrics instrumenting all critical code paths", "Standardized labels: database_type, model_provider, status, user_role", "Tests asserting `/metrics` endpoint returns valid Prometheus text format"],
             ["src/monitoring/prometheus_exporter.py", "tests/test_metrics.py"], ["task-day-77"], "Low"),
            (79, "Phase 9: Production Scalability & Autonomous Reliability", "Pre-Configured Grafana Dashboard for Operational Telemetry",
             "Author complete Grafana dashboard JSON visualizing system KPIs: query volume, p95 latencies, error rates, and cache hits.",
             ["Production-ready Grafana dashboard configuration JSON with panel templates", "Visual alerts for error spikes, high query latency, and database pool exhaustion", "Verification that dashboard imports and renders all metrics cleanly"],
             ["monitoring/grafana_dashboard.json", "docs/observability_guide.md"], ["task-day-78"], "Low"),
            (80, "Phase 9: Production Scalability & Autonomous Reliability", "OpenTelemetry Distributed Tracing across API, Engine, and DB",
             "Implement OpenTelemetry tracing attaching distributed trace and span IDs to HTTP requests, LLM calls, and database transactions.",
             ["Tracer instrumentation creating child spans for prompt synthesis, AST parsing, and DB execution", "Context propagation injecting trace headers for end-to-end distributed tracing", "Tests verifying trace spans recorded with proper durations and tags"],
             ["src/monitoring/tracer.py", "tests/test_tracer.py"], ["task-day-79"], "Medium"),
            (81, "Phase 9: Production Scalability & Autonomous Reliability", "Circuit Breakers and Graceful Degradation for External Dependencies",
             "Implement circuit breaker pattern for external database connections, LLM APIs, and cache clusters to prevent cascading failures.",
             ["Circuit breaker with CLOSED, OPEN, and HALF-OPEN state machine transitions", "Graceful fallback responses returning clear status messages during dependency outages", "Tests asserting circuit opens after 3 consecutive failures and recovers on success"],
             ["src/core/circuit_breaker.py", "tests/test_circuit_breaker.py"], ["task-day-80"], "Medium"),
            (82, "Phase 9: Production Scalability & Autonomous Reliability", "High-Concurrency Stress Testing with Locust (100+ Concurrent Queries)",
             "Build and execute high-concurrency stress test suite using Locust simulating 100 simultaneous users asking natural queries.",
             ["Locust load testing scenario file with realistic user think times and query distributions", "Load test execution asserting 0% HTTP 5xx error rate at 100 concurrent simulated users", "Produces load test benchmark report documenting throughput (RPS) and p99 latency"],
             ["benchmarks/locustfile.py", "reports/load_test_results.md"], ["task-day-81"], "High"),
            (83, "Phase 9: Production Scalability & Autonomous Reliability", "Async Event Loop Profiling and Memory Footprint Optimization",
             "Profile FastAPI async event loop to identify blocking calls, optimize connection pool sizing, and minimize memory leaks.",
             ["Event loop profiler flagging synchronous CPU-bound operations in async handlers", "Optimized database driver configuration and connection pool reuse", "Tests verifying steady-state memory utilization remains flat under continuous queries"],
             ["scripts/profile_event_loop.py", "tests/test_concurrency.py"], ["task-day-82"], "Medium"),
            (84, "Phase 9: Production Scalability & Autonomous Reliability", "Kubernetes Helm Charts and Multi-Environment Production Manifests",
             "Create production-ready Kubernetes Helm chart packaging FastAPI backend, React frontend, ingress, and config maps.",
             ["Helm chart with values.yaml supporting dev, staging, and production environments", "Horizontal Pod Autoscaler (HPA) manifest scaling pods based on CPU/memory utilization", "Kubernetes dry-run lint test verifying manifest syntax and security context"],
             ["deploy/helm/Chart.yaml", "deploy/helm/values.yaml", "deploy/helm/templates/deployment.yaml"], ["task-day-83"], "Medium"),
            (85, "Phase 9: Production Scalability & Autonomous Reliability", "Automated Database Migration Pipeline with Alembic Versioning",
             "Set up Alembic database migration environment managing relational schema evolution across development and production.",
             ["Alembic configuration and env.py targeting configured database engine dynamically", "Baseline migration generating all domain tables with rollback support", "Tests asserting migrations apply and revert cleanly without data loss"],
             ["alembic.ini", "alembic/env.py", "alembic/versions/001_initial_schema.py", "tests/test_migrations.py"], ["task-day-84"], "Medium"),
            (86, "Phase 9: Production Scalability & Autonomous Reliability", "Continuous Synthetic Query Probes and Alert Webhook Integrations",
             "Build synthetic health probe continuously executing canary queries every 5 minutes and dispatching alerts to Slack/Discord webhooks.",
             ["Canary query runner verifying end-to-end pipeline health on automated cadence", "Alert dispatcher formatting rich Markdown/Slack alert cards on probe failure", "Tests asserting webhook dispatched when canary query encounters synthetic failure"],
             ["scripts/canary_probe.py", "src/notifications/alert_dispatcher.py", "tests/test_canary.py"], ["task-day-85"], "Low"),
            (87, "Phase 9: Production Scalability & Autonomous Reliability", "End-to-End System Soak Testing and Resilience Verification",
             "Execute 12-hour continuous soak test subjecting system to constant stream of varied natural-language queries without crash.",
             ["Automated soak test harness running continuous query cycles", "Monitors for memory leaks, connection exhaustion, and unbounded cache growth", "Soak test summary report certifying system stability under sustained operational load"],
             ["scripts/soak_test.py", "reports/soak_test_report.md"], ["task-day-86"], "High"),
            (88, "Phase 9: Production Scalability & Autonomous Reliability", "Complete v2.0 Developer Documentation and Architecture Manual",
             "Author exhaustive system architecture manual, operational runbooks, and developer extension guides for ClarifySQL v2.0.",
             ["Architecture guide detailing multi-dialect engine, security guardrails, and visualization pipeline", "Operational runbook with troubleshooting procedures for common production alerts", "API documentation and developer guide for creating custom dialect adapters"],
             ["docs/architecture_v2.md", "docs/operations_runbook.md", "docs/dialect_authoring_guide.md"], ["task-day-87"], "Low"),
            (89, "Phase 9: Production Scalability & Autonomous Reliability", "Pre-Release Quality Sign-Off and Benchmark Regression Gate",
             "Execute full quality gate: 100% test pass rate across all unit and integration suites, zero security vulnerabilities, and lint pass.",
             ["Automated pre-release audit verifying 100% test pass rate across backend and frontend", "Regression benchmark asserting zero accuracy degradation compared to v1.0.0", "Publish pre-release verification checklist signed off for production"],
             ["reports/pre_release_audit.md", "scripts/pre_release_gate.py"], ["task-day-88"], "Medium"),
            (90, "Phase 9: Production Scalability & Autonomous Reliability", "Final 90-Day Retrospective, Release v2.0.0 Tagging, and Streak Milestone",
             "Conduct comprehensive 90-day project retrospective, tag v2.0.0 production release, and document engineering milestones.",
             ["All 90 daily acceptance criteria verified 100% complete", "Changelog and release notes published for v2.0.0 major release", "Publish 90-day retrospective documenting full system evolution, streak achievements, and future roadmap"],
             ["CHANGELOG.md", "reports/90_day_retrospective.md"], ["task-day-89"], "Low"),
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
