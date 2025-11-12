#!/usr/bin/env python3
"""
Generate API Reference Documentation from OpenAPI Spec

This script fetches the OpenAPI schema from the running API and generates
comprehensive API reference documentation in Markdown format.

Usage:
    python scripts/docs/generate_api_reference.py
    python scripts/docs/generate_api_reference.py --api-url http://localhost:8000
    python scripts/docs/generate_api_reference.py --output docs/API_REFERENCE.md

Requirements:
    - API must be running (defaults to http://localhost:8000)
    - Or provide path to openapi.json file with --schema-file option
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests


class APIReferenceGenerator:
    """Generate API reference documentation from OpenAPI spec."""

    def __init__(self, openapi_spec: Dict):
        self.spec = openapi_spec
        self.info = openapi_spec.get("info", {})
        self.servers = openapi_spec.get("servers", [])
        self.paths = openapi_spec.get("paths", {})
        self.components = openapi_spec.get("components", {})
        self.tags = openapi_spec.get("tags", [])

    def generate(self) -> str:
        """Generate complete API reference markdown."""
        sections = [
            self._generate_header(),
            self._generate_overview(),
            self._generate_base_url(),
            self._generate_authentication(),
            self._generate_rate_limiting(),
            self._generate_endpoints_by_tag(),
            self._generate_schemas(),
            self._generate_errors(),
            self._generate_footer(),
        ]
        return "\n\n".join(sections)

    def _generate_header(self) -> str:
        """Generate document header."""
        title = self.info.get("title", "API Reference")
        version = self.info.get("version", "1.0.0")
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        return f"""# {title}

**Version:** {version}
**Generated:** {generated_at}

> **⚠️ Auto-generated Documentation**
> This reference is automatically generated from the OpenAPI specification.
> For tutorials and guides, see [API_USAGE_GUIDE.md](./API_USAGE_GUIDE.md)
"""

    def _generate_overview(self) -> str:
        """Generate overview section."""
        description = self.info.get("description", "").strip()
        contact = self.info.get("contact", {})
        license_info = self.info.get("license", {})

        content = "## Overview\n\n"

        if description:
            # Clean up description (remove markdown headers if present)
            desc_lines = [line for line in description.split('\n')
                         if not line.strip().startswith('#')]
            content += '\n'.join(desc_lines).strip() + "\n\n"

        if contact:
            content += "### Contact\n\n"
            if contact.get("name"):
                content += f"**Team:** {contact['name']}  \n"
            if contact.get("email"):
                content += f"**Email:** {contact['email']}  \n"
            if contact.get("url"):
                content += f"**Website:** {contact['url']}  \n"
            content += "\n"

        if license_info:
            content += "### License\n\n"
            if license_info.get("name"):
                content += f"**License:** {license_info['name']}  \n"
            if license_info.get("url"):
                content += f"**URL:** {license_info['url']}  \n"
            content += "\n"

        return content

    def _generate_base_url(self) -> str:
        """Generate base URL section."""
        content = "## Base URL\n\n"

        if self.servers:
            content += "```\n"
            for server in self.servers:
                url = server.get("url", "")
                description = server.get("description", "")
                if description:
                    content += f"{url}  # {description}\n"
                else:
                    content += f"{url}\n"
            content += "```\n"
        else:
            content += "```\nhttps://api.ibco-ca.us/api/v1\n```\n"

        return content

    def _generate_authentication(self) -> str:
        """Generate authentication section."""
        security_schemes = self.components.get("securitySchemes", {})

        content = "## Authentication\n\n"

        if security_schemes:
            for name, scheme in security_schemes.items():
                scheme_type = scheme.get("type", "").title()
                content += f"### {name} ({scheme_type})\n\n"

                if scheme.get("description"):
                    content += f"{scheme['description']}\n\n"

                if scheme_type == "Http" and scheme.get("scheme") == "bearer":
                    content += "Include token in Authorization header:\n\n"
                    content += "```\nAuthorization: Bearer YOUR_API_TOKEN\n```\n\n"
        else:
            content += "Most endpoints are **public** and do not require authentication.\n\n"
            content += "Admin endpoints require an API token. Contact data@ibco-ca.us for access.\n"

        return content

    def _generate_rate_limiting(self) -> str:
        """Generate rate limiting section."""
        return """## Rate Limiting

API requests are rate limited by tier:

| Tier | Limit | Authentication |
|------|-------|----------------|
| Public | 100 requests/hour | None required |
| Researcher | 1,000 requests/hour | API token required |
| Admin | Unlimited | Admin token required |

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1609459200
```

When rate limit is exceeded, you'll receive a `429 Too Many Requests` response with a `Retry-After` header.
"""

    def _generate_endpoints_by_tag(self) -> str:
        """Generate endpoints organized by tag."""
        content = "## Endpoints\n\n"

        # Group endpoints by tag
        endpoints_by_tag = {}
        for path, methods in self.paths.items():
            for method, operation in methods.items():
                if method in ["get", "post", "put", "patch", "delete"]:
                    tags = operation.get("tags", ["Untagged"])
                    for tag in tags:
                        if tag not in endpoints_by_tag:
                            endpoints_by_tag[tag] = []
                        endpoints_by_tag[tag].append((path, method, operation))

        # Find tag descriptions
        tag_descriptions = {tag["name"]: tag.get("description", "")
                          for tag in self.tags}

        # Generate sections for each tag
        for tag, endpoints in sorted(endpoints_by_tag.items()):
            # Skip admin tags in public docs
            if tag in ["Admin", "Token Management", "Data Quality",
                      "Data Refresh", "Validation"]:
                continue

            content += f"### {tag}\n\n"

            if tag in tag_descriptions:
                content += f"{tag_descriptions[tag]}\n\n"

            for path, method, operation in endpoints:
                content += self._generate_endpoint(path, method, operation)
                content += "\n---\n\n"

        return content

    def _generate_endpoint(self, path: str, method: str, operation: Dict) -> str:
        """Generate documentation for a single endpoint."""
        summary = operation.get("summary", "")
        description = operation.get("description", "")
        operation_id = operation.get("operationId", "")

        # Header
        content = f"#### `{method.upper()} {path}`\n\n"

        if summary:
            content += f"**{summary}**\n\n"

        if description and description != summary:
            content += f"{description}\n\n"

        # Parameters
        parameters = operation.get("parameters", [])
        if parameters:
            content += "**Parameters:**\n\n"

            # Group by location
            path_params = [p for p in parameters if p.get("in") == "path"]
            query_params = [p for p in parameters if p.get("in") == "query"]
            header_params = [p for p in parameters if p.get("in") == "header"]

            if path_params:
                content += "*Path Parameters:*\n\n"
                content += "| Name | Type | Required | Description |\n"
                content += "|------|------|----------|-------------|\n"
                for param in path_params:
                    content += self._format_parameter_row(param)
                content += "\n"

            if query_params:
                content += "*Query Parameters:*\n\n"
                content += "| Name | Type | Required | Description |\n"
                content += "|------|------|----------|-------------|\n"
                for param in query_params:
                    content += self._format_parameter_row(param)
                content += "\n"

        # Request body
        request_body = operation.get("requestBody", {})
        if request_body:
            content += "**Request Body:**\n\n"
            request_content = request_body.get("content", {})
            for media_type, schema_info in request_content.items():
                content += f"*Content-Type:* `{media_type}`\n\n"
                schema = schema_info.get("schema", {})
                if schema:
                    content += "```json\n"
                    content += self._schema_to_example(schema)
                    content += "\n```\n\n"

        # Responses
        responses = operation.get("responses", {})
        if responses:
            content += "**Responses:**\n\n"
            for status_code, response_info in sorted(responses.items()):
                description = response_info.get("description", "")
                content += f"*{status_code}* - {description}\n\n"

                response_content = response_info.get("content", {})
                for media_type, schema_info in response_content.items():
                    schema = schema_info.get("schema", {})
                    if schema:
                        content += "```json\n"
                        content += self._schema_to_example(schema)
                        content += "\n```\n\n"
                    break  # Only show first media type

        # Example
        content += self._generate_example_curl(path, method, operation)

        return content

    def _format_parameter_row(self, param: Dict) -> str:
        """Format a parameter as a table row."""
        name = param.get("name", "")
        param_schema = param.get("schema", {})
        param_type = param_schema.get("type", "string")
        required = "✓" if param.get("required", False) else ""
        description = param.get("description", "")

        return f"| `{name}` | {param_type} | {required} | {description} |\n"

    def _schema_to_example(self, schema: Dict, depth: int = 0) -> str:
        """Convert JSON schema to example JSON."""
        if "$ref" in schema:
            # Reference to component schema
            ref_path = schema["$ref"].split("/")
            ref_name = ref_path[-1]
            schemas = self.components.get("schemas", {})
            if ref_name in schemas:
                return self._schema_to_example(schemas[ref_name], depth)
            return "{}"

        schema_type = schema.get("type", "object")

        if schema_type == "object":
            properties = schema.get("properties", {})
            if not properties:
                return "{}"

            indent = "  " * depth
            lines = ["{"]

            for i, (prop_name, prop_schema) in enumerate(properties.items()):
                is_last = i == len(properties) - 1
                comma = "" if is_last else ","

                prop_example = self._schema_to_example_value(prop_schema, depth + 1)
                lines.append(f'{indent}  "{prop_name}": {prop_example}{comma}')

            lines.append(indent + "}")
            return "\n".join(lines)

        elif schema_type == "array":
            items = schema.get("items", {})
            item_example = self._schema_to_example_value(items, depth)
            return f"[{item_example}]"

        else:
            return self._schema_to_example_value(schema, depth)

    def _schema_to_example_value(self, schema: Dict, depth: int = 0) -> str:
        """Convert schema to example value."""
        if "$ref" in schema:
            ref_path = schema["$ref"].split("/")
            ref_name = ref_path[-1]
            schemas = self.components.get("schemas", {})
            if ref_name in schemas:
                return self._schema_to_example(schemas[ref_name], depth)
            return "{}"

        schema_type = schema.get("type", "string")
        example = schema.get("example")

        if example is not None:
            if isinstance(example, str):
                return f'"{example}"'
            return str(example)

        # Default examples by type
        if schema_type == "string":
            return '"string"'
        elif schema_type == "integer":
            return "0"
        elif schema_type == "number":
            return "0.0"
        elif schema_type == "boolean":
            return "true"
        elif schema_type == "array":
            items = schema.get("items", {})
            item_val = self._schema_to_example_value(items, depth)
            return f"[{item_val}]"
        elif schema_type == "object":
            return self._schema_to_example(schema, depth)

        return "null"

    def _generate_example_curl(self, path: str, method: str, operation: Dict) -> str:
        """Generate curl example for endpoint."""
        base_url = "https://api.ibco-ca.us/api/v1"

        # Replace path parameters with examples
        example_path = path
        parameters = operation.get("parameters", [])
        for param in parameters:
            if param.get("in") == "path":
                param_name = param.get("name", "")
                example_value = param.get("example", "1")
                example_path = example_path.replace(f"{{{param_name}}}", str(example_value))

        full_url = base_url + example_path

        content = "**Example:**\n\n"
        content += "```bash\n"

        if method.upper() == "GET":
            content += f"curl \"{full_url}\"\n"
        elif method.upper() in ["POST", "PUT", "PATCH"]:
            content += f"curl -X {method.upper()} \"{full_url}\" \\\n"
            content += "  -H \"Content-Type: application/json\" \\\n"

            request_body = operation.get("requestBody", {})
            if request_body:
                content += "  -d '{"
                content += "...}'\n"
            else:
                content = content.rstrip(" \\\n") + "\n"
        elif method.upper() == "DELETE":
            content += f"curl -X DELETE \"{full_url}\"\n"

        content += "```\n"

        return content

    def _generate_schemas(self) -> str:
        """Generate schemas section."""
        schemas = self.components.get("schemas", {})
        if not schemas:
            return ""

        content = "## Data Models\n\n"
        content += "Common data structures used in API responses.\n\n"

        for schema_name, schema_def in sorted(schemas.items()):
            # Skip internal schemas
            if schema_name.startswith("_"):
                continue

            content += f"### {schema_name}\n\n"

            description = schema_def.get("description", "")
            if description:
                content += f"{description}\n\n"

            content += "```json\n"
            content += self._schema_to_example(schema_def)
            content += "\n```\n\n"

        return content

    def _generate_errors(self) -> str:
        """Generate error responses section."""
        return """## Error Responses

All errors follow a consistent format:

```json
{
  "error": "Error Type",
  "message": "Human-readable error message",
  "detail": "Additional details (optional)",
  "request_id": "unique-request-id"
}
```

### Common HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error occurred |
| 503 | Service Unavailable | API temporarily unavailable |

### Error Examples

**404 Not Found:**

```json
{
  "error": "Not Found",
  "message": "No risk score found for this city",
  "request_id": "req_abc123"
}
```

**429 Rate Limited:**

```json
{
  "error": "Rate Limit Exceeded",
  "message": "Rate limit exceeded. Retry after 60 seconds.",
  "request_id": "req_def456"
}
```

Response includes `Retry-After` header indicating when to retry.
"""

    def _generate_footer(self) -> str:
        """Generate document footer."""
        return """## Additional Resources

- **API Usage Guide**: [API_USAGE_GUIDE.md](./API_USAGE_GUIDE.md) - Tutorials and best practices
- **Developer Guide**: [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) - Contributing and extending
- **Code Examples**: [examples/](../examples/) - Python, JavaScript, curl, Jupyter
- **Interactive Docs**: [https://api.ibco-ca.us/docs](https://api.ibco-ca.us/docs) - Swagger UI
- **ReDoc**: [https://api.ibco-ca.us/redoc](https://api.ibco-ca.us/redoc) - Alternative docs

## Support

- **Email**: data@ibco-ca.us
- **Issues**: [GitHub Issues](https://github.com/your-org/vallejo-ibco-ca/issues)
- **Website**: [https://ibco-ca.us](https://ibco-ca.us)

---

*This documentation is automatically generated from the OpenAPI specification.*
*Last generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC") + "*"


def fetch_openapi_spec(api_url: str) -> Dict:
    """Fetch OpenAPI spec from running API."""
    openapi_url = f"{api_url.rstrip('/')}/openapi.json"

    try:
        response = requests.get(openapi_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching OpenAPI spec from {openapi_url}: {e}", file=sys.stderr)
        print("Ensure the API is running and accessible.", file=sys.stderr)
        sys.exit(1)


def load_openapi_from_file(schema_file: Path) -> Dict:
    """Load OpenAPI spec from file."""
    try:
        with open(schema_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Schema file not found: {schema_file}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from {schema_file}: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate API reference documentation from OpenAPI spec",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch from running API (default: http://localhost:8000)
  python scripts/docs/generate_api_reference.py

  # Specify API URL
  python scripts/docs/generate_api_reference.py --api-url http://localhost:8000

  # Load from file
  python scripts/docs/generate_api_reference.py --schema-file openapi.json

  # Custom output location
  python scripts/docs/generate_api_reference.py --output docs/API_REF.md
        """
    )

    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Base URL of running API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--schema-file",
        type=Path,
        help="Path to openapi.json file (alternative to fetching from API)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/API_REFERENCE.md"),
        help="Output file path (default: docs/API_REFERENCE.md)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    if args.verbose:
        print(f"Generating API reference documentation...")

    # Load OpenAPI spec
    if args.schema_file:
        if args.verbose:
            print(f"Loading OpenAPI spec from file: {args.schema_file}")
        openapi_spec = load_openapi_from_file(args.schema_file)
    else:
        if args.verbose:
            print(f"Fetching OpenAPI spec from API: {args.api_url}")
        openapi_spec = fetch_openapi_spec(args.api_url)

    # Generate documentation
    if args.verbose:
        print("Generating documentation...")

    generator = APIReferenceGenerator(openapi_spec)
    markdown_content = generator.generate()

    # Write to file
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown_content)

    print(f"✓ API reference generated: {args.output}")
    print(f"  Lines: {len(markdown_content.splitlines())}")
    print(f"  Size: {len(markdown_content)} bytes")

    if args.verbose:
        print(f"\nAPI Info:")
        print(f"  Title: {openapi_spec.get('info', {}).get('title')}")
        print(f"  Version: {openapi_spec.get('info', {}).get('version')}")
        print(f"  Endpoints: {len(openapi_spec.get('paths', {}))}")


if __name__ == "__main__":
    main()
