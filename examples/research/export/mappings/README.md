# WooCommerce Wine Attribute Mappings

This directory contains canonical bilingual (ES/EN) mappings for wine attributes used by the WooCommerce CSV Finalizer.

## Files

### `countries.csv`

Maps wine-producing countries from Spanish to English names.

- **Format**: `ES,EN`
- **Examples**: `Francia,France`, `España,Spain`, `Estados Unidos,United States`
- **Coverage**: 65+ wine-producing countries worldwide

### `types.csv`

Maps wine types/styles from Spanish to English.

- **Format**: `ES,EN`
- **Examples**: `Tinto,Red`, `Blanco,White`, `Espumoso,Sparkling`
- **Coverage**: 50+ wine types including:
  - Basic colors: Tinto/Red, Blanco/White, Rosado/Rosé
  - Sparkling: Cava/Sparkling, Champagne, Prosecco
  - Fortified: Jerez/Sherry, Oporto/Port, Generoso/Fortified
  - Sweetness levels: Seco/Dry, Semidulce/Semi-Sweet, Dulce/Sweet
  - Aging classifications: Crianza, Reserva, Gran Reserva
  - Special styles: Orange Wine, Natural, Organic

### `primary_grapes.csv`

Maps grape varieties with shortlist constraint for primary grape selection.

- **Format**: `ES,EN,shortlist`
- **Shortlist**: `true` = included in primary grapes, `false` = collapsed to "Otros varietales"/"Other varietals"
- **Coverage**: 180+ grape varieties including:
  - **Shortlist (70+ varieties)**: Major international and Spanish grapes
    - International: Cabernet Sauvignon, Merlot, Chardonnay, Pinot Noir
    - Spanish: Tempranillo, Albariño, Verdejo, Mencía, Bobal
    - Portuguese: Touriga Nacional, Alvarinho, Arinto
    - Italian: Sangiovese, Nebbiolo, Vermentino, Fiano
    - French: Syrah/Shiraz, Grenache/Garnacha, Viognier, Roussanne
  - **Non-shortlist (110+ varieties)**: Regional/minor varieties that collapse to "Other varietals"

## Usage

The WooCommerce Finalizer automatically loads these mappings:

```python
from export.woocommerce_finalizer import finalize_wine_to_woocommerce_csv

result = finalize_wine_to_woocommerce_csv(
    data_path="wine_data.json",
    mapping_dir="examples/research/export/mappings",  # Points to this directory
    output_es="products_es.csv",
    output_en="products_en.csv"
)
```

## Mapping Logic

### Countries & Types

- **Exact match**: Input must match ES column exactly (case-sensitive, whitespace-trimmed)
- **Fallback**: Unknown values return as-is for both ES and EN

### Primary Grapes

- **Shortlist filtering**: Only grapes with `shortlist=true` are included in `pa_uva-principal`
- **Fallback**: If no shortlist grapes found, uses `"Otros varietales"` (ES) / `"Other varietals"` (EN)
- **Multiple values**: Joined with `|` separator (e.g., `"Cabernet Sauvignon|Merlot|Syrah / Shiraz"`)

## Maintenance

### Adding New Mappings

1. **Countries**: Add new row with exact Spanish name and English equivalent
2. **Types**: Add wine style with appropriate Spanish/English translation
3. **Grapes**: Add variety with correct `shortlist` flag:
   - `true`: Major commercial varieties, well-known regional grapes
   - `false`: Minor/experimental varieties, hybrids, very regional grapes

### Testing Changes

Run the test suite after modifications:

```bash
cd /Users/fireharp/Prog/Wine/deepagents
python -m pytest tests/export/test_woocommerce_finalizer.py -v
```

### Validation Rules

- **CSV format**: UTF-8 encoding, comma-separated, header row required
- **No duplicates**: Each ES value should appear only once per file
- **Consistent naming**: Use standard wine industry terminology
- **Shortlist balance**: Keep shortlist comprehensive but not overwhelming (~70-80 varieties)

## Data Sources

Mappings based on:

- **DO/DOC regulations**: Spanish, Portuguese, Italian wine classifications
- **OIV standards**: International Organisation of Vine and Wine
- **Wine industry databases**: Jancis Robinson, Wine Grapes, VIVC
- **Regional expertise**: Native speaker validation for translations
- **Commercial relevance**: Focus on varieties with market presence

## Version History

- **v1.0**: Initial production mappings with 65 countries, 50 types, 180 grape varieties
- Shortlist: 70 grape varieties for primary selection
- Coverage: Major wine regions worldwide with focus on Spanish/European varieties
