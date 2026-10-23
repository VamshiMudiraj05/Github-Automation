"""Tests for 30-day roadmap generation, persistence, and markdown export."""

from pathlib import Path
from src.config import load_config
from src.planner.generator import RoadmapGenerator
from src.providers.mock_provider import MockLLMProvider
from src.state.manager import StateManager


def test_roadmap_generates_30_tasks(tmp_path: Path):
    config = load_config(Path("project.config.yaml"))
    config.workspace_root = tmp_path

    state_mgr = StateManager(tmp_path / "test_agent_state.db")
    mock_provider = MockLLMProvider()
    generator = RoadmapGenerator(config, state_mgr, provider=mock_provider)

    tasks = generator.generate_and_save(force=True)
    assert len(tasks) == 30
    assert state_mgr.has_roadmap() is True

    # Validate 5 phases
    phases = {t.phase for t in tasks}
    assert "Phase 1: Foundation" in phases
    assert "Phase 2: Core Functionality" in phases
    assert "Phase 3: Advanced Features" in phases
    assert "Phase 4: Reliability and Polish" in phases
    assert "Phase 5: Release" in phases

    # Validate generated files
    assert (tmp_path / "ROADMAP.md").exists()
    assert (tmp_path / "PROGRESS.md").exists()

    roadmap_text = (tmp_path / "ROADMAP.md").read_text(encoding="utf-8")
    assert "30-Day Engineering Roadmap" in roadmap_text
    assert "Day 01" in roadmap_text
    assert "Day 30" in roadmap_text
