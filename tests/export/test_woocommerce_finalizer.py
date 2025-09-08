"""
Unit and integration tests for WooCommerce CSV Finalizer
"""

import pytest
import json
import csv
import tempfile
import os
from pathlib import Path
import sys

# Add the examples/research directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "examples" / "research"))

from export.woocommerce_finalizer import (
    WooCommerceFinalizer,
    finalize_wine_to_woocommerce_csv,
)


class TestWooCommerceFinalizer:
    """Unit tests for WooCommerceFinalizer class methods."""

    @pytest.fixture
    def mapping_dir(self):
        """Fixture providing path to test mapping directory."""
        return str(
            Path(__file__).parent.parent.parent / "test_data" / "export" / "mappings"
        )

    @pytest.fixture
    def finalizer(self, mapping_dir):
        """Fixture providing initialized WooCommerceFinalizer."""
        return WooCommerceFinalizer(mapping_dir)

    def test_map_country(self, finalizer):
        """Test country mapping functionality."""
        # Test exact match
        es, en = finalizer.map_country("Francia")
        assert es == "Francia"
        assert en == "France"

        # Test with whitespace
        es, en = finalizer.map_country("  España  ")
        assert es == "España"
        assert en == "Spain"

        # Test unknown country (fallback)
        es, en = finalizer.map_country("Unknown Country")
        assert es == "Unknown Country"
        assert en == "Unknown Country"

    def test_map_type(self, finalizer):
        """Test wine type mapping functionality."""
        # Test exact match
        es, en = finalizer.map_type("Tinto")
        assert es == "Tinto"
        assert en == "Red"

        # Test with whitespace
        es, en = finalizer.map_type("  Blanco  ")
        assert es == "Blanco"
        assert en == "White"

        # Test unknown type (fallback)
        es, en = finalizer.map_type("Unknown Type")
        assert es == "Unknown Type"
        assert en == "Unknown Type"

    def test_map_primary_grapes(self, finalizer):
        """Test primary grapes mapping with shortlist constraint."""
        # Test shortlist grapes
        raw_grapes = ["Cabernet Sauvignon", "Merlot", "Syrah / Shiraz"]
        es_grapes, en_grapes = finalizer.map_primary_grapes(raw_grapes)
        assert "Cabernet Sauvignon" in es_grapes
        assert "Merlot" in es_grapes
        assert "Syrah / Shiraz" in es_grapes
        assert "Cabernet Sauvignon" in en_grapes
        assert "Merlot" in en_grapes
        assert "Syrah / Shiraz" in en_grapes

        # Test non-shortlist grapes (should return "Other varietals")
        raw_grapes = ["Unknown Grape"]
        es_grapes, en_grapes = finalizer.map_primary_grapes(raw_grapes)
        assert es_grapes == ["Otros varietales"]
        assert en_grapes == ["Other varietals"]

        # Test mixed shortlist and non-shortlist
        raw_grapes = ["Cabernet Sauvignon", "Unknown Grape"]
        es_grapes, en_grapes = finalizer.map_primary_grapes(raw_grapes)
        assert "Cabernet Sauvignon" in es_grapes
        assert "Cabernet Sauvignon" in en_grapes
        # Unknown grape should not appear since we have valid shortlist grapes

    def test_normalize_abv(self, finalizer):
        """Test ABV normalization."""
        # Test percent style with float
        result = finalizer.normalize_abv(13.5, "percent")
        assert result == "13.5%"

        # Test percent style with string
        result = finalizer.normalize_abv("13.5", "percent")
        assert result == "13.5%"

        # Test comma to dot conversion
        result = finalizer.normalize_abv("13,5", "percent")
        assert result == "13.5%"

        # Test None value
        result = finalizer.normalize_abv(None, "percent")
        assert result == ""

        # Test integer
        result = finalizer.normalize_abv(14, "percent")
        assert result == "14%"

    def test_normalize_temp(self, finalizer):
        """Test serving temperature normalization."""
        # Test default style
        result = finalizer.normalize_temp("14º - 17ºC", "14–17 °C")
        assert result == "14–17 °C"

        # Test alternative style
        result = finalizer.normalize_temp("14-17°C", "14º–17ºC")
        assert result == "14º–17ºC"

        # Test single temperature
        result = finalizer.normalize_temp("16°C", "14–17 °C")
        assert result == "16 °C"

        # Test empty string
        result = finalizer.normalize_temp("", "14–17 °C")
        assert result == ""

    def test_strip_vintage(self, finalizer):
        """Test vintage removal from wine names."""
        # Test with 4-digit year
        result = finalizer.strip_vintage("Mas de Daumas Gassac Rouge 2019")
        assert result == "Mas de Daumas Gassac Rouge"

        # Test with year in middle
        result = finalizer.strip_vintage("Château 2020 Bordeaux")
        assert result == "Château Bordeaux"

        # Test without vintage
        result = finalizer.strip_vintage("Simple Wine Name")
        assert result == "Simple Wine Name"

        # Test empty string
        result = finalizer.strip_vintage("")
        assert result == ""

        # Test multiple years
        result = finalizer.strip_vintage("Wine 1998 Vintage 2020")
        assert result == "Wine Vintage"

    def test_format_price(self, finalizer):
        """Test price formatting."""
        # Test float
        result = finalizer.format_price(29.9)
        assert result == "29.90"

        # Test string with comma
        result = finalizer.format_price("29,90")
        assert result == "29.90"

        # Test integer
        result = finalizer.format_price(30)
        assert result == "30.00"

        # Test None
        result = finalizer.format_price(None)
        assert result == "0.00"

        # Test string
        result = finalizer.format_price("10.95")
        assert result == "10.95"

    def test_validate_wine(self, finalizer):
        """Test wine record validation."""
        # Valid wine
        valid_wine = {
            "normalized_name": "Test Wine",
            "producer": "Test Producer",
            "region": "Test Region",
            "appellation": "Test Appellation",
            "vintage": 2020,
            "grapes": [{"name": "Cabernet Sauvignon", "percent": 100}],
        }
        errors = finalizer.validate_wine(valid_wine)
        assert len(errors) == 0

        # Missing required fields
        invalid_wine = {"normalized_name": "Test Wine"}
        errors = finalizer.validate_wine(invalid_wine)
        assert len(errors) > 0
        assert any("producer" in error for error in errors)

        # Invalid grapes structure
        invalid_grapes_wine = {
            "normalized_name": "Test Wine",
            "producer": "Test Producer",
            "region": "Test Region",
            "appellation": "Test Appellation",
            "vintage": 2020,
            "grapes": [{"invalid": "structure"}],
        }
        errors = finalizer.validate_wine(invalid_grapes_wine)
        assert len(errors) > 0
        assert any("name" in error for error in errors)

    def test_build_es_row(self, finalizer):
        """Test ES row building."""
        wine = {
            "sku": "test123",
            "normalized_name": "Test Wine 2020",
            "desc_es": "Spanish description",
            "tasting_es": "Spanish tasting notes",
            "price": 25.99,
            "stock": True,
            "country": "Francia",
            "region_es": "Test Region ES",
            "type": "Tinto",
            "grapes": [
                {"name": "Cabernet Sauvignon", "percent": 60},
                {"name": "Merlot", "percent": 40},
            ],
            "winery_es": "Test Winery ES",
            "serving_temp_es": "16-18°C",
            "alcohol_by_volume": 13.5,
        }

        row = finalizer.build_es_row(wine)

        assert row["sku"] == "test123"
        assert row["post_title"] == "Test Wine"  # vintage removed
        assert row["post_content"] == "Spanish description"
        assert row["post_excerpt"] == "Spanish tasting notes"
        assert row["regular_price"] == "25.99"
        assert row["stock_status"] == "instock"
        assert row["attribute:pa_pais"] == "Francia"
        assert row["attribute:pa_region"] == "Test Region ES"
        assert row["attribute:pa_tipo"] == "Tinto"
        assert "Cabernet Sauvignon 60%" in row["attribute:pa_uva"]
        assert "Merlot 40%" in row["attribute:pa_uva"]
        assert row["attribute:pa_enologo-bodega"] == "Test Winery ES"
        assert "16–18 °C" in row["attribute:pa_como-servirlo"]
        assert row["attribute:pa_graduacion-alcoholica"] == "13.5%"

    def test_build_en_row(self, finalizer):
        """Test EN row building."""
        wine = {
            "sku": "test123",
            "normalized_name": "Test Wine 2020",
            "name_en": "English Test Wine 2020",
            "desc_en": "English description",
            "tasting_en": "English tasting notes",
            "price": 25.99,
            "stock": True,
            "country": "Francia",
            "region_en": "Test Region EN",
            "type": "Tinto",
            "grapes": [
                {"name": "Cabernet Sauvignon", "percent": 60},
                {"name": "Merlot", "percent": 40},
            ],
            "winery_en": "Test Winery EN",
            "serving_temp_en": "16-18°C",
            "alcohol_by_volume": 13.5,
        }

        row = finalizer.build_en_row(wine, "test123", "test123-en")

        assert row["sku"] == "test123-en"
        assert row["wpml:original_product_sku"] == "test123"
        assert row["post_title"] == "English Test Wine"  # vintage removed
        assert row["post_content"] == "English description"
        assert row["post_excerpt"] == "English tasting notes"
        assert row["attribute:pa_pais"] == "France"  # translated
        assert row["attribute:pa_region"] == "Test Region EN"
        assert row["attribute:pa_tipo"] == "Red"  # translated
        assert row["attribute:pa_enologo-bodega"] == "Test Winery EN"


class TestIntegration:
    """Integration tests for the full finalize_wine_to_woocommerce_csv function."""

    @pytest.fixture
    def test_data_dir(self):
        """Fixture providing path to test data directory."""
        return str(Path(__file__).parent.parent.parent / "test_data" / "export")

    @pytest.fixture
    def mapping_dir(self, test_data_dir):
        """Fixture providing path to test mapping directory."""
        return str(Path(test_data_dir) / "mappings")

    def test_full_integration(self, test_data_dir, mapping_dir):
        """Test the complete end-to-end functionality."""
        wine_json_path = str(Path(test_data_dir) / "wine.json")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_es = os.path.join(temp_dir, "products_es.csv")
            output_en = os.path.join(temp_dir, "products_en.csv")

            # Run the finalizer
            result = finalize_wine_to_woocommerce_csv(
                data_path=wine_json_path,
                mapping_dir=mapping_dir,
                output_es=output_es,
                output_en=output_en,
                sku_strategy="suffix",
            )

            # Check result
            assert result["wines_processed"] == 1
            assert result["rows_written_es"] == 1
            assert result["rows_written_en"] == 1
            assert len(result["errors"]) == 0

            # Verify ES CSV
            assert os.path.exists(output_es)
            with open(output_es, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                rows = list(reader)
                assert len(rows) == 1

                row = rows[0]
                assert row["sku"] == "v0123"
                assert "Mas de Daumas Gassac Rouge" in row["post_title"]
                assert "2019" not in row["post_title"]  # vintage removed
                assert row["regular_price"] == "29.90"
                assert row["stock_status"] == "instock"
                assert row["attribute:pa_pais"] == "Francia"
                assert row["attribute:pa_tipo"] == "Tinto"
                assert "Cabernet Sauvignon 30%" in row["attribute:pa_uva"]
                assert "Merlot 30%" in row["attribute:pa_uva"]
                assert "Syrah / Shiraz 30%" in row["attribute:pa_uva"]
                assert "Grenache 10%" in row["attribute:pa_uva"]
                assert "Cabernet Sauvignon" in row["attribute:pa_uva-principal"]
                assert "Merlot" in row["attribute:pa_uva-principal"]
                assert "Syrah / Shiraz" in row["attribute:pa_uva-principal"]
                assert row["attribute:pa_graduacion-alcoholica"] == "13.5%"
                assert "14–17 °C" in row["attribute:pa_como-servirlo"]

            # Verify EN CSV
            assert os.path.exists(output_en)
            with open(output_en, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                rows = list(reader)
                assert len(rows) == 1

                row = rows[0]
                assert row["sku"] == "v0123-en"
                assert row["wpml:original_product_sku"] == "v0123"
                assert row["attribute:pa_pais"] == "France"  # translated
                assert row["attribute:pa_tipo"] == "Red"  # translated
                assert "Cabernet Sauvignon" in row["attribute:pa_uva-principal"]
                assert "Merlot" in row["attribute:pa_uva-principal"]
                assert "Syrah / Shiraz" in row["attribute:pa_uva-principal"]

    def test_sku_strategy_same(self, test_data_dir, mapping_dir):
        """Test SKU strategy 'same'."""
        wine_json_path = str(Path(test_data_dir) / "wine.json")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_es = os.path.join(temp_dir, "products_es.csv")
            output_en = os.path.join(temp_dir, "products_en.csv")

            result = finalize_wine_to_woocommerce_csv(
                data_path=wine_json_path,
                mapping_dir=mapping_dir,
                output_es=output_es,
                output_en=output_en,
                sku_strategy="same",
            )

            assert len(result["errors"]) == 0

            # Check EN CSV has same SKU
            with open(output_en, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                rows = list(reader)
                row = rows[0]
                assert row["sku"] == "v0123"  # same as ES
                assert row["wpml:original_product_sku"] == "v0123"

    def test_include_attribute_data(self, test_data_dir, mapping_dir):
        """Test including attribute positioning data."""
        wine_json_path = str(Path(test_data_dir) / "wine.json")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_es = os.path.join(temp_dir, "products_es.csv")
            output_en = os.path.join(temp_dir, "products_en.csv")

            result = finalize_wine_to_woocommerce_csv(
                data_path=wine_json_path,
                mapping_dir=mapping_dir,
                output_es=output_es,
                output_en=output_en,
                include_attribute_data=True,
            )

            assert len(result["errors"]) == 0

            # Check that attribute_data columns are present
            with open(output_es, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                rows = list(reader)
                row = rows[0]

                # Check some attribute_data fields
                if "attribute_data:pa_pais" in row:
                    assert "|1|0" in row["attribute_data:pa_pais"]

    def test_validation_errors(self, mapping_dir):
        """Test validation error handling."""
        # Create invalid wine data
        invalid_data = {
            "normalized_name": "Test Wine"
            # Missing required fields
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_data, f)
            temp_json_path = f.name

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                output_es = os.path.join(temp_dir, "products_es.csv")
                output_en = os.path.join(temp_dir, "products_en.csv")

                result = finalize_wine_to_woocommerce_csv(
                    data_path=temp_json_path,
                    mapping_dir=mapping_dir,
                    output_es=output_es,
                    output_en=output_en,
                )

                # Should have validation errors
                assert len(result["errors"]) > 0
                assert result["wines_processed"] == 0
                assert not os.path.exists(output_es)
                assert not os.path.exists(output_en)
        finally:
            os.unlink(temp_json_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
