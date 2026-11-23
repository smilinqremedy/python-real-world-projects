"""
Web Security Header Scanner Engine.
Evaluates defensive HTTP security headers, detects missing and misconfigured controls,
flags sensitive server disclosure, calculates security grades, and exports audit findings.
"""
from urllib.parse import urlparse
import json
import re
from typing import Dict, List, Optional, Any
import requests


class WebSecurityHeaderScanner:
    RECOMMENDED_HEADERS = {
        "Content-Security-Policy": {
            "importance": "High",
            "points": 25,
            "description": "Restricts sources from which content and scripts can be loaded to prevent XSS."
        },
        "Strict-Transport-Security": {
            "importance": "High",
            "points": 20,
            "description": "Enforces secure HTTPS communication and protects against SSL stripping."
        },
        "X-Content-Type-Options": {
            "importance": "Medium",
            "points": 15,
            "description": "Prevents MIME-type sniffing attacks (must be 'nosniff')."
        },
        "X-Frame-Options": {
            "importance": "Medium",
            "points": 15,
            "description": "Protects against clickjacking by controlling if the site can be framed."
        },
        "Referrer-Policy": {
            "importance": "Low",
            "points": 15,
            "description": "Controls how much referrer information is included with requests."
        },
        "Permissions-Policy": {
            "importance": "Low",
            "points": 10,
            "description": "Restricts browser features like microphone, camera, and geolocation."
        },
    }

    INFORMATION_LEAK_HEADERS = ["Server", "X-Powered-By", "X-AspNet-Version", "X-Runtime"]

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate format of HTTP/HTTPS target URL."""
        if not url or not isinstance(url, str):
            return False
        parsed = urlparse(url.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)

    @classmethod
    def evaluate_csp(cls, value: str) -> Dict[str, Any]:
        val_lower = value.lower()
        issues = []
        deduction = 0

        if "'unsafe-inline'" in val_lower:
            issues.append("Contains 'unsafe-inline' which weakens XSS protections.")
            deduction += 5
        if "'unsafe-eval'" in val_lower:
            issues.append("Contains 'unsafe-eval' which allows string-to-code execution.")
            deduction += 5
        if "default-src *" in val_lower:
            issues.append("Uses overly broad wildcard 'default-src *'.")
            deduction += 5

        status = "Misconfigured" if issues else "Present & Valid"
        return {"status": status, "issues": issues, "deduction": deduction}

    @classmethod
    def evaluate_hsts(cls, value: str) -> Dict[str, Any]:
        val_lower = value.lower()
        issues = []
        deduction = 0

        match = re.search(r"max-age=(\d+)", val_lower)
        if not match:
            issues.append("Missing 'max-age' directive.")
            deduction += 10
        else:
            seconds = int(match.group(1))
            if seconds < 15552000:  # < 180 days
                issues.append(f"Short max-age ({seconds}s). Recommended is >= 31536000 (1 year).")
                deduction += 5

        if "includesubdomains" not in val_lower:
            issues.append("Missing 'includeSubDomains' directive.")
            deduction += 2

        status = "Misconfigured" if issues else "Present & Valid"
        return {"status": status, "issues": issues, "deduction": deduction}

    @classmethod
    def evaluate_x_content_type_options(cls, value: str) -> Dict[str, Any]:
        if value.strip().lower() != "nosniff":
            return {
                "status": "Misconfigured",
                "issues": [f"Value is '{value}'. Must strictly be 'nosniff'."],
                "deduction": 10
            }
        return {"status": "Present & Valid", "issues": [], "deduction": 0}

    @classmethod
    def evaluate_x_frame_options(cls, value: str, csp_value: Optional[str] = None) -> Dict[str, Any]:
        val_upper = value.strip().upper()
        # If CSP has frame-ancestors, that supersedes XFO
        if csp_value and "frame-ancestors" in csp_value.lower():
            return {"status": "Present & Valid", "issues": ["Protected via CSP frame-ancestors directive."], "deduction": 0}

        if val_upper not in ("DENY", "SAMEORIGIN"):
            return {
                "status": "Misconfigured",
                "issues": [f"Value '{value}' is invalid or deprecated. Use 'DENY' or 'SAMEORIGIN'."],
                "deduction": 10
            }
        return {"status": "Present & Valid", "issues": [], "deduction": 0}

    def scan_headers_dict(self, headers: Dict[str, str], target_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluate headers dictionary against security criteria.
        Pure function usable offline without performing external requests.
        """
        # Normalize header keys to lowercase for lookups
        normalized_headers = {k.lower(): v for k, v in headers.items()}
        results = []
        total_score = 100
        findings_count = {"missing": 0, "misconfigured": 0, "valid": 0, "info_leak": 0}

        # 1. Evaluate Core Security Headers
        for h_name, spec in self.RECOMMENDED_HEADERS.items():
            key = h_name.lower()
            if key not in normalized_headers:
                total_score -= spec["points"]
                findings_count["missing"] += 1
                results.append({
                    "header": h_name,
                    "status": "Missing",
                    "importance": spec["importance"],
                    "value": None,
                    "description": spec["description"],
                    "issues": [f"Header '{h_name}' is not set by the server."],
                    "score_deduction": spec["points"]
                })
            else:
                raw_val = normalized_headers[key]
                eval_res = {"status": "Present & Valid", "issues": [], "deduction": 0}

                if h_name == "Content-Security-Policy":
                    eval_res = self.evaluate_csp(raw_val)
                elif h_name == "Strict-Transport-Security":
                    eval_res = self.evaluate_hsts(raw_val)
                elif h_name == "X-Content-Type-Options":
                    eval_res = self.evaluate_x_content_type_options(raw_val)
                elif h_name == "X-Frame-Options":
                    csp_val = normalized_headers.get("content-security-policy")
                    eval_res = self.evaluate_x_frame_options(raw_val, csp_val)

                total_score -= eval_res["deduction"]
                if eval_res["status"] == "Misconfigured":
                    findings_count["misconfigured"] += 1
                else:
                    findings_count["valid"] += 1

                results.append({
                    "header": h_name,
                    "status": eval_res["status"],
                    "importance": spec["importance"],
                    "value": raw_val,
                    "description": spec["description"],
                    "issues": eval_res["issues"],
                    "score_deduction": eval_res["deduction"]
                })

        # 2. Check for Information Leakage Headers
        leaks = []
        for leak_header in self.INFORMATION_LEAK_HEADERS:
            l_key = leak_header.lower()
            if l_key in normalized_headers:
                leaks.append({
                    "header": leak_header,
                    "value": normalized_headers[l_key],
                    "recommendation": "Remove or mask this header in web server configuration to prevent server fingerprinting."
                })
                total_score -= 2
                findings_count["info_leak"] += 1

        final_score = max(0, min(100, total_score))
        grade = self.calculate_grade(final_score)

        return {
            "target": target_url or "Offline Header Inspection",
            "score": final_score,
            "grade": grade,
            "summary": findings_count,
            "evaluated_headers": results,
            "information_leakage": leaks
        }

    @staticmethod
    def calculate_grade(score: int) -> str:
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 50:
            return "D"
        return "F"

    def scan_url(self, url: str, timeout: int = 10, verify_ssl: bool = True) -> Dict[str, Any]:
        """Safely fetch and analyze HTTP headers from target website."""
        if not self.validate_url(url):
            raise ValueError(f"Invalid URL: '{url}'. Must start with http:// or https://")

        headers_agent = {
            "User-Agent": "SecurityHeaderScanner/1.0 (+https://github.com/smilinqremedy/python-real-world-projects)"
        }
        try:
            # First try lightweight HEAD request
            resp = requests.head(url, headers=headers_agent, timeout=timeout, allow_redirects=True, verify=verify_ssl)
        except requests.RequestException:
            # Fallback to GET if HEAD rejected
            resp = requests.get(url, headers=headers_agent, timeout=timeout, allow_redirects=True, verify=verify_ssl)

        return self.scan_headers_dict(dict(resp.headers), target_url=url)

    def export_report(self, report: Dict[str, Any], format: str = "json", output_path: Optional[str] = None) -> str:
        format = format.lower()
        if format == "json":
            out = output_path or "security_headers_report.json"
            with open(out, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            return out
        elif format == "html":
            out = output_path or "security_headers_report.html"
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Web Security Header Audit - {report['target']}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f8fafc; color: #1e293b; }}
        .card {{ background: white; padding: 24px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 9999px; font-weight: bold; font-size: 1.25rem; }}
        .grade-A {{ background: #dcfce7; color: #15803d; }}
        .grade-F {{ background: #fee2e2; color: #b91c1c; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #e2e8f0; }}
        th {{ background: #f1f5f9; }}
        .valid {{ color: #16a34a; font-weight: bold; }}
        .missing {{ color: #dc2626; font-weight: bold; }}
        .misconfig {{ color: #ea580c; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Web Security Header Audit</h1>
        <p><strong>Target:</strong> {report['target']}</p>
        <p><strong>Security Score:</strong> {report['score']} / 100</p>
        <p><strong>Grade:</strong> <span class="badge {'grade-A' if report['grade'].startswith('A') else 'grade-F'}">{report['grade']}</span></p>
    </div>
    <div class="card">
        <h2>Evaluated Headers</h2>
        <table>
            <tr><th>Header</th><th>Status</th><th>Severity</th><th>Issues / Value</th></tr>
"""
            for h in report["evaluated_headers"]:
                st_cls = "valid" if h["status"] == "Present & Valid" else ("missing" if h["status"] == "Missing" else "misconfig")
                issues_str = "; ".join(h["issues"]) if h["issues"] else (h["value"] or "N/A")
                html += f"<tr><td><strong>{h['header']}</strong></td><td class='{st_cls}'>{h['status']}</td><td>{h['importance']}</td><td>{issues_str}</td></tr>\n"
            html += """
        </table>
    </div>
</body>
</html>"""
            with open(out, "w", encoding="utf-8") as f:
                f.write(html)
            return out
        raise ValueError("Format must be 'json' or 'html'")
