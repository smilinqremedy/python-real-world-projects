# Project 64: Web Security Header Scanner

A defensive web application security auditing tool that analyzes HTTP response headers, evaluates adherence to browser security standards, identifies missing or misconfigured defensive controls, flags server technology fingerprinting leaks, computes weighted security grades (A+ through F), and generates JSON or HTML reports.

## Evaluated Security Headers

- **Content-Security-Policy (CSP)**: Mitigates Cross-Site Scripting (XSS) and data injection attacks by restricting origins of scripts, stylesheets, and images. Evaluates usage of dangerous directives like `'unsafe-inline'` and `'unsafe-eval'`.
- **Strict-Transport-Security (HSTS)**: Protects against SSL stripping and man-in-the-middle attacks. Validates `max-age` (minimum 6 months / 15,552,000s recommended) and `includeSubDomains`.
- **X-Content-Type-Options**: Prevents MIME-type sniffing vulnerabilities by enforcing `nosniff`.
- **X-Frame-Options & CSP `frame-ancestors`**: Protects against clickjacking by disallowing unauthorized framing.
- **Referrer-Policy**: Restricts the amount of sensitive URL path data sent in the HTTP Referer header.
- **Permissions-Policy**: Restricts browser APIs (camera, microphone, geolocation).

## Information Leakage Auditing

Detects sensitive banner disclosure headers that assist attackers during reconnaissance:
- `Server` (e.g. `Apache/2.4.41 (Ubuntu)`)
- `X-Powered-By` (e.g. `PHP/7.4.3`, `Express`, `ASP.NET`)
- `X-AspNet-Version`

## Dependencies

- Python 3.10+
- `requests`

```bash
pip install requests
```

## Running the Application

Launch the interactive CLI:

```bash
cd 64-web-security-header-scanner
python3 main.py
```

Options `2`, `3`, and `4` allow auditing against pre-packaged offline sample responses (Hardened, Vulnerable, Misconfigured) without making network calls.

## Running Unit Tests

Execute the automated test suite:

```bash
python3 -m unittest test_scanner.py -v
```
