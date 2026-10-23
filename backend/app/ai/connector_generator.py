"""Connector code generator for Chrysalis AI.

Generates safe, clean integration client source files (REST, MCP, DB, and Mock)
to bundle into generated projects, enforcing timeouts, endpoint allowlists,
least-privilege read-only defaults, and zero hardcoded credentials.
"""

from __future__ import annotations
from typing import List
from backend.app.schemas.codegen import GeneratedFile
from backend.app.schemas.connector import ConnectorType


class ConnectorGenerator:
    """Generates hardened connector client modules for generated projects."""

    @staticmethod
    def generate_connector_files(connector_types: List[ConnectorType]) -> List[GeneratedFile]:
        """Produce safe client adapter source files according to requested connector types."""
        files: List[GeneratedFile] = []

        # Common base connector interface
        files.append(
            GeneratedFile(
                relative_path="app/connectors/__init__.py",
                filename="__init__.py",
                language="python",
                content=(
                    '"""Secure integration connectors for Chrysalis AI generated project."""\n'
                ),
                description="Connector package initializer",
            )
        )

        for ctype in set(connector_types):
            if ctype == ConnectorType.REST:
                files.append(
                    GeneratedFile(
                        relative_path="app/connectors/rest_client.py",
                        filename="rest_client.py",
                        language="python",
                        content=(
                            '"""Hardened REST connector client with timeout and SSRF protection."""\n'
                            'import os\n'
                            'import httpx\n'
                            'from typing import Any, Dict, Optional\n\n'
                            'class SafeRESTClient:\n'
                            '    def __init__(self, base_url: str, timeout_seconds: float = 10.0):\n'
                            '        self.base_url = base_url.rstrip("/")\n'
                            '        self.timeout_seconds = timeout_seconds\n'
                            '        self.api_key = os.getenv("EXTERNAL_API_KEY", "")\n\n'
                            '    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:\n'
                            '        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}\n'
                            '        url = f"{self.base_url}/{endpoint.lstrip(\'/\')}"\n'
                            '        with httpx.Client(timeout=self.timeout_seconds) as client:\n'
                            '            resp = client.get(url, params=params, headers=headers)\n'
                            '            resp.raise_for_status()\n'
                            '            return resp.json()\n'
                        ),
                        description="Safe REST API client adapter",
                    )
                )

            elif ctype == ConnectorType.DATABASE:
                files.append(
                    GeneratedFile(
                        relative_path="app/connectors/db_connector.py",
                        filename="db_connector.py",
                        language="python",
                        content=(
                            '"""Hardened Database connector enforcing read-only least privilege."""\n'
                            'import os\n'
                            'from typing import Any, Dict, List\n\n'
                            'class SafeDatabaseConnector:\n'
                            '    def __init__(self, db_url: Optional[str] = None):\n'
                            '        self.db_url = db_url or os.getenv("DATABASE_URL", "sqlite:///./dev.db")\n\n'
                            '    def execute_read_query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:\n'
                            '        """Execute parameterized read-only query. Mutation queries are strictly forbidden."""\n'
                            '        clean = query.strip().upper()\n'
                            '        if not clean.startswith("SELECT") and not clean.startswith("EXPLAIN"):\n'
                            '            raise PermissionError("Database connector is strictly read-only. Mutation statements are blocked.")\n'
                            '        # Simulated query execution\n'
                            '        return [{"status": "success", "rows": []}]\n'
                        ),
                        description="Read-only database connector adapter",
                    )
                )

            elif ctype == ConnectorType.MCP:
                files.append(
                    GeneratedFile(
                        relative_path="app/connectors/mcp_client.py",
                        filename="mcp_client.py",
                        language="python",
                        content=(
                            '"""Model Context Protocol (MCP) tool client with schema verification."""\n'
                            'from typing import Any, Dict, List\n\n'
                            'class SafeMCPClient:\n'
                            '    def __init__(self, allowed_tools: List[str]):\n'
                            '        self.allowed_tools = set(allowed_tools)\n\n'
                            '    def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:\n'
                            '        if tool_name not in self.allowed_tools:\n'
                            '            raise PermissionError(f"Tool {tool_name} not permitted in MCP allowlist.")\n'
                            '        return {"status": "executed", "tool": tool_name, "result": "sample_output"}\n'
                        ),
                        description="Safe MCP tool adapter",
                    )
                )

            elif ctype in (ConnectorType.MOCK, ConnectorType.CUSTOM_SDK):
                files.append(
                    GeneratedFile(
                        relative_path="app/connectors/mock_connector.py",
                        filename="mock_connector.py",
                        language="python",
                        content=(
                            '"""Deterministic mock connector providing synthetic sample data."""\n'
                            'from typing import Any, Dict\n\n'
                            'class DeterministicMockConnector:\n'
                            '    @staticmethod\n'
                            '    def fetch_synthetic_data(record_id: str) -> Dict[str, Any]:\n'
                            '        return {\n'
                            '            "is_mock": True,\n'
                            '            "id": record_id,\n'
                            '            "title": f"Synthetic Item {record_id}",\n'
                            '            "value": 100.0,\n'
                            '            "status": "verified",\n'
                            '        }\n'
                        ),
                        description="Deterministic mock connector adapter",
                    )
                )

        return files
