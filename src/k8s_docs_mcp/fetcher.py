import os
import subprocess
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()

UPSTREAM_REPO = "https://github.com/kubernetes/website.git"


class K8sDocFetcher:
    """Manages downloading, updating, and syncing official documentation from kubernetes/website."""

    def __init__(self, target_dir: Optional[Path] = None):
        if target_dir is None:
            self.target_dir = Path(__file__).resolve().parent.parent.parent / ".upstream"
        else:
            self.target_dir = Path(target_dir)

    @property
    def docs_dir(self) -> Path:
        return self.target_dir / "content" / "en" / "docs"

    @property
    def examples_dir(self) -> Path:
        return self.target_dir / "content" / "en" / "examples"

    def is_synced(self) -> bool:
        """Returns True if upstream docs directory exists and contains markdown files."""
        return self.docs_dir.exists() and any(self.docs_dir.glob("**/*.md"))

    def sync(self, depth: int = 1) -> bool:
        """Performs a lightweight sparse git clone or pull of kubernetes/website.

        Only retrieves 'content/en/docs' and 'content/en/examples', skipping
        translations and historical git blobs to minimize network usage (<30MB).
        """
        try:
            if not self.target_dir.exists():
                console.print(f"[bold cyan]Cloning upstream kubernetes/website (sparse mode)...[/bold cyan]")
                # 1. Initialize empty repo with sparse checkout
                subprocess.run(
                    [
                        "git",
                        "clone",
                        f"--depth={depth}",
                        "--filter=blob:none",
                        "--sparse",
                        UPSTREAM_REPO,
                        str(self.target_dir),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

                # 2. Configure sparse patterns
                subprocess.run(
                    ["git", "-C", str(self.target_dir), "sparse-checkout", "set", "content/en/docs", "content/en/examples"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                console.print("[bold green]Successfully initialized upstream documentation repository.[/bold green]")
                return True
            else:
                console.print("[bold cyan]Pulling latest changes from kubernetes/website...[/bold cyan]")
                subprocess.run(
                    ["git", "-C", str(self.target_dir), "pull", "--ff-only"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                console.print("[bold green]Upstream documentation updated successfully.[/bold green]")
                return True

        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]Git sync error:[/bold red] {e.stderr if hasattr(e, 'stderr') else str(e)}")
            return False
        except Exception as e:
            console.print(f"[bold red]Failed to sync upstream docs:[/bold red] {e}")
            return False
