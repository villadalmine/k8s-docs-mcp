import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from k8s_docs_mcp.models import K8sDocSection, K8sManifest


class K8sSqliteStore:
    """Embedded SQLite database with FTS5 full-text search for official Kubernetes documentation and YAML manifests."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            self.db_path = Path(__file__).resolve().parent.parent.parent / "data" / "k8s_docs.db"
        else:
            self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes tables and FTS5 virtual tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Documents FTS5 virtual table
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
                    title,
                    section_name,
                    content,
                    url UNINDEXED,
                    source_file UNINDEXED,
                    tokenize='porter unicode61'
                )
            """)

            # 2. Manifests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS manifests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    api_version TEXT NOT NULL,
                    name TEXT NOT NULL,
                    source_file TEXT,
                    content TEXT NOT NULL,
                    description TEXT,
                    url TEXT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_manifest_kind ON manifests(kind)")

            conn.commit()

    def is_populated(self) -> bool:
        """Returns True if the database already contains indexed sections and manifests."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) as cnt FROM docs_fts")
            doc_cnt = cursor.fetchone()["cnt"]
            cursor.execute("SELECT count(*) as cnt FROM manifests")
            man_cnt = cursor.fetchone()["cnt"]
            return doc_cnt > 0 and man_cnt > 0

    def populate(self, sections: List[K8sDocSection], manifests: List[K8sManifest], clear_existing: bool = True):
        """Inserts documents and manifests into SQLite FTS5."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if clear_existing:
                cursor.execute("DELETE FROM docs_fts")
                cursor.execute("DELETE FROM manifests")

            # Insert sections into FTS5
            for sec in sections:
                cursor.execute(
                    """
                    INSERT INTO docs_fts (title, section_name, content, url, source_file)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (sec.title, sec.section_name, sec.content, sec.url, sec.source_file),
                )

            # Insert manifests
            for m in manifests:
                cursor.execute(
                    """
                    INSERT INTO manifests (kind, api_version, name, source_file, content, description, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (m.kind, m.api_version, m.name, m.source_file, m.content, m.description, m.url),
                )

            conn.commit()

    def search_docs(self, query: str, limit: int = 3) -> List[Tuple[K8sDocSection, float]]:
        """Performs BM25 search over official Kubernetes documentation using SQLite FTS5."""
        # Sanitize query for FTS5 (escape special chars, match tokens)
        clean_tokens = [t for t in query.replace('"', "").replace("'", "").split() if t.isalnum() or "-" in t]
        if not clean_tokens:
            return []

        fts_query = " OR ".join(f'"{t}"' for t in clean_tokens)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    SELECT title, section_name, content, url, source_file, rank
                    FROM docs_fts
                    WHERE docs_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (fts_query, limit),
                )
                rows = cursor.fetchall()
            except sqlite3.OperationalError:
                return []

            results = []
            for row in rows:
                sec = K8sDocSection(
                    title=row["title"],
                    section_name=row["section_name"],
                    content=row["content"],
                    url=row["url"],
                    source_file=row["source_file"],
                )
                # In SQLite FTS5, lower rank is better (negative value)
                score = abs(float(row["rank"])) if row["rank"] is not None else 1.0
                results.append((sec, score))
            return results

    def get_manifests_by_kind(self, kind: str, limit: int = 3) -> List[K8sManifest]:
        """Returns verified manifests matching a resource Kind."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT kind, api_version, name, source_file, content, description, url
                FROM manifests
                WHERE LOWER(kind) = LOWER(?)
                LIMIT ?
                """,
                (kind.strip(), limit),
            )
            rows = cursor.fetchall()

            if not rows:
                # Substring fallback
                cursor.execute(
                    """
                    SELECT kind, api_version, name, source_file, content, description, url
                    FROM manifests
                    WHERE LOWER(kind) LIKE LOWER(?)
                    LIMIT ?
                    """,
                    (f"%{kind.strip()}%", limit),
                )
                rows = cursor.fetchall()

            manifests = []
            for row in rows:
                manifests.append(
                    K8sManifest(
                        kind=row["kind"],
                        api_version=row["api_version"],
                        name=row["name"],
                        source_file=row["source_file"],
                        content=row["content"],
                        description=row["description"] or "",
                        url=row["url"],
                    )
                )
            return manifests

    def list_kinds(self) -> List[str]:
        """Returns distinct indexed Kinds."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT kind FROM manifests ORDER BY kind")
            return [row["kind"] for row in cursor.fetchall() if row["kind"]]
