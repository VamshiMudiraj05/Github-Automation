# 🗺️ 90-Day Engineering Roadmap: ClarifySQL: Text-to-SQL with a Clarification Engine

> **Project Objective:** A production-minded, portfolio-quality application that converts natural-language questions into accurate SQL queries, detects ambiguity, asks users targeted clarification questions, validates generated SQL, executes safe read-only queries, and presents results in an interactive interface.
> **Start Date:** 2026-10-24 | **Schedule:** Daily at 06:17 (Asia/Kolkata)
> **Overall Progress:** 0/90 Days Completed (0.0%)

## 📊 Progress Overview

| Phase | Days | Focus Area | Status |
| :--- | :--- | :--- | :--- |
| **Phase 1: Foundation** | Days 1–5 | Requirements, Acceptance Criteria, Architecture, and Sy | Planned |
| **Phase 2: Core Functionality** | Days 6–12 | LLM Provider Interface and Structured Response Schemas | Planned |
| **Phase 3: Clarification & State** | Days 13–19 | Conversation State Manager Preserving Clarification Tur | Planned |
| **Phase 4: Evaluation, Hardening & Integration** | Days 20–25 | Full Frontend-Backend API Integration and User Journey  | Planned |
| **Phase 5: Release** | Days 26–30 | Production Deployment Configuration and Environment Set | Planned |
| **Phase 6: Multi-Dialect Support & Advanced Analytics** | Days 31–45 | SQLite and DuckDB Dialect Adapters and Schema Normaliza | Planned |
| **Phase 7: Enterprise Governance & Security** | Days 46–60 | Role-Based Access Control (RBAC) and Table Permissions | Planned |
| **Phase 8: Frontend Intelligence & Visualizations** | Days 61–75 | Automatic Chart Recommendation Engine Based on Result S | Planned |
| **Phase 9: Production Scalability & Autonomous Reliability** | Days 76–90 | Multi-LLM Dynamic Routing and Latency-Based Failover | Planned |

---

## 🗓️ Detailed 90-Day Milestone Breakdown

### Phase 1: Foundation

#### Day 01: Requirements, Acceptance Criteria, Architecture, and Synthetic Database Domain — ⚪ Planned
- **Description:** Define ClarifySQL system requirements, architecture specifications, and synthetic e-commerce database schema contracts.
- **Complexity:** `Low` | **Dependencies:** `None`
- **Acceptance Criteria:**
  - [ ] Specify schema entity-relationship model (customers, orders, products, order_items)
  - [ ] Document clarification engine state machine and ambiguity trigger thresholds
  - [ ] Define read-only safety guardrails, timeouts, and AST validation specifications
- **Key Deliverables:**
  - `docs/architecture.md`
  - `docs/requirements.md`
  - `docs/domain_schema.md`

#### Day 02: Project Scaffolding, Python/FastAPI Environment, PostgreSQL Config, and React Layout — ⚪ Planned
- **Description:** Initialize backend project layout with FastAPI and Pydantic v2, PostgreSQL connection driver, and React frontend scaffolding.
- **Complexity:** `Low` | **Dependencies:** `task-day-01`
- **Acceptance Criteria:**
  - [ ] FastAPI application skeleton with structured config management
  - [ ] Pydantic v2 settings loading database credentials from environment
  - [ ] React frontend scaffolding initialized with Tailwind CSS configuration
- **Key Deliverables:**
  - `src/core/config.py`
  - `src/main.py`
  - `frontend/package.json`
  - `frontend/src/App.tsx`

#### Day 03: Synthetic Database Domain: Customers, Orders, Products, and Realistic Seed Data — ⚪ Planned
- **Description:** Create relational schemas for customers, products, orders, and order_items with realistic sample data for text-to-sql evaluation.
- **Complexity:** `Medium` | **Dependencies:** `task-day-02`
- **Acceptance Criteria:**
  - [ ] SQLAlchemy models defined with primary keys, foreign keys, and indexes
  - [ ] Synthetic seed generator populates realistic customers, products, orders, and line items
  - [ ] Unit test verifies relational integrity and seed data consistency
- **Key Deliverables:**
  - `src/db/models.py`
  - `src/db/seed_data.py`
  - `tests/test_seed_data.py`

#### Day 04: Database Connection Management, Session Pooling, and Schema Introspection — ⚪ Planned
- **Description:** Implement robust database session management and automatic schema reflection extracting table names, columns, and data types.
- **Complexity:** `Medium` | **Dependencies:** `task-day-03`
- **Acceptance Criteria:**
  - [ ] Thread-safe engine pool with read-only execution session factory
  - [ ] Schema introspector extracts tables, columns, foreign keys, and sample distinct values
  - [ ] Tests verify schema reflection accurately matches database catalog
- **Key Deliverables:**
  - `src/db/connection.py`
  - `src/db/introspector.py`
  - `tests/test_introspector.py`

#### Day 05: Backend Configuration Validation, Health Endpoints, and Baseline Test Suite — ⚪ Planned
- **Description:** Add comprehensive health check endpoints, configuration sanity checks, and automated baseline pytest suite.
- **Complexity:** `Low` | **Dependencies:** `task-day-04`
- **Acceptance Criteria:**
  - [ ] GET /health endpoint reporting database ping latency and schema readiness
  - [ ] Configuration validator checking model API keys and connection parameters
  - [ ] Pytest suite executes and passes 100% on Phase 1 modules
- **Key Deliverables:**
  - `src/api/health.py`
  - `tests/test_health.py`
  - `tests/test_config.py`

### Phase 2: Core Functionality

#### Day 06: LLM Provider Interface and Structured Response Schemas — ⚪ Planned
- **Description:** Implement pluggable LLM provider abstraction supporting Gemini and OpenAI with structured JSON response schemas.
- **Complexity:** `Medium` | **Dependencies:** `task-day-05`
- **Acceptance Criteria:**
  - [ ] Pydantic models for SQLGenerationResponse, AmbiguityCheck, and ClarificationPrompt
  - [ ] Gemini and OpenAI provider implementations with exponential backoff
  - [ ] Unit tests verifying JSON response parsing and schema conformance
- **Key Deliverables:**
  - `src/llm/provider.py`
  - `src/llm/schemas.py`
  - `tests/test_llm_provider.py`

#### Day 07: Schema-Aware SQL Generation Engine — ⚪ Planned
- **Description:** Build prompt synthesis pipeline injecting introspected database schema, foreign keys, and constraints into LLM context.
- **Complexity:** `Medium` | **Dependencies:** `task-day-06`
- **Acceptance Criteria:**
  - [ ] Dynamic prompt builder formatting schema catalog into compact model context
  - [ ] Generates standard SQL queries adhering to database dialect without hallucinations
  - [ ] Unit tests verifying correct table joins on multi-table queries
- **Key Deliverables:**
  - `src/engine/sql_generator.py`
  - `tests/test_sql_generator.py`

#### Day 08: SQL Parsing, Read-Only Query Validation, and Query Limits — ⚪ Planned
- **Description:** Implement strict AST-based SQL validator enforcing read-only SELECT/CTE queries and blocking DDL/DML.
- **Complexity:** `High` | **Dependencies:** `task-day-07`
- **Acceptance Criteria:**
  - [ ] SQL AST parser rejects INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE
  - [ ] Blocks stacked queries, dangerous functions, and unauthorized system tables
  - [ ] Enforces statement limit (LIMIT 100) and query complexity checks
- **Key Deliverables:**
  - `src/security/sql_guard.py`
  - `tests/test_sql_guard.py`

#### Day 09: Safe Query Execution Engine and Tabular Result Serialization — ⚪ Planned
- **Description:** Execute validated queries under statement timeouts, serialize results to JSON tables, and compute column metadata.
- **Complexity:** `Medium` | **Dependencies:** `task-day-08`
- **Acceptance Criteria:**
  - [ ] Read-only database transaction execution with strict timeout (5 seconds)
  - [ ] Serializes rows and columns into JSON table structure with row count and duration
  - [ ] Error interceptor converting database exceptions into readable user messages
- **Key Deliverables:**
  - `src/engine/query_executor.py`
  - `tests/test_query_executor.py`

#### Day 10: Test Clear Questions, Invalid Queries, and Unsupported Requests — ⚪ Planned
- **Description:** Build rigorous test suite covering unambiguous questions, syntactic errors, and out-of-domain requests.
- **Complexity:** `Medium` | **Dependencies:** `task-day-09`
- **Acceptance Criteria:**
  - [ ] End-to-end tests for simple and aggregated clear questions (e.g. 'total sales in 2024')
  - [ ] Tests verifying rejection of malicious queries like 'DROP TABLE customers'
  - [ ] Negative tests handling unsupported queries with graceful error responses
- **Key Deliverables:**
  - `tests/test_clear_questions.py`
  - `tests/test_security_rejection.py`

#### Day 11: Ambiguity Detection and Clarification-State Models — ⚪ Planned
- **Description:** Implement ambiguity analyzer detecting underspecified metrics, missing time ranges, or multiple ranking criteria.
- **Complexity:** `High` | **Dependencies:** `task-day-10`
- **Acceptance Criteria:**
  - [ ] Ambiguity classifier determining if question requires user clarification
  - [ ] Identifies specific ambiguity type: ranking criteria, date range, entity filter
  - [ ] Tests verify clear questions are not unnecessarily flagged as ambiguous
- **Key Deliverables:**
  - `src/engine/ambiguity_detector.py`
  - `tests/test_ambiguity_detector.py`

#### Day 12: Targeted Clarification Question Generator with Selectable Options — ⚪ Planned
- **Description:** Generate one concise, targeted clarification question with 2-4 distinct selectable options when ambiguity is detected.
- **Complexity:** `Medium` | **Dependencies:** `task-day-11`
- **Acceptance Criteria:**
  - [ ] Clarification generator outputs clear question and structured choice options
  - [ ] Example: 'Show top customers' -> choices: Total Spending, Order Count, Recent Activity
  - [ ] Tests confirm concise wording and mutually exclusive options
- **Key Deliverables:**
  - `src/engine/clarification_generator.py`
  - `tests/test_clarification_generator.py`

### Phase 3: Clarification & State

#### Day 13: Conversation State Manager Preserving Clarification Turns — ⚪ Planned
- **Description:** Build stateful conversation store preserving original user question, detected ambiguities, and user answers.
- **Complexity:** `Medium` | **Dependencies:** `task-day-12`
- **Acceptance Criteria:**
  - [ ] Session state store caching multi-turn dialogue history with TTL cleanup
  - [ ] ConversationTurn model linking question, clarification options, and selection
  - [ ] Integration tests verifying conversation state persistence across turns
- **Key Deliverables:**
  - `src/engine/conversation.py`
  - `tests/test_conversation.py`

#### Day 14: Clarification-Informed SQL Regeneration — ⚪ Planned
- **Description:** Incorporate user clarification choice into the SQL generator prompt to produce accurate, tailored queries.
- **Complexity:** `Medium` | **Dependencies:** `task-day-13`
- **Acceptance Criteria:**
  - [ ] Prompt pipeline augments schema and original question with selected clarification
  - [ ] Generates refined SQL directly matching the clarified user intent
  - [ ] Tests verify generated SQL reflects the clarified metric (e.g. SUM(total_amount))
- **Key Deliverables:**
  - `src/engine/sql_regenerator.py`
  - `tests/test_sql_regenerator.py`

#### Day 15: Test Suite for Ambiguous, Underspecified, and Clear Questions — ⚪ Planned
- **Description:** Comprehensive automated test matrix asserting correct routing between direct execution and clarification flow.
- **Complexity:** `Medium` | **Dependencies:** `task-day-14`
- **Acceptance Criteria:**
  - [ ] Tests asserting clarification triggers on underspecified ranking requests
  - [ ] Tests asserting direct execution on fully specified date-filtered queries
  - [ ] Verification that default assumptions are explicitly documented when no clarification is needed
- **Key Deliverables:**
  - `tests/test_clarification_workflow.py`

#### Day 16: React Chat Interface and Question Submission Workflow — ⚪ Planned
- **Description:** Build modern, responsive React chat interface with Tailwind CSS for natural language question input.
- **Complexity:** `Medium` | **Dependencies:** `task-day-15`
- **Acceptance Criteria:**
  - [ ] Clean chat message timeline supporting user questions and assistant responses
  - [ ] Input box with auto-focus, send button, and keyboard shortcut (Enter)
  - [ ] Component tests asserting input handling and loading state transitions
- **Key Deliverables:**
  - `frontend/src/components/ChatTimeline.tsx`
  - `frontend/src/components/QuestionInput.tsx`

#### Day 17: Interactive Clarification Option Controls and Turn History — ⚪ Planned
- **Description:** Render clickable clarification option buttons within the chat stream allowing 1-click option selection.
- **Complexity:** `Medium` | **Dependencies:** `task-day-16`
- **Acceptance Criteria:**
  - [ ] ClarificationCard component rendering option pills/buttons for user selection
  - [ ] Disables choices once answered and updates conversation timeline seamlessly
  - [ ] Frontend interaction tests verifying choice submission callback
- **Key Deliverables:**
  - `frontend/src/components/ClarificationCard.tsx`
  - `frontend/src/components/HistorySidebar.tsx`

#### Day 18: SQL Preview Modal, Plain-English Explanations, and Tabular Results — ⚪ Planned
- **Description:** Display formatted SQL preview with syntax highlighting, plain-English explanation, and interactive data table.
- **Complexity:** `Medium` | **Dependencies:** `task-day-17`
- **Acceptance Criteria:**
  - [ ] SqlPreview component with copy-to-clipboard and syntax highlighting
  - [ ] QueryExplanation card detailing why the query was constructed that way
  - [ ] ResultTable component with pagination, sortable columns, and row counts
- **Key Deliverables:**
  - `frontend/src/components/SqlPreview.tsx`
  - `frontend/src/components/ResultTable.tsx`

#### Day 19: Responsive UI Polish, Skeleton Loading States, and Error Banners — ⚪ Planned
- **Description:** Implement polished dark-mode styling, loading skeletons during SQL execution, and actionable error toasts.
- **Complexity:** `Low` | **Dependencies:** `task-day-18`
- **Acceptance Criteria:**
  - [ ] Skeleton placeholders for SQL generation and data table loading states
  - [ ] Error banner explaining syntax or security policy rejections clearly
  - [ ] Responsive mobile-friendly drawer and desktop side-by-side view
- **Key Deliverables:**
  - `frontend/src/components/ErrorBanner.tsx`
  - `frontend/src/components/LoadingSkeleton.tsx`

### Phase 4: Evaluation, Hardening & Integration

#### Day 20: Full Frontend-Backend API Integration and User Journey Test — ⚪ Planned
- **Description:** Connect React frontend with FastAPI backend endpoints over HTTP and test complete clarification journey.
- **Complexity:** `High` | **Dependencies:** `task-day-19`
- **Acceptance Criteria:**
  - [ ] POST /api/v1/query endpoint handling initial question, ambiguity, and clarification
  - [ ] End-to-end integration test asserting full question -> clarify -> execute flow
  - [ ] CORS and API client error handling verified
- **Key Deliverables:**
  - `src/api/routes.py`
  - `tests/test_api_integration.py`

#### Day 21: Representative Text-to-SQL Benchmark Dataset — ⚪ Planned
- **Description:** Curate benchmark suite of 50 diverse e-commerce questions across simple, multi-join, ambiguous, and edge cases.
- **Complexity:** `Medium` | **Dependencies:** `task-day-20`
- **Acceptance Criteria:**
  - [ ] Benchmark dataset JSON containing questions, expected tables, and golden SQL
  - [ ] Categories covering simple lookups, aggregations, multi-table joins, and ambiguous prompts
  - [ ] Automated dataset loader and test runner
- **Key Deliverables:**
  - `benchmarks/dataset.json`
  - `benchmarks/evaluator.py`

#### Day 22: Execution Accuracy and Clarification Effectiveness Measurement — ⚪ Planned
- **Description:** Run automated evaluation computing exact-match accuracy, execution accuracy, and ambiguity recall.
- **Complexity:** `High` | **Dependencies:** `task-day-21`
- **Acceptance Criteria:**
  - [ ] Evaluation script calculates execution accuracy (% of queries producing identical results)
  - [ ] Measures clarification precision: does the engine ask questions only when needed?
  - [ ] Generates benchmark evaluation report in Markdown
- **Key Deliverables:**
  - `benchmarks/run_eval.py`
  - `reports/evaluation_results.md`

#### Day 23: Prompt Engineering Improvements and Failure Analysis — ⚪ Planned
- **Description:** Analyze failed benchmark questions to refine schema prompts, few-shot examples, and ambiguity triggers.
- **Complexity:** `Medium` | **Dependencies:** `task-day-22`
- **Acceptance Criteria:**
  - [ ] Incorporate few-shot representative join examples into generator prompt
  - [ ] Fine-tune ambiguity detection thresholds to minimize false positive clarifications
  - [ ] Re-run benchmarks demonstrating measurable accuracy improvement
- **Key Deliverables:**
  - `src/engine/prompts.py`
  - `tests/test_prompt_improvements.py`

#### Day 24: Database Security Audit, Parameterization, and Vulnerability Scan — ⚪ Planned
- **Description:** Audit SQL security rules, enforce parameterized execution for literals, and run dependency audit.
- **Complexity:** `Medium` | **Dependencies:** `task-day-23`
- **Acceptance Criteria:**
  - [ ] Verify parameterization of user-supplied filter constants to prevent SQL injection
  - [ ] Audit query timeout enforcement preventing Denial-of-Service on heavy scans
  - [ ] Run security audit verifying zero high/critical vulnerabilities
- **Key Deliverables:**
  - `src/security/sanitizer.py`
  - `tests/test_security_audit.py`

#### Day 25: Full Regression Testing and Defect Resolution — ⚪ Planned
- **Description:** Execute full regression test suite across backend API, database engine, guardrails, and frontend mocks.
- **Complexity:** `Medium` | **Dependencies:** `task-day-24`
- **Acceptance Criteria:**
  - [ ] 100% test pass rate across all backend unit and integration test suites
  - [ ] Resolve all outstanding edge-case defects identified during evaluation
  - [ ] Produce quality and reliability sign-off checklist
- **Key Deliverables:**
  - `tests/test_full_regression.py`
  - `reports/quality_audit.md`

### Phase 5: Release

#### Day 26: Production Deployment Configuration and Environment Setup — ⚪ Planned
- **Description:** Configure production environment profiles, database connection pooling, and Gunicorn/Uvicorn workers.
- **Complexity:** `Low` | **Dependencies:** `task-day-25`
- **Acceptance Criteria:**
  - [ ] Production settings profile with strict environment variable validation
  - [ ] Production ASGI server configuration with optimized worker processes
  - [ ] Configuration tests validating production parameters
- **Key Deliverables:**
  - `src/core/prod_config.py`
  - `tests/test_prod_config.py`

#### Day 27: Containerization: Multi-Stage Dockerfile & Docker Compose Pipeline — ⚪ Planned
- **Description:** Create multi-stage Dockerfile packaging FastAPI backend, React build, and PostgreSQL database service.
- **Complexity:** `Medium` | **Dependencies:** `task-day-26`
- **Acceptance Criteria:**
  - [ ] Multi-stage Dockerfile producing minimal, hardened production container
  - [ ] docker-compose.yml orchestrating ClarifySQL API, PostgreSQL, and React frontend
  - [ ] Automated container startup smoke test verifying all services healthy
- **Key Deliverables:**
  - `Dockerfile`
  - `docker-compose.yml`
  - `.dockerignore`

#### Day 28: End-to-End Production Smoke Testing in Sandbox — ⚪ Planned
- **Description:** Deploy containerized ClarifySQL stack in isolated sandbox and execute comprehensive smoke test suite.
- **Complexity:** `Medium` | **Dependencies:** `task-day-27`
- **Acceptance Criteria:**
  - [ ] Automated smoke test exercises natural language question, clarification, SQL execution, and table output
  - [ ] Verifies read-only permission isolation on production database account
  - [ ] Sandbox health verification passes without warnings
- **Key Deliverables:**
  - `scripts/smoke_test.py`
  - `tests/test_smoke.py`

#### Day 29: Comprehensive Developer Guide, Architecture Specs, and Interactive Demo Guide — ⚪ Planned
- **Description:** Author complete technical documentation, architecture diagrams, API reference, and demo walk-throughs.
- **Complexity:** `Low` | **Dependencies:** `task-day-28`
- **Acceptance Criteria:**
  - [ ] Comprehensive README.md with system architecture diagram and feature highlights
  - [ ] API documentation covering all REST endpoints with curl examples
  - [ ] Interactive demo guide with sample ambiguous and clear questions to try
- **Key Deliverables:**
  - `README.md`
  - `docs/api_reference.md`
  - `docs/demo_guide.md`

#### Day 30: Final Acceptance Audit, Release v1.0.0 Tagging, and 30-Day Retrospective — ⚪ Planned
- **Description:** Conduct final acceptance audit against all requirements, tag v1.0.0 release, and document project achievements.
- **Complexity:** `Low` | **Dependencies:** `task-day-29`
- **Acceptance Criteria:**
  - [ ] All 30 daily acceptance criteria verified 100% complete
  - [ ] Changelog and release notes published for v1.0.0
  - [ ] Publish 30-day retrospective report documenting architecture, evaluation, and future roadmap
- **Key Deliverables:**
  - `CHANGELOG.md`
  - `reports/30_day_retrospective.md`

### Phase 6: Multi-Dialect Support & Advanced Analytics

#### Day 31: SQLite and DuckDB Dialect Adapters and Schema Normalization — ⚪ Planned
- **Description:** Implement pluggable dialect adapter interface supporting SQLite and DuckDB alongside PostgreSQL with schema type normalization.
- **Complexity:** `Medium` | **Dependencies:** `task-day-30`
- **Acceptance Criteria:**
  - [ ] Abstract DialectAdapter base class with type translation matrices
  - [ ] SQLite and DuckDB adapter implementations tested against sample schemas
  - [ ] Unit tests verifying dialect auto-detection from connection strings
- **Key Deliverables:**
  - `src/dialects/base.py`
  - `src/dialects/sqlite_adapter.py`
  - `src/dialects/duckdb_adapter.py`
  - `tests/test_dialects.py`

#### Day 32: MySQL Dialect Specialization and Dialect-Specific AST Validation — ⚪ Planned
- **Description:** Add MySQL 8.0+ dialect support and configure sqlglot parser rules for dialect-specific syntax quirks and reserved words.
- **Complexity:** `Medium` | **Dependencies:** `task-day-31`
- **Acceptance Criteria:**
  - [ ] MySQL dialect adapter handling backtick identifiers and MySQL date functions
  - [ ] AST guardrail validator adapted to check statements across all target dialects
  - [ ] Tests asserting dialect-aware AST validation for PostgreSQL, MySQL, and SQLite
- **Key Deliverables:**
  - `src/dialects/mysql_adapter.py`
  - `src/security/dialect_guard.py`
  - `tests/test_dialect_guard.py`

#### Day 33: Multi-Database Connection Router and Dynamic Pool Manager — ⚪ Planned
- **Description:** Build connection router allowing queries to execute across configured SQLite, PostgreSQL, or MySQL data sources dynamically.
- **Complexity:** `Medium` | **Dependencies:** `task-day-32`
- **Acceptance Criteria:**
  - [ ] Connection registry managing active pools per configured database target
  - [ ] Header/payload parameter routing queries to specific registered database
  - [ ] Integration tests asserting dynamic routing between SQLite and PostgreSQL
- **Key Deliverables:**
  - `src/db/router.py`
  - `tests/test_db_router.py`

#### Day 34: Analytical Window Functions and Ranking SQL Generation — ⚪ Planned
- **Description:** Extend SQL generation prompt and few-shot examples to support window functions: ROW_NUMBER, RANK, DENSE_RANK, and OVER clauses.
- **Complexity:** `High` | **Dependencies:** `task-day-33`
- **Acceptance Criteria:**
  - [ ] Few-shot window function prompt templates for ranking and partition queries
  - [ ] Validator rules ensuring window functions execute safely without unbounded memory
  - [ ] Tests verifying natural queries like 'rank top products by category' generate valid SQL
- **Key Deliverables:**
  - `src/engine/window_functions.py`
  - `tests/test_window_functions.py`

#### Day 35: Temporal Analytics: Rolling Averages, Date Truncation, and Intervals — ⚪ Planned
- **Description:** Support natural-language temporal queries generating moving averages, date truncations (DATE_TRUNC), and period-over-period comparisons.
- **Complexity:** `Medium` | **Dependencies:** `task-day-34`
- **Acceptance Criteria:**
  - [ ] Temporal prompt module mapping colloquial timeframes ('last quarter', 'year-to-date', '30-day moving average')
  - [ ] Dialect-aware date arithmetic generator for SQLite, Postgres, and MySQL
  - [ ] Tests verifying correct date bounds generated for relative time queries
- **Key Deliverables:**
  - `src/engine/temporal.py`
  - `tests/test_temporal.py`

#### Day 36: Query Cost Estimation and EXPLAIN Plan Complexity Analyzer — ⚪ Planned
- **Description:** Run EXPLAIN queries prior to execution to estimate cost, detect unindexed full table scans, and reject dangerous runaway plans.
- **Complexity:** `High` | **Dependencies:** `task-day-35`
- **Acceptance Criteria:**
  - [ ] EXPLAIN query planner extracting cost metrics, rows examined, and plan depth
  - [ ] Cost threshold guardrail rejecting queries exceeding configurable cost limit
  - [ ] Tests verifying high-cost Cartesian product queries are blocked
- **Key Deliverables:**
  - `src/security/explain_analyzer.py`
  - `tests/test_explain_analyzer.py`

#### Day 37: Semantic Schema Tagging and Domain Jargon Synonym Dictionary — ⚪ Planned
- **Description:** Implement synonym dictionary mapping business terminology ('GMV', 'churned', 'top tier') to actual database columns and formulas.
- **Complexity:** `Medium` | **Dependencies:** `task-day-36`
- **Acceptance Criteria:**
  - [ ] YAML/JSON-driven domain vocabulary registry mapping business concepts to SQL expressions
  - [ ] Preprocessor injecting business jargon definitions into LLM prompt context
  - [ ] Tests asserting 'top GMV customers' maps correctly to SUM(orders.total_amount)
- **Key Deliverables:**
  - `src/engine/synonyms.py`
  - `config/business_synonyms.yaml`
  - `tests/test_synonyms.py`

#### Day 38: Automated Indexing Advisor Based on Query Workloads — ⚪ Planned
- **Description:** Analyze generated query workloads to detect missing indexes on frequently filtered or joined columns and provide DDL recommendations.
- **Complexity:** `Medium` | **Dependencies:** `task-day-37`
- **Acceptance Criteria:**
  - [ ] Workload tracker aggregating WHERE filter and JOIN columns across queries
  - [ ] Index recommendation engine suggesting single and composite B-tree indexes
  - [ ] Tests verifying index suggestions generated for slow unindexed filter columns
- **Key Deliverables:**
  - `src/engine/index_advisor.py`
  - `tests/test_index_advisor.py`

#### Day 39: Query Result Caching Layer with LRU and Schema Invalidation — ⚪ Planned
- **Description:** Implement high-performance query result caching with SHA-256 query hashing, configurable TTL, and cache bypass options.
- **Complexity:** `Medium` | **Dependencies:** `task-day-38`
- **Acceptance Criteria:**
  - [ ] In-memory and Redis-compatible cache store with cache hit/miss telemetry
  - [ ] SHA-256 query hash normalizer ignoring whitespace and casing differences
  - [ ] Tests asserting second identical query executes with sub-millisecond cache latency
- **Key Deliverables:**
  - `src/cache/query_cache.py`
  - `tests/test_query_cache.py`

#### Day 40: Streaming Data Exporters: CSV, JSON, and Formatted Excel — ⚪ Planned
- **Description:** Build memory-efficient streaming data export endpoints outputting query results to CSV, JSON Lines, and Excel spreadsheets.
- **Complexity:** `Low` | **Dependencies:** `task-day-39`
- **Acceptance Criteria:**
  - [ ] Streaming response generator yielding chunks to minimize backend memory footprint
  - [ ] Excel workbook exporter with styled headers and automatic column width sizing
  - [ ] Unit tests verifying data fidelity across exported CSV, JSON, and Excel outputs
- **Key Deliverables:**
  - `src/export/data_exporter.py`
  - `tests/test_data_exporter.py`

#### Day 41: Natural Language Question Auto-Completion and Suggestions Engine — ⚪ Planned
- **Description:** Implement question suggestion engine providing schema-relevant prompt completions and sample questions based on active database tables.
- **Complexity:** `Medium` | **Dependencies:** `task-day-40`
- **Acceptance Criteria:**
  - [ ] Prefix trie and schema-driven query suggestion generator
  - [ ] GET /api/v1/suggestions endpoint returning recommended query prompts for database schema
  - [ ] Tests asserting relevant query prompts returned for customer and order entities
- **Key Deliverables:**
  - `src/api/suggestions.py`
  - `tests/test_suggestions.py`

#### Day 42: Few-Shot Query Memory Bank with Semantic Similarity Search — ⚪ Planned
- **Description:** Store verified, successful query pairs (question -> validated SQL) and retrieve the most relevant few-shot examples dynamically.
- **Complexity:** `High` | **Dependencies:** `task-day-41`
- **Acceptance Criteria:**
  - [ ] Vector/TF-IDF similarity matcher scoring semantic proximity to user query
  - [ ] Dynamic few-shot prompt injection ranking top 3 most relevant golden queries
  - [ ] Tests asserting relevant few-shot examples injected into prompt context
- **Key Deliverables:**
  - `src/engine/memory_bank.py`
  - `tests/test_memory_bank.py`

#### Day 43: SQL Query Formatter, Syntax Linter, and Code Beautifier — ⚪ Planned
- **Description:** Integrate SQL formatting and linting utilities producing standardized, indented, readable SQL queries with keyword capitalization.
- **Complexity:** `Low` | **Dependencies:** `task-day-42`
- **Acceptance Criteria:**
  - [ ] SQL formatter wrapping lines, indenting subqueries, and capitalizing keywords (SELECT, FROM, WHERE)
  - [ ] Linter flagging redundant joins, missing aliases, or unoptimized predicates
  - [ ] Tests verifying ugly unformatted queries are cleaned and beautified
- **Key Deliverables:**
  - `src/engine/sql_formatter.py`
  - `tests/test_sql_formatter.py`

#### Day 44: Comprehensive Multi-Dialect Integration Test Suite — ⚪ Planned
- **Description:** Run automated end-to-end test suite asserting query generation and execution across PostgreSQL, SQLite, and DuckDB databases.
- **Complexity:** `Medium` | **Dependencies:** `task-day-43`
- **Acceptance Criteria:**
  - [ ] End-to-end integration test executing 20 standard business queries across all three dialects
  - [ ] Assure identical tabular datasets returned across dialects for isomorphic schemas
  - [ ] Phase 6 integration test pass rate achieves 100%
- **Key Deliverables:**
  - `tests/test_multi_dialect_e2e.py`

#### Day 45: Phase 6 Milestone Audit and Dialect Architecture Benchmark — ⚪ Planned
- **Description:** Benchmark dialect execution latency, evaluate memory footprint, and publish Phase 6 architecture performance report.
- **Complexity:** `Low` | **Dependencies:** `task-day-44`
- **Acceptance Criteria:**
  - [ ] Benchmark report recording latencies across SQLite, DuckDB, and PostgreSQL engines
  - [ ] Audit code quality, test coverage, and static type conformance
  - [ ] Publish Phase 6 milestone documentation and update technical specifications
- **Key Deliverables:**
  - `benchmarks/dialect_benchmark.py`
  - `reports/phase_6_audit.md`

### Phase 7: Enterprise Governance & Security

#### Day 46: Role-Based Access Control (RBAC) and Table Permissions — ⚪ Planned
- **Description:** Implement fine-grained RBAC restricting which tables and views each user role (admin, analyst, viewer) can query.
- **Complexity:** `Medium` | **Dependencies:** `task-day-45`
- **Acceptance Criteria:**
  - [ ] Role permission mapping table defining allowed tables per role
  - [ ] Security interceptor rejecting queries touching forbidden tables before SQL execution
  - [ ] Tests asserting analyst role cannot query restricted payroll or credential tables
- **Key Deliverables:**
  - `src/security/rbac.py`
  - `tests/test_rbac.py`

#### Day 47: Dynamic Column-Level Data Masking for Sensitive PII — ⚪ Planned
- **Description:** Enforce runtime data masking on sensitive columns (emails, phone numbers, credit cards) based on user role and permissions.
- **Complexity:** `Medium` | **Dependencies:** `task-day-46`
- **Acceptance Criteria:**
  - [ ] Data masking policy engine supporting full redaction, email masking, and partial digits (***-**-1234)
  - [ ] Result transformer applying masks to query result rows dynamically
  - [ ] Tests asserting unprivileged users receive masked PII values
- **Key Deliverables:**
  - `src/security/masking.py`
  - `tests/test_masking.py`

#### Day 48: Row-Level Security (RLS) Filter Injection for Multi-Tenancy — ⚪ Planned
- **Description:** Automatically inject tenant-isolation WHERE clauses (e.g., `tenant_id = ?`) into generated ASTs to prevent multi-tenant data leakage.
- **Complexity:** `High` | **Dependencies:** `task-day-47`
- **Acceptance Criteria:**
  - [ ] AST rewriter appending mandatory tenant filter conditions to every table in query
  - [ ] Handles joins, subqueries, and CTEs without bypassing tenant isolation
  - [ ] Tests verifying tenant filter cannot be bypassed by tricky phrasing
- **Key Deliverables:**
  - `src/security/rls_injector.py`
  - `tests/test_rls_injector.py`

#### Day 49: Immutable Audit Logging for Natural Queries and Executed SQL — ⚪ Planned
- **Description:** Implement structured, append-only security audit log recording every user prompt, generated SQL, execution latency, and actor identity.
- **Complexity:** `Medium` | **Dependencies:** `task-day-48`
- **Acceptance Criteria:**
  - [ ] Audit log schema with cryptographic SHA-256 chaining to prevent tampering
  - [ ] Structured JSON audit event logger with log rotation and retention policies
  - [ ] Tests verifying audit record written for every accepted and rejected query
- **Key Deliverables:**
  - `src/security/audit_logger.py`
  - `tests/test_audit_logger.py`

#### Day 50: Query Anomaly Detection on Latency and Result Volumes — ⚪ Planned
- **Description:** Build anomaly detector identifying suspicious spikes in row volume or abnormal query frequencies indicating data scraping.
- **Complexity:** `Medium` | **Dependencies:** `task-day-49`
- **Acceptance Criteria:**
  - [ ] Statistical baseline tracker measuring moving average of row counts and execution duration
  - [ ] Alert trigger flagging queries returning 10x normal volume
  - [ ] Tests asserting data egress alert triggers on bulk export queries
- **Key Deliverables:**
  - `src/security/anomaly_detector.py`
  - `tests/test_anomaly_detector.py`

#### Day 51: API Rate Limiting and Token Bucket Request Throttling — ⚪ Planned
- **Description:** Add token bucket rate limiter to protect API endpoints against denial-of-service and abusive automated traffic.
- **Complexity:** `Low` | **Dependencies:** `task-day-50`
- **Acceptance Criteria:**
  - [ ] Token bucket rate limiter with sliding window tracking per IP and API key
  - [ ] HTTP 429 response with Retry-After header and descriptive error payload
  - [ ] Tests asserting rate limit enforcement under simulated burst traffic
- **Key Deliverables:**
  - `src/api/rate_limiter.py`
  - `tests/test_rate_limiter.py`

#### Day 52: OAuth2 and JWT Authentication Middleware Integration — ⚪ Planned
- **Description:** Integrate JWT authentication middleware validating bearer tokens, extracting user claims, and establishing request security context.
- **Complexity:** `Medium` | **Dependencies:** `task-day-51`
- **Acceptance Criteria:**
  - [ ] JWT validator checking signature, expiration, and issuer claims
  - [ ] FastAPI dependency injecting AuthenticatedUser into route handlers
  - [ ] Tests asserting protected endpoints reject unauthenticated or expired tokens
- **Key Deliverables:**
  - `src/auth/jwt_handler.py`
  - `src/auth/middleware.py`
  - `tests/test_auth.py`

#### Day 53: Read-Only Database Replica Load Balancing and Health Probes — ⚪ Planned
- **Description:** Implement round-robin connection load balancer across read-only database replicas with automatic unhealthy replica eviction.
- **Complexity:** `Medium` | **Dependencies:** `task-day-52`
- **Acceptance Criteria:**
  - [ ] Replica pool manager routing read queries across multiple read replicas
  - [ ] Periodic background health probe detecting connection lag or network partitions
  - [ ] Tests asserting queries route to healthy replicas when one node goes offline
- **Key Deliverables:**
  - `src/db/replica_pool.py`
  - `tests/test_replica_pool.py`

#### Day 54: Query Complexity Scoring and Maximum Join/Subquery Depth Limits — ⚪ Planned
- **Description:** Calculate static query complexity score based on join count, subquery nesting depth, and aggregation complexity to prevent heavy queries.
- **Complexity:** `Medium` | **Dependencies:** `task-day-53`
- **Acceptance Criteria:**
  - [ ] Complexity evaluator inspecting SQL AST and assigning weighted score
  - [ ] Rejection threshold blocking queries exceeding maximum allowable complexity
  - [ ] Tests asserting queries with 10+ nested joins are safely rejected with actionable guidance
- **Key Deliverables:**
  - `src/security/complexity_scorer.py`
  - `tests/test_complexity_scorer.py`

#### Day 55: Data Lineage Graph: Mapping SQL Columns to Base Schema Tables — ⚪ Planned
- **Description:** Analyze SQL queries to build column-level lineage graph mapping output attributes back to physical source tables and expressions.
- **Complexity:** `High` | **Dependencies:** `task-day-54`
- **Acceptance Criteria:**
  - [ ] Lineage extractor tracing alias chains and transformations back to root database columns
  - [ ] Generates JSON data lineage graph indicating source dependencies
  - [ ] Tests asserting correct source column attribution on multi-table joined queries
- **Key Deliverables:**
  - `src/engine/lineage_tracker.py`
  - `tests/test_lineage_tracker.py`

#### Day 56: Compliance Audit Export Engine (GDPR/HIPAA Data Access Logs) — ⚪ Planned
- **Description:** Provide automated export tools generating audit-ready compliance reports detailing who accessed which tables and sensitive fields.
- **Complexity:** `Low` | **Dependencies:** `task-day-55`
- **Acceptance Criteria:**
  - [ ] Compliance report generator outputting standardized access logs for specified time windows
  - [ ] Filters logs by user ID, table, or sensitive classification tag
  - [ ] Tests verifying audit report accuracy against simulated query logs
- **Key Deliverables:**
  - `src/export/compliance_exporter.py`
  - `tests/test_compliance_exporter.py`

#### Day 57: Secrets Rotation and Environment Credential Isolation — ⚪ Planned
- **Description:** Implement zero-downtime secrets rotation for database passwords, API tokens, and JWT signing keys without service restart.
- **Complexity:** `Medium` | **Dependencies:** `task-day-56`
- **Acceptance Criteria:**
  - [ ] Dual-key verification mechanism supporting overlapping key rotation periods
  - [ ] Secrets reload watcher detecting updated credentials safely
  - [ ] Tests asserting queries succeed continuously during credential rotation
- **Key Deliverables:**
  - `src/core/secrets_manager.py`
  - `tests/test_secrets_manager.py`

#### Day 58: Automated SQL Injection and Security Penetration Test Suite — ⚪ Planned
- **Description:** Execute automated penetration test suite executing 50+ adversarial SQL injection and prompt injection payloads.
- **Complexity:** `High` | **Dependencies:** `task-day-57`
- **Acceptance Criteria:**
  - [ ] Penetration test suite containing tautology injection, union-based extraction, and stacked statements
  - [ ] Prompt injection battery attempting system prompt overrides and jailbreaks
  - [ ] 100% of injection attempts safely blocked by guardrails without execution
- **Key Deliverables:**
  - `tests/test_penetration_suite.py`
  - `tests/test_prompt_injection.py`

#### Day 59: Security Regression Benchmark and Vulnerability Assessment Report — ⚪ Planned
- **Description:** Run automated security regression benchmark, verify zero open vulnerabilities, and generate security assessment report.
- **Complexity:** `Low` | **Dependencies:** `task-day-58`
- **Acceptance Criteria:**
  - [ ] Automated security audit generating comprehensive markdown report
  - [ ] Documents threat modeling, risk mitigations, and penetration test evidence
  - [ ] Produce security compliance checklist signed off for enterprise deployment
- **Key Deliverables:**
  - `reports/security_audit_report.md`
  - `scripts/run_security_benchmark.py`

#### Day 60: Phase 7 Milestone Audit and Enterprise Security Certification — ⚪ Planned
- **Description:** Conduct complete Phase 7 milestone audit, verify RBAC, masking, and audit logging, and tag enterprise security milestone.
- **Complexity:** `Low` | **Dependencies:** `task-day-59`
- **Acceptance Criteria:**
  - [ ] Verification that all 15 Phase 7 security criteria pass cleanly
  - [ ] Audit log retention and masking benchmarks verified
  - [ ] Publish Phase 7 release notes and update project architecture documentation
- **Key Deliverables:**
  - `reports/phase_7_audit.md`
  - `docs/security_architecture.md`

### Phase 8: Frontend Intelligence & Visualizations

#### Day 61: Automatic Chart Recommendation Engine Based on Result Schema — ⚪ Planned
- **Description:** Analyze query result tabular schema, data types, and row cardinalities to recommend the optimal visualization type.
- **Complexity:** `Medium` | **Dependencies:** `task-day-60`
- **Acceptance Criteria:**
  - [ ] Heuristic classifier choosing between Bar, Line, Area, Pie, or Table display
  - [ ] Categorizes columns into dimensions (categorical/temporal) and measures (numeric/aggregations)
  - [ ] Unit tests verifying time-series data maps to Line charts and category sums to Bar charts
- **Key Deliverables:**
  - `frontend/src/utils/chartRecommender.ts`
  - `frontend/src/tests/test_chart_recommender.test.ts`

#### Day 62: Interactive Recharts Data Visualizations (Bar, Line, Area, Pie) — ⚪ Planned
- **Description:** Build interactive React visualization components using Recharts with tooltips, legends, and responsive auto-sizing.
- **Complexity:** `Medium` | **Dependencies:** `task-day-61`
- **Acceptance Criteria:**
  - [ ] ChartContainer component dynamically rendering recommended chart type
  - [ ] Interactive hover tooltips formatting currency, percentages, and large numbers cleanly
  - [ ] Component tests verifying chart rendering and legend toggles
- **Key Deliverables:**
  - `frontend/src/components/ChartContainer.tsx`
  - `frontend/src/components/MetricCard.tsx`

#### Day 63: Chart Image and Document Exporter (PNG, SVG, and PDF Reports) — ⚪ Planned
- **Description:** Implement client-side export allowing users to download generated charts as high-resolution PNG, SVG, or printable PDF reports.
- **Complexity:** `Low` | **Dependencies:** `task-day-62`
- **Acceptance Criteria:**
  - [ ] Canvas export utility rendering SVG charts to 300 DPI PNG images
  - [ ] Download report generator assembling question, SQL preview, chart, and data table into PDF
  - [ ] Frontend interaction tests verifying export triggers file download without error
- **Key Deliverables:**
  - `frontend/src/utils/chartExporter.ts`
  - `frontend/src/components/ExportModal.tsx`

#### Day 64: SQL Query Diff Viewer Highlighting Clarification Impact — ⚪ Planned
- **Description:** Build visual diff viewer comparing original preliminary SQL against refined SQL following user clarification selection.
- **Complexity:** `Medium` | **Dependencies:** `task-day-63`
- **Acceptance Criteria:**
  - [ ] Side-by-side or inline diff component highlighting added/modified SQL clauses in green/yellow
  - [ ] Displays summary explanation of how clarification altered query semantics
  - [ ] Component tests asserting diff highlights added WHERE or JOIN clauses
- **Key Deliverables:**
  - `frontend/src/components/SqlDiffViewer.tsx`

#### Day 65: Conversational Breadcrumbs and Multi-Branch Exploration UI — ⚪ Planned
- **Description:** Allow users to branch conversations by exploring alternative clarification options without losing prior chat history.
- **Complexity:** `High` | **Dependencies:** `task-day-64`
- **Acceptance Criteria:**
  - [ ] Conversation tree visualizer allowing rollback or branching from any past turn
  - [ ] State management storing branched chat turns cleanly in local storage / session
  - [ ] Tests verifying switching between branches restores respective SQL previews and charts
- **Key Deliverables:**
  - `frontend/src/components/BranchExplorer.tsx`
  - `frontend/src/state/conversationStore.ts`

#### Day 66: Natural Language Executive Summary Generator for Query Results — ⚪ Planned
- **Description:** Generate automated natural language insights and executive takeaways summarizing query result patterns in plain English.
- **Complexity:** `Medium` | **Dependencies:** `task-day-65`
- **Acceptance Criteria:**
  - [ ] Summary engine analyzing tabular results for trends, peaks, anomalies, and top contributors
  - [ ] Generates concise bulleted executive highlights displayed alongside charts
  - [ ] Tests asserting correct statistical highlights generated for sales summary queries
- **Key Deliverables:**
  - `src/engine/result_summarizer.py`
  - `tests/test_result_summarizer.py`

#### Day 67: Customizable Analytics Dashboard with Pin-to-Board Widgets — ⚪ Planned
- **Description:** Enable users to pin query cards, charts, and metric counters to a customizable grid dashboard with drag-and-drop layout.
- **Complexity:** `High` | **Dependencies:** `task-day-66`
- **Acceptance Criteria:**
  - [ ] Dashboard grid component supporting drag-and-drop reordering and resizing
  - [ ] Persistent dashboard state saving pinned widgets and query configurations
  - [ ] Component tests verifying adding, removing, and reordering dashboard widgets
- **Key Deliverables:**
  - `frontend/src/components/DashboardView.tsx`
  - `frontend/src/components/DashboardWidget.tsx`

#### Day 68: Accessible Theme Switcher: Dark/Light Mode and WCAG Contrast — ⚪ Planned
- **Description:** Implement accessible theme manager supporting system preference detection, smooth dark/light transitions, and WCAG AA contrast.
- **Complexity:** `Low` | **Dependencies:** `task-day-67`
- **Acceptance Criteria:**
  - [ ] Tailwind CSS dark mode integration with high-contrast color tokens for data visualizations
  - [ ] Accessible focus indicators and ARIA roles across all interactive controls
  - [ ] Accessibility test suite validating WCAG 2.1 AA compliance across UI components
- **Key Deliverables:**
  - `frontend/src/theme/ThemeProvider.tsx`
  - `frontend/src/components/ThemeToggle.tsx`

#### Day 69: Power-User Keyboard Navigation and Command Palette (Ctrl+K) — ⚪ Planned
- **Description:** Build fast command palette allowing power users to search query history, switch databases, run common queries, and navigate via keyboard.
- **Complexity:** `Medium` | **Dependencies:** `task-day-68`
- **Acceptance Criteria:**
  - [ ] Command palette modal triggered via Ctrl+K / Cmd+K with fuzzy search
  - [ ] Keyboard navigation supporting Arrow keys, Enter selection, and Escape dismissal
  - [ ] Component tests verifying quick actions execute correctly from command palette
- **Key Deliverables:**
  - `frontend/src/components/CommandPalette.tsx`

#### Day 70: Shareable Query Snapshots with Encrypted URL State Tokens — ⚪ Planned
- **Description:** Generate shareable URL links containing compressed, encrypted query states allowing colleagues to view identical SQL and results.
- **Complexity:** `Medium` | **Dependencies:** `task-day-69`
- **Acceptance Criteria:**
  - [ ] Base64 URL-safe compressor encoding query parameters, selected options, and chart types
  - [ ] Shared view mode rendering read-only snapshot view for external viewers
  - [ ] Tests asserting encoded URL faithfully reconstructs complete query context
- **Key Deliverables:**
  - `frontend/src/utils/shareableUrl.ts`
  - `frontend/src/components/SharedSnapshotView.tsx`

#### Day 71: Query Latency Waterfall and Execution Performance Profiler UI — ⚪ Planned
- **Description:** Display visual breakdown of query latency showing time spent in LLM generation, AST validation, database execution, and rendering.
- **Complexity:** `Low` | **Dependencies:** `task-day-70`
- **Acceptance Criteria:**
  - [ ] Waterfall timing bar component visualizing duration of each execution stage
  - [ ] Highlights bottlenecks (e.g. slow database scan vs LLM token generation latency)
  - [ ] Component tests asserting correct latency segmentation display
- **Key Deliverables:**
  - `frontend/src/components/LatencyProfiler.tsx`

#### Day 72: Streaming Query Execution Progress with Server-Sent Events (SSE) — ⚪ Planned
- **Description:** Stream real-time execution phases (Validating -> Generating -> Executing -> Profiling) to frontend via SSE stream.
- **Complexity:** `Medium` | **Dependencies:** `task-day-71`
- **Acceptance Criteria:**
  - [ ] FastAPI SSE endpoint streaming lifecycle event payloads to client
  - [ ] React hook consuming event stream and updating step progress indicator smoothly
  - [ ] Tests verifying client receives lifecycle events in proper sequence
- **Key Deliverables:**
  - `src/api/streaming.py`
  - `frontend/src/hooks/useExecutionStream.ts`
  - `tests/test_streaming.py`

#### Day 73: Frontend Component Integration and Automated User Journey Tests — ⚪ Planned
- **Description:** Build comprehensive frontend interaction test suite simulating natural query input, clarification selection, and chart toggles.
- **Complexity:** `Medium` | **Dependencies:** `task-day-72`
- **Acceptance Criteria:**
  - [ ] Test suite exercising full user journey from empty state to interactive chart visualization
  - [ ] Verifies error state recovery when server returns 500 or validation errors
  - [ ] 100% test pass rate across all frontend component tests
- **Key Deliverables:**
  - `frontend/src/tests/userJourney.test.tsx`

#### Day 74: Virtualized Table Rendering for High-Volume Datasets (10k+ Rows) — ⚪ Planned
- **Description:** Integrate virtual scrolling for data tables rendering tens of thousands of rows smoothly at 60 FPS without DOM bloat.
- **Complexity:** `Medium` | **Dependencies:** `task-day-73`
- **Acceptance Criteria:**
  - [ ] Windowing virtualization component rendering only visible DOM nodes
  - [ ] Smooth scroll performance with fixed header and resizable column widths
  - [ ] Performance test asserting sub-16ms frame render times on 10,000 row dataset
- **Key Deliverables:**
  - `frontend/src/components/VirtualizedTable.tsx`

#### Day 75: Phase 8 Milestone Audit and Frontend Usability Evaluation — ⚪ Planned
- **Description:** Conduct Phase 8 audit reviewing UI responsiveness, visualization fidelity, and accessibility compliance benchmarks.
- **Complexity:** `Low` | **Dependencies:** `task-day-74`
- **Acceptance Criteria:**
  - [ ] Lighthouse performance audit achieving 95+ score across Performance, Accessibility, and Best Practices
  - [ ] Documentation of visualization components, props, and theme guidelines
  - [ ] Publish Phase 8 milestone sign-off and retrospective
- **Key Deliverables:**
  - `reports/phase_8_audit.md`
  - `docs/frontend_design_system.md`

### Phase 9: Production Scalability & Autonomous Reliability

#### Day 76: Multi-LLM Dynamic Routing and Latency-Based Failover — ⚪ Planned
- **Description:** Implement dynamic LLM provider router falling back across Gemini, Anthropic, and OpenAI based on health and latency probes.
- **Complexity:** `High` | **Dependencies:** `task-day-75`
- **Acceptance Criteria:**
  - [ ] Provider router maintaining active circuit state and rolling latency percentiles
  - [ ] Automatic fallback to secondary provider when primary returns 429, 503, or times out
  - [ ] Tests asserting graceful fallback execution when primary provider mock simulates downtime
- **Key Deliverables:**
  - `src/llm/dynamic_router.py`
  - `tests/test_dynamic_router.py`

#### Day 77: Prompt Drift Detection and Output Conformance Telemetry — ⚪ Planned
- **Description:** Monitor model output syntax and adherence over time to detect LLM prompt drift or unexpected degradation in SQL validity.
- **Complexity:** `Medium` | **Dependencies:** `task-day-76`
- **Acceptance Criteria:**
  - [ ] Drift telemetry collector tracking syntax error rate and retry counts per model version
  - [ ] Automated alert triggered when error rate exceeds 5% statistical threshold
  - [ ] Tests asserting drift alert fires under elevated synthetic error conditions
- **Key Deliverables:**
  - `src/monitoring/drift_detector.py`
  - `tests/test_drift_detector.py`

#### Day 78: Prometheus Metrics Exporter for System and Query Telemetry — ⚪ Planned
- **Description:** Expose Prometheus metrics endpoint (`/metrics`) instrumenting query throughput, latencies, cache ratios, and error counts.
- **Complexity:** `Low` | **Dependencies:** `task-day-77`
- **Acceptance Criteria:**
  - [ ] Prometheus counter, histogram, and gauge metrics instrumenting all critical code paths
  - [ ] Standardized labels: database_type, model_provider, status, user_role
  - [ ] Tests asserting `/metrics` endpoint returns valid Prometheus text format
- **Key Deliverables:**
  - `src/monitoring/prometheus_exporter.py`
  - `tests/test_metrics.py`

#### Day 79: Pre-Configured Grafana Dashboard for Operational Telemetry — ⚪ Planned
- **Description:** Author complete Grafana dashboard JSON visualizing system KPIs: query volume, p95 latencies, error rates, and cache hits.
- **Complexity:** `Low` | **Dependencies:** `task-day-78`
- **Acceptance Criteria:**
  - [ ] Production-ready Grafana dashboard configuration JSON with panel templates
  - [ ] Visual alerts for error spikes, high query latency, and database pool exhaustion
  - [ ] Verification that dashboard imports and renders all metrics cleanly
- **Key Deliverables:**
  - `monitoring/grafana_dashboard.json`
  - `docs/observability_guide.md`

#### Day 80: OpenTelemetry Distributed Tracing across API, Engine, and DB — ⚪ Planned
- **Description:** Implement OpenTelemetry tracing attaching distributed trace and span IDs to HTTP requests, LLM calls, and database transactions.
- **Complexity:** `Medium` | **Dependencies:** `task-day-79`
- **Acceptance Criteria:**
  - [ ] Tracer instrumentation creating child spans for prompt synthesis, AST parsing, and DB execution
  - [ ] Context propagation injecting trace headers for end-to-end distributed tracing
  - [ ] Tests verifying trace spans recorded with proper durations and tags
- **Key Deliverables:**
  - `src/monitoring/tracer.py`
  - `tests/test_tracer.py`

#### Day 81: Circuit Breakers and Graceful Degradation for External Dependencies — ⚪ Planned
- **Description:** Implement circuit breaker pattern for external database connections, LLM APIs, and cache clusters to prevent cascading failures.
- **Complexity:** `Medium` | **Dependencies:** `task-day-80`
- **Acceptance Criteria:**
  - [ ] Circuit breaker with CLOSED, OPEN, and HALF-OPEN state machine transitions
  - [ ] Graceful fallback responses returning clear status messages during dependency outages
  - [ ] Tests asserting circuit opens after 3 consecutive failures and recovers on success
- **Key Deliverables:**
  - `src/core/circuit_breaker.py`
  - `tests/test_circuit_breaker.py`

#### Day 82: High-Concurrency Stress Testing with Locust (100+ Concurrent Queries) — ⚪ Planned
- **Description:** Build and execute high-concurrency stress test suite using Locust simulating 100 simultaneous users asking natural queries.
- **Complexity:** `High` | **Dependencies:** `task-day-81`
- **Acceptance Criteria:**
  - [ ] Locust load testing scenario file with realistic user think times and query distributions
  - [ ] Load test execution asserting 0% HTTP 5xx error rate at 100 concurrent simulated users
  - [ ] Produces load test benchmark report documenting throughput (RPS) and p99 latency
- **Key Deliverables:**
  - `benchmarks/locustfile.py`
  - `reports/load_test_results.md`

#### Day 83: Async Event Loop Profiling and Memory Footprint Optimization — ⚪ Planned
- **Description:** Profile FastAPI async event loop to identify blocking calls, optimize connection pool sizing, and minimize memory leaks.
- **Complexity:** `Medium` | **Dependencies:** `task-day-82`
- **Acceptance Criteria:**
  - [ ] Event loop profiler flagging synchronous CPU-bound operations in async handlers
  - [ ] Optimized database driver configuration and connection pool reuse
  - [ ] Tests verifying steady-state memory utilization remains flat under continuous queries
- **Key Deliverables:**
  - `scripts/profile_event_loop.py`
  - `tests/test_concurrency.py`

#### Day 84: Kubernetes Helm Charts and Multi-Environment Production Manifests — ⚪ Planned
- **Description:** Create production-ready Kubernetes Helm chart packaging FastAPI backend, React frontend, ingress, and config maps.
- **Complexity:** `Medium` | **Dependencies:** `task-day-83`
- **Acceptance Criteria:**
  - [ ] Helm chart with values.yaml supporting dev, staging, and production environments
  - [ ] Horizontal Pod Autoscaler (HPA) manifest scaling pods based on CPU/memory utilization
  - [ ] Kubernetes dry-run lint test verifying manifest syntax and security context
- **Key Deliverables:**
  - `deploy/helm/Chart.yaml`
  - `deploy/helm/values.yaml`
  - `deploy/helm/templates/deployment.yaml`

#### Day 85: Automated Database Migration Pipeline with Alembic Versioning — ⚪ Planned
- **Description:** Set up Alembic database migration environment managing relational schema evolution across development and production.
- **Complexity:** `Medium` | **Dependencies:** `task-day-84`
- **Acceptance Criteria:**
  - [ ] Alembic configuration and env.py targeting configured database engine dynamically
  - [ ] Baseline migration generating all domain tables with rollback support
  - [ ] Tests asserting migrations apply and revert cleanly without data loss
- **Key Deliverables:**
  - `alembic.ini`
  - `alembic/env.py`
  - `alembic/versions/001_initial_schema.py`
  - `tests/test_migrations.py`

#### Day 86: Continuous Synthetic Query Probes and Alert Webhook Integrations — ⚪ Planned
- **Description:** Build synthetic health probe continuously executing canary queries every 5 minutes and dispatching alerts to Slack/Discord webhooks.
- **Complexity:** `Low` | **Dependencies:** `task-day-85`
- **Acceptance Criteria:**
  - [ ] Canary query runner verifying end-to-end pipeline health on automated cadence
  - [ ] Alert dispatcher formatting rich Markdown/Slack alert cards on probe failure
  - [ ] Tests asserting webhook dispatched when canary query encounters synthetic failure
- **Key Deliverables:**
  - `scripts/canary_probe.py`
  - `src/notifications/alert_dispatcher.py`
  - `tests/test_canary.py`

#### Day 87: End-to-End System Soak Testing and Resilience Verification — ⚪ Planned
- **Description:** Execute 12-hour continuous soak test subjecting system to constant stream of varied natural-language queries without crash.
- **Complexity:** `High` | **Dependencies:** `task-day-86`
- **Acceptance Criteria:**
  - [ ] Automated soak test harness running continuous query cycles
  - [ ] Monitors for memory leaks, connection exhaustion, and unbounded cache growth
  - [ ] Soak test summary report certifying system stability under sustained operational load
- **Key Deliverables:**
  - `scripts/soak_test.py`
  - `reports/soak_test_report.md`

#### Day 88: Complete v2.0 Developer Documentation and Architecture Manual — ⚪ Planned
- **Description:** Author exhaustive system architecture manual, operational runbooks, and developer extension guides for ClarifySQL v2.0.
- **Complexity:** `Low` | **Dependencies:** `task-day-87`
- **Acceptance Criteria:**
  - [ ] Architecture guide detailing multi-dialect engine, security guardrails, and visualization pipeline
  - [ ] Operational runbook with troubleshooting procedures for common production alerts
  - [ ] API documentation and developer guide for creating custom dialect adapters
- **Key Deliverables:**
  - `docs/architecture_v2.md`
  - `docs/operations_runbook.md`
  - `docs/dialect_authoring_guide.md`

#### Day 89: Pre-Release Quality Sign-Off and Benchmark Regression Gate — ⚪ Planned
- **Description:** Execute full quality gate: 100% test pass rate across all unit and integration suites, zero security vulnerabilities, and lint pass.
- **Complexity:** `Medium` | **Dependencies:** `task-day-88`
- **Acceptance Criteria:**
  - [ ] Automated pre-release audit verifying 100% test pass rate across backend and frontend
  - [ ] Regression benchmark asserting zero accuracy degradation compared to v1.0.0
  - [ ] Publish pre-release verification checklist signed off for production
- **Key Deliverables:**
  - `reports/pre_release_audit.md`
  - `scripts/pre_release_gate.py`

#### Day 90: Final 90-Day Retrospective, Release v2.0.0 Tagging, and Streak Milestone — ⚪ Planned
- **Description:** Conduct comprehensive 90-day project retrospective, tag v2.0.0 production release, and document engineering milestones.
- **Complexity:** `Low` | **Dependencies:** `task-day-89`
- **Acceptance Criteria:**
  - [ ] All 90 daily acceptance criteria verified 100% complete
  - [ ] Changelog and release notes published for v2.0.0 major release
  - [ ] Publish 90-day retrospective documenting full system evolution, streak achievements, and future roadmap
- **Key Deliverables:**
  - `CHANGELOG.md`
  - `reports/90_day_retrospective.md`
