"""Official Kubernetes Documentation & Canonical Manifest MCP Server.

Provides AI coding assistants and autonomous agents with direct, verifiable access
to official Kubernetes documentation (kubernetes.io) and canonical YAML manifests,
preventing API deprecation hallucinations.
"""

from typing import Optional
from mcp.server.mcpserver import MCPServer
from k8s_docs_mcp.fetcher import K8sDocFetcher
from k8s_docs_mcp.indexer import K8sDocIndexer

# Initialize MCPServer
mcp = MCPServer(
    "k8s-docs-mcp",
    description="Official Kubernetes Documentation & Canonical YAML Manifest Assistant",
)

# Global indexer instance
fetcher = K8sDocFetcher()
indexer = K8sDocIndexer()
indexer.ensure_initialized(docs_dir=fetcher.docs_dir, examples_dir=fetcher.examples_dir)


@mcp.tool()
def search_k8s_docs(query: str, limit: int = 3) -> str:
    """Searches official Kubernetes documentation (kubernetes.io) for concepts, policies, and architectures.

    Args:
        query: Search keywords or question (e.g., 'network policies ingress rules', 'validating admission webhook cel').
        limit: Maximum number of documentation sections to return (default: 3).

    Returns:
        Authoritative documentation sections with official kubernetes.io URLs.
    """
    results = indexer.search_docs(query, top_k=limit)
    if not results:
        return f"No official documentation sections found matching '{query}'."

    output = [f"### Official Kubernetes Documentation for: '{query}'\n"]
    for i, (sec, score) in enumerate(results, 1):
        output.append(
            f"#### [{i}] {sec.title}\n"
            f"**Official URL:** {sec.url}\n"
            f"**File Origin:** `{sec.source_file}`\n\n"
            f"{sec.content}\n"
        )
    return "\n---\n".join(output)


@mcp.tool()
def get_canonical_manifest(kind: str) -> str:
    """Retrieves verified, unaltered Kubernetes YAML manifests directly from official kubernetes.io examples.

    Bypasses LLM generative alterations to prevent indentation errors, invalid fields, or deprecated apiVersions.

    Args:
        kind: The Kubernetes resource kind (e.g. 'NetworkPolicy', 'Deployment', 'ValidatingAdmissionPolicy', 'ValidatingWebhookConfiguration').

    Returns:
        Exact canonical YAML manifests with source file provenance.
    """
    manifests = indexer.get_manifests_by_kind(kind, top_k=2)
    if not manifests:
        all_kinds = ", ".join(indexer.list_all_kinds()[:15])
        return (
            f"No verified manifest found for Kind: '{kind}'.\n"
            f"Currently indexed sample Kinds include: {all_kinds}...\n"
            f"(Run 'sync_upstream_docs' to pull the complete catalog from kubernetes/website)."
        )

    output = [f"### Canonical Kubernetes Manifest(s) for Kind: `{kind}`\n"]
    for i, m in enumerate(manifests, 1):
        url_info = f"\n**Reference:** {m.url}" if m.url else ""
        output.append(
            f"#### Manifest {i}: `{m.name}` ({m.api_version}){url_info}\n"
            f"**Origin:** `{m.source_file}`\n\n"
            f"```yaml\n{m.content.strip()}\n```"
        )
    return "\n\n".join(output)


@mcp.tool()
def list_supported_resources() -> str:
    """Lists all Kubernetes API resource Kinds currently indexed with canonical YAML manifests."""
    kinds = indexer.list_all_kinds()
    if not kinds:
        return "No resource Kinds currently indexed."
    return "### Indexed Kubernetes Resource Kinds:\n" + "\n".join(f"- `{k}`" for k in kinds)


@mcp.tool()
def sync_upstream_docs() -> str:
    """Fetches or updates the latest official documentation and examples from github.com/kubernetes/website.

    Rebuilds the local BM25 index upon completion.
    """
    success = fetcher.sync(depth=1)
    if not success:
        return "Failed to sync with upstream kubernetes/website. Check network connectivity or git installation."

    indexer.build_from_directory(fetcher.docs_dir, fetcher.examples_dir)
    return (
        f"Successfully synchronized upstream documentation!\n"
        f"Indexed {len(indexer.sections)} documentation sections and {len(indexer.manifests)} canonical manifests."
    )


def main():
    """CLI Entrypoint for running the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
