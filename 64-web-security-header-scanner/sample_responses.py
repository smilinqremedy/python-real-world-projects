"""
Sample HTTP response headers for offline testing and security benchmarking.
"""

SECURE_HARDENED_SITE = {
    "Content-Type": "text/html; charset=UTF-8",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none';",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}

VULNERABLE_LEGACY_SITE = {
    "Content-Type": "text/html",
    "Server": "Apache/2.4.41 (Ubuntu) OpenSSL/1.1.1d",
    "X-Powered-By": "PHP/7.4.3",
    # Missing all modern security headers
}

MISCONFIGURED_SITE = {
    "Content-Type": "text/html; charset=UTF-8",
    "Content-Security-Policy": "default-src * 'unsafe-inline' 'unsafe-eval'",  # overly permissive
    "Strict-Transport-Security": "max-age=60",  # way too short (less than recommended 6 months)
    "X-Content-Type-Options": "sniff",  # invalid value (must be nosniff)
    "X-Frame-Options": "ALLOW-FROM https://untrusted.com",  # deprecated and dangerous
    "Referrer-Policy": "unsafe-url",  # leaks full path
}
