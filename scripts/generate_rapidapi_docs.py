#!/usr/bin/env python3
"""
Generate RapidAPI OpenAPI Spec

This script creates a customized OpenAPI JSON file for RapidAPI by:
1. Reading the base openapi.json file
2. Reading markdown documentation files from RapidAPI_Docs/
3. Replacing operationId, description, requestBody example, and response example
4. Removing 422 error responses
5. Writing the result to rapidapi.json

Usage:
    python scripts/generate_rapidapi_docs.py
    python scripts/generate_rapidapi_docs.py -u https://custom-url.example.com

Markdown Format Expected:
    ## Endpoint
    /api/v5/chart/birth-chart

    ## Name
    Birth Chart

    ## Description
    Full description text...

    ### Parameters
    - param1: description

    ## Request Body Example
    ```json
    { "subject": { ... } }
    ```

    ## Response Body Example
    ```json
    { "status": "OK", ... }
    ```
"""

import argparse
import json
import re
from pathlib import Path


# =============================================================================
# CONFIGURATION
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
OPENAPI_FILE = PROJECT_ROOT / "openapi.json"
RAPIDAPI_DOCS_DIR = PROJECT_ROOT / "RapidAPI_Docs"
OUTPUT_FILE = PROJECT_ROOT / "rapidapi.json"


# =============================================================================
# STEP 1: READ OPENAPI.JSON
# =============================================================================


def load_openapi() -> dict:
    """Load the base OpenAPI specification from openapi.json."""
    print(f"Loading: {OPENAPI_FILE}")

    with open(OPENAPI_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"  Found {len(data.get('paths', {}))} endpoints")
    return data


# =============================================================================
# STEP 2: PARSE MARKDOWN DOCUMENTATION FILES
# =============================================================================


def extract_endpoint(content: str) -> str | None:
    """
    Extract the endpoint path from markdown.

    Looks for:
        ## Endpoint
        /api/v5/chart/birth-chart
    """
    match = re.search(r"## Endpoint\s*\n(.+)", content)
    if match:
        return match.group(1).strip()
    return None


def extract_name(content: str) -> str | None:
    """
    Extract the operation name from markdown.

    Looks for:
        ## Name
        Birth Chart
    """
    match = re.search(r"## Name\s*\n(.+)", content)
    if match:
        return match.group(1).strip()
    return None


def extract_description(content: str) -> str:
    """
    Extract the description (including ### Parameters) from markdown.

    Looks for:
        ## Description
        Text...
        ### Parameters
        ...

    Stops at the next ## section.
    """
    match = re.search(r"## Description\s*\n(.*?)(?=\n## (?!#)|$)", content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def extract_request_body_example(content: str) -> dict | None:
    """
    Extract the request body example JSON from markdown.

    Looks for:
        ## Request Body Example
        ```json
        { ... }
        ```
    """
    match = re.search(
        r"## Request Body Example\s*\n```json\s*\n(.*?)\n```", content, re.DOTALL
    )
    if match:
        json_str = match.group(1).strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"    WARNING: Invalid JSON in Request Body Example: {e}")
            return None
    return None


def extract_response_body_example(content: str) -> dict | None:
    """
    Extract the response body example JSON from markdown.

    Looks for:
        ## Response Body Example
        ```json
        { ... }
        ```
    """
    match = re.search(
        r"## Response Body Example\s*\n```json\s*\n(.*?)\n```", content, re.DOTALL
    )
    if match:
        json_str = match.group(1).strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"    WARNING: Invalid JSON in Response Body Example: {e}")
            return None
    return None


def parse_markdown_file(file_path: Path) -> dict | None:
    """
    Parse a single markdown documentation file.

    Returns a dict with: endpoint, name, description, request_example, response_example
    Or None if required fields are missing.
    """
    content = file_path.read_text(encoding="utf-8")

    endpoint = extract_endpoint(content)
    name = extract_name(content)
    description = extract_description(content)
    request_example = extract_request_body_example(content)
    response_example = extract_response_body_example(content)

    # Validate required fields
    if not endpoint:
        print(f"  WARNING: No endpoint in {file_path.name}")
        return None

    if not name:
        print(f"  WARNING: No name in {file_path.name}")
        return None

    return {
        "endpoint": endpoint,
        "name": name,
        "description": description,
        "request_example": request_example,
        "response_example": response_example,
        "source": file_path.name,
    }


def load_all_markdown_docs() -> list[dict]:
    """Load and parse all markdown files from RapidAPI_Docs directory."""
    print(f"\nLoading markdown files from: {RAPIDAPI_DOCS_DIR}")

    docs = []
    md_files = sorted(RAPIDAPI_DOCS_DIR.rglob("*.md"))

    for md_file in md_files:
        parsed = parse_markdown_file(md_file)
        if parsed:
            docs.append(parsed)
            print(f"  Parsed: {md_file.relative_to(RAPIDAPI_DOCS_DIR)}")

    print(f"  Total: {len(docs)} documentation files")
    return docs


# =============================================================================
# STEP 3: UPDATE OPENAPI SPEC
# =============================================================================


def find_operation_in_openapi(openapi_data: dict, endpoint: str) -> dict | None:
    """Find the operation object for a given endpoint path."""
    paths = openapi_data.get("paths", {})

    if endpoint not in paths:
        return None

    path_item = paths[endpoint]

    for method in ["post", "get", "put", "delete", "patch"]:
        if method in path_item:
            return path_item[method]

    return None


def update_request_body(operation: dict, request_example: dict | None) -> None:
    """
    Update the requestBody with the example from markdown.

    Sets the example in: requestBody.content.application/json.example
    """
    if request_example is None:
        return

    if "requestBody" not in operation:
        return

    request_body = operation["requestBody"]

    if "content" not in request_body:
        return

    content = request_body["content"]

    if "application/json" not in content:
        return

    # Set the example
    content["application/json"]["example"] = request_example


def update_responses(operation: dict, response_example: dict | None) -> None:
    """
    Update the responses with the example from markdown.

    - Sets the example in: responses.200.content.application/json.example
    - Removes 422 and other error responses
    """
    if "responses" not in operation:
        return

    responses = operation["responses"]

    # Remove 422 error response
    if "422" in responses:
        del responses["422"]

    # Remove other error responses (4xx, 5xx)
    keys_to_remove = [key for key in responses.keys() if key.startswith(("4", "5"))]
    for key in keys_to_remove:
        del responses[key]

    # Set the success response example
    if response_example is None:
        return

    if "200" not in responses:
        return

    response_200 = responses["200"]

    if "content" not in response_200:
        return

    content = response_200["content"]

    if "application/json" not in content:
        return

    # Set the example and remove schema $ref for RapidAPI compatibility
    # RapidAPI has issues with complex anyOf schemas, so we provide just the example
    json_content = content["application/json"]

    # Remove the schema reference (RapidAPI doesn't need it when example is provided)
    if "schema" in json_content:
        del json_content["schema"]

    json_content["example"] = response_example


def update_openapi_with_docs(openapi_data: dict, docs: list[dict]) -> int:
    """
    Update the OpenAPI spec with documentation from markdown files.

    For each doc:
    - Set operationId = doc["name"]
    - Set description = doc["description"]
    - Set requestBody example = doc["request_example"]
    - Set response example = doc["response_example"]
    - Remove 422 error responses

    Returns the number of endpoints updated.
    """
    print("\nUpdating OpenAPI spec:")

    updated_count = 0

    for doc in docs:
        endpoint = doc["endpoint"]

        # Find the operation in OpenAPI
        operation = find_operation_in_openapi(openapi_data, endpoint)

        if operation is None:
            print(f"  NOT FOUND: {endpoint}")
            continue

        # Update operationId
        old_operation_id = operation.get("operationId", "")
        operation["operationId"] = doc["name"]

        # Update description
        operation["description"] = doc["description"]

        # Update requestBody example
        update_request_body(operation, doc["request_example"])

        # Update responses (and remove 422)
        update_responses(operation, doc["response_example"])

        # Remove security and parameters
        if "security" in operation:
            del operation["security"]
        if "parameters" in operation:
            del operation["parameters"]

        # Log
        print(f"  Updated: {endpoint}")
        print(f"           operationId: {old_operation_id!r} -> {doc['name']!r}")
        if doc["request_example"]:
            print(f"           requestBody: example added")
        if doc["response_example"]:
            print(f"           response: example added, 422 removed")

        updated_count += 1

    return updated_count


# =============================================================================
# STEP 4: REORDER ENDPOINTS
# =============================================================================

# Define the exact order of endpoints as shown in RapidAPI dashboard
ENDPOINT_ORDER = [
    # Charts (SVG)
    "/api/v5/chart/birth-chart",
    "/api/v5/chart/synastry",
    "/api/v5/chart/transit",
    "/api/v5/chart/composite",
    "/api/v5/chart/solar-return",
    "/api/v5/chart/lunar-return",
    "/api/v5/now/chart",
    # Chart Data
    "/api/v5/chart-data/birth-chart",
    "/api/v5/chart-data/synastry",
    "/api/v5/chart-data/transit",
    "/api/v5/chart-data/composite",
    "/api/v5/chart-data/solar-return",
    "/api/v5/chart-data/lunar-return",
    "/api/v5/subject",
    "/api/v5/now/subject",
    "/api/v5/compatibility-score",
    # Moon Phase
    "/api/v5/moon-phase",
    "/api/v5/moon-phase/context",
    "/api/v5/moon-phase/now-utc",
    "/api/v5/moon-phase/now-utc/context",
    # AI Context
    "/api/v5/context/birth-chart",
    "/api/v5/context/synastry",
    "/api/v5/context/transit",
    "/api/v5/context/composite",
    "/api/v5/context/solar-return",
    "/api/v5/context/lunar-return",
    "/api/v5/context/subject",
    "/api/v5/now/context",
]


def reorder_paths(openapi_data: dict) -> None:
    """
    Reorder the paths in OpenAPI spec to match the desired RapidAPI order.

    Endpoints are ordered according to ENDPOINT_ORDER constant.
    Any endpoints not in the list are appended at the end.
    """
    print("\nReordering endpoints:")

    old_paths = openapi_data.get("paths", {})
    new_paths = {}

    # Add paths in the specified order
    for endpoint in ENDPOINT_ORDER:
        if endpoint in old_paths:
            new_paths[endpoint] = old_paths[endpoint]
            print(f"  {len(new_paths):2d}. {endpoint}")

    # Add any remaining paths not in the order list
    for endpoint in old_paths:
        if endpoint not in new_paths:
            new_paths[endpoint] = old_paths[endpoint]
            print(f"  {len(new_paths):2d}. {endpoint} (not in order list)")

    openapi_data["paths"] = new_paths
    print(f"  Total: {len(new_paths)} endpoints reordered")


# =============================================================================
# STEP 5: WRITE OUTPUT FILE
# =============================================================================


def save_rapidapi_json(openapi_data: dict) -> None:
    """Save the modified OpenAPI spec to rapidapi.json."""
    print(f"\nWriting: {OUTPUT_FILE}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(openapi_data, f, indent=2, ensure_ascii=False)

    print("  Done!")


# =============================================================================
# MAIN
# =============================================================================


def main() -> None:
    """
    Main entry point.

    Steps:
    1. Load openapi.json
    2. Parse all markdown docs from RapidAPI_Docs/
    3. Update operationId, description, examples, remove 422
    4. Reorder endpoints to match RapidAPI dashboard
    5. Override server URL if provided
    6. Write rapidapi.json
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Generate RapidAPI OpenAPI Spec from markdown documentation."
    )
    parser.add_argument(
        "-u",
        "--url",
        type=str,
        help="Override the server URL in the OpenAPI spec (e.g., https://astrologer-api.example.com)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Generate RapidAPI OpenAPI Spec")
    print("=" * 60)

    # Step 1: Load base OpenAPI spec
    openapi_data = load_openapi()

    # Step 2: Load all markdown documentation
    docs = load_all_markdown_docs()

    # Step 3: Update OpenAPI with documentation
    updated_count = update_openapi_with_docs(openapi_data, docs)

    # Step 4: Reorder endpoints
    reorder_paths(openapi_data)

    # Step 5: Override server URL if provided
    if args.url:
        print(f"\nOverriding server URL: {args.url}")
        if "servers" in openapi_data and openapi_data["servers"]:
            openapi_data["servers"][0]["url"] = args.url
        else:
            openapi_data["servers"] = [{"url": args.url}]

    # Step 6: Write output
    save_rapidapi_json(openapi_data)

    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Documentation files: {len(docs)}")
    print(f"  Endpoints updated:   {updated_count}")
    print(f"  Output file:         {OUTPUT_FILE.name}")
    print("=" * 60)


if __name__ == "__main__":
    main()
