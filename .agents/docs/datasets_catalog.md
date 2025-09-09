# Datasets Catalog

This document catalogs all evaluation and test datasets used in the DeepAgents wine research system.

## Wine Research Evaluation Datasets

### 1. Wine Research Cases (`test_data/evals/wines/`)

**Description**: Real wine evaluation cases with ground truth data for testing wine research accuracy. Contains detailed wine information including normalized names, grape varieties, regions, and correction flags.

**Schema**:

- `wine_query`: Input query string
- `inventory_name`: Name as it appears in inventory
- `inventory_vintage`: Vintage from inventory
- `normalized_name`: Expected normalized wine name
- `producer`: Wine producer/winery
- `region`: Geographic region
- `appellation`: Wine appellation/classification
- `vintage`: Wine vintage year
- `grapes`: Grape varieties and percentages
- `corrections`: Validation flags and spelling corrections
- `notes`: Additional context and notes
- `metadata`: Source information and categorization

**Examples**:

```yaml
# Casa Sosegada 2022 - Grape variety correction case
wine_query: "Rafa Cambra Casa Sosegada"
inventory_name: "Rafa Cambra Casa Sosegada"
inventory_vintage: "2022"
normalized_name: "Rafa Cambra Casa Sosegada 2022"
grapes: "Monastrell 50% + indigenous varieties (Forcalla, Arco, Mando)"
notes: "95pt Parker wine. Main grape is Monastrell (~50%) plus indigenous varieties. Explicitly NOT Bobal - there is no Bobal in this region."
metadata:
  source: "mark_review_10aug.md"
  category: "tech_facts"
  issue_type: "wrong_grape_variety"
```

**Files**: 10 wine cases covering various scenarios:

- `casa_sosegada_2022.yaml` - Grape variety correction
- `clos_de_oratoire_2021.yaml` - Bordeaux classification
- `finca_calvestra_merseguera_2023.yaml` - Spanish white wine
- `laventura_viura_2022.yaml` - Rioja white
- `nivarius_finca_la_nevera_2018.yaml` - Premium Rioja
- `pepe_mendoza_giro.yaml` - Natural wine
- `rall_white.yaml` - South African white blend
- `tantum_ergo_rose_2022.yaml` - Rosé wine
- `umbretum_brut_nature.yaml` - Sparkling wine
- `veuve_ambal_rose.yaml` - Champagne rosé

## Ambiguity & Validation Evaluation Datasets

### 2. Disambiguation Cases (`test_data/evals/ambiguity_validation/disambiguation/`)

**Description**: Test cases for query disambiguation logic, categorizing wine queries into three outcomes: one_exact (specific enough), needs_clarification (too generic), or overcommit (too many/conflicting constraints).

**Schema**:

- `query`: Wine query string to disambiguate
- `expected_outcome`: Expected classification ("one_exact" | "needs_clarification" | "overcommit")
- `gold_name`: Expected normalized name (for one_exact cases)
- `notes`: Explanation of the expected outcome

**Examples**:

**One Exact** (4 cases):

```yaml
# Specific producer, wine, and vintage
query: "Domaine de la Romanee-Conti Montrachet 2018"
expected_outcome: "one_exact"
gold_name: "Domaine de la Romanee-Conti Montrachet 2018"
notes: "Specific producer, wine, and vintage - should find exactly one match"
```

**Needs Clarification** (4 cases):

```yaml
# Too generic
query: "Chardonnay"
expected_outcome: "needs_clarification"
notes: "Too generic - could be thousands of different wines"
```

**Overcommit** (4 cases):

```yaml
# Too many constraints
query: "Domaine de la Romanee-Conti Montrachet 2018 from the specific vineyard plot Les Chevaliers du Tastevin with malolactic fermentation completed in March"
expected_outcome: "overcommit"
notes: "Overly specific constraints that may not be searchable or verifiable"
```

### 3. Validation Cases (`test_data/evals/ambiguity_validation/validation/`)

**Description**: Test cases for query feasibility validation, determining whether a wine query is realistic and researchable.

**Schema**:

- `query`: Wine query string to validate
- `expected_pass`: Whether validation should pass (boolean)
- `reason_code`: Classification reason for the outcome
- `notes`: Explanation of the validation decision

**Examples**:

**Should Pass** (4 cases):

```yaml
# Realistic wine query
query: "Domaine de la Romanee-Conti Montrachet 2018"
expected_pass: true
reason_code: "specific_wine_vintage"
notes: "Well-known wine with specific vintage - validation should pass"
```

**Should Fail** (4 cases):

```yaml
# Impossible constraints
query: "Wine from the planet Mars vintage 3021"
expected_pass: false
reason_code: "impossible_location_vintage"
notes: "Impossible location and future vintage - validation should fail"
```

## Export & Reference Datasets

### 4. WooCommerce Export Mappings (`test_data/export/mappings/`)

**Description**: Reference data for normalizing wine attributes when exporting to WooCommerce format.

**Files**:

- `countries.csv`: Country name normalization mappings
- `primary_grapes.csv`: Grape variety standardization
- `types.csv`: Wine type classifications

**Example** (`countries.csv`):

```csv
input,normalized
France,France
España,Spain
Espagne,Spain
Deutschland,Germany
```

### 5. Export Format Example (`test_data/export/wine.json`)

**Description**: Example of properly formatted wine data for WooCommerce export, showing the expected JSON structure with all required fields.

**Schema**:

- `sku`: Product SKU
- `normalized_name`: Standardized wine name
- `producer`: Winery/producer name
- `region`: Geographic region
- `appellation`: Wine classification
- `vintage`: Year
- `grapes`: Array of grape objects with name and percentage
- `alcohol_content`: ABV percentage
- `serving_temp`: Recommended serving temperature
- `food_pairings`: Array of food pairing suggestions
- `tasting_notes`: Flavor and aroma descriptions
- `price`: Pricing information

**Example**:

```json
{
  "sku": "v0123",
  "normalized_name": "Mas de Daumas Gassac Rouge",
  "producer": "Mas de Daumas Gassac",
  "region": "IGP Pays d'Hérault",
  "appellation": "IGP",
  "vintage": 2019,
  "grapes": [
    {
      "name": "Cabernet Sauvignon",
      "percentage": 80
    }
  ],
  "alcohol_content": 14.5,
  "serving_temp": "16-18°C",
  "food_pairings": ["Red meat", "Aged cheese"],
  "tasting_notes": {
    "aroma": "Dark fruit, herbs",
    "palate": "Full-bodied, structured tannins"
  }
}
```

## Dataset Usage

### Evaluation Runners

- **Wine Research**: Use `run_offline_eval()` with `test_data/evals/wines/`
- **Ambiguity & Validation**: Use `run_ambiguity_validation_eval()` with `test_data/evals/ambiguity_validation/`

### Test Coverage

- **Total Cases**: 26 evaluation cases
  - 10 wine research cases
  - 12 disambiguation cases (4 each: one_exact, needs_clarification, overcommit)
  - 8 validation cases (4 pass, 4 fail)
- **Reference Data**: 3 mapping files + 1 export format example

### Quality Standards

- All datasets include comprehensive metadata and notes
- Balanced distribution across different scenarios
- Real-world examples based on actual wine data
- Deterministic evaluation for consistent testing
- 100% test coverage with acceptance criteria ≥0.9 accuracy
