use pyo3::prelude::*;
use pyo3::types::PyDict;
use regex::Regex;
use std::collections::{HashMap, HashSet};
use std::sync::LazyLock;

// ---------------------------------------------------------------------------
// Compiled regexes
// ---------------------------------------------------------------------------

static EMAIL_RE: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}").unwrap()
});

static PHONE_PATTERNS: LazyLock<Vec<Regex>> = LazyLock::new(|| {
    vec![
        Regex::new(r"(?:\+61|0)[2-478](?:[ \-]?\d){8}").unwrap(),
        Regex::new(r"\(\d{2}\)[ \-]?\d{4}[ \-]?\d{4}").unwrap(),
        Regex::new(r"1[38]00[ \-]?\d{3}[ \-]?\d{3}").unwrap(),
        Regex::new(r"13[ \-]?\d{2}[ \-]?\d{2}").unwrap(),
    ]
});

static PHONE_NORMALIZE_RE: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"[^\d+]").unwrap()
});

// Spam email patterns (compiled)
static SPAM_EMAIL_RES: LazyLock<Vec<Regex>> = LazyLock::new(|| {
    vec![
        Regex::new(r"(?i).*@error-tracking\..*").unwrap(),
        Regex::new(r"(?i).*@sentry\.io").unwrap(),
        Regex::new(r"(?i).*@bugsnag\.com").unwrap(),
        Regex::new(r"(?i).*@errortracking\..*").unwrap(),
        Regex::new(r"(?i).*@tracking\..*").unwrap(),
        Regex::new(r"(?i).*noreply@.*").unwrap(),
        Regex::new(r"(?i).*no-reply@.*").unwrap(),
        Regex::new(r"(?i).*donotreply@.*").unwrap(),
        Regex::new(r"(?i).*do-not-reply@.*").unwrap(),
        Regex::new(r"(?i).*mailer-daemon@.*").unwrap(),
        Regex::new(r"(?i).*postmaster@.*").unwrap(),
        Regex::new(r"(?i).*automated@.*").unwrap(),
        Regex::new(r"(?i).*notifications@.*").unwrap(),
        Regex::new(r"(?i)[a-f0-9]{20,}@.*").unwrap(),
    ]
});

// Exclude patterns for emails (compiled)
static EXCLUDE_EMAIL_RES: LazyLock<Vec<Regex>> = LazyLock::new(|| {
    vec![
        Regex::new(r"(?i)@example\.").unwrap(),
        Regex::new(r"(?i)@test\.").unwrap(),
        Regex::new(r"(?i)@localhost").unwrap(),
        Regex::new(r"(?i)@domain\.").unwrap(),
        Regex::new(r"(?i)@email\.").unwrap(),
        Regex::new(r"(?i)@your").unwrap(),
        Regex::new(r"(?i)@site").unwrap(),
        Regex::new(r"(?i)@sample\.").unwrap(),
        Regex::new(r"(?i)@placeholder\.").unwrap(),
        Regex::new(r"(?i)cloudflare").unwrap(),
        Regex::new(r"(?i)googleapis").unwrap(),
        Regex::new(r"(?i)jquery").unwrap(),
        Regex::new(r"(?i)bootstrap").unwrap(),
        Regex::new(r"(?i)fontawesome").unwrap(),
        Regex::new(r"(?i)\.png$").unwrap(),
        Regex::new(r"(?i)\.jpg$").unwrap(),
        Regex::new(r"(?i)\.gif$").unwrap(),
        Regex::new(r"(?i)\.css$").unwrap(),
        Regex::new(r"(?i)\.js$").unwrap(),
        Regex::new(r"(?i)\.svg$").unwrap(),
        Regex::new(r"(?i)\.woff").unwrap(),
        Regex::new(r"(?i)\.webp$").unwrap(),
        Regex::new(r"(?i)@2x\.").unwrap(),
        Regex::new(r"(?i)@3x\.").unwrap(),
    ]
});

// Spam email domains
static SPAM_EMAIL_DOMAINS: LazyLock<HashSet<&'static str>> = LazyLock::new(|| {
    HashSet::from([
        "error-tracking.reddit.com",
        "sentry.io",
        "bugsnag.com",
        "wix.com",
        "wixpress.com",
        "wordpress.com",
        "squarespace.com",
        "squarespace-mail.com",
        "mailchimp.com",
        "sendgrid.net",
        "amazonses.com",
        "mailgun.org",
        "mandrillapp.com",
        "sparkpostmail.com",
        "postmarkapp.com",
        "intercom-mail.com",
        "zendesk.com",
        "freshdesk.com",
    ])
});

// ---------------------------------------------------------------------------
// CMS / Tracking / Booking / Framework signatures
// ---------------------------------------------------------------------------

static CMS_SIGNATURES: LazyLock<Vec<(&str, Vec<&str>)>> = LazyLock::new(|| {
    vec![
        ("WordPress", vec!["/wp-content/", "/wp-includes/", "wp-json", "wordpress"]),
        ("Wix", vec!["wix.com", "wixsite.com", "_wix_browser_sess", "wix-code"]),
        ("Squarespace", vec!["squarespace.com", "static.squarespace", "sqsp.net"]),
        ("Shopify", vec!["cdn.shopify.com", "myshopify.com", "shopify"]),
        ("Webflow", vec!["webflow.com", "assets-global.website-files", "webflow.io"]),
        ("Weebly", vec!["weebly.com", "weeblycloud.com"]),
        ("GoDaddy Website Builder", vec!["godaddy.com", "secureserver.net", "godaddysites"]),
        ("Joomla", vec!["joomla", "/components/com_"]),
        ("Drupal", vec!["drupal", "/sites/default/"]),
    ]
});

static TRACKING_SIGNATURES: LazyLock<Vec<(&str, Vec<&str>)>> = LazyLock::new(|| {
    vec![
        ("google_analytics", vec![
            "google-analytics.com", "gtag(", "ga(", "g-", "ua-", "googletagmanager.com",
        ]),
        ("facebook_pixel", vec![
            "facebook.com/tr", "fbq(", "connect.facebook.net",
        ]),
        ("google_ads", vec![
            "googleadservices.com", "googlesyndication.com", "aw-", "google_conversion",
        ]),
    ]
});

static BOOKING_SIGNATURES: LazyLock<Vec<&str>> = LazyLock::new(|| {
    vec![
        "calendly.com", "acuityscheduling", "youcanbook.me", "setmore.com",
        "square.site/book", "fresha.com", "book-online", "book-now",
        "schedule-appointment", "hubspot.com/meetings", "bookings.google.com",
        "appointlet.com", "simplybook.me", "timify.com",
    ]
});

static FRAMEWORK_SIGNATURES: LazyLock<Vec<(&str, Vec<&str>)>> = LazyLock::new(|| {
    vec![
        ("React", vec!["react", "reactdom", "__react"]),
        ("Vue.js", vec!["vue.js", "vuejs", "__vue__"]),
        ("Angular", vec!["ng-app", "ng-controller", "angular"]),
        ("jQuery", vec!["jquery", "$(document)", "$.ajax"]),
        ("Bootstrap", vec!["bootstrap.min", "bootstrap.css"]),
        ("Tailwind", vec!["tailwindcss", "tailwind.css"]),
    ]
});

static RESPONSIVE_INDICATORS: LazyLock<Vec<&str>> = LazyLock::new(|| {
    vec!["viewport", "media=", "@media", "responsive", "mobile", "bootstrap", "tailwind"]
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn is_spam_email(email: &str) -> bool {
    // Check domain blocklist
    if let Some(pos) = email.rfind('@') {
        let domain = &email[pos + 1..];
        if SPAM_EMAIL_DOMAINS.contains(domain) {
            return true;
        }
    }

    // Check spam patterns
    for re in SPAM_EMAIL_RES.iter() {
        if re.is_match(email) {
            return true;
        }
    }

    false
}

fn format_au_number(digits: &str) -> String {
    if digits.len() == 9 {
        if digits.starts_with('4') {
            // Mobile: 0XXX XXX XXX
            format!("0{} {} {}", &digits[0..3], &digits[3..6], &digits[6..])
        } else {
            // Landline: 0X XXXX XXXX
            format!("0{} {} {}", &digits[0..1], &digits[1..5], &digits[5..])
        }
    } else {
        digits.to_string()
    }
}

fn normalize_phone(phone: &str) -> String {
    if phone.is_empty() {
        return String::new();
    }

    let digits = PHONE_NORMALIZE_RE.replace_all(phone, "").to_string();

    // Count actual digits (excluding +)
    let digit_count = digits.chars().filter(|c| c.is_ascii_digit()).count();
    if digit_count < 8 {
        return String::new();
    }

    if digits.starts_with("+61") {
        let mut rest = &digits[3..];
        if rest.starts_with('0') {
            rest = &rest[1..];
        }
        format_au_number(rest)
    } else if digits.starts_with('0') {
        format_au_number(&digits[1..])
    } else if digits.starts_with("1300") || digits.starts_with("1800") {
        format!("{} {} {}", &digits[..4], &digits[4..7], &digits[7..])
    } else if digits.starts_with("13") && digits.len() == 6 {
        format!("{} {} {}", &digits[..2], &digits[2..4], &digits[4..])
    } else {
        phone.trim().to_string()
    }
}

// ---------------------------------------------------------------------------
// PyO3 functions
// ---------------------------------------------------------------------------

#[pyfunction]
pub fn extract_emails(html: &str) -> Vec<String> {
    if html.is_empty() {
        return Vec::new();
    }

    let mut valid_emails = Vec::new();
    let mut seen: HashSet<String> = HashSet::new();

    for m in EMAIL_RE.find_iter(html) {
        let email_lower = m.as_str().to_lowercase();

        if email_lower.len() > 100 {
            continue;
        }

        if seen.contains(&email_lower) {
            continue;
        }

        if is_spam_email(&email_lower) {
            continue;
        }

        if EXCLUDE_EMAIL_RES.iter().any(|re| re.is_match(&email_lower)) {
            continue;
        }

        // Skip hash-like local parts
        if let Some(pos) = email_lower.find('@') {
            let local_part = &email_lower[..pos];
            if local_part.len() > 15 {
                let hex_count = local_part
                    .chars()
                    .filter(|c| matches!(c, '0'..='9' | 'a'..='f'))
                    .count();
                if (hex_count as f64 / local_part.len() as f64) > 0.7 {
                    continue;
                }
            }
        }

        seen.insert(email_lower.clone());
        valid_emails.push(email_lower);

        if valid_emails.len() >= 5 {
            break;
        }
    }

    valid_emails
}

#[pyfunction]
pub fn extract_phones(html: &str) -> Vec<String> {
    if html.is_empty() {
        return Vec::new();
    }

    let mut phones = Vec::new();
    let mut seen: HashSet<String> = HashSet::new();

    for pattern in PHONE_PATTERNS.iter() {
        for m in pattern.find_iter(html) {
            let normalized = normalize_phone(m.as_str());
            if !normalized.is_empty() && !seen.contains(&normalized) {
                seen.insert(normalized.clone());
                phones.push(normalized);
            }
        }
    }

    phones
}

#[pyfunction]
pub fn detect_cms(html: &str) -> Option<String> {
    if html.is_empty() {
        return None;
    }

    let html_lower = html.to_lowercase();

    for (cms_name, signatures) in CMS_SIGNATURES.iter() {
        for sig in signatures {
            if html_lower.contains(&sig.to_lowercase()) {
                return Some(cms_name.to_string());
            }
        }
    }

    None
}

#[pyfunction]
pub fn detect_tracking(html: &str) -> HashMap<String, bool> {
    let mut result = HashMap::new();
    result.insert("google_analytics".to_string(), false);
    result.insert("facebook_pixel".to_string(), false);
    result.insert("google_ads".to_string(), false);

    if html.is_empty() {
        return result;
    }

    let html_lower = html.to_lowercase();

    for (tracker, signatures) in TRACKING_SIGNATURES.iter() {
        for sig in signatures {
            if html_lower.contains(sig) {
                result.insert(tracker.to_string(), true);
                break;
            }
        }
    }

    result
}

#[pyfunction]
pub fn detect_booking_system(html: &str) -> bool {
    if html.is_empty() {
        return false;
    }

    let html_lower = html.to_lowercase();

    BOOKING_SIGNATURES.iter().any(|sig| html_lower.contains(&sig.to_lowercase()))
}

#[pyfunction]
pub fn detect_frameworks(html: &str) -> Vec<String> {
    if html.is_empty() {
        return Vec::new();
    }

    let html_lower = html.to_lowercase();
    let mut frameworks = Vec::new();

    for (name, signatures) in FRAMEWORK_SIGNATURES.iter() {
        for sig in signatures {
            if html_lower.contains(sig) {
                frameworks.push(name.to_string());
                break;
            }
        }
    }

    frameworks
}

#[pyfunction]
pub fn detect_responsive(html: &str) -> bool {
    if html.is_empty() {
        return false;
    }

    let html_lower = html.to_lowercase();

    RESPONSIVE_INDICATORS.iter().any(|ind| html_lower.contains(ind))
}

#[pyfunction]
pub fn analyze_tech_stack(py: Python<'_>, html: &str) -> PyResult<PyObject> {
    let dict = PyDict::new(py);

    let cms = detect_cms(html);
    let tracking = detect_tracking(html);
    let has_booking = detect_booking_system(html);
    let frameworks = detect_frameworks(html);
    let has_responsive = detect_responsive(html);

    match cms {
        Some(ref v) => dict.set_item("cms", v)?,
        None => dict.set_item("cms", py.None())?,
    }

    let tracking_dict = PyDict::new(py);
    for (k, v) in &tracking {
        tracking_dict.set_item(k, *v)?;
    }
    dict.set_item("tracking", tracking_dict)?;

    dict.set_item("has_booking", has_booking)?;
    dict.set_item("frameworks", &frameworks)?;
    dict.set_item("has_ssl", false)?;
    dict.set_item("has_responsive", has_responsive)?;

    Ok(dict.into())
}
