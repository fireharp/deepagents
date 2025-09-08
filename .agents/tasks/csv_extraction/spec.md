## WooCommerce CSV Finalizer — Specification (ES/EN)

### Purpose

- Convert normalized wine data (JSON) into two WooCommerce-importable CSVs compliant with the `dev_brief.md` rules:
  - ES CSV: authoritative Spanish products to sell.
  - EN CSV: English mirror with `wpml:original_product_sku` = ES `sku`.

### Inputs (Data Contract)

- `data_path` (str): Path to a JSON file containing wine records.
  - Accepts either a single object or an array of objects.
  - Minimal required fields for each wine:
    - `normalized_name` (str)
    - `producer` (str)
    - `region` (str)
    - `appellation` (str)
    - `vintage` (int|str)
    - `grapes` (array of { name: str, percent?: number|null })
  - Optional fields used for text columns:
    - `name_es`, `name_en`
    - `desc_es`, `desc_en`
    - `tasting_es`, `tasting_en`
    - `region_es`, `region_en`
    - `winery_es`, `winery_en`
    - `serving_temp_es`, `serving_temp_en`
    - `alcohol_by_volume` (number|string, e.g., 13.5)
    - `blend_text` (string for `pa_uva`; otherwise derived from `grapes`)
    - `closure_type` (for `pa_tipo-tapon`, optional)
    - `price` (number|string)
    - `stock` (boolean) or `stock_status` ("instock"|"outofstock")
    - `country` (str)
    - `type` (str) — color/style (e.g., Tinto/Red)
    - `primary_grapes` (array of str) — if provided, used for `pa_uva-principal`; otherwise derived from `grapes` names.
- `mapping_dir` (str): Directory containing canonical attribute mappings (ES/EN pairs + shortlist):
  - `Atributos.xlsx` (authoritative source) or pre-extracted fixtures:
    - `countries.csv` with columns: ES, EN
    - `types.csv` with columns: ES, EN
    - `primary_grapes.csv` with columns: ES, EN, shortlist:boolean (or separate shortlist file)
  - For unit/integration tests, use small CSV fixtures in `test_data/export/mappings/`.
- `output_es` (str): Path for ES CSV (default: `products_es.csv`).
- `output_en` (str): Path for EN CSV (default: `products_en.csv`).
- `sku_strategy` (enum): `suffix` (default, EN `sku = es_sku + "-en"`) or `same`.
- `include_attribute_data` (bool, default: false): If true, include `attribute_data:* = position|1|0` columns.
- `normalize_temp_style` (enum): `"14–17 °C"` or `"14º–17ºC"` (default: `"14–17 °C"`).
- `normalize_abv_style` (enum): `percent` (e.g., `"13.5%"`; default and only initial option).

### Outputs

- Two UTF-8 CSV files with `;` as field delimiter and `|` as list delimiter (no spaces around `|`).
  - ES columns (minimum set):
    - `sku`, `post_title`, `post_content`, `post_excerpt`, `regular_price`, `stock_status`
    - Attributes:
      - `attribute:pa_pais` (mapped, ES)
      - `attribute:pa_region` (free text)
      - `attribute:pa_tipo` (mapped, ES)
      - `attribute:pa_uva` (free text, `|` allowed)
      - `attribute:pa_uva-principal` (controlled shortlist, `|`)
      - `attribute:pa_enologo-bodega`
      - `attribute:pa_como-servirlo`
      - `attribute:pa_graduacion-alcoholica`
      - Optional: `attribute:pa_tipo-tapon`
    - Optional: `tax:product_cat`, `tax:product_tag`, and `attribute_data:*` if enabled
  - EN columns mirror ES, plus:
    - `wpml:original_product_sku` = ES `sku`
    - `attribute:pa_pais`, `attribute:pa_tipo`, `attribute:pa_uva-principal` use EN canonical values
  - Column order stable and consistent across runs.

### Rules and Normalization

- No vintages in names: Remove vintage tokens from `post_title`.
- Price: dot decimal only (e.g., `10.95`).
- Stock: `instock`|`outofstock` only.
- ABV: `normalize_abv_style = percent` → `13.5%` (dot decimals).
- Serving temperature: normalize to the configured style (default `14–17 °C`).
- Multi-value fields: join with `|` (no surrounding spaces), e.g., `Cabernet Sauvignon|Merlot`.
- Controlled attributes:
  - `pa_pais`, `pa_tipo`, `pa_uva-principal` MUST map to canonical ES/EN sets.
  - `pa_uva-principal` must be constrained to the curated shortlist; all other grapes → `"Otros varietales"` (ES) / `"Other varietals"` (EN).
- Encoding: UTF-8 with `\n` line endings.

### Public API (planned)

Python module target (no code yet): `src/deepagents/export/woocommerce_finalizer.py`

Function (planned signature):

```
def finalize_wine_to_woocommerce_csv(
    data_path: str,
    mapping_dir: str,
    output_es: str = "products_es.csv",
    output_en: str = "products_en.csv",
    sku_strategy: str = "suffix",  # one of {"suffix","same"}
    include_attribute_data: bool = False,
    normalize_temp_style: str = "14–17 °C",
    normalize_abv_style: str = "percent",
) -> dict:
    """
    Returns a report dict with keys:
      - wines_processed (int)
      - rows_written_es (int)
      - rows_written_en (int)
      - warnings (list[str])
      - errors (list[str])  # empty if successful
    """
```

Notes:

- The function MUST validate inputs and fail fast with clear errors; it MUST NOT emit partial CSVs on fatal validation errors.
- If `sku_strategy == "same"`, EN `sku` equals ES `sku`; linking still requires `wpml:original_product_sku`.
- If bilingual free-text fields are missing, EN row mirrors ES text fields; attributes are still translated via mappings.

### Validation (pre-write)

- Required presence per wine: `normalized_name`, `producer`, `region`, `appellation`, `vintage`, `grapes` (or an equivalent to derive `primary_grapes`).
- `sku` policy: input may provide `sku`; otherwise generate stable `sku` (implementation detail TBD). For tests, include explicit `sku` in fixtures.
- `stock_status` resolves to `instock`/`outofstock` using `stock` boolean or explicit value.
- `regular_price` parses to dot-decimal string.
- `post_title` contains no vintage after normalization.
- `attribute:pa_pais`, `attribute:pa_tipo`, `attribute:pa_uva-principal` mapped to canonical values per language.

### Attribute Positioning (if enabled)

- Include `attribute_data:*` columns with `position|1|0` values.
- Suggested positions (stable):
  1: `pa_maridaje`, 2: `pa_region`, 3: `pa_enologo-bodega`, 4: `pa_graduacion-alcoholica`, 5: `pa_tipo-tapon`, 6: `pa_pais`, 7: `pa_tipo`, 8: `pa_uva-principal`, 9: `pa_como-servirlo`, 10: `pa_uva`.
- Only positions for attributes present should be emitted.

### Test Plan (spec-first)

File layout:

- Tests: `tests/export/`
- Fixtures: `test_data/export/`

Unit tests:

1. Mapping:
   - `map_country(raw) -> (es, en)` exact-match against canonical sets; trims whitespace.
   - `map_type(raw) -> (es, en)` exact-match; trims whitespace.
   - `map_primary_grapes(raw_list) -> (es_list, en_list)` with shortlist constraint; non-shortlist → `Otros varietales` / `Other varietals`.
2. Normalizers:
   - `normalize_abv(13.5, "percent") -> "13.5%"`; commas become dots.
   - `normalize_temp("14º - 17ºC", style="14–17 °C") -> "14–17 °C"`.
   - `strip_vintage("Mas de Daumas Gassac Rouge 2019") -> "Mas de Daumas Gassac Rouge"`.
   - `format_price(29.9) -> "29.90"`.
3. Row builder:
   - ES and EN rows conform to column set; EN has `wpml:original_product_sku` and translated attributes.
   - Multi-values join with `|` and no spaces.
4. Validation:
   - Price/stock/controlled-attributes enforcement; raises on fatal issues; accumulates non-fatal warnings.

Integration/E2E test:

- Given fixture `test_data/export/wine.json`:
  ```json
  {
    "sku": "v0123",
    "normalized_name": "Mas de Daumas Gassac Rouge",
    "producer": "Mas de Daumas Gassac",
    "region": "IGP Pays d'Hérault",
    "appellation": "IGP",
    "vintage": 2019,
    "grapes": [
      { "name": "Cabernet Sauvignon", "percent": 30 },
      { "name": "Merlot", "percent": 30 },
      { "name": "Syrah / Shiraz", "percent": 30 },
      { "name": "Grenache", "percent": 10 }
    ],
    "country": "Francia",
    "type": "Tinto",
    "price": 29.9,
    "stock": true,
    "desc_es": "Tinto mediterráneo elegante...",
    "tasting_es": "Aromas de frutos rojos, especias...",
    "serving_temp_es": "14º - 17ºC",
    "alcohol_by_volume": 13.5,
    "winery_es": "Mas de Daumas Gassac",
    "region_es": "IGP Pays d'Hérault"
  }
  ```
- And mappings:
  - countries: `Francia ↔ France`
  - types: `Tinto ↔ Red`
  - primary_grapes shortlist includes: Cabernet Sauvignon, Merlot, Syrah / Shiraz; others collapse to `Otros varietales` / `Other varietals` if outside shortlist (here, all four can be accepted in shortlist for the test or treat `Grenache` per shortlist choice).
- When run with defaults, the module writes:
  - `products_es.csv` row (semicolon, pipes):
    - `sku=v0123; post_title=Mas de Daumas Gassac Rouge; post_content=...; post_excerpt=...; regular_price=29.90; stock_status=instock; attribute:pa_pais=Francia; attribute:pa_region=IGP Pays d'Hérault; attribute:pa_tipo=Tinto; attribute:pa_uva=Cabernet Sauvignon 30%|Merlot 30%|Syrah / Shiraz 30%|Grenache 10%; attribute:pa_uva-principal=Cabernet Sauvignon|Merlot|Syrah / Shiraz; attribute:pa_enologo-bodega=Mas de Daumas Gassac; attribute:pa_como-servirlo=14–17 °C; attribute:pa_graduacion-alcoholica=13.5%`
  - `products_en.csv` row mirrors ES, with:
    - `sku=v0123-en; wpml:original_product_sku=v0123; attribute:pa_pais=France; attribute:pa_tipo=Red; attribute:pa_uva-principal=Cabernet Sauvignon|Merlot|Syrah / Shiraz`

Golden assertions:

- CSV delimiter is `;` and list delimiter is `|`.
- EN file preserves row order and links via `wpml:original_product_sku`.
- No vintage in `post_title`.

### Non-Goals (initial)

- XLSX parsing in production path (tests may use CSV fixtures derived from `Atributos.xlsx`).
- Advanced localization of EN text content (future subagent). For now, EN may mirror ES text fields if not provided.

### Integration Plan (later)

- Wrap this function as a subagent named `woocommerce-finalizer`:
  - Inputs: `data_path`, `mapping_dir`, `output_es`, `output_en`, config flags.
  - Tools: use existing `read_file`, `write_file`, `ls`.
  - Trigger: invoked after `wine.json` is complete and validated.

### Acceptance Criteria

- On valid input, both CSVs are written with correct delimiters, stable columns, and canonical attribute values per language.
- `wpml:original_product_sku` links EN to ES.
- Primary grapes conform to shortlist; non-shortlist values collapse as specified.
- Tests (unit + E2E) pass against fixtures.
