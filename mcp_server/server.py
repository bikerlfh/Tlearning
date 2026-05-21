"""FastMCP server instance.

Tools are imported from `mcp_server.tools` and registered as MCP tools.
For HTTP transport, run `python -m mcp_server` (see __main__.py).
For in-process testing, use `fastmcp.Client(mcp)`.
"""

from fastmcp import FastMCP

from . import tools

mcp = FastMCP(name="tlearning")

# fastmcp 3.3.1: `mcp.tool` accepts `name_or_fn` as its first positional argument,
# so calling it directly with a pre-defined function registers that function as a tool.
mcp.tool(tools.remember_word)
mcp.tool(tools.find_word)
mcp.tool(tools.mark_as_known)
mcp.tool(tools.list_due_today)
