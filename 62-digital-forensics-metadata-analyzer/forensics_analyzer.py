"""
Digital Forensics File Metadata Analyzer Engine.
Performs read-only forensic metadata extraction, cryptographic hashing,
duplicate detection, suspicious extension analysis, and integrity verification.
"""
import os
import hashlib
from pathlib import Path
from datetime import datetime
import json
import re
from typing import Optional, Dict, List, Any
from database import get_connection, init_db


class ForensicsAnalyzer:
    CHUNK_SIZE = 65536  # 64 KB chunk for memory-efficient hashing
    SUSPICIOUS_DOUBLE_EXT_REGEX = re.compile(
        r"\.(pdf|docx?|xlsx?|pptx?|jpe?g|png|txt|csv)\.(exe|vbs|bat|ps1|cmd|scr|pif|js|hta|jar|sh)$",
        re.IGNORECASE
    )
    DANGEROUS_EXTENSIONS = {
        ".exe", ".scr", ".vbs", ".bat", ".cmd", ".ps1", ".pif", ".hta", ".jar", ".dll"
    }

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def _get_connection(self):
        return get_connection(self.db_path)

    @classmethod
    def calculate_hashes(cls, file_path: str) -> Dict[str, str]:
        """Compute SHA-256 and MD5 hashes in read-only chunked mode."""
        sha256 = hashlib.sha256()
        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            while chunk := f.read(cls.CHUNK_SIZE):
                sha256.update(chunk)
                md5.update(chunk)
        return {
            "sha256": sha256.hexdigest(),
            "md5": md5.hexdigest()
        }

    @classmethod
    def check_suspicious_patterns(cls, filename: str, size: int) -> List[str]:
        """Examine filename, extension, and characteristics for forensic red flags."""
        flags = []
        name_lower = filename.lower()

        # Check for deceptive double extension (e.g. invoice.pdf.exe)
        if cls.SUSPICIOUS_DOUBLE_EXT_REGEX.search(name_lower):
            flags.append("Deceptive double extension masquerading as document")

        # Dangerous standalone executable in documents context
        ext = os.path.splitext(name_lower)[1]
        if ext in cls.DANGEROUS_EXTENSIONS:
            flags.append(f"Executable script or binary format ({ext})")

        # Hidden file with executable or script format
        if filename.startswith(".") and len(filename) > 1 and ext in cls.DANGEROUS_EXTENSIONS:
            flags.append("Hidden executable file")

        # Zero-byte anomaly
        if size == 0:
            flags.append("Zero-byte empty file")

        return flags

    def analyze_file(self, file_path: str, base_dir: Optional[str] = None) -> Dict[str, Any]:
        """Extract forensic metadata without modifying the target evidence."""
        p = Path(file_path).resolve()
        if not p.is_file():
            raise FileNotFoundError(f"Target is not a valid file: {file_path}")

        stat = p.stat()
        hashes = self.calculate_hashes(str(p))
        flags = self.check_suspicious_patterns(p.name, stat.st_size)

        rel_path = str(p.relative_to(base_dir)) if base_dir else p.name

        # Extract timestamps
        # Note: on Linux, st_ctime is change time; st_mtime is modification time; st_atime is access time
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        atime = datetime.fromtimestamp(stat.st_atime).strftime("%Y-%m-%d %H:%M:%S")
        ctime = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")

        return {
            "absolute_path": str(p),
            "relative_path": rel_path,
            "filename": p.name,
            "extension": p.suffix.lower() if p.suffix else "None",
            "size_bytes": stat.st_size,
            "sha256": hashes["sha256"],
            "md5": hashes["md5"],
            "modified_time": mtime,
            "accessed_time": atime,
            "created_time": ctime,
            "suspicious_flags": flags,
        }

    def scan_directory(self, target_dir: str, case_number: str,
                       investigator: str = "Forensic Examiner") -> Dict[str, Any]:
        """
        Recursively scan target directory, register forensic case, detect duplicates and suspicious files,
        and save immutable baseline to SQLite.
        """
        target_path = Path(target_dir).resolve()
        if not target_path.is_dir():
            raise NotADirectoryError(f"Directory not found: {target_dir}")

        evidence_list = []
        hash_registry: Dict[str, List[int]] = {}

        # 1. Read-only walk of target directory
        for root, _, files in os.walk(target_path):
            for fname in sorted(files):
                full_path = os.path.join(root, fname)
                try:
                    record = self.analyze_file(full_path, base_dir=str(target_path))
                    evidence_list.append(record)
                except (PermissionError, FileNotFoundError):
                    continue

        # 2. Duplicate Detection via SHA-256 hash collision
        for idx, item in enumerate(evidence_list):
            h = item["sha256"]
            if h not in hash_registry:
                hash_registry[h] = []
            hash_registry[h].append(idx)

        duplicate_count = 0
        for h, indices in hash_registry.items():
            if len(indices) > 1:
                duplicate_count += len(indices) - 1
                for idx in indices:
                    evidence_list[idx]["is_duplicate"] = True
                    evidence_list[idx]["duplicate_group_hash"] = h
            else:
                evidence_list[indices[0]]["is_duplicate"] = False
                evidence_list[indices[0]]["duplicate_group_hash"] = None

        # 3. Store Case Baseline in SQLite
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO forensic_cases (case_number, investigator, target_directory)
                    VALUES (?, ?, ?)
                    """,
                    (case_number, investigator, str(target_path))
                )
                case_id = cursor.lastrowid

                for item in evidence_list:
                    flags_str = "; ".join(item["suspicious_flags"]) if item["suspicious_flags"] else None
                    conn.execute(
                        """
                        INSERT INTO evidence_items (
                            case_id, relative_path, file_name, extension, size_bytes,
                            sha256, md5, created_timestamp, modified_timestamp, accessed_timestamp,
                            is_duplicate, duplicate_group_hash, suspicious_flags
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            case_id, item["relative_path"], item["filename"], item["extension"],
                            item["size_bytes"], item["sha256"], item["md5"], item["created_time"],
                            item["modified_time"], item["accessed_time"], 1 if item["is_duplicate"] else 0,
                            item["duplicate_group_hash"], flags_str
                        )
                    )

            return {
                "case_id": case_id,
                "case_number": case_number,
                "target_directory": str(target_path),
                "total_files_analyzed": len(evidence_list),
                "duplicate_files_found": duplicate_count,
                "suspicious_files_flagged": sum(1 for e in evidence_list if e["suspicious_flags"]),
                "evidence_items": evidence_list,
            }
        finally:
            conn.close()

    def verify_case_integrity(self, case_number: str) -> Dict[str, Any]:
        """
        Recalculate cryptographic SHA-256 hashes of all evidence items
        to verify evidence has not been tampered with or modified.
        """
        conn = self._get_connection()
        try:
            case = conn.execute("SELECT * FROM forensic_cases WHERE case_number = ?", (case_number,)).fetchone()
            if not case:
                raise ValueError(f"Case '{case_number}' not found.")

            target_dir = case["target_directory"]
            items = conn.execute("SELECT * FROM evidence_items WHERE case_id = ?", (case["id"],)).fetchall()

            intact = []
            modified = []
            missing = []

            for item in items:
                file_path = os.path.join(target_dir, item["relative_path"])
                if not os.path.exists(file_path):
                    missing.append({"file": item["relative_path"], "expected_sha256": item["sha256"]})
                    continue

                current_hashes = self.calculate_hashes(file_path)
                if current_hashes["sha256"] == item["sha256"]:
                    intact.append(item["relative_path"])
                else:
                    modified.append({
                        "file": item["relative_path"],
                        "original_sha256": item["sha256"],
                        "current_sha256": current_hashes["sha256"],
                    })

            # Record verification log
            with conn:
                conn.execute(
                    """
                    INSERT INTO integrity_verifications (case_id, total_checked, intact_count, modified_count, missing_count, summary_notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (case["id"], len(items), len(intact), len(modified), len(missing),
                     f"Intact: {len(intact)}, Tampered: {len(modified)}, Missing: {len(missing)}")
                )

            return {
                "case_number": case_number,
                "total_evidence_items": len(items),
                "intact_count": len(intact),
                "modified_count": len(modified),
                "missing_count": len(missing),
                "is_evidence_intact": len(modified) == 0 and len(missing) == 0,
                "modified_files": modified,
                "missing_files": missing,
            }
        finally:
            conn.close()

    def export_report(self, case_number: str, output_path: Optional[str] = None) -> str:
        conn = self._get_connection()
        try:
            case = conn.execute("SELECT * FROM forensic_cases WHERE case_number = ?", (case_number,)).fetchone()
            if not case:
                raise ValueError(f"Case '{case_number}' not found.")

            items = conn.execute("SELECT * FROM evidence_items WHERE case_id = ?", (case["id"],)).fetchall()
            evidence_data = [dict(i) for i in items]

            report = {
                "forensic_report_header": {
                    "case_number": case["case_number"],
                    "investigator": case["investigator"],
                    "target_directory": case["target_directory"],
                    "initial_scan_time": case["created_at"],
                    "total_evidence_files": len(evidence_data),
                },
                "evidence_manifest": evidence_data,
            }

            out = output_path or f"forensic_report_{case_number}.json"
            with open(out, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            return out
        finally:
            conn.close()
