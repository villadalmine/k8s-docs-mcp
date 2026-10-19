import re
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

CODENUM_REGEX = re.compile(r"\{\{[%<]\s*(?:code|codenew)\s+file=[\"']([^\"']+)[\"'][^%>]*[%>]\}\}")
FEATURE_STATE_REGEX = re.compile(
    r"\{\{[%<]\s*feature-state(?:\s+for_k8s_version=[\"']([^\"']+)[\"'])?(?:\s+state=[\"']([^\"']+)[\"'])?[^%>]*[%>]\}\}"
)
GLOSSARY_TOOLTIP_REGEX = re.compile(
    r"\{\{[%<]\s*glossary_tooltip(?:\s+text=[\"']([^\"']+)[\"'])?(?:\s+term_id=[\"']([^\"']+)[\"'])?[^%>]*[%>]\}\}"
)
CALLOUT_REGEX = re.compile(
    r"\{\{[%<]\s*(note|caution|warning)\s*[%>]\}\}(.*?)\{\{[%<]\s*/\1\s*[%>]\}\}",
    re.DOTALL | re.IGNORECASE,
)
GENERIC_SHORTCODE_REGEX = re.compile(r"\{\{[%<].*?[%>]\}\}")


class HugoPreprocessor:
    """Preprocesses Hugo markdown files from kubernetes/website into clean, standard Markdown."""

    def __init__(self, examples_dir: Optional[Path] = None, docs_dir: Optional[Path] = None):
        self.examples_dir = examples_dir
        self.docs_dir = docs_dir

    def resolve_codenew(self, markdown_text: str) -> str:
        """Finds {{< codenew file="..." >}} shortcodes and inlines the actual YAML content from examples/."""
        if not self.examples_dir:
            return markdown_text

        def _replace_code(match: re.Match) -> str:
            rel_file = match.group(1).strip()
            # Try finding the file in examples_dir
            candidate_paths = [
                self.examples_dir / rel_file,
                self.examples_dir / rel_file.lstrip("/"),
            ]
            if self.docs_dir:
                candidate_paths.append(self.docs_dir / rel_file)

            found_path = None
            for p in candidate_paths:
                if p.exists() and p.is_file():
                    found_path = p
                    break

            if found_path:
                try:
                    content = found_path.read_text(encoding="utf-8", errors="replace").strip()
                    lang = "yaml" if rel_file.endswith((".yaml", ".yml")) else ""
                    return f"\n```{lang}\n# Origin: {rel_file}\n{content}\n```\n"
                except Exception:
                    pass
            return f"\n*(Canonical example: `{rel_file}`)*\n"

        return CODENUM_REGEX.sub(_replace_code, markdown_text)

    def resolve_feature_states(self, markdown_text: str) -> str:
        """Replaces {{< feature-state ... >}} with explicit Markdown badges."""
        def _replace_feature(match: re.Match) -> str:
            ver = match.group(1) or ""
            state = (match.group(2) or "stable").upper()
            ver_str = f" in {ver}" if ver else ""
            return f"\n> **Feature State:** `{state}`{ver_str}\n"

        return FEATURE_STATE_REGEX.sub(_replace_feature, markdown_text)

    def resolve_callouts(self, markdown_text: str) -> str:
        """Converts {{< note >}}...{{< /note >}} into GitHub-style blockquote alerts."""
        def _replace_alert(match: re.Match) -> str:
            alert_type = match.group(1).upper()
            body = match.group(2).strip()
            indented = "\n".join(f"> {line}" for line in body.split("\n"))
            return f"\n> [!{alert_type}]\n{indented}\n"

        return CALLOUT_REGEX.sub(_replace_alert, markdown_text)

    def resolve_tooltips(self, markdown_text: str) -> str:
        """Replaces {{< glossary_tooltip text="..." term_id="..." >}} with plain text."""
        def _replace_tooltip(match: re.Match) -> str:
            text = match.group(1)
            term_id = match.group(2)
            return text or term_id or ""

        return GLOSSARY_TOOLTIP_REGEX.sub(_replace_tooltip, markdown_text)

    def preprocess(self, markdown_text: str) -> str:
        """Applies all Hugo shortcode transformations in sequence."""
        # 1. Inline actual code files (crucial for YAML indexing)
        text = self.resolve_codenew(markdown_text)
        # 2. Convert alerts
        text = self.resolve_callouts(text)
        # 3. Convert feature states
        text = self.resolve_feature_states(text)
        # 4. Resolve glossary tooltips
        text = self.resolve_tooltips(text)
        # 5. Strip any remaining unsupported shortcodes
        text = GENERIC_SHORTCODE_REGEX.sub("", text)
        return text.strip()
