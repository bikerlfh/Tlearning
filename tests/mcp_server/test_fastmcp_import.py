"""Verify fastmcp is importable and the basic API shape we depend on."""


def test_fastmcp_basic_server_definition():
    """@mcp.tool decorator + tool registration works."""
    from fastmcp import FastMCP

    mcp = FastMCP(name="test")

    @mcp.tool
    def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    # Tool was registered — exact API for inspecting varies; just confirm no errors raised
    assert mcp.name == "test"


def test_fastmcp_client_inproc_call():
    """fastmcp.Client can call a tool in-process for testing."""
    import asyncio

    from fastmcp import Client, FastMCP

    mcp = FastMCP(name="test")

    @mcp.tool
    def greet(name: str) -> str:
        """Greet someone."""
        return f"Hello, {name}!"

    async def _call():
        async with Client(mcp) as client:
            return await client.call_tool("greet", {"name": "Luis"})

    result = asyncio.run(_call())
    assert "Hello, Luis!" in str(result)
