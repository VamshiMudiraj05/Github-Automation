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
            (1, "Phase 1: Foundation", "Project Architecture, Scaffolding, and Environment Validation",
             "Analyze telemetry ingestion requirements, establish modular workspace layout, and define project contracts.",
             ["Establish clean directory structure and package exports", "Validate Python runtime and dependency isolation", "Set up baseline documentation and architecture design record"],
             ["src/core/__init__.py", "src/models/__init__.py", "tests/__init__.py", "docs/architecture.md"], [], "Low"),
            (2, "Phase 1: Foundation", "Telemetry Data Models, Schema Validation, and Envelope Types",
             "Implement strongly-typed metrics schemas (Counter, Gauge, Histogram, Summary) with serialization support.",
             ["MetricEvent and MetricBatch schemas defined with type annotations", "Nanosecond-precision timestamping and tags dictionary validation", "Serialization to JSON and binary format validated with unit tests"],
             ["src/models/metrics.py", "tests/test_metrics_model.py"], ["task-day-01"], "Low"),
            (3, "Phase 1: Foundation", "High-Throughput In-Memory Ring Buffer & Sliding Window",
             "Implement thread-safe, lock-free ring buffer for zero-allocation telemetry sample queuing.",
             ["Lock-free or mutex-guarded bounded circular buffer implemented", "Buffer drops or backpressure signals handled correctly on overflow", "Unit tests verifying FIFO order under high concurrency"],
             ["src/core/ring_buffer.py", "tests/test_ring_buffer.py"], ["task-day-02"], "Medium"),
            (4, "Phase 1: Foundation", "Persistent Timeseries Storage Adapter (SQLite & WAL Engine)",
             "Build ACID-compliant local timeseries persistence adapter with indexing on metric name, timestamp, and host.",
             ["SQLite schema with timeseries chunking and WAL mode enabled", "Batch insertion method achieving >10,000 events/sec", "Query interface filtering by timerange and tag keys"],
             ["src/storage/sqlite_adapter.py", "tests/test_storage_adapter.py"], ["task-day-03"], "Medium"),
            (5, "Phase 1: Foundation", "Automated Health Checks, Logging Subsystem, and Baseline Suite",
             "Add structured JSON logging, system diagnostics, and automated baseline test execution.",
             ["Diagnostic health check verifies disk space, buffer status, and DB connection", "Configurable JSON logger with correlation IDs", "Pytest suite achieves 100% pass on Phase 1 modules"],
             ["src/core/diagnostics.py", "src/core/logger.py", "tests/test_diagnostics.py"], ["task-day-04"], "Medium"),

            # Phase 2: Core Functionality (Days 6–12)
            (6, "Phase 2: Core Functionality", "Asynchronous HTTP & REST Ingestion Endpoints",
             "Implement lightweight HTTP endpoint receiving metric batch payloads with gzip decompression support.",
             ["HTTP handler accepts POST /api/v1/metrics payload", "Validates bearer token and rejects malformed payloads with 400 Bad Request", "Integration tests verify end-to-end ingestion pipeline"],
             ["src/ingestion/http_server.py", "tests/test_http_ingestion.py"], ["task-day-05"], "Medium"),
            (7, "Phase 2: Core Functionality", "Streaming Metrics Aggregator (Quantiles & Percentiles)",
             "Implement t-digest or P2 quantile estimator for calculating accurate P50, P90, P99 latencies on the fly.",
             ["Streaming quantile estimator calculates P50, P90, P99 within 1% error margin", "Windowed downsampling aggregations for 1m, 5m, and 1h intervals", "Unit tests compare calculated percentiles with exact distributions"],
             ["src/aggregation/quantiles.py", "tests/test_quantiles.py"], ["task-day-06"], "Medium"),
            (8, "Phase 2: Core Functionality", "Prometheus Exporter & OpenTelemetry Protocol Adapter",
             "Expose /metrics endpoint formatted according to Prometheus text-based exposition format.",
             ["Prometheus exposition format serializer correctly formats HELP and TYPE lines", "OpenTelemetry metric mapping converts OTLP samples to internal representation", "Verified scraper compatibility via automated tests"],
             ["src/exporters/prometheus.py", "tests/test_prometheus_exporter.py"], ["task-day-07"], "Medium"),
            (9, "Phase 2: Core Functionality", "Dynamic Tag Filtering & Dimensional Indexing",
             "Build fast in-memory inverted index for multi-dimensional label querying (e.g., service=auth AND env=prod).",
             ["Inverted index maps tag key-value pairs to metric series identifiers", "Intersection and union query operations execute in sub-millisecond time", "Property-based tests confirm index consistency"],
             ["src/storage/tag_index.py", "tests/test_tag_index.py"], ["task-day-08"], "Medium"),
            (10, "Phase 2: Core Functionality", "API Authentication, Token Rotation, and Rate Limiting",
             "Implement token-bucket rate limiter and HMAC signature verification for secure client access.",
             ["Token bucket rate limiter prevents client ingestion starvation", "HMAC SHA-256 header verification for payload integrity", "Security test cases verifying rejection of expired or forged tokens"],
             ["src/security/auth.py", "src/security/rate_limiter.py", "tests/test_security_auth.py"], ["task-day-09"], "Medium"),
            (11, "Phase 2: Core Functionality", "Timeseries Query Engine & DSL Parsing",
             "Implement query parser supporting rate(), sum_by(), and delta() expressions over stored metrics.",
             ["Lexer and parser for metric aggregation expressions", "Execution engine evaluates expressions against timeseries storage", "End-to-end query tests validating calculation correctness"],
             ["src/query/engine.py", "src/query/parser.py", "tests/test_query_engine.py"], ["task-day-10"], "High"),
            (12, "Phase 2: Core Functionality", "Phase 2 Integration Verification & End-to-End Test Suite",
             "Comprehensive integration of ingestion, aggregation, storage, and querying pipelines.",
             ["Automated integration test simulates 5 concurrent producers pushing 50,000 metrics", "Metrics verify queryable with accurate P99 latencies within 50ms", "Zero data loss under controlled throughput"],
             ["tests/test_phase2_integration.py"], ["task-day-11"], "High"),

            # Phase 3: Advanced Features (Days 13–19)
            (13, "Phase 3: Advanced Features", "Dynamic Threshold Alerting Rule Engine",
             "Build background evaluation loop checking metric thresholds (e.g. error_rate > 5% for 3 consecutive minutes).",
             ["AlertRule schema supporting condition types (> , < , delta, absent)", "Stateful rule evaluator tracks pending, firing, and resolved alert states", "Tests verify alert state transitions without flapping"],
             ["src/alerts/rule_engine.py", "tests/test_alert_rules.py"], ["task-day-12"], "Medium"),
            (14, "Phase 3: Advanced Features", "Multi-Channel Notification Dispatcher (Webhook & Email)",
             "Implement retry-safe notification dispatcher sending alerts to Slack, Discord webhooks, and SMTP email.",
             ["Webhook dispatcher formats rich payloads with severity badges and runbooks", "Exponential backoff retry with dead-letter queue for failed deliveries", "Mocked integration tests for webhook and email channels"],
             ["src/alerts/dispatcher.py", "tests/test_dispatcher.py"], ["task-day-13"], "Medium"),
            (15, "Phase 3: Advanced Features", "Real-Time Anomaly Detection via Moving Z-Score & Holt-Winters",
             "Implement statistical anomaly detector flagging outliers based on rolling standard deviations.",
             ["Rolling Z-Score algorithm identifies sudden metric spikes and drops", "Configurable sensitivity threshold and warmup period", "Benchmark tests with synthetic noisy timeseries"],
             ["src/analytics/anomaly_detector.py", "tests/test_anomaly_detector.py"], ["task-day-14"], "High"),
            (16, "Phase 3: Advanced Features", "Terminal UI & Interactive CLI Dashboard",
             "Build interactive command-line dashboard displaying real-time ingestion throughput, memory, and top metrics.",
             ["Click-based CLI command `telemetry top` and `telemetry query`", "ASCII sparklines and status tables for live terminal monitoring", "CLI integration tests with Click test runner"],
             ["src/cli/dashboard.py", "tests/test_cli_dashboard.py"], ["task-day-15"], "Medium"),
            (17, "Phase 3: Advanced Features", "Distributed Tracing Context Propagation (W3C TraceContext)",
             "Add distributed tracing context injection and extraction conforming to W3C TraceContext spec.",
             ["Traceparent and tracestate header parsing and generation", "Span model supporting parent-child relationships and span attributes", "Unit tests verifying trace propagation across synthetic boundaries"],
             ["src/tracing/context.py", "src/tracing/span.py", "tests/test_tracing.py"], ["task-day-16"], "Medium"),
            (18, "Phase 3: Advanced Features", "Timeseries Data Compression & Retention Pruner",
             "Implement Gorilla double-delta timestamp and XOR floating-point compression to reduce disk usage by 70%.",
             ["Double-delta timestamp compression algorithm implemented", "Automated TTL pruning job removes raw samples older than configured retention", "Compression tests verify exact floating-point recovery"],
             ["src/storage/compression.py", "src/storage/retention.py", "tests/test_compression.py"], ["task-day-17"], "High"),
            (19, "Phase 3: Advanced Features", "Phase 3 Advanced Feature Integration & Stress Benchmark",
             "Integrated stress run combining alerting, anomaly detection, tracing, and compression.",
             ["Load generator executes 100k samples with embedded anomalies", "Anomaly detector alerts fire correctly and trigger dispatchers", "No memory leaks detected across 10-minute continuous run"],
             ["tests/test_phase3_advanced_e2e.py"], ["task-day-18"], "High"),

            # Phase 4: Reliability and Polish (Days 20–25)
            (20, "Phase 4: Reliability and Polish", "Comprehensive Edge-Case Testing & Fuzz Testing",
             "Subject parsers, serializers, and buffers to fuzzed inputs, corrupted packets, and extreme values.",
             ["Fuzz testing harness with NaN, Inf, empty payloads, and huge tags", "Defensive boundary validation prevents unhandled exceptions or crashes", "All fuzzer tests integrated into regular pytest suite"],
             ["tests/test_fuzz_boundary.py"], ["task-day-19"], "Medium"),
            (21, "Phase 4: Reliability and Polish", "Concurrency Hardening & Race Condition Elimination",
             "Audit multithreaded and asynchronous primitives using thread stress tests to verify thread safety.",
             ["Thread-safety stress tests executing 20 concurrent writer threads", "Zero race conditions or data corruption verified under lock profiling", "Documented concurrency guidelines"],
             ["tests/test_concurrency.py"], ["task-day-20"], "High"),
            (22, "Phase 4: Reliability and Polish", "Database Query Optimization & WAL Checkpointing",
             "Optimize SQLite indexes, implement automated PRAGMA optimize, and tune WAL checkpoint intervals.",
             ["Database query latency reduced by >40% on historical timerange scans", "Scheduled WAL auto-checkpointing prevents unbounded WAL file growth", "Benchmark tests asserting sub-10ms query times on 1M rows"],
             ["src/storage/sqlite_optimizer.py", "tests/test_storage_optimization.py"], ["task-day-21"], "Medium"),
            (23, "Phase 4: Reliability and Polish", "Circuit Breaker & Graceful Degradation Policy",
             "Implement circuit breaker pattern for downstream storage and external dispatchers under load.",
             ["Circuit breaker with CLOSED, OPEN, HALF_OPEN states", "Graceful shedding of non-critical metrics when disk I/O saturates", "Unit tests verifying circuit state transitions and automatic recovery"],
             ["src/core/circuit_breaker.py", "tests/test_circuit_breaker.py"], ["task-day-22"], "Medium"),
            (24, "Phase 4: Reliability and Polish", "Security Hardening, Dependency Audit, and Secret Scrubbing",
             "Run dependency vulnerability check, configure secure defaults, and enforce TLS/token validation.",
             ["Zero high/critical security vulnerabilities in project dependencies", "Internal logs scrub sensitive tokens, passwords, and private IPs", "Automated security test asserts sanitized log output"],
             ["src/security/sanitizer.py", "tests/test_security_audit.py"], ["task-day-23"], "Low"),
            (25, "Phase 4: Reliability and Polish", "Full Regression & 90%+ Test Coverage Audit",
             "Execute entire test suite across all modules, asserting high branch coverage and clean pass.",
             ["Overall project test suite passes 100% cleanly", "All critical packages achieve >90% test coverage", "Generated coverage report and quality audit checklist"],
             ["tests/test_full_regression.py", "reports/quality_audit.md"], ["task-day-24"], "Medium"),

            # Phase 5: Release (Days 26–30)
            (26, "Phase 5: Release", "Production Configuration Engine & Environment Profiles",
             "Implement flexible configuration engine supporting dev, staging, and prod environment profiles.",
             ["Typed configuration model with hierarchical overriding (file < env < CLI)", "Strict validation with informative error messages for missing required keys", "Config tests verifying environment profiles"],
             ["src/core/profile_config.py", "tests/test_profile_config.py"], ["task-day-25"], "Low"),
            (27, "Phase 5: Release", "Containerization & Multi-Arch Dockerfile Configuration",
             "Create lightweight multi-stage Dockerfile and docker-compose setup for zero-friction deployment.",
             ["Multi-stage Dockerfile producing minimal, secure production image (<80MB)", "docker-compose.yml orchestrating collector, Prometheus exporter, and sample app", "Container build and startup verified via automated script"],
             ["Dockerfile", "docker-compose.yml", ".dockerignore"], ["task-day-26"], "Medium"),
            (28, "Phase 5: Release", "End-to-End Production Verification & Smoke Test Suite",
             "Deploy containerized agent in isolated sandbox and execute automated smoke test suite.",
             ["Production sandbox deployment script validates startup within 3 seconds", "Smoke test suite exercises all API endpoints, ingestion, and querying", "Clean shutdown test verifies zero data loss during SIGTERM"],
             ["scripts/smoke_test.py", "tests/test_smoke.py"], ["task-day-27"], "Medium"),
            (29, "Phase 5: Release", "Comprehensive Developer Guide, Architecture Specs, and API Docs",
             "Write complete documentation covering architecture, REST API references, configuration, and tutorials.",
             ["Comprehensive README.md with architecture diagrams, quickstart, and badges", "Interactive API documentation with curl and Python code samples", "Runbooks for production operations and troubleshooting"],
             ["README.md", "docs/api_reference.md", "docs/runbook.md"], ["task-day-28"], "Low"),
            (30, "Phase 5: Release", "Final Acceptance Audit, Release v1.0.0 Tagging, and 30-Day Retrospective",
             "Perform final acceptance audit, package distribution artifacts, and publish 30-day milestone summary.",
             ["All 30 daily acceptance criteria verified 100% complete", "Changelog and release notes published for v1.0.0", "30-day project retrospective report generated documenting achievements"],
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
