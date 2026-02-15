use pyo3::prelude::*;
use regex::Regex;
use std::collections::HashSet;
use std::sync::LazyLock;
use url::Url;

// ---------------------------------------------------------------------------
// Static data
// ---------------------------------------------------------------------------

static DIRECTORY_DOMAINS: LazyLock<HashSet<&'static str>> = LazyLock::new(|| {
    HashSet::from([
        // Social media
        "facebook.com",
        "linkedin.com",
        "instagram.com",
        "twitter.com",
        "x.com",
        "youtube.com",
        "tiktok.com",
        "reddit.com",
        "quora.com",
        "pinterest.com",
        "threads.net",
        // Australian directories
        "yelp.com",
        "yelp.com.au",
        "yellowpages.com.au",
        "yellowpages.com",
        "truelocal.com.au",
        "hotfrog.com.au",
        "oneflare.com.au",
        "hipages.com.au",
        "productreview.com.au",
        "localsearch.com.au",
        "startlocal.com.au",
        "whereis.com",
        "whitepages.com.au",
        "aussieweb.com.au",
        "fyple.com.au",
        "brownbook.net",
        "wordofmouth.com.au",
        "findabusiness.com.au",
        "cylex.com.au",
        "opendi.com.au",
        "tuugo.com.au",
        "yalwa.com.au",
        // Marketplaces
        "airtasker.com",
        "airtasker.com.au",
        "serviceseeking.com.au",
        "bark.com",
        "bark.com.au",
        "thumbtack.com",
        "homeadvisor.com",
        "angi.com",
        "angieslist.com",
        "taskrabbit.com",
        "fiverr.com",
        "upwork.com",
        "freelancer.com",
        "freelancer.com.au",
        // Job boards
        "seek.com.au",
        "indeed.com",
        "indeed.com.au",
        "au.indeed.com",
        "glassdoor.com",
        "glassdoor.com.au",
        "jora.com",
        "careerone.com.au",
        // Review aggregators
        "birdeye.com",
        "trustpilot.com",
        "reviews.io",
        "podium.com",
        // Generic/tech
        "wikipedia.org",
        "google.com",
        "bing.com",
        "duckduckgo.com",
        "apple.com",
        "g2.com",
        "capterra.com",
        "crunchbase.com",
        "medium.com",
        "github.com",
        "stackoverflow.com",
        // News/media
        "news.com.au",
        "smh.com.au",
        "theaustralian.com.au",
        "abc.net.au",
        "9news.com.au",
        "7news.com.au",
        "sbs.com.au",
    ])
});

static DIRECTORY_URL_PATTERNS: &[&str] = &[
    "/r/",
    "/company/",
    "/biz/",
    "/local/",
    "/business/",
    "/pages/",
    "/profile/",
    "/user/",
    "/comments/",
    "/questions/",
    "/listing/",
    "/directory/",
    "/find-a-",
    "/search?",
    "/review/",
    "/reviews/",
    "/category/",
    "/service-provider/",
    "/tradies/",
];

static GENERIC_EMAIL_PROVIDERS: &[&str] = &[
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "live.com",
    "icloud.com",
    "me.com",
    "aol.com",
    "mail.com",
    "protonmail.com",
    "zoho.com",
    "bigpond.com",
    "bigpond.net.au",
    "optusnet.com.au",
    "telstra.com",
    "tpg.com.au",
    "internode.on.net",
];

// ---------------------------------------------------------------------------
// Lazy-compiled regexes
// ---------------------------------------------------------------------------

static RE_STAR_EMOJIS: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"[\u{2B50}\u{2605}\u{2606}\u{2729}\u{272A}\u{2730}\u{1F31F}]+").unwrap());

static RE_REVIEW_COUNT: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?i)\d+\.?\d*[Kk]?\+?\s*reviews?").unwrap());

static RE_REVIEW_COUNT_PARENS: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?i)\(\d+\.?\d*[Kk]?\+?\s*reviews?\)").unwrap());

static RE_NON_WORD_SPACE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"[^\w\s]").unwrap());

static RE_NORMALIZE_PHONE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"[^\d+]").unwrap());

static MARKETING_SUFFIX_PATTERNS: LazyLock<Vec<Regex>> = LazyLock::new(|| {
    let patterns = [
        r"(?i)\s*-\s*local\s*&\s*reliable.*",
        r"(?i)\s*-\s*trusted.*",
        r"(?i)\s*-\s*best\s*reviewed.*",
        r"(?i)\s*-\s*same[- ]?day.*",
        r"(?i)\s*\d+\+?\s*local.*",
        r"(?i)\s*-\s*#1\s*rated.*",
        r"(?i)\s*-\s*fast\s*&\s*reliable.*",
        r"(?i)\s*-\s*affordable.*",
        r"(?i)\s*-\s*professional.*",
        r"(?i)\s*-\s*expert.*",
        r"(?i)\s*-\s*your\s*local.*",
        r"(?i)\s*-\s*licensed\s*&\s*insured.*",
        r"(?i)\s*-\s*24/7.*",
        r"(?i)\s*-\s*free\s*quotes?.*",
    ];
    patterns.iter().map(|p| Regex::new(p).unwrap()).collect()
});

// Build suffix regexes for normalize_name
static NAME_SUFFIX_PATTERNS: LazyLock<Vec<Regex>> = LazyLock::new(|| {
    let suffixes = [
        "pty ltd", "pty\\. ltd\\.", "pty\\. ltd", "pty ltd\\.", "limited", "ltd", "inc", "llc",
        "corp", "co",
    ];
    suffixes
        .iter()
        .map(|s| Regex::new(&format!(r"(?i)\s+{}\.?$", s)).unwrap())
        .collect()
});

// ---------------------------------------------------------------------------
// Functions
// ---------------------------------------------------------------------------

#[pyfunction]
pub fn normalize_domain(raw_url: &str) -> Option<String> {
    let url = raw_url.trim();
    if url.is_empty() {
        return None;
    }

    // Reject stub URLs
    if matches!(url, "https:" | "http:" | "https://" | "http://") {
        return None;
    }

    // Add scheme if missing
    let with_scheme = if url.starts_with("http://") || url.starts_with("https://") {
        url.to_string()
    } else {
        format!("https://{}", url)
    };

    let parsed = Url::parse(&with_scheme).ok()?;
    let host = parsed.host_str()?;
    let mut domain = host.to_lowercase();

    // Remove www. prefix
    if let Some(stripped) = domain.strip_prefix("www.") {
        domain = stripped.to_string();
    }

    // Remove port (already handled by Url::host_str, but just in case of host:port in input)
    if let Some(idx) = domain.find(':') {
        domain = domain[..idx].to_string();
    }

    // Validate
    if !domain.contains('.') || domain.len() < 4 {
        return None;
    }
    if domain.contains(|c: char| matches!(c, ' ' | '<' | '>' | '"' | '\'' | ';')) {
        return None;
    }

    Some(domain)
}

#[pyfunction]
pub fn normalize_name(name: &str) -> String {
    if name.is_empty() {
        return String::new();
    }

    let mut normalized = name.to_lowercase();

    // Remove common business suffixes
    for re in NAME_SUFFIX_PATTERNS.iter() {
        normalized = re.replace(&normalized, "").to_string();
    }

    // Remove special characters except spaces (equivalent to [^\w\s])
    normalized = RE_NON_WORD_SPACE.replace_all(&normalized, "").to_string();

    // Normalize whitespace
    normalized.split_whitespace().collect::<Vec<_>>().join(" ")
}

#[pyfunction]
pub fn clean_business_name(name: &str) -> String {
    if name.is_empty() {
        return String::new();
    }

    let mut result = name.to_string();

    // Remove star emojis
    result = RE_STAR_EMOJIS.replace_all(&result, "").to_string();

    // Remove review counts (parenthesized first, then bare)
    result = RE_REVIEW_COUNT_PARENS.replace_all(&result, "").to_string();
    result = RE_REVIEW_COUNT.replace_all(&result, "").to_string();

    // Split at delimiters, keep first part
    for delimiter in [" | ", " - ", ": "] {
        if let Some(idx) = result.find(delimiter) {
            result = result[..idx].to_string();
        }
    }

    // Remove marketing suffixes
    for re in MARKETING_SUFFIX_PATTERNS.iter() {
        result = re.replace(&result, "").to_string();
    }

    // Clean whitespace
    result = result.split_whitespace().collect::<Vec<_>>().join(" ");
    result.trim().to_string()
}

#[pyfunction]
pub fn normalize_phone(phone: &str) -> String {
    if phone.is_empty() {
        return String::new();
    }

    // Remove all non-digit chars except +
    let mut digits = RE_NORMALIZE_PHONE.replace_all(phone, "").to_string();

    // Handle Australian +61 format
    if let Some(rest) = digits.strip_prefix("+61") {
        digits = format!("0{}", rest);
    } else if digits.starts_with("61") && digits.len() > 10 {
        digits = format!("0{}", &digits[2..]);
    }

    digits
}

#[pyfunction]
pub fn is_directory_domain(domain: &str) -> bool {
    if domain.is_empty() {
        return false;
    }
    let domain_lower = domain.to_lowercase();
    for dir_domain in DIRECTORY_DOMAINS.iter() {
        if domain_lower == *dir_domain {
            return true;
        }
        if domain_lower.ends_with(&format!(".{}", dir_domain)) {
            return true;
        }
    }
    false
}

#[pyfunction]
pub fn is_directory_url(url: &str, domain: &str) -> bool {
    if domain.is_empty() {
        return false;
    }

    // Check domain
    if is_directory_domain(domain) {
        return true;
    }

    // Check URL patterns
    if !url.is_empty() {
        let url_lower = url.to_lowercase();
        for pattern in DIRECTORY_URL_PATTERNS {
            if url_lower.contains(pattern) {
                return true;
            }
        }
    }

    false
}

fn get_base_domain(parts: &[&str]) -> String {
    let len = parts.len();
    if len >= 3 && matches!(parts[len - 2], "com" | "net" | "org" | "gov" | "edu") {
        parts[len - 3..].join(".")
    } else if len >= 2 {
        parts[len - 2..].join(".")
    } else {
        parts.join(".")
    }
}

#[pyfunction]
pub fn validate_email_domain(email: &str, website_domain: &str) -> (bool, String) {
    if email.is_empty() || website_domain.is_empty() {
        return (true, "No email or domain".to_string());
    }

    let email_domain = match email.rsplit_once('@') {
        Some((_, d)) => d.to_lowercase(),
        None => return (true, "Invalid email format".to_string()),
    };

    if email_domain.is_empty() {
        return (true, "Invalid email format".to_string());
    }

    let website = website_domain.to_lowercase().replace("www.", "");

    // Exact match
    if email_domain == website {
        return (true, "Exact match".to_string());
    }

    // Subdomain
    if email_domain.ends_with(&format!(".{}", website)) {
        return (true, "Subdomain".to_string());
    }

    // Parent domain
    if website.ends_with(&format!(".{}", email_domain)) {
        return (true, "Parent domain".to_string());
    }

    // Same base domain
    let email_parts: Vec<&str> = email_domain.split('.').collect();
    let website_parts: Vec<&str> = website.split('.').collect();
    if get_base_domain(&email_parts) == get_base_domain(&website_parts) {
        return (true, "Same base domain".to_string());
    }

    // Generic providers
    for provider in GENERIC_EMAIL_PROVIDERS {
        if email_domain == *provider {
            return (true, "Generic provider".to_string());
        }
    }

    (
        false,
        format!("Domain mismatch: {} vs {}", email_domain, website),
    )
}

#[pyfunction]
pub fn filter_emails_for_domain(emails: Vec<String>, website_domain: &str) -> Vec<String> {
    if emails.is_empty() {
        return Vec::new();
    }
    emails
        .into_iter()
        .filter(|email| validate_email_domain(email, website_domain).0)
        .collect()
}
