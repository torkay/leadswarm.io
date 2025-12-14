"""Tests for search depth control features."""

import pytest
from prospect.scraper.locations import (
    get_nearby_suburbs,
    expand_query_variations,
    haversine_distance,
    location_to_coords,
)
from prospect.scraper.orchestrator import SearchOrchestrator, SearchPlan


class TestLocationExpansion:
    """Test location expansion functionality."""

    def test_get_nearby_suburbs_brisbane(self):
        """Test getting nearby suburbs for Brisbane."""
        suburbs = get_nearby_suburbs("Brisbane", radius_km=5, max_results=5)
        assert len(suburbs) >= 1
        assert "Brisbane CBD" in suburbs

    def test_get_nearby_suburbs_unknown_location(self):
        """Test unknown location returns original."""
        suburbs = get_nearby_suburbs("Unknown City", radius_km=10, max_results=5)
        assert suburbs == ["Unknown City"]

    def test_get_nearby_suburbs_limits_results(self):
        """Test that max_results is respected."""
        suburbs = get_nearby_suburbs("Brisbane", radius_km=50, max_results=3)
        assert len(suburbs) <= 3

    def test_haversine_distance_same_point(self):
        """Test distance between same point is 0."""
        dist = haversine_distance(-27.4698, 153.0251, -27.4698, 153.0251)
        assert dist == 0.0

    def test_haversine_distance_brisbane_sydney(self):
        """Test approximate distance Brisbane to Sydney."""
        # Brisbane CBD
        lat1, lon1 = -27.4698, 153.0251
        # Sydney CBD
        lat2, lon2 = -33.8688, 151.2093

        dist = haversine_distance(lat1, lon1, lat2, lon2)
        # Should be approximately 730km
        assert 700 < dist < 800

    def test_location_to_coords_brisbane(self):
        """Test coordinate lookup for Brisbane."""
        coords = location_to_coords("Brisbane")
        assert "@-27.4698,153.0251,12z" in coords

    def test_location_to_coords_unknown(self):
        """Test unknown location defaults to Brisbane."""
        coords = location_to_coords("Unknown City")
        # Should default to Brisbane
        assert "27.4698" in coords


class TestQueryExpansion:
    """Test query expansion functionality."""

    def test_expand_simple_query(self):
        """Test expanding a simple query."""
        variations = expand_query_variations(
            "plumber",
            ["{business_type} services", "{business_type} near me"]
        )
        assert "plumber" in variations
        assert "plumber services" in variations
        assert "plumber near me" in variations

    def test_expand_empty_templates(self):
        """Test with no templates returns base query."""
        variations = expand_query_variations("accountant", [])
        assert variations == ["accountant"]

    def test_expand_no_duplicates(self):
        """Test that duplicates are not added."""
        variations = expand_query_variations(
            "plumber",
            ["plumber", "{business_type}"]  # Both resolve to "plumber"
        )
        # Should only have one "plumber"
        assert variations.count("plumber") == 1


class TestSearchPlan:
    """Test search plan creation."""

    def test_plan_quick_search(self):
        """Test quick search plan has minimal API calls."""
        orchestrator = SearchOrchestrator()
        config = {
            "organic_pages": 1,
            "maps_pages": 0,
            "use_query_variations": False,
            "query_variations": [],
            "use_location_expansion": False,
            "search_organic": True,
            "search_maps": True,
            "search_local_services": False,
            "max_api_calls": 1,
            "estimated_cost_cents": 1,
        }

        plan = orchestrator.plan_search("plumber", "Brisbane", config)

        assert plan.total_api_calls == 1
        assert len(plan.queries) == 1
        assert len(plan.locations) == 1

    def test_plan_deep_search(self):
        """Test deep search plan has expanded queries and locations."""
        orchestrator = SearchOrchestrator()
        config = {
            "organic_pages": 3,
            "maps_pages": 2,
            "use_query_variations": True,
            "query_variations": [
                "{business_type} services",
                "{business_type} near me",
                "best {business_type}",
            ],
            "use_location_expansion": True,
            "expansion_radius_km": 10,
            "max_locations": 5,
            "search_organic": True,
            "search_maps": True,
            "search_local_services": True,
            "max_api_calls": 20,
            "estimated_cost_cents": 15,
        }

        plan = orchestrator.plan_search("plumber", "Brisbane", config)

        assert len(plan.queries) > 1  # Should have variations
        assert len(plan.locations) >= 1  # Should have expansions
        assert plan.total_api_calls <= 20  # Capped by max

    def test_plan_estimate_cost(self):
        """Test cost estimation."""
        orchestrator = SearchOrchestrator()
        config = {
            "organic_pages": 2,
            "maps_pages": 1,
            "use_query_variations": False,
            "query_variations": [],
            "use_location_expansion": False,
            "search_organic": True,
            "search_maps": True,
            "search_local_services": False,
            "max_api_calls": 5,
            "estimated_cost_cents": 5,
        }

        plan = orchestrator.plan_search("plumber", "Brisbane", config)
        estimate = orchestrator.estimate_cost(plan)

        assert "total_api_calls" in estimate
        assert "estimated_cost_cents" in estimate
        assert estimate["estimated_cost_cents"] > 0


class TestSearchConfigModel:
    """Test SearchConfig database model."""

    def test_search_config_seeded(self):
        """Test that search configs are seeded on init."""
        from prospect.web.database import SessionLocal, SearchConfig, init_db

        init_db()
        db = SessionLocal()

        try:
            configs = db.query(SearchConfig).all()
            names = [c.name for c in configs]

            assert "quick" in names
            assert "standard" in names
            assert "deep" in names
            assert "exhaustive" in names

        finally:
            db.close()

    def test_search_config_values(self):
        """Test that config values are correct."""
        from prospect.web.database import SessionLocal, SearchConfig, init_db

        init_db()
        db = SessionLocal()

        try:
            quick = db.query(SearchConfig).filter(SearchConfig.name == "quick").first()
            assert quick is not None
            assert quick.max_api_calls == 1
            assert quick.organic_pages == 1

            exhaustive = db.query(SearchConfig).filter(SearchConfig.name == "exhaustive").first()
            assert exhaustive is not None
            assert exhaustive.max_api_calls == 50
            assert exhaustive.use_location_expansion is True

        finally:
            db.close()
