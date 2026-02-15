"""Benchmark: Rust native vs pure Python implementations."""

import time
import re
from urllib.parse import urlparse


def py_normalize_domain(url):
    if not url:
        return None
    url = url.strip()
    if url in ("https:", "http:", "https://", "http://"):
        return None
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    if ":" in domain:
        domain = domain.split(":")[0]
    if not domain or "." not in domain or len(domain) < 4:
        return None
    return domain


def py_clean_business_name(name):
    if not name:
        return ""
    name = re.sub(r'[\u2B50\u2605\u2606\u2729\u272A\u2730\U0001F31F]+', '', name)
    name = re.sub(r'\d+\.?\d*[Kk]?\+?\s*reviews?', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\(\d+\.?\d*[Kk]?\+?\s*reviews?\)', '', name, flags=re.IGNORECASE)
    for delimiter in [' | ', ' - ', ': ']:
        if delimiter in name:
            name = name.split(delimiter)[0]
    return ' '.join(name.split()).strip()


from _leadswarm_native import (
    normalize_domain as rust_normalize_domain,
    clean_business_name as rust_clean_business_name,
    extract_emails as rust_extract_emails,
    detect_cms as rust_detect_cms,
    detect_tracking as rust_detect_tracking,
)

# Email regex (Python)
EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', re.IGNORECASE)


def py_extract_emails(html):
    return list(set(EMAIL_RE.findall(html)))[:5]


# Test data
URLS = [
    "https://www.example.com/page",
    "http://sub.mybusiness.com.au/about",
    "mybiz.com",
    "https://shop.bigstore.com:8080/products",
    "not a url",
] * 200  # 1000 URLs

NAMES = [
    "Best Plumber ⭐ 4.8 (500+ Reviews) | Local & Reliable",
    "Smith's Electrical Pty Ltd - Professional Services",
    "ABC Roofing - #1 Rated - Free Quotes",
    "Joe's Landscaping 2.2K+ reviews - Trusted",
] * 250  # 1000 names

SAMPLE_HTML = """
<html><head><link href="/wp-content/themes/starter">
<script>gtag('config', 'G-12345')</script>
<script>fbq('init', '123')</script>
</head><body>
Contact us at info@example-biz.com or sales@example-biz.com
Call 0412 345 678 or (07) 1234 5678
<a href="https://calendly.com/booking">Book now</a>
</body></html>
""" * 100  # ~10KB HTML repeated

N = 1000


def bench(label, py_fn, rust_fn, args_list):
    # Python
    start = time.perf_counter()
    for args in args_list:
        py_fn(*args) if isinstance(args, tuple) else py_fn(args)
    py_time = time.perf_counter() - start

    # Rust
    start = time.perf_counter()
    for args in args_list:
        rust_fn(*args) if isinstance(args, tuple) else rust_fn(args)
    rust_time = time.perf_counter() - start

    speedup = py_time / rust_time if rust_time > 0 else float('inf')
    print(f"{label:30s}  Python: {py_time*1000:8.2f}ms  Rust: {rust_time*1000:8.2f}ms  Speedup: {speedup:.1f}x")


print(f"Benchmarking {N} iterations each...\n")
bench("normalize_domain", py_normalize_domain, rust_normalize_domain, URLS)
bench("clean_business_name", py_clean_business_name, rust_clean_business_name, NAMES)
bench("extract_emails (HTML)", py_extract_emails, rust_extract_emails, [SAMPLE_HTML] * 100)
bench("detect_cms (HTML)", lambda h: None, rust_detect_cms, [SAMPLE_HTML] * 100)
bench("detect_tracking (HTML)", lambda h: {}, rust_detect_tracking, [SAMPLE_HTML] * 100)
