import pickle
import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from rank_bm25 import BM25Okapi
from rich.console import Console

from k8s_docs_mcp.models import K8sDocSection, K8sManifest
from k8s_docs_mcp.parser import K8sDocParser
from k8s_docs_mcp.seed_data import get_seed_sections, get_seed_manifests

console = Console()
TOKEN_REGEX = re.compile(r"[A-Za-z0-9_./:-]+")


def tokenize(text: str) -> List[str]:
    """Tokenizes technical text preserving dot-separated and hyphenated identifiers."""
    return TOKEN_REGEX.findall(text.lower())


class K8sDocIndexer:
    """Indexes Kubernetes documentation and manifests using BM25 Okapi for instant retrieval."""

    def __init__(self, cache_file: Optional[Path] = None):
        if cache_file is None:
            self.cache_file = Path(__file__).resolve().parent.parent.parent / "data" / "cache" / "k8s_index.pkl"
        else:
            self.cache_file = Path(cache_file)

        self.sections: List[K8sDocSection] = []
        self.manifests: List[K8sManifest] = []
        self.manifest_by_kind: Dict[str, List[K8sManifest]] = {}
        self.doc_bm25: Optional[BM25Okapi] = None
        self.manifest_bm25: Optional[BM25Okapi] = None

    def ensure_initialized(self, docs_dir: Optional[Path] = None, examples_dir: Optional[Path] = None):
        """Loads cached index or builds from upstream docs or bundled seed data."""
        if self.load_cache():
            return

        if docs_dir and docs_dir.exists() and any(docs_dir.glob("**/*.md")):
            console.print("[cyan]Building index from upstream documentation...[/cyan]")
            self.build_from_directory(docs_dir, examples_dir)
            return

        console.print("[yellow]Upstream docs not found on disk. Initializing with bundled canonical seed data...[/yellow]")
        self.sections = get_seed_sections()
        self.manifests = get_seed_manifests()
        self.manifest_by_kind = {}
        for m in self.manifests:
            k = m.kind.lower()
            self.manifest_by_kind.setdefault(k, []).append(m)

        doc_corpus = [tokenize(f"{s.title} {s.section_name} {s.content}") for s in self.sections]
        self.doc_bm25 = BM25Okapi(doc_corpus)

        manifest_corpus = [tokenize(f"{m.kind} {m.api_version} {m.name} {m.content}") for m in self.manifests]
        self.manifest_bm25 = BM25Okapi(manifest_corpus)

        self.save_cache()

    def build_from_directory(self, docs_dir: Path, examples_dir: Optional[Path] = None):
        """Scans docs and examples directories, parses content, and builds the BM25 indexes."""
        parser = K8sDocParser()
        sections: List[K8sDocSection] = []
        manifests: List[K8sManifest] = []

        console.print(f"[cyan]Parsing Markdown documentation from {docs_dir}...[/cyan]")
        md_files = list(docs_dir.glob("**/*.md"))
        for md_path in md_files:
            file_sections, file_manifests = parser.parse_markdown_file(md_path, docs_dir)
            sections.extend(file_sections)
            manifests.extend(file_manifests)

        if examples_dir and examples_dir.exists():
            console.print(f"[cyan]Parsing YAML examples from {examples_dir}...[/cyan]")
            for yml_path in list(examples_dir.glob("**/*.yaml")) + list(examples_dir.glob("**/*.yml")):
                m = parser.parse_example_yaml(yml_path, examples_dir)
                if m:
                    manifests.append(m)

        self.sections = sections
        self.manifests = manifests

        # Group manifests by Kind
        self.manifest_by_kind = {}
        for m in manifests:
            k = m.kind.lower()
            self.manifest_by_kind.setdefault(k, []).append(m)

        console.print(f"[green]Indexed {len(self.sections)} doc sections and {len(self.manifests)} manifests.[/green]")

        # Build BM25 indexes
        if self.sections:
            doc_corpus = [tokenize(f"{s.title} {s.section_name} {s.content}") for s in self.sections]
            self.doc_bm25 = BM25Okapi(doc_corpus)

        if self.manifests:
            manifest_corpus = [tokenize(f"{m.kind} {m.api_version} {m.name} {m.content}") for m in self.manifests]
            self.manifest_bm25 = BM25Okapi(manifest_corpus)

        self.save_cache()

    def save_cache(self):
        """Serializes index data to disk."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "sections": self.sections,
            "manifests": self.manifests,
            "manifest_by_kind": self.manifest_by_kind,
        }
        with open(self.cache_file, "wb") as f:
            pickle.dump(data, f)
        console.print(f"[green]Index cached to {self.cache_file}[/green]")

    def load_cache(self) -> bool:
        """Loads index from disk cache and reconstructs BM25 index."""
        if not self.cache_file.exists():
            return False

        try:
            with open(self.cache_file, "rb") as f:
                data = pickle.load(f)
            self.sections = data.get("sections", [])
            self.manifests = data.get("manifests", [])
            self.manifest_by_kind = data.get("manifest_by_kind", {})

            if self.sections:
                doc_corpus = [tokenize(f"{s.title} {s.section_name} {s.content}") for s in self.sections]
                self.doc_bm25 = BM25Okapi(doc_corpus)

            if self.manifests:
                manifest_corpus = [tokenize(f"{m.kind} {m.api_version} {m.name} {m.content}") for m in self.manifests]
                self.manifest_bm25 = BM25Okapi(manifest_corpus)

            return True
        except Exception as e:
            console.print(f"[yellow]Failed to load index cache: {e}[/yellow]")
            return False

    def search_docs(self, query: str, top_k: int = 3) -> List[Tuple[K8sDocSection, float]]:
        """Performs lexical BM25 search over official Kubernetes documentation."""
        if not self.doc_bm25 or not self.sections:
            return []

        tokens = tokenize(query)
        if not tokens:
            return []

        scores = self.doc_bm25.get_scores(tokens)
        scored_pairs = list(enumerate(scores))
        scored_pairs.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scored_pairs[:top_k]:
            if score > 0.05:
                results.append((self.sections[idx], float(score)))
        return results

    def get_manifests_by_kind(self, kind: str, top_k: int = 2) -> List[K8sManifest]:
        """Returns verified Kubernetes manifests for a given Kind (e.g. NetworkPolicy, Deployment)."""
        k = kind.strip().lower()
        if k in self.manifest_by_kind:
            return self.manifest_by_kind[k][:top_k]

        # Fallback to BM25 search over manifests
        if self.manifest_bm25 and self.manifests:
            tokens = tokenize(kind)
            scores = self.manifest_bm25.get_scores(tokens)
            scored = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
            return [self.manifests[idx] for idx, s in scored[:top_k] if s > 0.1]

        return []

    def list_all_kinds(self) -> List[str]:
        """Returns sorted list of all unique resource Kinds indexed."""
        return sorted(list({m.kind for m in self.manifests if m.kind}))
