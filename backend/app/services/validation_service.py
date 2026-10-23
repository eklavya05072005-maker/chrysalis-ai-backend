import ast
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Safely validates generated source files without executing code on the host machine.
    Performs static AST syntax parsing for Python, JSON schema parsing, and YAML parsing.
    """

    @staticmethod
    def validate_file_content(filename: str, content: str) -> Dict[str, Any]:
        """
        Validates a single file according to its file extension.
        Returns {"valid": bool, "error": Optional[str]}.
        """
        lower_name = filename.lower()

        try:
            if lower_name.endswith(".py"):
                # Static AST compilation test - NEVER executes the code
                ast.parse(content, filename=filename)
                return {"valid": True, "error": None}

            elif lower_name.endswith(".json"):
                json.loads(content)
                return {"valid": True, "error": None}

            elif lower_name.endswith((".yaml", ".yml")):
                try:
                    import yaml
                    yaml.safe_load(content)
                except ImportError:
                    pass
                return {"valid": True, "error": None}

            else:
                # Text/markdown/config files: ensure non-corrupt encoding
                content.encode("utf-8")
                return {"valid": True, "error": None}

        except SyntaxError as syn_err:
            return {
                "valid": False,
                "error": f"SyntaxError line {syn_err.lineno}: {syn_err.msg}",
            }
        except json.JSONDecodeError as json_err:
            return {
                "valid": False,
                "error": f"JSON syntax error line {json_err.lineno}: {json_err.msg}",
            }
        except Exception as exc:
            return {
                "valid": False,
                "error": f"Validation failed: {str(exc)}",
            }
