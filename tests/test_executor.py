"""Tests for CodingAgent task execution and deliverable generation."""

from pathlib import Path
from src.config import load_config
from src.executor.agent import CodingAgent
from src.executor.tools import WorkspaceTools
from src.providers.mock_provider import MockLLMProvider
from src.state.manager import Task, TaskStatus


def test_executor_generates_deliverables(tmp_path: Path):
    config = load_config(Path("project.config.yaml"))
    config.workspace_root = tmp_path
    config.run_tests_before_commit = False  # Isolate file generation
    config.tech_stack.toolchain.lint_command = ""
    config.tech_stack.toolchain.build_command = ""

    tools = WorkspaceTools(tmp_path)
    mock_provider = MockLLMProvider()
    agent = CodingAgent(config, provider=mock_provider, tools=tools)

    task = Task(
        id="task-day-01",
        day_number=1,
        title="Telemetry Models and Validation",
        phase="Phase 1: Foundation",
        description="Implement data models",
        acceptance_criteria=["Models defined", "Tests pass"],
        deliverables=["src/models.py", "tests/test_models.py"],
        status=TaskStatus.PENDING,
    )

    result = agent.execute_task(task)
    assert result.success is True
    assert len(result.changed_files) == 2
    assert (tmp_path / "src" / "models.py").exists()
    assert (tmp_path / "tests" / "test_models.py").exists()
