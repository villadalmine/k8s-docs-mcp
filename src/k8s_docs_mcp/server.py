"""Official Kubernetes Documentation & Canonical Manifest MCP Server.

Provides AI coding assistants and autonomous agents with direct, verifiable access
to official Kubernetes documentation (kubernetes.io) and canonical YAML manifests,
preventing API deprecation hallucinations.
"""

from typing import Optional
from mcp.server.mcpserver import MCPServer
from k8s_docs_mcp.fetcher import K8sDocFetcher
from k8s_docs_mcp.sqlite_store import K8sSqliteStore
from k8s_docs_mcp.parser import K8sDocParser
from k8s_docs_mcp.seed_data import get_seed_sections, get_seed_manifests
from k8s_docs_mcp.openapi_client import K8sApiRegistry

# Initialize MCPServer
mcp = MCPServer(
    "k8s-docs-mcp",
    description="Official Kubernetes Documentation & Canonical YAML Manifest Assistant",
)

# Global instances
fetcher = K8sDocFetcher()
store = K8sSqliteStore()

# Ensure database is populated (with upstream docs or seed)
if not store.is_populated():
    if fetcher.is_synced():
        parser = K8sDocParser()
        sections, manifests = [], []
        for md in fetcher.docs_dir.glob("**/*.md"):
            s, m = parser.parse_markdown_file(md, fetcher.docs_dir, examples_dir=fetcher.examples_dir)
            sections.extend(s)
            manifests.extend(m)
        if fetcher.examples_dir.exists():
            for yml in list(fetcher.examples_dir.glob("**/*.yaml")) + list(fetcher.examples_dir.glob("**/*.yml")):
                ex_m = parser.parse_example_yaml(yml, fetcher.examples_dir)
                if ex_m:
                    manifests.append(ex_m)
        store.populate(sections, manifests)
    else:
        store.populate(get_seed_sections(), get_seed_manifests())


@mcp.tool()
def search_k8s_docs(query: str, limit: int = 3) -> str:
    """Searches official Kubernetes documentation (kubernetes.io) for concepts, policies, and architectures.

    Args:
        query: Search keywords or question (e.g., 'network policies ingress rules', 'validating admission webhook cel').
        limit: Maximum number of documentation sections to return (default: 3).

    Returns:
        Authoritative documentation sections with official kubernetes.io URLs.
    """
    results = store.search_docs(query, limit=limit)
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
def get_canonical_manifest(kind: str, limit: int = 3) -> str:
    """Retrieves verified, unaltered Kubernetes YAML manifests directly from official kubernetes.io examples.

    Bypasses LLM generative alterations to prevent indentation errors, invalid fields, or deprecated apiVersions.

    Args:
        kind: The Kubernetes resource kind (e.g. 'Pod', 'Service', 'Deployment', 'NetworkPolicy', 'ValidatingAdmissionPolicy').
        limit: Maximum number of canonical manifest examples to return (default: 3).

    Returns:
        Exact canonical YAML manifests with source file provenance.
    """
    manifests = store.get_manifests_by_kind(kind, limit=limit)
    if not manifests:
        all_kinds = ", ".join(store.list_kinds()[:15])
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
def check_api_version(kind: str, api_version: Optional[str] = None) -> str:
    """Verifies Kubernetes API version compatibility, deprecations, and removals deterministically via OpenAPI registry.

    Args:
        kind: The Kubernetes resource Kind (e.g. 'Ingress', 'PodSecurityPolicy', 'CronJob', 'ValidatingAdmissionPolicy').
        api_version: Optional apiVersion to test (e.g. 'extensions/v1beta1', 'networking.k8s.io/v1').

    Returns:
        Authoritative validation report with current stable apiVersion, deprecation notices, and migration advice.
    """
    res = K8sApiRegistry.check_resource(kind, query_api_version=api_version)
    if not res.get("found"):
        return f"### API Check for Kind: `{kind}`\n{res.get('message')}"

    output = [
        f"### Authoritative Kubernetes API Check: `{res['kind']}`",
        f"- **Current Stable apiVersion:** `{res['current_api_version']}`",
        f"- **Status:** `{res['status'].upper()}`",
    ]

    if res.get("warning"):
        output.append(f"\n> [!WARNING]\n> {res['warning']}\n")

    if res.get("deprecated_versions"):
        dep_list = ", ".join(f"`{v}`" for v in res["deprecated_versions"])
        output.append(f"- **Deprecated / Legacy Versions:** {dep_list}")

    if res.get("removed_in"):
        output.append(f"- **Removed In Release:** `{res['removed_in']}`")

    if res.get("recommended_replacement"):
        output.append(f"- **Recommended Replacement:** `{res['recommended_replacement']}`")

    if res.get("notes"):
        output.append(f"\n**Technical Guidance:**\n{res['notes']}")

    return "\n".join(output)


@mcp.tool()
def list_supported_resources() -> str:
    """Lists all Kubernetes API resource Kinds currently indexed with canonical YAML manifests."""
    kinds = store.list_kinds()
    if not kinds:
        return "No resource Kinds currently indexed."
    return "### Indexed Kubernetes Resource Kinds:\n" + "\n".join(f"- `{k}`" for k in kinds)


@mcp.tool()
def sync_upstream_docs() -> str:
    """Fetches or updates the latest official documentation and examples from github.com/kubernetes/website.

    Preprocesses Hugo shortcodes (resolving {{< codenew >}} into inline YAML) and rebuilds the SQLite FTS5 database.
    """
    success = fetcher.sync(depth=1)
    if not success:
        return "Failed to sync with upstream kubernetes/website. Check network connectivity or git installation."

    parser = K8sDocParser()
    sections, manifests = [], []

    for md in fetcher.docs_dir.glob("**/*.md"):
        s, m = parser.parse_markdown_file(md, fetcher.docs_dir, examples_dir=fetcher.examples_dir)
        sections.extend(s)
        manifests.extend(m)

    if fetcher.examples_dir.exists():
        for yml in list(fetcher.examples_dir.glob("**/*.yaml")) + list(fetcher.examples_dir.glob("**/*.yml")):
            ex_m = parser.parse_example_yaml(yml, fetcher.examples_dir)
            if ex_m:
                manifests.append(ex_m)

    store.populate(sections, manifests, clear_existing=True)
    return (
        f"Successfully synchronized upstream documentation!\n"
        f"SQLite FTS5 database populated with {len(sections)} sections and {len(manifests)} canonical manifests."
    )


def main():
    """CLI Entrypoint for running the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
