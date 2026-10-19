import re
import yaml
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from k8s_docs_mcp.models import K8sDocSection, K8sManifest
from k8s_docs_mcp.hugo_preprocessor import HugoPreprocessor

FRONTMATTER_REGEX = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
YAML_BLOCK_REGEX = re.compile(r"```(?:yaml|yml)\s*\n(.*?)```", re.DOTALL)
HEADING_REGEX = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)


class K8sDocParser:
    """Parses Hugo Markdown documentation and examples from kubernetes/website."""

    @staticmethod
    def extract_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
        """Extracts YAML frontmatter and returns (metadata, body)."""
        match = FRONTMATTER_REGEX.match(content)
        if not match:
            return {}, content

        raw_yaml = match.group(1)
        body = content[match.end():]
        try:
            metadata = yaml.safe_load(raw_yaml) or {}
        except Exception:
            metadata = {}
        return metadata, body

    @staticmethod
    def file_to_canonical_url(relative_path: Path) -> str:
        """Converts local file path relative to content/en/docs into canonical kubernetes.io URL.

        Example:
            concepts/services-networking/network-policies.md ->
            https://kubernetes.io/docs/concepts/services-networking/network-policies/
        """
        parts = list(relative_path.parts)
        # Remove 'content', 'en', 'docs' if present
        while parts and parts[0] in ("content", "en", "docs", ".upstream"):
            parts.pop(0)

        path_str = "/".join(parts)
        if path_str.endswith(".md"):
            path_str = path_str[:-3]
        if path_str.endswith("/_index") or path_str == "_index":
            path_str = path_str[:-6]

        path_str = path_str.strip("/")
        return f"https://kubernetes.io/docs/{path_str}/" if path_str else "https://kubernetes.io/docs/"

    def parse_markdown_file(self, file_path: Path, base_docs_dir: Path, examples_dir: Optional[Path] = None) -> Tuple[List[K8sDocSection], List[K8sManifest]]:
        """Parses a single markdown document into atomic sections and manifest snippets."""
        sections: List[K8sDocSection] = []
        manifests: List[K8sManifest] = []

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return sections, manifests

        metadata, body = self.extract_frontmatter(content)
        title = metadata.get("title") or file_path.stem.replace("-", " ").title()
        description = metadata.get("description") or ""

        # Preprocess Hugo shortcodes (resolves {{< codenew file="..." >}} into actual YAML)
        preprocessor = HugoPreprocessor(examples_dir=examples_dir, docs_dir=base_docs_dir)
        body = preprocessor.preprocess(body)

        try:
            rel_path = file_path.relative_to(base_docs_dir)
        except ValueError:
            rel_path = file_path

        canonical_url = self.file_to_canonical_url(rel_path)

        # 1. Extract embedded YAML manifests from code blocks
        for match in YAML_BLOCK_REGEX.finditer(body):
            yaml_code = match.group(1).strip()
            manifest = self._parse_yaml_snippet(yaml_code, str(rel_path), canonical_url, title)
            if manifest:
                manifests.append(manifest)

        # 2. Split body into sections by markdown headings
        heading_matches = list(HEADING_REGEX.finditer(body))
        if not heading_matches:
            # Single section
            clean_body = self._clean_markdown(body)
            if clean_body.strip():
                sections.append(
                    K8sDocSection(
                        title=title,
                        url=canonical_url,
                        source_file=str(rel_path),
                        section_name="Overview",
                        content=clean_body[:4000],
                        metadata=metadata,
                    )
                )
            return sections, manifests

        # Multi-section document
        # Add introductory section before first heading
        first_pos = heading_matches[0].start()
        intro_text = self._clean_markdown(body[:first_pos])
        if intro_text.strip():
            sections.append(
                K8sDocSection(
                    title=title,
                    url=canonical_url,
                    source_file=str(rel_path),
                    section_name="Overview",
                    content=intro_text[:4000],
                    metadata=metadata,
                )
            )

        # Process each heading section
        for i, h_match in enumerate(heading_matches):
            sec_title = h_match.group(2).strip()
            sec_start = h_match.end()
            sec_end = heading_matches[i + 1].start() if i + 1 < len(heading_matches) else len(body)
            sec_content = self._clean_markdown(body[sec_start:sec_end])

            if len(sec_content.strip()) > 40:
                sections.append(
                    K8sDocSection(
                        title=f"{title}: {sec_title}",
                        url=f"{canonical_url}#{self._slugify(sec_title)}",
                        source_file=str(rel_path),
                        section_name=sec_title,
                        content=sec_content[:4000],
                        metadata=metadata,
                    )
                )

        return sections, manifests

    def parse_example_yaml(self, file_path: Path, base_examples_dir: Path) -> Optional[K8sManifest]:
        """Parses a standalone YAML example file from content/en/examples."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None

        try:
            rel_path = file_path.relative_to(base_examples_dir)
        except ValueError:
            rel_path = file_path

        return self._parse_yaml_snippet(content, str(rel_path), None, file_path.stem)

    def _parse_yaml_snippet(self, yaml_text: str, source_file: str, url: Optional[str], default_name: str) -> Optional[K8sManifest]:
        """Attempts to parse a Kubernetes manifest to extract kind, apiVersion, and metadata.name."""
        if "kind:" not in yaml_text or "apiVersion:" not in yaml_text:
            return None

        kind = ""
        api_version = ""
        name = default_name

        for doc in yaml_text.split("---"):
            doc_str = doc.strip()
            if not doc_str:
                continue
            try:
                data = yaml.safe_load(doc_str)
                if isinstance(data, dict) and "kind" in data and "apiVersion" in data:
                    kind = str(data.get("kind", ""))
                    api_version = str(data.get("apiVersion", ""))
                    metadata = data.get("metadata", {})
                    if isinstance(metadata, dict) and "name" in metadata:
                        name = str(metadata.get("name", default_name))
                    return K8sManifest(
                        kind=kind,
                        api_version=api_version,
                        name=name,
                        source_file=source_file,
                        content=yaml_text,
                        url=url,
                    )
            except Exception:
                continue

        # Regex fallback
        kind_m = re.search(r"^kind:\s*([A-Za-z0-9_]+)", yaml_text, re.MULTILINE)
        api_m = re.search(r"^apiVersion:\s*([A-Za-z0-9_./-]+)", yaml_text, re.MULTILINE)
        name_m = re.search(r"^\s+name:\s*([A-Za-z0-9_.-]+)", yaml_text, re.MULTILINE)

        if kind_m and api_m:
            return K8sManifest(
                kind=kind_m.group(1),
                api_version=api_m.group(1),
                name=name_m.group(1) if name_m else default_name,
                source_file=source_file,
                content=yaml_text,
                url=url,
            )

        return None

    @staticmethod
    def _clean_markdown(text: str) -> str:
        """Removes Hugo shortcodes like {{< note >}} or {{% /note %}}."""
        text = re.sub(r"\{\{[%<].*?[%>]\}\}", "", text)
        return text.strip()

    @staticmethod
    def _slugify(text: str) -> str:
        """Converts a heading to a URL anchor slug."""
        text = text.lower().strip()
        text = re.sub(r"[^\w\s-]", "", text)
        return re.sub(r"[-\s]+", "-", text)
