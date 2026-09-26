"""MCP server for listing-claim-check (stdio)."""
from __future__ import annotations

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from .checker import check

mcp = MCPServer("listing-claim-check")
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)


@mcp.tool(annotations=READ_ONLY)
def check_listing(specifics: dict, title: str = "", description: str = "") -> dict:
    """Check an AI-written marketplace listing against the seller's item specifics before it's published.

    Finds claims in the title and description (condition, authenticity, model, storage, carrier lock,
    battery health, size, brand, warranty, included items, color, material, and any number) and marks
    each one SUPPORTED, CONTRADICTED or UNSUPPORTED by the specifics. Returns
    {"decision": "PUBLISH" | "REVIEW", "claims": [{"attribute", "claimed", "text", "status", "harm", "reason"}]}.
    Any claim that isn't SUPPORTED means REVIEW; show the seller each claim's text and reason.
    Deterministic, no model: claims phrased outside its vocabulary aren't seen, so PUBLISH means
    "nothing unbacked was found", not "verified true".

    Args:
        specifics: The seller's structured item specifics, e.g. {"category": "smartphone", "brand": "Apple",
            "model": "iPhone 13", "condition": "Used", "storage": "128GB", "carrier": "Unlocked",
            "battery_health": 88, "includes": ["cable"]}. "includes" is a list of lowercase item names.
        title: The AI-written listing title.
        description: The AI-written listing description.
    """
    if not isinstance(specifics, dict):
        raise ToolError("specifics must be an object of item specifics, e.g. {\"brand\": \"Apple\"}")
    return check(specifics, title, description)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
