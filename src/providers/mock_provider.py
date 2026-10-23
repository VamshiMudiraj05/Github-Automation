"""Deterministic Mock LLM Provider for unit testing, offline dry-runs, and CI verification."""

import json
from typing import Optional
from src.providers.base import LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    """Provides canned yet intelligent responses for automated tests and dry runs."""

    def __init__(self, model: str = "mock-model"):
        self.model = model
        self.call_count = 0
        self.last_prompt = None

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_mode: bool = False,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        self.call_count += 1
        self.last_prompt = prompt

        if "roadmap" in prompt.lower() or "30-day" in prompt.lower():
            # Generate a 30-day roadmap JSON
            roadmap_items = []
            phases = [
                ("Phase 1: Foundation", 1, 5),
                ("Phase 2: Core Functionality", 6, 12),
                ("Phase 3: Advanced Features", 13, 19),
                ("Phase 4: Reliability and Polish", 20, 25),
                ("Phase 5: Release", 26, 30),
            ]
            for phase_name, start_day, end_day in phases:
                for day in range(start_day, end_day + 1):
                    roadmap_items.append({
                        "id": f"task-day-{day:02d}",
                        "day_number": day,
                        "title": f"Day {day:02d} Milestone Deliverable",
                        "phase": phase_name,
                        "description": f"Engineered implementation of Day {day} architecture and features.",
                        "acceptance_criteria": [
                            f"Milestone {day} functional code written and reviewed",
                            f"Automated unit tests for day {day} pass without error",
                            "Documentation and types updated",
                        ],
                        "deliverables": [f"src/module_day_{day}.py", f"tests/test_day_{day}.py"],
                        "dependencies": [f"task-day-{day-1:02d}"] if day > 1 else [],
                        "complexity": "Low" if day <= 5 else ("Medium" if day <= 20 else "High"),
                    })

            if json_mode:
                content = json.dumps({"tasks": roadmap_items})
            else:
                content = f"```json\n{json.dumps({'tasks': roadmap_items}, indent=2)}\n```"

            return LLMResponse(content=content, prompt_tokens=50, completion_tokens=300)

        # Default coding response
        content = (
            "# Auto-generated implementation by Autonomous Project Builder Agent\n"
            "# Verified acceptance criteria completed successfully.\n"
        )
        return LLMResponse(content=content, prompt_tokens=20, completion_tokens=30)

    def health_check(self) -> bool:
        return True
