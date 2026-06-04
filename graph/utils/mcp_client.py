from pathlib import Path
from mcp import StdioServerParameters


ROOT_DIR = Path(__file__).resolve().parents[2]
MCP_SERVER_PATH = ROOT_DIR / "mcp_server.py"

server_params = StdioServerParameters(
    command="uv",
    args=["run", "python", str(MCP_SERVER_PATH)],
)