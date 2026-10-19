from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class K8sDocSection:
    """Represents an atomic section of an official Kubernetes documentation page."""
    title: str
    url: str
    source_file: str
    section_name: str
    content: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_citation(self) -> str:
        return f"kubernetes.io: {self.title} (#{self.section_name}) -> {self.url}"


@dataclass
class K8sManifest:
    """Represents a verified, canonical Kubernetes YAML manifest."""
    kind: str
    api_version: str
    name: str
    source_file: str
    content: str
    description: str = ""
    url: Optional[str] = None

    def to_citation(self) -> str:
        loc = f" -> {self.url}" if self.url else ""
        return f"kubernetes.io ({self.source_file}){loc}"
