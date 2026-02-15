use pyo3::prelude::*;
use rayon::prelude::*;
use std::collections::HashMap;

// ---------------------------------------------------------------------------
// Helpers for extracting values from the Python dict
// ---------------------------------------------------------------------------

fn extract_opt_string(py: Python<'_>, map: &HashMap<String, PyObject>, key: &str) -> Option<String> {
    map.get(key)
        .and_then(|obj| obj.extract::<Option<String>>(py).ok())
        .flatten()
}

fn extract_opt_f64(py: Python<'_>, map: &HashMap<String, PyObject>, key: &str) -> Option<f64> {
    map.get(key)
        .and_then(|obj| obj.extract::<Option<f64>>(py).ok())
        .flatten()
}

fn extract_opt_i64(py: Python<'_>, map: &HashMap<String, PyObject>, key: &str) -> Option<i64> {
    map.get(key)
        .and_then(|obj| obj.extract::<Option<i64>>(py).ok())
        .flatten()
}

fn extract_bool(py: Python<'_>, map: &HashMap<String, PyObject>, key: &str) -> bool {
    map.get(key)
        .and_then(|obj| obj.extract::<bool>(py).ok())
        .unwrap_or(false)
}

/// Extract a Python tristate: None → None, True → Some(true), False → Some(false)
fn extract_opt_bool(py: Python<'_>, map: &HashMap<String, PyObject>, key: &str) -> Option<bool> {
    map.get(key)
        .and_then(|obj| obj.extract::<Option<bool>>(py).ok())
        .flatten()
}

fn extract_list_nonempty(py: Python<'_>, map: &HashMap<String, PyObject>, key: &str) -> bool {
    map.get(key)
        .and_then(|obj| obj.extract::<Vec<PyObject>>(py).ok())
        .map(|v| !v.is_empty())
        .unwrap_or(false)
}

fn extract_signals(py: Python<'_>, map: &HashMap<String, PyObject>) -> Option<HashMap<String, PyObject>> {
    map.get("signals")
        .and_then(|obj| obj.extract::<Option<HashMap<String, PyObject>>>(py).ok())
        .flatten()
}

// ---------------------------------------------------------------------------
// Fit score  (prospect/scoring/fit.py)
// ---------------------------------------------------------------------------

const WEIGHT_WEBSITE: u32 = 15;
const WEIGHT_PHONE: u32 = 15;
const WEIGHT_EMAIL: u32 = 10;
const WEIGHT_MAPS_PRESENCE: u32 = 15;
const WEIGHT_GOOD_RATING: u32 = 10;
const WEIGHT_REVIEW_COUNT: u32 = 10;
const WEIGHT_ADS_PRESENCE: u32 = 10;
const WEIGHT_ORGANIC_TOP10: u32 = 15;

fn fit_score_inner(py: Python<'_>, prospect: &HashMap<String, PyObject>) -> u32 {
    let mut score: u32 = 0;

    if extract_opt_string(py, prospect, "website").is_some() {
        score += WEIGHT_WEBSITE;
    }
    if extract_opt_string(py, prospect, "phone").is_some() {
        score += WEIGHT_PHONE;
    }
    if extract_list_nonempty(py, prospect, "emails") {
        score += WEIGHT_EMAIL;
    }
    if extract_bool(py, prospect, "found_in_maps") {
        score += WEIGHT_MAPS_PRESENCE;
    }
    if let Some(rating) = extract_opt_f64(py, prospect, "rating") {
        if rating >= 4.0 {
            score += WEIGHT_GOOD_RATING;
        }
    }
    if let Some(rc) = extract_opt_i64(py, prospect, "review_count") {
        if rc >= 10 {
            score += WEIGHT_REVIEW_COUNT;
        }
    }
    if extract_bool(py, prospect, "found_in_ads") {
        score += WEIGHT_ADS_PRESENCE;
    }
    if extract_bool(py, prospect, "found_in_organic") {
        if let Some(pos) = extract_opt_i64(py, prospect, "organic_position") {
            if pos <= 10 {
                score += WEIGHT_ORGANIC_TOP10;
            }
        }
    }

    score.min(100)
}

#[pyfunction]
pub fn calculate_fit_score(prospect: HashMap<String, PyObject>) -> u32 {
    Python::with_gil(|py| fit_score_inner(py, &prospect))
}

// ---------------------------------------------------------------------------
// Opportunity score  (prospect/scoring/opportunity.py)
// ---------------------------------------------------------------------------

const OPP_NO_ANALYTICS: i32 = 15;
const OPP_NO_PIXEL: i32 = 10;
const OPP_NO_BOOKING: i32 = 15;
const OPP_NO_CONTACT: i32 = 10;
const OPP_WEAK_CMS: i32 = 10;
const OPP_SLOW_SITE: i32 = 10;
const OPP_RUNNING_ADS_PENALTY: i32 = -10;
const OPP_GOOD_TRACKING_PENALTY: i32 = -10;
const OPP_POOR_MAPS: i32 = 10;
const OPP_POOR_ORGANIC: i32 = 20;

fn opportunity_score_inner(py: Python<'_>, prospect: &HashMap<String, PyObject>) -> u32 {
    // No website → huge opportunity
    if extract_opt_string(py, prospect, "website").is_none() {
        return 80;
    }

    let signals = match extract_signals(py, prospect) {
        Some(s) => s,
        None => return 50, // can't analyse
    };

    let mut score: i32 = 0;

    // Missing GA (confirmed false) → +15
    if extract_opt_bool(py, &signals, "has_google_analytics") == Some(false) {
        score += OPP_NO_ANALYTICS;
    }

    // Missing FB pixel (confirmed false) → +10
    if extract_opt_bool(py, &signals, "has_facebook_pixel") == Some(false) {
        score += OPP_NO_PIXEL;
    }

    // No booking (confirmed false) → +15
    if extract_opt_bool(py, &signals, "has_booking_system") == Some(false) {
        score += OPP_NO_BOOKING;
    }

    // No contact emails → +10
    if !extract_list_nonempty(py, &signals, "emails") {
        score += OPP_NO_CONTACT;
    }

    // Weak CMS → +10
    let weak_cms = ["Wix", "Weebly", "GoDaddy Website Builder"];
    if let Some(cms) = extract_opt_string(py, &signals, "cms") {
        if weak_cms.contains(&cms.as_str()) {
            score += OPP_WEAK_CMS;
        }
    }

    // Slow site (>3000ms) → +10
    if let Some(load_time) = extract_opt_i64(py, &signals, "load_time_ms") {
        if load_time > 3000 {
            score += OPP_SLOW_SITE;
        }
    }

    // Penalty: already running ads
    if extract_bool(py, prospect, "found_in_ads") {
        score += OPP_RUNNING_ADS_PENALTY;
    }

    // Penalty: has both GA AND FB pixel (both confirmed true)
    if extract_opt_bool(py, &signals, "has_google_analytics") == Some(true)
        && extract_opt_bool(py, &signals, "has_facebook_pixel") == Some(true)
    {
        score += OPP_GOOD_TRACKING_PENALTY;
    }

    // Poor Maps ranking (found in maps but position > 1)
    if extract_bool(py, prospect, "found_in_maps") {
        if let Some(pos) = extract_opt_i64(py, prospect, "maps_position") {
            if pos > 1 {
                score += OPP_POOR_MAPS;
            }
        }
    }

    // Poor or no organic ranking
    if !extract_bool(py, prospect, "found_in_organic") {
        score += OPP_POOR_ORGANIC;
    } else if let Some(pos) = extract_opt_i64(py, prospect, "organic_position") {
        if pos > 5 {
            score += OPP_POOR_ORGANIC;
        }
    }

    score.clamp(0, 100) as u32
}

#[pyfunction]
pub fn calculate_opportunity_score(prospect: HashMap<String, PyObject>) -> u32 {
    Python::with_gil(|py| opportunity_score_inner(py, &prospect))
}

// ---------------------------------------------------------------------------
// Batch scoring with Rayon
// ---------------------------------------------------------------------------

#[pyfunction]
pub fn score_prospects_batch(prospects: Vec<HashMap<String, PyObject>>) -> Vec<(u32, u32)> {
    if prospects.len() <= 10 {
        // Sequential for small batches
        Python::with_gil(|py| {
            prospects
                .iter()
                .map(|p| (fit_score_inner(py, p), opportunity_score_inner(py, p)))
                .collect()
        })
    } else {
        // Parallel via Rayon for larger batches
        Python::with_gil(|py| {
            let results: Vec<(u32, u32)> = prospects
                .par_iter()
                .map(|p| {
                    Python::with_gil(|py_inner| {
                        (
                            fit_score_inner(py_inner, p),
                            opportunity_score_inner(py_inner, p),
                        )
                    })
                })
                .collect();
            let _ = py; // keep outer GIL reference alive
            results
        })
    }
}
