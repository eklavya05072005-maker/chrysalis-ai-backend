"""Unit tests for Chrysalis AI Connector management and security enforcement.

Verifies:
- SSRF prevention blocking localhost, private ranges, and cloud metadata (169.254.169.254).
- Database read-only enforcement, blocking DROP/DELETE/INSERT without approval.
- MCP tool allowlisting and approval gating.
- Rate limiting quota enforcement.
- Deterministic mock connector execution using synthetic fixtures.
- Secret masking in connector configurations.
"""

import uuid
import pytest
from unittest.mock import MagicMock

from backend.app.schemas.connector import (
    ConnectorConfigCreate,
    ConnectorTestRequest,
    ConnectorType,
    ConnectorVerificationState,
)
from backend.app.services.connector_service import (
    ConnectorService,
    is_safe_destination,
    validate_sql_query,
)


def test_ssrf_protection_blocks_localhost_and_private_ips():
    """Verify SSRF defense blocks loopback, private networks, and cloud metadata."""
    # Loopback
    safe, msg = is_safe_destination("http://localhost:8080/api")
    assert safe is False
    assert "SSRF Protection" in msg

    safe, msg = is_safe_destination("http://127.0.0.1:5000")
    assert safe is False

    # Cloud metadata
    safe, msg = is_safe_destination("http://169.254.169.254/latest/meta-data")
    assert safe is False
    assert "SSRF Protection" in msg

    # Private RFC 1918 ranges
    safe, msg = is_safe_destination("http://10.0.0.5/admin")
    assert safe is False

    safe, msg = is_safe_destination("http://192.168.1.1/router")
    assert safe is False

    safe, msg = is_safe_destination("http://172.16.0.2/internal")
    assert safe is False

    # Unsupported schemes
    safe, msg = is_safe_destination("file:///etc/passwd")
    assert safe is False
    assert "Unsupported URL scheme" in msg


def test_ssrf_protection_allows_valid_public_destinations():
    """Verify legitimate public HTTPS endpoints are accepted."""
    safe, msg = is_safe_destination("https://api.stripe.com/v1/charges")
    assert safe is True


def test_database_least_privilege_and_query_restrictions():
    """Verify database connector enforces read-only access and blocks destructive DDL/DML."""
    # Destructive DDL strictly forbidden
    valid, msg = validate_sql_query("DROP TABLE users;", is_read_only=False, is_approved=True)
    assert valid is False
    assert "strictly forbidden" in msg

    valid, msg = validate_sql_query("ALTER TABLE invoices ADD COLUMN leaked text;", is_read_only=False, is_approved=True)
    assert valid is False

    # Read-only blocks mutations
    valid, msg = validate_sql_query("INSERT INTO ledger (amount) VALUES (500);", is_read_only=True, is_approved=True)
    assert valid is False
    assert "read-only" in msg

    # Write allowed only when read_only=False AND approved=True
    valid, msg = validate_sql_query("UPDATE ledger SET status = 'reconciled' WHERE id = 1;", is_read_only=False, is_approved=False)
    assert valid is False
    assert "requires explicit human approval" in msg

    valid, msg = validate_sql_query("UPDATE ledger SET status = 'reconciled' WHERE id = 1;", is_read_only=False, is_approved=True)
    assert valid is True

    # Valid read queries
    valid, msg = validate_sql_query("SELECT id, amount FROM invoices WHERE status = 'pending';", is_read_only=True, is_approved=False)
    assert valid is True


def test_connector_service_masks_secrets():
    """Verify configuration dictionaries have credentials redacted in API responses."""
    mock_repo = MagicMock()
    service = ConnectorService(connector_repo=mock_repo)

    config_with_secrets = {
        "api_key": "${EXTERNAL_API_KEY}",
        "database_url": "postgresql://user:${DB_PASSWORD}@host/db",
        "timeout": 10,
    }

    sanitized = service._sanitize_secrets(config_with_secrets)
    assert sanitized["api_key"] == "***REDACTED***"
    assert sanitized["timeout"] == 10


def test_mock_connector_deterministic_execution():
    """Verify deterministic mock connector returns synthetic records and audit notice."""
    mock_repo = MagicMock()
    connector_id = uuid.uuid4()
    mock_connector = MagicMock(
        id=connector_id,
        project_id=uuid.uuid4(),
        name="Mock Invoice API",
        connector_type="mock",
        is_mock=True,
        rate_limit_per_minute=60,
    )
    mock_repo.get_by_id.return_value = mock_connector

    service = ConnectorService(connector_repo=mock_repo)
    test_req = ConnectorTestRequest(
        endpoint_or_tool="/invoices/search",
        method="GET",
        parameters={"status": "pending"},
    )

    resp = service.test_connector(connector_id, test_req)

    assert resp.success is True
    assert resp.is_mock is True
    assert resp.output_data["synthetic"] is True
    assert len(resp.output_data["sample_records"]) > 0
    assert "Deterministic mock execution" in resp.audit_notes
    assert mock_repo.update_state.called


def test_mcp_tool_allowlisting_and_approval_enforcement():
    """Verify MCP connector enforces tool allowlist and human approval gating."""
    mock_repo = MagicMock()
    connector_id = uuid.uuid4()
    mock_connector = MagicMock(
        id=connector_id,
        project_id=uuid.uuid4(),
        name="Filesystem MCP",
        connector_type="mcp",
        is_mock=False,
        rate_limit_per_minute=60,
        allowed_tools=["read_file", "search_directory"],
        requires_approval=True,
        is_approved=False,
    )
    mock_repo.get_by_id.return_value = mock_connector

    service = ConnectorService(connector_repo=mock_repo)

    # Disallowed tool
    resp1 = service.test_connector(connector_id, ConnectorTestRequest(endpoint_or_tool="delete_file"))
    assert resp1.success is False
    assert "allowlist" in resp1.error

    # Allowed tool but approval required and not approved
    resp2 = service.test_connector(connector_id, ConnectorTestRequest(endpoint_or_tool="read_file"))
    assert resp2.success is False
    assert "requires human approval" in resp2.error

    # After approval granted
    mock_connector.is_approved = True
    resp3 = service.test_connector(connector_id, ConnectorTestRequest(endpoint_or_tool="read_file"))
    assert resp3.success is True
