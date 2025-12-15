"""Scoring module for prospect prioritization."""

from .fit import calculate_fit_score
from .opportunity import calculate_opportunity_score
from .notes import generate_opportunity_notes
from .industry import classify_industry, get_industry_multiplier, IndustryClassification
from .competition import calculate_competition_score, get_default_competition, CompetitionAnalysis
from .engine import score_prospect, apply_scores_to_prospect, calculate_priority_score, ProspectScore

__all__ = [
    # Original scoring functions
    "calculate_fit_score",
    "calculate_opportunity_score",
    "generate_opportunity_notes",
    # Industry classification (Andy's methodology)
    "classify_industry",
    "get_industry_multiplier",
    "IndustryClassification",
    # Competition analysis (Andy's methodology)
    "calculate_competition_score",
    "get_default_competition",
    "CompetitionAnalysis",
    # Unified scoring engine (Andy's methodology)
    "score_prospect",
    "apply_scores_to_prospect",
    "calculate_priority_score",
    "ProspectScore",
]
