Here’s a tight, developer-centric brief you can hand to your teammate. It extracts the requirements from the chat + your attached files and tells them exactly what to export and how to format it.

WooCommerce CSV Export — Dev Brief

Goal

Produce two importable CSVs for WooCommerce (plugin: Product Import Export for WooCommerce – WebToffee):
	•	ES CSV = authoritative Spanish products to launch with (only wines you intend to sell).
	•	EN CSV = English mirror of the ES list, linked by SKU.

Both files must be semicolon-delimited (;) and use | to separate multi-value attributes.

⸻

Key rules (must-haves)
	•	No vintages anywhere (neither in columns nor in product names).
	•	Price uses dot decimals (e.g., 10.95).
	•	Stock updates happen via CSV using stock_status = instock | outofstock.
If a product is discontinued, it will be set to post_status = draft on request (they’ll handle redirects/SEO).
	•	SKU is the key (stable, unique per product).
	•	Two languages: ES and EN. The EN CSV must reference the ES product by wpml:original_product_sku (equal to the ES sku) and keep the same row order.
	•	Attributes used in filters must be normalized and constrained:
	•	pa_pais (Country) — ES & EN values.
	•	pa_tipo (Type/Color) — ES & EN values.
	•	pa_uva-principal (Primary grape) — ES & EN values; keep a short controlled list (≈15–16); everything else → “Otros varietales / Other varietals”.

⸻

Files you provided (parsed)
	•	example-import.xlsx → Reference of the final structure (89 columns). Notable columns present:
	•	post_title, post_content, post_excerpt, regular_price, stock_status, sku, images, tax:product_cat, tax:product_tag
	•	Attributes & configs:
	•	attribute:pa_como-servirlo (serving temp) — sample: 14º - 17ºC
	•	attribute:pa_enologo-bodega (winemaker/winery)
	•	attribute:pa_graduacion-alcoholica (ABV) — sample: 13,5% (normalize to dot or consistent format)
	•	attribute:pa_maridaje (pairing)
	•	attribute:pa_pais, attribute:pa_region, attribute:pa_tipo, attribute:pa_tipo-tapon
	•	attribute:pa_uva (blend details, free text, multi-value OK)
	•	attribute:pa_uva-principal (primary grapes, multi-value with |), e.g. Cabernet Sauvignon|Merlot|Syrah / Shiraz
	•	Matching attribute_data:* columns exist (e.g., 9|1|0 meaning position|visible|is_variation).
	•	Translation linking: wpml:original_product_sku present.
	•	Yoast: meta:_yoast_wpseo_title, meta:_yoast_wpseo_metadesc (can be left blank).
	•	Atributos.xlsx → Canonical attribute values (ES / EN) for:
	•	pa_pais (ES/EN pairs, e.g., Francia ↔ France)
	•	pa_tipo (ES/EN pairs: Tinto/Red, Blanco/White, Rosado/Rosé, Espumoso/Sparkling, Dulce/Sweet, Frizzante/Frizzante, Vermut/Vermouth)
	•	pa_uva-principal (ES/EN pairs; contains many; trim to shortlist)
	•	product_name-sku.csv → Current mapping (columns: post_title;sku) — 228 rows.

⸻

Columns to export

Minimum (ES file)
	•	sku (string, unique, stable)
	•	post_title (name)
	•	post_content (full description, concise)
	•	post_excerpt (short tasting note)
	•	regular_price (e.g., 10.95)
	•	stock_status (instock|outofstock)
	•	images (optional, comma-separated URLs accepted by WooCommerce)
	•	tax:product_cat / tax:product_tag (optional)
	•	Attributes:
	•	attribute:pa_pais (value from Atributos.xlsx ES column)
	•	attribute:pa_region (free text region)
	•	attribute:pa_tipo (from Atributos.xlsx ES)
	•	attribute:pa_uva (free text; multi values allowed but typically freeform)
	•	attribute:pa_uva-principal (controlled, multi-value |, from Atributos.xlsx ES)
	•	attribute:pa_enologo-bodega (winery/winemaker)
	•	attribute:pa_como-servirlo (e.g., 10–12 °C or 15º–18ºC, pick one style consistently)
	•	attribute:pa_graduacion-alcoholica (12% or 12.5%, pick one style consistently)
	•	attribute:pa_tipo-tapon (optional; e.g., Corcho / Screwcap)
	•	(Optional) Yoast:
	•	meta:_yoast_wpseo_title
	•	meta:_yoast_wpseo_metadesc
	•	If unsure, leave blank.

EN file mirrors ES but:
	•	sku = English product’s SKU (can be same as ES or a distinct EN SKU; whichever convention you lock in).
	•	wpml:original_product_sku = ES sku (this links ES↔EN).
	•	Attribute values use the EN column from Atributos.xlsx for pa_pais, pa_tipo, pa_uva-principal.

Attribute metadata (optional but recommended for consistent display)

For each attribute above, include the matching attribute_data:* with position|visible|is_variation. Suggested defaults:
	•	attribute_data:* = position|1|0
	•	Positions (example ordering):
1:pa_maridaje, 2:pa_region, 3:pa_enologo-bodega, 4:pa_graduacion-alcoholica, 5:pa_tipo-tapon, 6:pa_pais, 7:pa_tipo, 8:pa_uva-principal, 9:pa_como-servirlo, 10:pa_uva
	•	You can adjust; keep stable.

⸻

Transform rules (build into the export)
	1.	Delimiter: write CSV with ; as the field delimiter.
	2.	Multi-values:
	•	Convert internal lists (e.g., grapes) → | separated (no spaces around the pipe), e.g. Grenache|Syrah|Cinsault.
	3.	Taxonomies (normalized):
	•	Map pa_pais, pa_tipo, pa_uva-principal via Atributos.xlsx (ES/EN). Trim whitespace and exact-match canonical labels to avoid duplicate terms (watch trailing spaces).
	•	Keep pa_uva-principal limited to the agreed shortlist; map all other grapes → Otros varietales / Other varietals.
	4.	ABV: normalize to either 12% or 12.5% (pick one style globally; dot vs comma — use dot).
	5.	Serving temperature: normalize to 10–12 °C format (en dash, space, °C) or keep 15º–18ºC — pick one and apply everywhere.
	6.	Price: ensure dot decimals.
	7.	No vintages: drop any vintage fields & strip from strings.
	8.	Yoast: leave blank unless you’re injecting drafts.
	9.	Images: if provided, comma-separated absolute URLs.
	10.	Encoding: UTF-8, \n line breaks.

⸻

Update strategy (so it’s “any time, no hassle”)
	•	Idempotent merges by SKU:
	•	Full refresh: re-export complete ES/EN CSVs; import with “Update existing” enabled → upserts by sku.
	•	Quick stock update: export minimal CSV with sku;stock_status.
	•	Language link: keep wpml:original_product_sku = ES sku in the EN file on every export.
	•	No hard cutoff needed; you can re-run exports whenever.

⸻

Minimal sample rows (illustrative)

ES CSV (semicolon; pipes for multi)

sku;post_title;post_content;post_excerpt;regular_price;stock_status;attribute:pa_pais;attribute:pa_region;attribute:pa_tipo;attribute:pa_uva;attribute:pa_uva-principal;attribute:pa_enologo-bodega;attribute:pa_como-servirlo;attribute:pa_graduacion-alcoholica
v0123;Mas de Daumas Gassac Rouge;Tinto mediterráneo elegante...;Aromas de frutos rojos, especias...;29.90;instock;Francia;IGP Pays d'Hérault;Tinto;Cabernet Sauvignon 30%|Merlot 30%|Syrah 30%|Grenache 10%;Cabernet Sauvignon|Merlot|Syrah / Shiraz;Mas de Daumas Gassac;14º–17ºC;13.5%

EN CSV

sku;wpml:original_product_sku;post_title;post_content;post_excerpt;regular_price;stock_status;attribute:pa_pais;attribute:pa_region;attribute:pa_tipo;attribute:pa_uva;attribute:pa_uva-principal;attribute:pa_enologo-bodega;attribute:pa_como-servirlo;attribute:pa_graduacion-alcoholica
v0123-en;v0123;Mas de Daumas Gassac Red;Elegant Mediterranean red...;Red fruit, spice...;29.90;instock;France;IGP Pays d'Hérault;Red;Cabernet Sauvignon 30%|Merlot 30%|Syrah 30%|Grenache 10%;Cabernet Sauvignon|Merlot|Syrah / Shiraz;Mas de Daumas Gassac;14–17 °C;13.5%


⸻

QA checklist before import
	•	No vintages present anywhere.
	•	All rows have sku (unique).
	•	Prices parse with dot decimals.
	•	stock_status only instock/outofstock.
	•	Multi-value attributes use | (not commas).
	•	pa_pais, pa_tipo, pa_uva-principal match canonical values (ES or EN per file) from Atributos.xlsx.
	•	EN file has wpml:original_product_sku pointing to ES sku.
	•	Optional: include attribute_data:* with visible=1, is_variation=0, stable position.

⸻

Quick export pseudocode (Python, outline)

# Pseudocode: adapt to your DB models

ES, EN = [], []

for wine in db.wines.to_export():  # only wines to sell
    sku = wine.sku or generate_sku(wine)  # stable
    price = format_price(wine.price)      # "10.95"
    stock_status = "instock" if wine.in_stock else "outofstock"

    # Normalize attributes via Atributos.xlsx mappings
    pais_es, pais_en = map_country(wine.country)              # canonical ES/EN
    tipo_es, tipo_en = map_type(wine.type)                    # ES/EN
    prim_es, prim_en = map_primary_grapes(wine.primary_grapes)# canonical list; others -> "Otros varietales"/"Other varietals"

    # Multi-values with "|"
    blend_text = "|".join(clean_part(p) for p in wine.blend_parts)
    prim_es_str = "|".join(prim_es)
    prim_en_str = "|".join(prim_en)

    row_es = {
        "sku": sku,
        "post_title": wine.name_es,
        "post_content": concise(wine.desc_es),
        "post_excerpt": concise_tasting(wine.tasting_es),
        "regular_price": price,
        "stock_status": stock_status,
        "attribute:pa_pais": pais_es,
        "attribute:pa_region": wine.region_es,
        "attribute:pa_tipo": tipo_es,
        "attribute:pa_uva": blend_text,                      # freeform ok
        "attribute:pa_uva-principal": prim_es_str,           # controlled
        "attribute:pa_enologo-bodega": wine.winery_es,
        "attribute:pa_como-servirlo": normalize_temp(wine.serving_temp_es),
        "attribute:pa_graduacion-alcoholica": normalize_abv(wine.abv),
        # Optional Yoast keys -> ""
    }
    ES.append(row_es)

    row_en = {
        "sku": sku + "-en",                      # or same sku if that’s your convention
        "wpml:original_product_sku": sku,        # links to ES
        "post_title": wine.name_en,
        "post_content": concise(wine.desc_en),
        "post_excerpt": concise_tasting(wine.tasting_en),
        "regular_price": price,
        "stock_status": stock_status,
        "attribute:pa_pais": pais_en,
        "attribute:pa_region": wine.region_en,
        "attribute:pa_tipo": tipo_en,
        "attribute:pa_uva": blend_text,
        "attribute:pa_uva-principal": prim_en_str,
        "attribute:pa_enologo-bodega": wine.winery_en,
        "attribute:pa_como-servirlo": normalize_temp(wine.serving_temp_en),
        "attribute:pa_graduacion-alcoholica": normalize_abv(wine.abv),
    }
    EN.append(row_en)

write_csv("products_es.csv", ES, delimiter=";")
write_csv("products_en.csv", EN, delimiter=";")

Tip: For quick stock-only updates, export sku;stock_status and import with “Update existing” checked.

⸻

If you want, I can also generate a starter Python script wired to your DB schema that outputs both CSVs with the right delimiters and normalizations—just say the word.
