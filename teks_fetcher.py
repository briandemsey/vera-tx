"""
TEKS Data Fetcher - Acquires Texas Essential Knowledge and Skills from TEA CASE API

Data Source: https://teks-api.texasgateway.org/ims/case/v1p0/
Format: IMS Global CASE (Competency and Academic Standards Exchange) v1.0
License: Public domain / Creative Commons Attribution 4.0

This module fetches TEKS standards from the Texas Education Agency's public CASE API
and stores them in a local SQLite database for use in VERA-TX.
"""

import requests
import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Any

# ============================================================================
# CONFIGURATION
# ============================================================================

CASE_API_BASE = "https://teks-api.texasgateway.org/ims/case/v1p0"
DB_PATH = os.path.join(os.path.dirname(__file__), "teks_data.db")

# TEKS Chapters to fetch (from CFDocuments endpoint)
TEKS_CHAPTERS = [
    ("c22d9405-c1f7-51e6-9883-b3c807e67e6c", "Chapter 110. English Language Arts and Reading"),
    ("bc997e24-7f3b-5df0-a0cd-3a8ac9cf0e2e", "Chapter 111. Mathematics"),
    ("2ccca18f-b9cf-5710-8e66-13be2b1b71ba", "Chapter 112. Science"),
    ("a5db260d-f0b9-5315-9adb-6b41f7e18947", "Chapter 113. Social Studies"),
    ("f72881dd-9796-57da-a12a-f649e03f4c92", "Chapter 114. Languages Other Than English"),
    ("a22d0672-8316-5eec-b72e-a3664b091c41", "Chapter 115. Health Education"),
    ("09876a91-a9a1-50a8-a99f-6a1dd0435b91", "Chapter 116. Physical Education"),
    ("13fce3da-d993-5a21-9beb-c7958e9345c7", "Chapter 117. Fine Arts"),
    ("0b4fa3a5-934a-586a-b300-8a56d0cf0a3d", "Chapter 126. Technology Applications"),
    ("f9132300-bcc2-502d-b181-cb289bd4024c", "Chapter 127. Career Development and CTE"),
    ("927efa98-1add-5134-8b15-c5c988cf4d7e", "Chapter 128. Spanish Language Arts and ESL"),
    ("bb580de0-2a00-5612-b3a2-26a419dfedd1", "Texas Prekindergarten Guidelines"),
]

# ============================================================================
# DATABASE SCHEMA (tx_ namespace)
# ============================================================================

SCHEMA = """
-- TEKS Documents (Chapters)
CREATE TABLE IF NOT EXISTS tx_teks_documents (
    identifier TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    subject TEXT,
    version TEXT,
    adoption_status TEXT,
    official_source_url TEXT,
    last_change_datetime TEXT,
    notes TEXT,
    fetched_at TEXT NOT NULL
);

-- TEKS Items (Standards, Student Expectations, etc.)
CREATE TABLE IF NOT EXISTS tx_teks_items (
    identifier TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    item_type TEXT,
    human_coding_scheme TEXT,
    full_statement TEXT,
    alternative_label TEXT,
    list_enumeration TEXT,
    notes TEXT,
    language TEXT DEFAULT 'en',
    last_change_datetime TEXT,
    FOREIGN KEY (document_id) REFERENCES tx_teks_documents(identifier)
);

-- TEKS Associations (Relationships between items)
CREATE TABLE IF NOT EXISTS tx_teks_associations (
    identifier TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    association_type TEXT,
    origin_item_id TEXT,
    destination_item_id TEXT,
    sequence_number INTEGER,
    FOREIGN KEY (document_id) REFERENCES tx_teks_documents(identifier)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_tx_teks_items_document ON tx_teks_items(document_id);
CREATE INDEX IF NOT EXISTS idx_tx_teks_items_type ON tx_teks_items(item_type);
CREATE INDEX IF NOT EXISTS idx_tx_teks_items_coding ON tx_teks_items(human_coding_scheme);
CREATE INDEX IF NOT EXISTS idx_tx_teks_associations_origin ON tx_teks_associations(origin_item_id);
CREATE INDEX IF NOT EXISTS idx_tx_teks_associations_dest ON tx_teks_associations(destination_item_id);

-- Metadata table for tracking sync state
CREATE TABLE IF NOT EXISTS tx_teks_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT
);
"""

# ============================================================================
# API CLIENT
# ============================================================================

class TEKSFetcher:
    """Fetches TEKS data from TEA CASE API."""

    def __init__(self, base_url: str = CASE_API_BASE):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "VERA-TX/1.0 (H-EDU.Solutions TEKS Browser)"
        })

    def fetch_documents(self) -> List[Dict]:
        """Fetch list of all TEKS documents (chapters)."""
        url = f"{self.base_url}/CFDocuments"
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()

    def fetch_package(self, identifier: str) -> Dict:
        """Fetch a complete TEKS package (document + items + associations)."""
        url = f"{self.base_url}/CFPackages/{identifier}"
        response = self.session.get(url, timeout=120)
        response.raise_for_status()
        return response.json()

    def fetch_item(self, identifier: str) -> Dict:
        """Fetch a single TEKS item."""
        url = f"{self.base_url}/CFItems/{identifier}"
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

class TEKSDatabase:
    """Manages TEKS data storage in SQLite."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(SCHEMA)

    def store_document(self, doc: Dict):
        """Store a TEKS document (chapter)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO tx_teks_documents
                (identifier, title, description, subject, version, adoption_status,
                 official_source_url, last_change_datetime, notes, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc.get('identifier'),
                doc.get('title'),
                doc.get('description'),
                doc.get('subject'),
                doc.get('version'),
                doc.get('adoptionStatus'),
                doc.get('officialSourceURL'),
                doc.get('lastChangeDateTime'),
                doc.get('notes'),
                datetime.utcnow().isoformat()
            ))

    def store_items(self, document_id: str, items: List[Dict]):
        """Store TEKS items (standards)."""
        with sqlite3.connect(self.db_path) as conn:
            for item in items:
                conn.execute("""
                    INSERT OR REPLACE INTO tx_teks_items
                    (identifier, document_id, item_type, human_coding_scheme,
                     full_statement, alternative_label, list_enumeration,
                     notes, language, last_change_datetime)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.get('identifier'),
                    document_id,
                    item.get('CFItemType'),
                    item.get('humanCodingScheme'),
                    item.get('fullStatement'),
                    item.get('alternativeLabel'),
                    item.get('listEnumeration'),
                    item.get('notes'),
                    item.get('language', 'en'),
                    item.get('lastChangeDateTime')
                ))

    def store_associations(self, document_id: str, associations: List[Dict]):
        """Store TEKS associations (relationships)."""
        with sqlite3.connect(self.db_path) as conn:
            for assoc in associations:
                conn.execute("""
                    INSERT OR REPLACE INTO tx_teks_associations
                    (identifier, document_id, association_type, origin_item_id,
                     destination_item_id, sequence_number)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    assoc.get('identifier'),
                    document_id,
                    assoc.get('associationType'),
                    assoc.get('originNodeURI', {}).get('identifier'),
                    assoc.get('destinationNodeURI', {}).get('identifier'),
                    assoc.get('sequenceNumber')
                ))

    def update_metadata(self, key: str, value: str):
        """Update metadata."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO tx_teks_metadata (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, value, datetime.utcnow().isoformat()))

    def get_metadata(self, key: str) -> Optional[str]:
        """Get metadata value."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT value FROM tx_teks_metadata WHERE key = ?", (key,)
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def get_documents(self) -> List[Dict]:
        """Get all stored TEKS documents."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT identifier, title, subject, version, adoption_status
                FROM tx_teks_documents
                ORDER BY title
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_items_by_document(self, document_id: str, item_type: Optional[str] = None) -> List[Dict]:
        """Get items for a document, optionally filtered by type."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if item_type:
                cursor = conn.execute("""
                    SELECT * FROM tx_teks_items
                    WHERE document_id = ? AND item_type = ?
                    ORDER BY human_coding_scheme
                """, (document_id, item_type))
            else:
                cursor = conn.execute("""
                    SELECT * FROM tx_teks_items
                    WHERE document_id = ?
                    ORDER BY human_coding_scheme
                """, (document_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_item_types(self, document_id: str) -> List[str]:
        """Get distinct item types for a document."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT item_type FROM tx_teks_items
                WHERE document_id = ?
                ORDER BY item_type
            """, (document_id,))
            return [row[0] for row in cursor.fetchall()]

    def search_items(self, query: str, limit: int = 100) -> List[Dict]:
        """Search TEKS items by text."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT i.*, d.title as document_title
                FROM tx_teks_items i
                JOIN tx_teks_documents d ON i.document_id = d.identifier
                WHERE i.full_statement LIKE ? OR i.human_coding_scheme LIKE ?
                ORDER BY i.human_coding_scheme
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            stats['documents'] = conn.execute(
                "SELECT COUNT(*) FROM tx_teks_documents"
            ).fetchone()[0]
            stats['items'] = conn.execute(
                "SELECT COUNT(*) FROM tx_teks_items"
            ).fetchone()[0]
            stats['student_expectations'] = conn.execute(
                "SELECT COUNT(*) FROM tx_teks_items WHERE item_type = 'Student Expectation'"
            ).fetchone()[0]
            stats['associations'] = conn.execute(
                "SELECT COUNT(*) FROM tx_teks_associations"
            ).fetchone()[0]
            stats['last_sync'] = self.get_metadata('last_sync')
            return stats


# ============================================================================
# SYNC OPERATIONS
# ============================================================================

def sync_all_teks(verbose: bool = True) -> Dict:
    """Fetch and store all TEKS chapters from TEA API."""
    fetcher = TEKSFetcher()
    db = TEKSDatabase()

    results = {
        'documents': 0,
        'items': 0,
        'associations': 0,
        'errors': []
    }

    if verbose:
        print("Starting TEKS data sync from TEA CASE API...")
        print(f"Database: {DB_PATH}")
        print()

    for identifier, title in TEKS_CHAPTERS:
        try:
            if verbose:
                print(f"Fetching: {title}...")

            # Fetch complete package
            package = fetcher.fetch_package(identifier)

            # Store document
            doc = package.get('CFDocument', {})
            db.store_document(doc)
            results['documents'] += 1

            # Store items
            items = package.get('CFItems', [])
            db.store_items(identifier, items)
            results['items'] += len(items)

            # Store associations
            associations = package.get('CFAssociations', [])
            db.store_associations(identifier, associations)
            results['associations'] += len(associations)

            if verbose:
                print(f"  -> {len(items)} items, {len(associations)} associations")

        except Exception as e:
            error_msg = f"Error fetching {title}: {str(e)}"
            results['errors'].append(error_msg)
            if verbose:
                print(f"  -> ERROR: {e}")

    # Update sync metadata
    db.update_metadata('last_sync', datetime.utcnow().isoformat())
    db.update_metadata('api_source', CASE_API_BASE)

    if verbose:
        print()
        print("=== Sync Complete ===")
        print(f"Documents: {results['documents']}")
        print(f"Items: {results['items']}")
        print(f"Associations: {results['associations']}")
        if results['errors']:
            print(f"Errors: {len(results['errors'])}")

    return results


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "sync":
        sync_all_teks(verbose=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "stats":
        db = TEKSDatabase()
        stats = db.get_stats()
        print("TEKS Database Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    elif len(sys.argv) > 1 and sys.argv[1] == "search":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        db = TEKSDatabase()
        results = db.search_items(query)
        print(f"Found {len(results)} results for '{query}':")
        for item in results[:20]:
            print(f"  [{item['item_type']}] {item['human_coding_scheme']}: {item['full_statement'][:60]}...")
    else:
        print("TEKS Data Fetcher")
        print("Usage:")
        print("  python teks_fetcher.py sync     - Fetch all TEKS from TEA API")
        print("  python teks_fetcher.py stats    - Show database statistics")
        print("  python teks_fetcher.py search <query>  - Search TEKS items")
