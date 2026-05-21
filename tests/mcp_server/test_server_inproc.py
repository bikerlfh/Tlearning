import asyncio

import pytest

from artifacts.models import Artifact
from mcp_server.auth import set_current_user


@pytest.mark.django_db(transaction=True)
def test_remember_word_via_inproc_client(user):
    """Smoke-test the in-process FastMCP Client → tool function path.

    Uses transaction=True because fastmcp 3.x runs sync tools in a worker
    thread (run_in_thread=True by default), which gets its own DB connection
    and cannot see uncommitted data from the test's outer transaction.
    """
    from fastmcp import Client

    from mcp_server.server import mcp

    set_current_user(user)

    async def _call():
        async with Client(mcp) as client:
            return await client.call_tool(
                "remember_word",
                {
                    "lemma": "perspicacious",
                    "meaning": "showing keen insight",
                    "type": "word",
                    "part_of_speech": "adjective",
                },
            )

    asyncio.run(_call())
    assert Artifact.objects.filter(user=user, lemma="perspicacious").exists()


@pytest.mark.django_db(transaction=True)
def test_all_four_tools_registered(user):
    """list_tools should show our 4 high-level tools."""
    from fastmcp import Client

    from mcp_server.server import mcp

    set_current_user(user)

    async def _ls():
        async with Client(mcp) as client:
            return await client.list_tools()

    tools = asyncio.run(_ls())
    # tools may be a list of tool objects or dicts; just check names appear somewhere
    serialized = str(tools)
    for name in ("remember_word", "find_word", "mark_as_known", "list_due_today"):
        assert name in serialized, f"Missing tool: {name} in {serialized}"
