"""Strict Content Security Policy (CSP) Headers."""
CSP_POLICIES = {
    "default-src": ["'self'"],
    "script-src": ["'self'", "'unsafe-inline'"],
    "style-src": ["'self'", "'unsafe-inline'"],
    "img-src": ["'self'", "data:"],
    "frame-ancestors": ["'none'"],
}
