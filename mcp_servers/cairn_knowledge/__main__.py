"""Entry point for ``python -m mcp_servers.cairn_knowledge``.

Starts the cairn_knowledge MCP stdio server that wraps cairn_query tools
over the Model Context Protocol stdio transport.
"""

from .server import run

run()
