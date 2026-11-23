"""
Cloud Storage Security Configuration Auditor Engine.
Evaluates AWS S3 bucket configurations (JSON/YAML) against security baselines
(CIS AWS Foundations Benchmark, NIST SP 800-53 controls).
"""
import os
import json
import yaml
from typing import Dict, List, Optional, Any


class CloudStorageSecurityAuditor:
    def __init__(self):
        pass

    @classmethod
    def load_config_file(cls, file_path: str) -> Dict[str, Any]:
        """Load storage configuration from a JSON or YAML file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        with open(file_path, "r", encoding="utf-8") as f:
            if ext in (".yaml", ".yml"):
                return yaml.safe_load(f)
            else:
                return json.load(f)

    def audit_bucket(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audit a bucket configuration dictionary and generate security findings.
        """
        bucket_name = config.get("BucketName", "unnamed-bucket")
        findings = []

        # ---------------- Check 1: S3 Public Access Block ----------------
        pab = config.get("PublicAccessBlockConfiguration")
        if not pab:
            findings.append({
                "check_id": "S3.1",
                "title": "S3 Public Access Block is Not Configured",
                "severity": "Critical",
                "description": f"Bucket '{bucket_name}' has no Public Access Block configuration, exposing it to accidental public exposure.",
                "remediation": f"aws s3api put-public-access-block --bucket {bucket_name} --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
            })
        else:
            disabled_flags = [k for k, v in pab.items() if not v]
            if disabled_flags:
                findings.append({
                    "check_id": "S3.1",
                    "title": "S3 Public Access Block Incomplete",
                    "severity": "High",
                    "description": f"Bucket '{bucket_name}' has public access controls disabled: {', '.join(disabled_flags)}.",
                    "remediation": f"aws s3api put-public-access-block --bucket {bucket_name} --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
                })

        # ---------------- Check 2: Bucket Policy Public Grant ----------------
        policy = config.get("BucketPolicy")
        if policy and isinstance(policy, dict):
            statements = policy.get("Statement", [])
            for stmt in statements:
                effect = stmt.get("Effect", "")
                principal = stmt.get("Principal", "")
                condition = stmt.get("Condition", {})

                is_wildcard = (principal == "*") or (isinstance(principal, dict) and principal.get("AWS") == "*")
                if effect == "Allow" and is_wildcard and not condition:
                    findings.append({
                        "check_id": "S3.2",
                        "title": "Overly Permissive Public Bucket Policy",
                        "severity": "Critical",
                        "description": f"Bucket policy statement '{stmt.get('Sid', 'unnamed')}' allows public access (Principal: '*') without IP or Org conditions.",
                        "remediation": f"Remove wildcard Principal grant or attach explicit Condition blocks to restrict access."
                    })

        # ---------------- Check 3: Server-Side Encryption (SSE) ----------------
        sse = config.get("ServerSideEncryptionConfiguration")
        if not sse or not sse.get("Rules"):
            findings.append({
                "check_id": "S3.3",
                "title": "Missing Default Server-Side Encryption",
                "severity": "High",
                "description": f"Bucket '{bucket_name}' does not enforce default server-side encryption for objects stored at rest.",
                "remediation": f"aws s3api put-bucket-encryption --bucket {bucket_name} --server-side-encryption-configuration '{{\"Rules\": [{{\"ApplyServerSideEncryptionByDefault\": {{\"SSEAlgorithm\": \"AES256\"}}}}]}}'"
            })

        # ---------------- Check 4: Access Logging Configuration ----------------
        logging_conf = config.get("LoggingConfiguration")
        if not logging_conf or not logging_conf.get("LoggingEnabled"):
            findings.append({
                "check_id": "S3.4",
                "title": "Server Access Logging Disabled",
                "severity": "Medium",
                "description": f"Bucket '{bucket_name}' does not have access logging enabled, preventing forensic tracking of requests and data exfiltration.",
                "remediation": f"aws s3api put-bucket-logging --bucket {bucket_name} --bucket-logging-status '{{\"LoggingEnabled\": {{\"TargetBucket\": \"audit-logs-bucket\", \"TargetPrefix\": \"{bucket_name}/\"}}}}'"
            })

        # ---------------- Check 5: Versioning Configuration ----------------
        versioning = config.get("VersioningConfiguration")
        v_status = versioning.get("Status") if versioning else None
        if v_status != "Enabled":
            findings.append({
                "check_id": "S3.5",
                "title": "S3 Bucket Versioning Disabled or Suspended",
                "severity": "Medium",
                "description": f"Bucket '{bucket_name}' versioning is '{v_status or 'Not Configured'}'. Versioning protects against ransomware overwriting and accidental deletions.",
                "remediation": f"aws s3api put-bucket-versioning --bucket {bucket_name} --versioning-configuration Status=Enabled"
            })

        # ---------------- Check 6: Enforce Secure Transport (HTTPS Only) ----------------
        enforces_tls = False
        if policy and isinstance(policy, dict):
            for stmt in policy.get("Statement", []):
                if stmt.get("Effect") == "Deny":
                    cond = stmt.get("Condition", {})
                    bool_cond = cond.get("Bool", {})
                    if str(bool_cond.get("aws:SecureTransport")).lower() == "false":
                        enforces_tls = True
                        break

        if not enforces_tls:
            findings.append({
                "check_id": "S3.6",
                "title": "Bucket Policy Does Not Enforce TLS/HTTPS",
                "severity": "Medium",
                "description": f"Bucket '{bucket_name}' does not explicitly deny non-TLS (unencrypted HTTP) data in transit.",
                "remediation": "Add an explicit Deny statement in bucket policy where aws:SecureTransport is false."
            })

        # ---------------- Calculate Risk Score & Posture ----------------
        total_checks = 6
        failed_checks = len(findings)
        passed_checks = max(0, total_checks - failed_checks)
        compliance_pct = round((passed_checks / total_checks) * 100, 1)

        critical_count = sum(1 for f in findings if f["severity"] == "Critical")
        high_count = sum(1 for f in findings if f["severity"] == "High")
        medium_count = sum(1 for f in findings if f["severity"] == "Medium")

        if critical_count > 0:
            posture = "POOR (CRITICAL EXPOSURE)"
        elif high_count > 0:
            posture = "SUBSTANDARD (HIGH RISK)"
        elif medium_count > 0:
            posture = "MODERATE (IMPROVEMENT NEEDED)"
        else:
            posture = "STRONG (EXCELLENT POSTURE)"

        return {
            "bucket_name": bucket_name,
            "compliance_percentage": compliance_pct,
            "security_posture": posture,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "severity_summary": {
                "Critical": critical_count,
                "High": high_count,
                "Medium": medium_count,
                "Low": 0,
            },
            "findings": findings
        }

    def export_report(self, audit_result: Dict[str, Any], output_path: Optional[str] = None) -> str:
        out = output_path or f"audit_report_{audit_result['bucket_name']}.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(audit_result, f, indent=2)
        return out
