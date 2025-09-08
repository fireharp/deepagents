# WooCommerce CSV Finalizer - Usage Guide

## Overview

The WooCommerce CSV Finalizer converts normalized wine data (JSON) into bilingual ES/EN WooCommerce-importable CSV files. It's located at `examples/research/export/woocommerce_finalizer.py` and is ready for production use.

## Basic Usage

```python
from examples.research.export.woocommerce_finalizer import finalize_wine_to_woocommerce_csv

# Convert wine data to WooCommerce CSVs
result = finalize_wine_to_woocommerce_csv(
    data_path="wine_data.json",           # Input JSON file
    mapping_dir="mappings/",              # Directory with attribute mappings
    output_es="products_es.csv",          # Spanish output file
    output_en="products_en.csv",          # English output file
    sku_strategy="suffix",                # "suffix" or "same"
    include_attribute_data=False,         # Include positioning data
    normalize_temp_style="14–17 °C",      # Temperature format
    normalize_abv_style="percent",        # ABV format (13.5%)
    output_format="csv"                   # "csv", "excel", or "both"
)

# Check results
print(f"Processed: {result['wines_processed']} wines")
print(f"ES rows: {result['rows_written_es']}")
print(f"EN rows: {result['rows_written_en']}")
if result['errors']:
    print("Errors:", result['errors'])
```

## Input Requirements

### Wine JSON Structure

```json
{
  "sku": "v0123", // Optional, auto-generated if missing
  "normalized_name": "Wine Name", // Required
  "producer": "Producer Name", // Required
  "region": "Wine Region", // Required
  "appellation": "Appellation", // Required
  "vintage": 2020, // Required
  "grapes": [
    // Required
    { "name": "Cabernet Sauvignon", "percent": 60 },
    { "name": "Merlot", "percent": 40 }
  ],
  "country": "Francia", // For attribute mapping
  "type": "Tinto", // For attribute mapping
  "price": 29.9, // Price in decimal format
  "stock": true, // Boolean or "instock"/"outofstock"

  // Optional bilingual text fields
  "name_es": "Spanish Name",
  "name_en": "English Name",
  "desc_es": "Spanish description",
  "desc_en": "English description",
  "tasting_es": "Spanish tasting notes",
  "tasting_en": "English tasting notes",
  "region_es": "Spanish region",
  "region_en": "English region",
  "winery_es": "Spanish winery",
  "winery_en": "English winery",
  "serving_temp_es": "14º-17ºC",
  "serving_temp_en": "14-17°C",
  "alcohol_by_volume": 13.5,
  "closure_type": "Cork", // Optional
  "blend_text": "Custom blend text" // Optional, overrides grape percentages
}
```

### Mapping Directory Structure

```
mappings/
├── countries.csv      # ES,EN country mappings
├── types.csv         # ES,EN wine type mappings
└── primary_grapes.csv # ES,EN,shortlist grape mappings
```

Production mapping files are in `examples/research/export/mappings/`.
Test mapping files are also available in `test_data/export/mappings/`.

## Integration within DeepAgents System

### As a Standalone Function

```python
# Direct integration in wine processing pipeline
from examples.research.export.woocommerce_finalizer import finalize_wine_to_woocommerce_csv

def process_wine_to_woocommerce(wine_data_path, output_dir):
    """Process wine data for WooCommerce import."""
    result = finalize_wine_to_woocommerce_csv(
        data_path=wine_data_path,
        mapping_dir="examples/research/export/mappings",
        output_es=f"{output_dir}/products_es.csv",
        output_en=f"{output_dir}/products_en.csv"
    )
    return result
```

### As a Subagent (Future Integration)

```python
# Planned subagent integration
class WooCommerceFinalizerAgent:
    def __init__(self):
        self.tools = ["read_file", "write_file", "ls"]

    def process(self, wine_json_path, mapping_dir, output_dir):
        return finalize_wine_to_woocommerce_csv(
            data_path=wine_json_path,
            mapping_dir=mapping_dir,
            output_es=f"{output_dir}/products_es.csv",
            output_en=f"{output_dir}/products_en.csv"
        )
```

### With Wine Agent Pipeline

```python
# Integration with existing wine_agent.py
def complete_wine_processing_pipeline(source_data):
    # 1. Extract and normalize wine data
    normalized_data = wine_agent.process_wine_data(source_data)

    # 2. Save normalized JSON
    with open("normalized_wines.json", "w") as f:
        json.dump(normalized_data, f)

    # 3. Generate WooCommerce CSVs
    result = finalize_wine_to_woocommerce_csv(
        data_path="normalized_wines.json",
        mapping_dir="examples/research/export/mappings",
        output_es="products_es.csv",
        output_en="products_en.csv"
    )

    return result
```

## Output Formats

### CSV Format (Default)

- **Delimiter**: Semicolon (`;`)
- **Multi-value separator**: Pipe (`|`) with no spaces
- **Encoding**: UTF-8

### Excel Format (XLSX)

- **Formatting**: Professional styling with header formatting
- **Features**: Auto-sized columns, frozen header row, price formatting
- **Compatibility**: Compatible with Excel, LibreOffice, Google Sheets

### Column Structure

#### ES Columns

- `sku`, `post_title`, `post_content`, `post_excerpt`, `regular_price`, `stock_status`
- `attribute:pa_pais` (mapped country)
- `attribute:pa_region` (free text)
- `attribute:pa_tipo` (mapped wine type)
- `attribute:pa_uva` (grape blend with percentages)
- `attribute:pa_uva-principal` (shortlist grapes only)
- `attribute:pa_enologo-bodega` (winery/producer)
- `attribute:pa_como-servirlo` (serving temperature)
- `attribute:pa_graduacion-alcoholica` (ABV percentage)
- `attribute:pa_tipo-tapon` (closure type, optional)

#### EN Columns

Same as ES, plus:

- `wpml:original_product_sku` (links to ES product)
- Translated attributes: `pa_pais`, `pa_tipo`, `pa_uva-principal`

## Key Features

### ✅ Validation & Error Handling

- Validates required fields before processing
- Returns detailed error reports
- Fails fast on validation errors (no partial CSVs)

### ✅ Normalization

- **Vintage removal**: "Wine Name 2020" → "Wine Name"
- **Price formatting**: 29.9 → "29.90"
- **ABV formatting**: 13.5 → "13.5%"
- **Temperature**: "14º-17ºC" → "14–17 °C"

### ✅ Bilingual Support

- ES/EN attribute mapping via canonical CSV files
- WPML linking with `wpml:original_product_sku`
- Fallback to ES text if EN not provided

### ✅ Grape Shortlist Constraint

- Primary grapes filtered to curated shortlist
- Non-shortlist grapes become "Otros varietales"/"Other varietals"

## Testing

Run comprehensive test suite:

```bash
cd /Users/fireharp/Prog/Wine/deepagents
python -m pytest tests/export/test_woocommerce_finalizer.py -v
```

All 14 tests pass, including:

- Unit tests for mapping, normalization, validation
- E2E integration test with spec example
- Edge cases and error handling

## Production Readiness

✅ **Complete implementation** following specification  
✅ **Comprehensive test coverage** (14 tests)  
✅ **Error handling** with detailed reporting  
✅ **CSV format compliance** (semicolon delimiters, pipe separators)  
✅ **WPML integration** for bilingual WooCommerce  
✅ **Canonical attribute mapping** system

The finalizer is ready for immediate production use and can be integrated as a subagent in the DeepAgents system.

## Database Export Examples

### Export Recent Runs

```bash
# Export to CSV (default)
uv run export_runs_to_csv.py --limit 5

# Export to Excel
uv run export_runs_to_csv.py --limit 5 --format excel

# Export to both CSV and Excel
uv run export_runs_to_csv.py --limit 5 --format both

# Export specific runs
uv run export_runs_to_csv.py --run-ids 9dc76d8a-cac1-41d3-a21d-c0cc6d229d2e --format excel

# Custom output directory
uv run export_runs_to_csv.py --output-dir my_exports --format both
```

## Example Command Line Usage

```bash
cd examples/research

# CSV Export
uv run -c "
from export.woocommerce_finalizer import finalize_wine_to_woocommerce_csv
result = finalize_wine_to_woocommerce_csv(
    'wine_data.json', 'mappings/', 'products_es.csv', 'products_en.csv'
)
print(f'Success: {len(result[\"errors\"]) == 0}')
print(f'Processed: {result[\"wines_processed\"]} wines')
"

# Excel Export
uv run -c "
from export.woocommerce_finalizer import finalize_wine_to_woocommerce_csv
result = finalize_wine_to_woocommerce_csv(
    'wine_data.json', 'mappings/', 'products_es.xlsx', 'products_en.xlsx',
    output_format='excel'
)
print(f'Excel files: {result.get(\"excel_files_written\", 0)}')
"

# Both formats
uv run -c "
from export.woocommerce_finalizer import finalize_wine_to_woocommerce_csv
result = finalize_wine_to_woocommerce_csv(
    'wine_data.json', 'mappings/', 'products_es.csv', 'products_en.csv',
    output_format='both'
)
print(f'CSV + Excel generated')
"
```
