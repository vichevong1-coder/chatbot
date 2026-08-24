"""Unit tests for agent tools and ReAct agent loop."""

from __future__ import annotations

import pytest
from app.core.agent.tools import AgentTools
from app.core.agent.react_agent import ReActAgent

pytestmark = pytest.mark.anyio


class FakeClients:
    def __init__(self) -> None:
        self.retrieval = None
        self.profile = None
        self.solver = None


async def test_agent_tools_declarations():
    clients = FakeClients()
    tools = AgentTools(clients)
    decls = tools.declarations()
    assert len(decls) == 4
    names = {d["name"] for d in decls}
    assert "tool_query_curriculum" in names
    assert "tool_get_student_mastery" in names
    assert "tool_generate_custom_exercise" in names
    assert "tool_verify_solution" in names


async def test_tool_generate_custom_exercise():
    clients = FakeClients()
    tools = AgentTools(clients)
    res = await tools.tool_generate_custom_exercise("multiplication", difficulty=1)
    assert res["id"] == "dyn-mult-1"
    assert "គណនា" in res["problem_statement_khmer"]


async def test_react_agent_turn():
    clients = FakeClients()
    agent = ReActAgent(clients)
    result = await agent.execute_turn(
        prompt="I want to practice multiplication",
        student_id="anonymous",
        grade=4,
        language="km",
    )
    assert result["status"] == "completed"
    assert result["generated_exercise"] is not None
    assert len(result["tools_used"]) >= 1
