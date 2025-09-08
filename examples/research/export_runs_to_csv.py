#!/usr/bin/env python3
"""
Extract wine data from recent runs in Neon database and generate WooCommerce CSV files.
"""

import sys
import json
import os
from pathlib import Path
from typing import List, Dict, Any
from run_store import get_db_url, POSTGRES_AVAILABLE

# Add export module to path
sys.path.insert(0, str(Path(__file__).parent))
from export.woocommerce_finalizer import finalize_wine_to_woocommerce_csv


def get_wine_data_from_runs(
    run_ids: List[str] = None, limit: int = 5
) -> List[Dict[str, Any]]:
    """Extract wine.json data from recent runs."""
    if not POSTGRES_AVAILABLE:
        print("❌ psycopg2 not available. Install with: pip install psycopg2-binary")
        return []

    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor

        db_url = get_db_url()
        wines_data = []

        with psycopg2.connect(db_url) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as c:
                if run_ids:
                    # Get specific runs
                    placeholders = ",".join(["%s"] * len(run_ids))
                    query = f"""
                        SELECT r.id, r.wine_slug, r.created_at, a.content as wine_json
                        FROM runs r
                        JOIN artifacts a ON r.id = a.run_id
                        WHERE r.id IN ({placeholders}) AND a.name = 'wine.json'
                        ORDER BY r.created_at DESC
                    """
                    c.execute(query, run_ids)
                else:
                    # Get recent runs with wine.json
                    c.execute(
                        """
                        SELECT r.id, r.wine_slug, r.created_at, a.content as wine_json
                        FROM runs r
                        JOIN artifacts a ON r.id = a.run_id
                        WHERE a.name = 'wine.json'
                        ORDER BY r.created_at DESC
                        LIMIT %s
                    """,
                        (limit,),
                    )

                runs = c.fetchall()

                # Track wines by multiple keys to deduplicate, keeping most recent
                wine_by_key = {}
                
                for run in runs:
                    try:
                        # Try to fix common JSON issues before parsing
                        json_content = run["wine_json"]
                        
                        try:
                            wine_json = json.loads(json_content)
                        except json.JSONDecodeError as e:
                            print(f"🔧 Attempting to repair JSON for run {run['id'][:8]}: {str(e)[:50]}...")
                            
                            # Fix common escape sequence issues
                            import re
                            
                            # Fix invalid single quote escapes
                            json_content = json_content.replace("\\'", "'")
                            
                            # Fix other invalid escape sequences (keep valid ones)
                            json_content = re.sub(r'\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', '', json_content)
                            
                            # Try parsing again
                            try:
                                wine_json = json.loads(json_content)
                                print(f"✅ JSON repair successful for run {run['id'][:8]}")
                            except json.JSONDecodeError as e2:
                                print(f"❌ JSON repair failed for run {run['id'][:8]}: {str(e2)[:50]}...")
                                raise e2
                        
                        wine_data = wine_json.get("wine", {})

                        if wine_data:
                            # Transform the data structure for CSV finalizer
                            normalized_wine = transform_wine_data(wine_data, run)
                            sku = normalized_wine.get('sku', '')
                            wine_name = normalized_wine.get('normalized_name', '')
                            vintage = normalized_wine.get('vintage', '')
                            
                            # Create deduplication key based on wine name and vintage
                            # Normalize wine name for better deduplication
                            normalized_name = wine_name.lower()
                            # Remove common variations and extra descriptors
                            normalized_name = normalized_name.replace('val do bibei godello', '').replace('valdeorras', '')
                            normalized_name = normalized_name.replace('  ', ' ').strip()
                            dedup_key = f"{normalized_name}_{vintage}".replace(' ', '_')
                            
                            if sku and dedup_key:
                                # Check if we already have this wine (by name + vintage)
                                if dedup_key in wine_by_key:
                                    # Compare creation dates (runs are already ordered by created_at DESC)
                                    # So the first occurrence is the most recent
                                    existing_sku = wine_by_key[dedup_key]['wine'].get('sku', '')
                                    print(f"🔄 Skipping duplicate wine: {wine_name} ({vintage}) - SKU: {sku} from older run {run['id'][:8]} (keeping {existing_sku})")
                                else:
                                    wine_by_key[dedup_key] = {
                                        'wine': normalized_wine,
                                        'run_info': run
                                    }
                                    print(f"✅ Extracted: {run['wine_slug']} ({run['id'][:8]}) - SKU: {sku}")
                            else:
                                print(f"⚠️  No SKU or wine name for: {run['wine_slug']} ({run['id'][:8]})")
                        else:
                            print(
                                f"⚠️  No wine data in: {run['wine_slug']} ({run['id'][:8]})"
                            )

                    except Exception as e:
                        print(f"❌ Failed to parse wine data for {run['id'][:8]}: {e}")

                # Convert back to list, preserving order by creation date
                wines_data = [entry['wine'] for entry in wine_by_key.values()]
                
                total_runs_with_data = len([r for r in runs if 'wine_json' in str(r)])
                if len(wines_data) < total_runs_with_data:
                    duplicates_removed = total_runs_with_data - len(wines_data)
                    print(f"🔍 Removed {duplicates_removed} duplicate wines, kept {len(wines_data)} unique wines")

        return wines_data

    except Exception as e:
        print(f"❌ Database query failed: {e}")
        return []


def transform_wine_data(
    wine_data: Dict[str, Any], run_info: Dict[str, Any]
) -> Dict[str, Any]:
    """Transform wine data from research format to CSV finalizer format."""

    def extract_value(field_data):
        """Extract value from field structure."""
        if isinstance(field_data, dict):
            return field_data.get("value", "")
        return field_data or ""

    def extract_grapes(grapes_data):
        """Extract grapes list from research format."""
        grapes_value = extract_value(grapes_data)
        if not grapes_value:
            return []

        # Handle different grape formats
        if isinstance(grapes_value, list):
            return grapes_value
        elif isinstance(grapes_value, str):
            # Try to parse grape string
            grape_parts = [g.strip() for g in grapes_value.split(",")]
            return [{"name": grape} for grape in grape_parts if grape]
        return []

    # Generate SKU from run info
    wine_slug = run_info.get("wine_slug", "").replace("research-", "").replace("-", "_")
    sku = f"wine_{wine_slug}"[:50]  # Limit SKU length

    # Extract basic wine info
    normalized_wine = {
        "sku": sku,
        "normalized_name": extract_value(wine_data.get("normalized_name")),
        "producer": extract_value(wine_data.get("producer")),
        "region": extract_value(wine_data.get("region")),
        "appellation": extract_value(
            wine_data.get("appellation", wine_data.get("region"))
        ),  # Fallback
        "vintage": extract_value(wine_data.get("vintage")),
        "grapes": extract_grapes(wine_data.get("grapes")),
        "country": extract_value(
            wine_data.get("country", "España")
        ),  # Default to Spain
        "type": extract_value(wine_data.get("type", "Tinto")),  # Default to red
        "alcohol_by_volume": extract_value(wine_data.get("alcohol_by_volume")),
        "price": 25.00,  # Default price - would need to be set manually
        "stock": True,  # Default in stock
    }

    # Add optional fields if available
    optional_fields = {
        "notes": "desc_es",
        "tasting_notes": "tasting_es",
        "serving_temperature": "serving_temp_es",
        "aging": "aging_es",
        "fermentation": "fermentation_es",
        "soil_type": "soil_es",
    }

    for source_field, target_field in optional_fields.items():
        value = extract_value(wine_data.get(source_field))
        if value:
            normalized_wine[target_field] = value

    # Ensure required fields have values
    if not normalized_wine["appellation"]:
        normalized_wine["appellation"] = normalized_wine["region"] or "Unknown"

    if not normalized_wine["grapes"]:
        normalized_wine["grapes"] = [{"name": "Unknown Grape"}]

    # Convert vintage to int if possible
    try:
        if normalized_wine["vintage"]:
            normalized_wine["vintage"] = int(str(normalized_wine["vintage"]).strip())
    except:
        normalized_wine["vintage"] = 2023  # Default vintage

    return normalized_wine


def export_runs_to_csv(
    run_ids: List[str] = None,
    limit: int = 5,
    output_dir: str = "csv_exports",
    output_format: str = "csv",
):
    """Export recent runs to WooCommerce CSV format."""
    print(
        f"🔍 Extracting wine data from {'specific runs' if run_ids else f'recent {limit} runs'}..."
    )

    # Get wine data from database
    wines_data = get_wine_data_from_runs(run_ids, limit)

    if not wines_data:
        print("❌ No wine data found to export")
        return

    print(f"✅ Found {len(wines_data)} wines to export")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Save wines data to JSON for processing
    wines_json_path = os.path.join(output_dir, "wines_from_runs.json")
    with open(wines_json_path, "w", encoding="utf-8") as f:
        json.dump(wines_data, f, indent=2, ensure_ascii=False)

    print(f"💾 Saved wine data to: {wines_json_path}")

    # Generate CSV files using our finalizer
    mapping_dir = "export/mappings"
    output_es = os.path.join(output_dir, "products_es.csv")
    output_en = os.path.join(output_dir, "products_en.csv")

    print("🏭 Generating WooCommerce CSV files...")

    result = finalize_wine_to_woocommerce_csv(
        data_path=wines_json_path,
        mapping_dir=mapping_dir,
        output_es=output_es,
        output_en=output_en,
        sku_strategy="suffix",
        include_attribute_data=False,
        output_format=output_format,
    )

    # Report results
    print("\n📊 Export Results:")
    print(f"   Wines processed: {result['wines_processed']}")
    print(f"   ES rows written: {result['rows_written_es']}")
    print(f"   EN rows written: {result['rows_written_en']}")

    if result["errors"]:
        print(f"   ❌ Errors: {len(result['errors'])}")
        for error in result["errors"]:
            print(f"      - {error}")

    if result["warnings"]:
        print(f"   ⚠️  Warnings: {len(result['warnings'])}")
        for warning in result["warnings"]:
            print(f"      - {warning}")

    if result["wines_processed"] > 0:
        print("\n✅ Files generated successfully:")

        if output_format in ["csv", "both"]:
            print(f"   📄 Spanish CSV: {output_es}")
            print(f"   📄 English CSV: {output_en}")

        if output_format in ["excel", "both"]:
            excel_es = output_es.replace(".csv", ".xlsx")
            excel_en = output_en.replace(".csv", ".xlsx")
            print(f"   📊 Spanish Excel: {excel_es}")
            print(f"   📊 English Excel: {excel_en}")

            if result.get("excel_files_written"):
                print(f"   ✅ Excel files written: {result['excel_files_written']}")

        # Show sample content
        if output_format in ["csv", "both"]:
            print("\n📋 Sample CSV content:")
            try:
                with open(output_es, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines[:3]):  # Header + first 2 rows
                        print(f"   {i+1}: {line.strip()[:100]}...")
            except Exception as e:
                print(f"   Error reading CSV: {e}")


def main():
    """Main CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Export wine runs to WooCommerce CSV")
    parser.add_argument(
        "--limit", type=int, default=5, help="Number of recent runs to export"
    )
    parser.add_argument("--run-ids", nargs="+", help="Specific run IDs to export")
    parser.add_argument(
        "--output-dir", default="csv_exports", help="Output directory for files"
    )
    parser.add_argument(
        "--format",
        choices=["csv", "excel", "both"],
        default="csv",
        help="Output format: csv, excel, or both",
    )

    args = parser.parse_args()

    export_runs_to_csv(
        run_ids=args.run_ids,
        limit=args.limit,
        output_dir=args.output_dir,
        output_format=args.format,
    )


if __name__ == "__main__":
    main()
