# Extra Datasets for Evaluation

This document contains additional test cases for the wine research system evaluations, expanding the total number of cases to enhance test coverage and robustness.

## 1. Wine Research Cases (20 new cases)

Here are 20 additional wine research cases, covering a wider range of scenarios including rare grape varieties, specific vineyard designations, and less common wine regions.

```yaml
# albarino_2022.yaml - Galician white wine
wine_query: "Do Ferreiro Albariño 2022"
inventory_name: "Do Ferreiro Albariño"
inventory_vintage: "2022"
normalized_name: "Do Ferreiro Albariño 2022"
producer: "Do Ferreiro"
region: "Rías Baixas"
appellation: "DO Rías Baixas"
vintage: "2022"
grapes: "Albariño 100%"
corrections: {}
notes: "Classic Albariño from a top producer in Galicia, Spain."
metadata:
  source: "internal_knowledge"
  category: "tech_facts"
  issue_type: "standard_case"
```

```yaml
# chateneves_2020.yaml - Burgundy classification
wine_query: "Domaine Ramonet Chassagne-Montrachet 1er Cru Les Ruchottes 2020"
inventory_name: "Ramonet Chassagne 1er Cru Ruchottes"
inventory_vintage: "2020"
normalized_name: "Domaine Ramonet Chassagne-Montrachet 1er Cru Les Ruchottes 2020"
producer: "Domaine Ramonet"
region: "Burgundy"
appellation: "Chassagne-Montrachet 1er Cru"
vintage: "2020"
grapes: "Chardonnay 100%"
corrections: {}
notes: "High-end white Burgundy with specific Premier Cru vineyard."
metadata:
  source: "internal_knowledge"
  category: "tech_facts"
  issue_type: "bordeaux_classification_equivalent"
```

```yaml
# priorat_2019.yaml - Spanish red blend
wine_query: "Clos Mogador 2019"
inventory_name: "Clos Mogador"
inventory_vintage: "2019"
normalized_name: "Clos Mogador 2019"
producer: "Clos Mogador"
region: "Priorat"
appellation: "DOCa Priorat"
vintage: "2019"
grapes: "Garnacha, Cariñena, Syrah, Cabernet Sauvignon"
corrections: {}
notes: "Iconic wine from Priorat, known for its powerful and complex blends."
metadata:
  source: "internal_knowledge"
  category: "tech_facts"
  issue_type: "complex_blend"
```

```yaml
# riesling_gg_2021.yaml - German Grand Cru
wine_query: "Keller G-Max Riesling Trocken 2021"
inventory_name: "Keller G-Max"
inventory_vintage: "2021"
normalized_name: "Keller G-Max Riesling Trocken 2021"
producer: "Weingut Keller"
region: "Rheinhessen"
appellation: "VDP.Grosses Gewächs"
vintage: "2021"
grapes: "Riesling 100%"
corrections: {}
notes: "One of Germany's most sought-after dry Rieslings. G-Max is a special cuvée, not a specific vineyard."
metadata:
  source: "internal_knowledge"
  category: "tech_facts"
  issue_type: "vineyard_designation"
```

```yaml
# orange_wine_georgia_2020.yaml - Qvevri wine
wine_query: "Pheasant's Tears Rkatsiteli 2020"
inventory_name: "Pheasant's Tears Rkatsiteli"
inventory_vintage: "2020"
normalized_name: "Pheasant's Tears Rkatsiteli 2020"
producer: "Pheasant's Tears"
region: "Kakheti"
appellation: ""
vintage: "2020"
grapes: "Rkatsiteli 100%"
corrections: {}
notes: "Traditional Georgian orange wine fermented in qvevri (clay amphorae)."
metadata:
  source: "internal_knowledge"
  category: "tech_facts"
  issue_type: "unconventional_wine"
```

```yaml
# napa_cab_2018.yaml - High-end Napa Cabernet
wine_query: "Screaming Eagle Cabernet Sauvignon 2018"
inventory_name: "Screaming Eagle"
inventory_vintage: "2018"
normalized_name: "Screaming Eagle Cabernet Sauvignon 2018"
producer: "Screaming Eagle"
region: "Napa Valley"
appellation: "Oakville"
vintage: "2018"
grapes: "Cabernet Sauvignon, Merlot, Cabernet Franc"
corrections: {}
notes: "Cult classic Napa Cabernet Sauvignon, very expensive and rare."
metadata:
  source: "internal_knowledge"
  category: "tech_facts"
  issue_type: "cult_wine"
```

```yaml
# loire_chenin_2019.yaml - Biodynamic wine
wine_query: "Nicolas Joly Coulée de Serrant 2019"
inventory_name: "Coulée de Serrant"
inventory_vintage: "2019"
normalized_name: "Nicolas Joly Coulée de Serrant 2019"
producer: "Nicolas Joly"
region: "Loire Valley"
appellation: "Savennières-Coulée de Serrant"
vintage: "2019"
grapes: "Chenin Blanc 100%"
corrections: {}
notes: "A benchmark for biodynamic winemaking from its own appellation."
metadata:
  source: "internal_knowledge"
  category: "tech_facts"
  issue_type: "biodynamic"
```

```yaml
# aussie_shiraz_2017.yaml - Australian icon
wine_query: "Penfolds Grange 2017"
inventory_name: "Penfolds Grange"
inventory_vintage: "2017"
normalized_name: "Penfolds Grange 2017"
producer: "Penfolds"
region: "South Australia"
appellation: ""
vintage: "2017"
grapes: "Shiraz, Cabernet Sauvignon"
corrections: {}
notes: "Australia's most famous wine, a multi-vineyard, multi-regional blend."
metadata:
  source: "internal_knowledge"
  category: "tech_facts"
  issue_type: "icon_wine"
```

```yaml
# oregon_pinot_2019.yaml - Willamette Valley Pinot Noir
wine_query: "Domaine Drouhin Oregon Pinot Noir Laurène 2019"
inventory_name: "DDO Laurène"
inventory_vintage: "2019"
normalized_name: "Domaine Drouhin Oregon Pinot Noir Laurène 2019"
producer: "Domaine Drouhin Oregon"
region: "Willamette Valley"
appellation: "Dundee Hills"
vintage: "2019"
grapes: "Pinot Noir 100%"
corrections: {}
notes: "High-quality Pinot Noir from a respected producer in Oregon."
metadata:
  source: "internal_knowledge"
  category: "tech_facts"
  issue_type: "new_world_pinot"
```

```yaml
# vintage_port_2017.yaml - Fortified wine
wine_query: "Taylor Fladgate Vintage Port 2017"
inventory_name: "Taylor's Vintage Port"
inventory_vintage: "2017"
normalized_name: "Taylor Fladgate Vintage Port 2017"
producer: "Taylor Fladgate"
region: "Douro"
appellation: "Porto"
vintage: "2017"
grapes: "Touriga Nacional, Touriga Franca, Tinta Roriz, etc."
corrections: {}
notes: "A classic vintage port from a top house. Made from a blend of traditional Portuguese grapes."
metadata:
  source: "internal_knowledge"
  category: "tech_facts"
  issue_type: "fortified_wine"
```

```yaml
# nerello_mascalese_2020.yaml - Etna Rosso
wine_query: "Tenuta delle Terre Nere Etna Rosso Calderara Sottana 2020"
inventory_name: "Terre Nere Calderara Sottana"
inventory_vintage: "2020"
normalized_name: "Tenuta delle Terre Nere Etna Rosso Calderara Sottana 2020"
producer: "Tenuta delle Terre Nere"
region: "Sicily"
appellation: "Etna DOC"
vintage: "2020"
grapes: "Nerello Mascalese, Nerello Cappuccio"
corrections: {}
notes: "Volcanic wine from Mount Etna, often compared to Burgundy."
metadata:
  source: "internal_knowledge"
  category: "tech_facts"
  issue_type: "volcanic_wine"
```

```yaml
# carmenere_2018.yaml - Chilean specialty
wine_query: "Montes Purple Angel 2018"
inventory_name: "Montes Purple Angel"
inventory_vintage: "2018"
normalized_name: "Montes Purple Angel 2018"
producer: "Montes"
region: "Colchagua Valley"
appellation: ""
vintage: "2018"
grapes: "Carménère 92%, Petit Verdot 8%"
corrections: {}
notes: "A benchmark for high-quality Carménère from Chile."
metadata:
  source: "internal_knowledge"
  category: "tech_facts"
  issue_type: "signature_grape"
```

```yaml
# tokaji_2013.yaml - Hungarian dessert wine
wine_query: "Royal Tokaji 5 Puttonyos Aszú 2013"
inventory_name: "Royal Tokaji 5 Putt"
inventory_vintage: "2013"
normalized_name: "Royal Tokaji 5 Puttonyos Aszú 2013"
producer: "Royal Tokaji"
region: "Tokaj"
appellation: ""
vintage: "2013"
grapes: "Furmint, Hárslevelű"
corrections: {}
notes: "Famous Hungarian sweet wine, with sweetness level indicated by 'Puttonyos'."
metadata:
  source: "internal_knowledge"
  category: "tech_facts"
  issue_type: "dessert_wine"
```

```yaml
# malbec_2018.yaml - Argentinian Malbec
wine_query: "Catena Zapata Malbec Argentino 2018"
inventory_name: "Catena Zapata Malbec Argentino"
inventory_vintage: "2018"
normalized_name: "Catena Zapata Malbec Argentino 2018"
producer: "Catena Zapata"
region: "Mendoza"
appellation: ""
vintage: "2018"
grapes: "Malbec 100%"
corrections: {}
notes: "Iconic Malbec from one of Argentina's most renowned producers."
metadata:
  source: "internal_knowledge"
  category: "tech_facts"
  issue_type: "standard_case"
```

```yaml
# santorini_assyrtiko_2021.yaml - Greek white wine
wine_query: "Domaine Sigalas Assyrtiko 2021"
inventory_name: "Sigalas Assyrtiko"
inventory_vintage: "2021"
normalized_name: "Domaine Sigalas Assyrtiko 2021"
producer: "Domaine Sigalas"
region: "Santorini"
appellation: "PDO Santorini"
vintage: "2021"
grapes: "Assyrtiko 100%"
corrections: {}
notes: "Crisp, mineral-driven white wine from the volcanic island of Santorini."
metadata:
  source: "internal_knowledge"
  category: "tech_facts"
  issue_type: "volcanic_wine"
```

```yaml
# barolo_2016.yaml - Italian classic
wine_query: "Giacomo Conterno Barolo Riserva Monfortino 2016"
inventory_name: "Conterno Monfortino"
inventory_vintage: "2016"
normalized_name: "Giacomo Conterno Barolo Riserva Monfortino 2016"
producer: "Giacomo Conterno"
region: "Piedmont"
appellation: "Barolo DOCG"
vintage: "2016"
grapes: "Nebbiolo 100%"
corrections: {}
notes: "Legendary Barolo, only produced in exceptional vintages."
metadata:
  source: "internal_knowledge"
  category: "tech_facts"
  issue_type: "icon_wine"
```

```yaml
# bordeaux_right_bank_2015.yaml - Pomerol
wine_query: "Château Pétrus 2015"
inventory_name: "Pétrus"
inventory_vintage: "2015"
normalized_name: "Château Pétrus 2015"
producer: "Château Pétrus"
region: "Bordeaux"
appellation: "Pomerol"
vintage: "2015"
grapes: "Merlot 100%"
corrections: {}
notes: "One of the world's most famous and expensive wines, from the right bank of Bordeaux."
metadata:
  source: "internal_knowledge"
  category: "tech_facts"
  issue_type: "cult_wine"
```

```yaml
# sauternes_2001.yaml - Bordeaux sweet wine
wine_query: "Château d'Yquem 2001"
inventory_name: "Yquem"
inventory_vintage: "2001"
normalized_name: "Château d'Yquem 2001"
producer: "Château d'Yquem"
region: "Bordeaux"
appellation: "Sauternes"
vintage: "2001"
grapes: "Sémillon, Sauvignon Blanc"
corrections: {}
notes: "The most famous sweet wine in the world, from a legendary vintage."
metadata:
  source: "internal_knowledge"
  category: "tech_facts"
  issue_type: "dessert_wine"
```

```yaml
# new_zealand_sb_2022.yaml - Sauvignon Blanc
wine_query: "Cloudy Bay Sauvignon Blanc 2022"
inventory_name: "Cloudy Bay SB"
inventory_vintage: "2022"
normalized_name: "Cloudy Bay Sauvignon Blanc 2022"
producer: "Cloudy Bay"
region: "Marlborough"
appellation: ""
vintage: "2022"
grapes: "Sauvignon Blanc 100%"
corrections: {}
notes: "The wine that put New Zealand on the map for Sauvignon Blanc."
metadata:
  source: "internal_knowledge"
  category: "tech_facts"
  issue_type: "standard_case"
```

```yaml
# zinfandel_2019.yaml - California Zinfandel
wine_query: "Ridge Geyserville 2019"
inventory_name: "Ridge Geyserville"
inventory_vintage: "2019"
normalized_name: "Ridge Geyserville 2019"
producer: "Ridge Vineyards"
region: "Sonoma County"
appellation: "Alexander Valley"
vintage: "2019"
grapes: "Zinfandel, Carignane, Petite Sirah, Alicante Bouschet"
corrections: {}
notes: "A classic California field blend, labeled as Zinfandel."
metadata:
  source: "internal_knowledge"
  category: "tech_facts"
  issue_type: "complex_blend"
```

## 2. Ambiguity & Validation Evaluation Datasets

### Disambiguation Cases (20 new cases for each category)

#### One Exact

```yaml
# Specific producer, wine, and vintage
- query: "Château Margaux 1982"
  expected_outcome: "one_exact"
  gold_name: "Château Margaux 1982"
  notes: "Iconic first growth Bordeaux from a legendary vintage."
- query: "Egon Müller Scharzhofberger Riesling Trockenbeerenauslese 2003"
  expected_outcome: "one_exact"
  gold_name: "Egon Müller Scharzhofberger Riesling Trockenbeerenauslese 2003"
  notes: "Extremely specific German dessert wine."
- query: "Domaine de la Romanée-Conti La Tâche 2015"
  expected_outcome: "one_exact"
  gold_name: "Domaine de la Romanée-Conti La Tâche 2015"
  notes: "Specific vineyard monopoly from a top Burgundy producer."
- query: "Vega Sicilia Único 1995"
  expected_outcome: "one_exact"
  gold_name: "Vega Sicilia Único 1995"
  notes: "Spain's most famous wine from a specific vintage."
- query: "Krug Clos du Mesnil 2008"
  expected_outcome: "one_exact"
  gold_name: "Krug Clos du Mesnil 2008"
  notes: "Single vineyard, single grape, single vintage Champagne."
- query: "Gaja Barbaresco 2017"
  expected_outcome: "one_exact"
  gold_name: "Gaja Barbaresco 2017"
  notes: "Well-known producer, wine, and vintage from Piedmont."
- query: "Caymus Special Selection Cabernet Sauvignon 2018"
  expected_outcome: "one_exact"
  gold_name: "Caymus Special Selection Cabernet Sauvignon 2018"
  notes: "Popular high-end Napa Cabernet with a specific designation."
- query: "Opus One 2016"
  expected_outcome: "one_exact"
  gold_name: "Opus One 2016"
  notes: "Napa Valley icon with a specific vintage."
- query: "Château Musar 1999"
  expected_outcome: "one_exact"
  gold_name: "Château Musar 1999"
  notes: "Cult wine from Lebanon with a specific vintage."
- query: "Cloudy Bay Te Koko 2019"
  expected_outcome: "one_exact"
  gold_name: "Cloudy Bay Te Koko 2019"
  notes: "Specific barrel-fermented Sauvignon Blanc from a well-known producer."
- query: "Biondi Santi Brunello di Montalcino Riserva 2012"
  expected_outcome: "one_exact"
  gold_name: "Biondi Santi Brunello di Montalcino Riserva 2012"
  notes: "Iconic Brunello from a historic producer, riserva designation."
- query: "Henschke Hill of Grace 2015"
  expected_outcome: "one_exact"
  gold_name: "Henschke Hill of Grace 2015"
  notes: "Single vineyard Australian Shiraz from a top vintage."
- query: "Weingut Knoll Grüner Veltliner Smaragd Vinothekfüllung 2019"
  expected_outcome: "one_exact"
  gold_name: "Weingut Knoll Grüner Veltliner Smaragd Vinothekfüllung 2019"
  notes: "Top-tier Austrian Grüner Veltliner with specific classification and bottling."
- query: "Masseto 2016"
  expected_outcome: "one_exact"
  gold_name: "Masseto 2016"
  notes: "Iconic single-vineyard Merlot from Tuscany."
- query: "Château Rayas Châteauneuf-du-Pape Réserve 2007"
  expected_outcome: "one_exact"
  gold_name: "Château Rayas Châteauneuf-du-Pape Réserve 2007"
  notes: "Legendary and rare Châteauneuf-du-Pape."
- query: "Alvaro Palacios L'Ermita 2018"
  expected_outcome: "one_exact"
  gold_name: "Alvaro Palacios L'Ermita 2018"
  notes: "Cult wine from Priorat, specific vineyard and vintage."
- query: "Soldera Case Basse Brunello di Montalcino 2010"
  expected_outcome: "one_exact"
  gold_name: "Soldera Case Basse Brunello di Montalcino 2010"
  notes: "Highly sought-after, cult Brunello."
- query: "Schrader Cellars CCS Beckstoffer To Kalon Vineyard Cabernet Sauvignon 2018"
  expected_outcome: "one_exact"
  gold_name: "Schrader Cellars CCS Beckstoffer To Kalon Vineyard Cabernet Sauvignon 2018"
  notes: "Extremely specific Napa Cabernet: producer, clone, vineyard, vintage."
- query: "Domaine Leroy Musigny Grand Cru 2009"
  expected_outcome: "one_exact"
  gold_name: "Domaine Leroy Musigny Grand Cru 2009"
  notes: "One of the most expensive and rare red Burgundies."
- query: "J.J. Prüm Wehlener Sonnenuhr Riesling Auslese Goldkapsel 2011"
  expected_outcome: "one_exact"
  gold_name: "J.J. Prüm Wehlener Sonnenuhr Riesling Auslese Goldkapsel 2011"
  notes: "Specific vineyard, ripeness level, and bottling (Goldkap) for a German Riesling."
```

#### Needs Clarification

```yaml
- query: "Red wine"
  expected_outcome: "needs_clarification"
  notes: "Extremely generic, could be any red wine."
- query: "Italian wine"
  expected_outcome: "needs_clarification"
  notes: "Too broad, Italy has thousands of wines."
- query: "A nice bottle for a gift"
  expected_outcome: "needs_clarification"
  notes: "Subjective and lacks any specific constraints."
- query: "Something from 2015"
  expected_outcome: "needs_clarification"
  notes: "Vintage alone is not enough to identify a wine."
- query: "Pinot"
  expected_outcome: "needs_clarification"
  notes: "Could be Pinot Noir, Pinot Grigio, Pinot Blanc, etc., from anywhere."
- query: "Bordeaux"
  expected_outcome: "needs_clarification"
  notes: "A huge region with thousands of producers."
- query: "Sparkling"
  expected_outcome: "needs_clarification"
  notes: "Could be Champagne, Prosecco, Cava, etc."
- query: "A bold red"
  expected_outcome: "needs_clarification"
  notes: "Style description is too subjective and broad."
- query: "Wine from Spain"
  expected_outcome: "needs_clarification"
  notes: "Country is too broad a filter."
- query: "Something that goes well with steak"
  expected_outcome: "needs_clarification"
  notes: "Food pairing is a preference, not a specific wine identifier."
- query: "An oaky Chardonnay"
  expected_outcome: "needs_clarification"
  notes: "A common style produced worldwide."
- query: "A dry Riesling"
  expected_outcome: "needs_clarification"
  notes: "Many producers make dry Riesling."
- query: "A wine that costs around $50"
  expected_outcome: "needs_clarification"
  notes: "Price is not a unique identifier."
- query: "Something with high tannins"
  expected_outcome: "needs_clarification"
  notes: "A characteristic shared by many grape varieties and wines."
- query: "A good value wine"
  expected_outcome: "needs_clarification"
  notes: "Value is subjective."
- query: "A wine from a famous producer"
  expected_outcome: "needs_clarification"
  notes: "Too many famous producers to narrow down."
- query: "A sweet dessert wine"
  expected_outcome: "needs_clarification"
  notes: "Could be Sauternes, Port, Tokaji, etc."
- query: "French red wine"
  expected_outcome: "needs_clarification"
  notes: "Extremely broad category."
- query: "A wine from a volcanic soil"
  expected_outcome: "needs_clarification"
  notes: "Many regions have volcanic soils (e.g., Etna, Santorini, Canary Islands)."
- query: "An organic wine"
  expected_outcome: "needs_clarification"
  notes: "Organic is a production method, not a specific wine."
```

#### Overcommit

```yaml
- query: "A 2018 Napa Cabernet that was harvested on a full moon and aged in barrels made from a specific tree in the Tronçais forest."
  expected_outcome: "overcommit"
  notes: "Harvest date details and specific barrel origins are usually not searchable."
- query: "Château Lafite Rothschild 1787 that was owned by Thomas Jefferson"
  expected_outcome: "overcommit"
  notes: "Provenance is not a searchable attribute for the wine's technical details."
- query: "A Pinot Noir from Burgundy that tastes like strawberries but not raspberries, with a hint of mushroom."
  expected_outcome: "overcommit"
  notes: "Highly subjective tasting notes are not reliable search criteria."
- query: "A vegan Chianti Classico from 2019 that was bottled on a Tuesday."
  expected_outcome: "overcommit"
  notes: "Bottling day of the week is not recorded or searchable."
- query: "A Spanish red wine with exactly 14.2% alcohol, served at my cousin's wedding last year."
  expected_outcome: "overcommit"
  notes: "Precise alcohol level and personal events are not searchable criteria."
- query: "A wine from the oldest vine in France."
  expected_outcome: "overcommit"
  notes: "While interesting, 'oldest vine' is not a standard search filter and is debatable."
- query: "A Sauvignon Blanc from Marlborough that has never been rated by a critic."
  expected_outcome: "overcommit"
  notes: "Absence of a rating is not a searchable attribute."
- query: "A Barolo that was fermented in stainless steel for exactly 12 days and then aged for 36 months in Slovenian oak."
  expected_outcome: "overcommit"
  notes: "Extremely specific winemaking details that are often not available or consistent."
- query: "The wine that was featured in the third episode of that one TV show about chefs."
  expected_outcome: "overcommit"
  notes: "Media appearances are not standard wine data."
- query: "A Champagne that has a pressure of exactly 6 atmospheres and was disgorged in my birth month."
  expected_outcome: "overcommit"
  notes: "Precise bottle pressure and personal disgorgement dates are not practical search terms."
- query: "A Riesling from Mosel with a residual sugar of 45 g/L but a pH of 3.0"
  expected_outcome: "overcommit"
  notes: "Extremely specific and conflicting technical data."
- query: "A Cabernet Sauvignon from Chile that is also a Pinot Noir from Oregon"
  expected_outcome: "overcommit"
  notes: "Contradictory grape and region information."
- query: "A red wine that is also white"
  expected_outcome: "overcommit"
  notes: "Mutually exclusive categories."
- query: "An unoaked Chardonnay from California that was aged in new French oak barrels"
  expected_outcome: "overcommit"
  notes: "Contradictory winemaking information."
- query: "A 2020 vintage wine that was bottled in 2019"
  expected_outcome: "overcommit"
  notes: "Impossible timeline."
- query: "A wine with no alcohol"
  expected_outcome: "overcommit"
  notes: "While non-alcoholic wines exist, the query is likely for a standard wine and this constraint is too restrictive."
- query: "A red Sancerre made from Chardonnay"
  expected_outcome: "overcommit"
  notes: "Red Sancerre is Pinot Noir; Chardonnay is not allowed for red."
- query: "A Brunello di Montalcino made in Piedmont"
  expected_outcome: "overcommit"
  notes: "Brunello is from Tuscany, not Piedmont."
- query: "A vintage Champagne from a non-vintage year"
  expected_outcome: "overcommit"
  notes: "A vintage is only declared in specific, good years."
- query: "A dry wine with 200 g/L of residual sugar"
  expected_outcome: "overcommit"
  notes: "Contradiction: 200 g/L is extremely sweet, not dry."
```

### Validation Cases (20 new cases for each category)

#### Should Pass

```yaml
- query: "Silver Oak Alexander Valley Cabernet Sauvignon 2017"
  expected_pass: true
  reason_code: "specific_wine_vintage"
  notes: "Well-known California Cabernet."
- query: "Whispering Angel Rosé 2022"
  expected_pass: true
  reason_code: "popular_wine"
  notes: "Extremely popular rosé from Provence."
- query: "What are the main grapes in Amarone?"
  expected_pass: true
  reason_code: "question_about_wine_style"
  notes: "A researchable question about a famous wine style."
- query: "Tell me about the 2010 vintage in Bordeaux."
  expected_pass: true
  reason_code: "question_about_vintage"
  notes: "A valid query about a specific vintage in a region."
- query: "Meiomi Pinot Noir"
  expected_pass: true
  reason_code: "popular_wine_no_vintage"
  notes: "A very popular, widely available non-vintage specific wine."
- query: "Grüner Veltliner from Austria"
  expected_pass: true
  reason_code: "grape_and_country"
  notes: "A common and valid request."
- query: "What is a good wine to pair with salmon?"
  expected_pass: true
  reason_code: "food_pairing_query"
  notes: "A common and answerable question."
- query: "Zinfandel from Lodi"
  expected_pass: true
  reason_code: "grape_and_region"
  notes: "Lodi is famous for Zinfandel."
- query: "Compare Chianti Classico and Brunello di Montalcino"
  expected_pass: true
  reason_code: "comparison_query"
  notes: "A valid request to compare two well-known wines."
- query: "What does 'sur lie' mean?"
  expected_pass: true
  reason_code: "winemaking_term_query"
  notes: "A query about a common winemaking term."
- query: "Rombauer Chardonnay"
  expected_pass: true
  reason_code: "popular_wine"
  notes: "A well-known California Chardonnay."
- query: "Cava from Spain"
  expected_pass: true
  reason_code: "style_and_country"
  notes: "A classic sparkling wine from Spain."
- query: "What is carbonic maceration?"
  expected_pass: true
  reason_code: "winemaking_term_query"
  notes: "A query about a specific winemaking technique."
- query: "Best red wines under $20"
  expected_pass: true
  reason_code: "price_based_query"
  notes: "A common, answerable query."
- query: "Tell me about the terroir of the Mosel valley"
  expected_pass: true
  reason_code: "terroir_query"
  notes: "A valid query about a specific wine region's characteristics."
- query: "La Crema Sonoma Coast Chardonnay"
  expected_pass: true
  reason_code: "specific_wine"
  notes: "A popular and specific wine."
- query: "What is the difference between Shiraz and Syrah?"
  expected_pass: true
  reason_code: "grape_comparison_query"
  notes: "A classic wine question."
- query: "Find me a dry rosé"
  expected_pass: true
  reason_code: "style_query"
  notes: "A common request for a wine style."
- query: "Natural wine from Jura"
  expected_pass: true
  reason_code: "style_and_region_query"
  notes: "Jura is known for its natural wines."
- query: "What is a Super Tuscan?"
  expected_pass: true
  reason_code: "wine_category_query"
  notes: "A valid query about a well-known category of wine."
```

#### Should Fail

```yaml
- query: "Wine made from apples and oranges"
  expected_pass: false
  reason_code: "not_grape_based"
  notes: "Wine is made from grapes; this is a fruit cider/wine query, not for this system."
- query: "A wine that can make me fly"
  expected_pass: false
  reason_code: "impossible_request"
  notes: "A nonsensical request with magical properties."
- query: "The best wine in the entire world"
  expected_pass: false
  reason_code: "subjective_unanswerable"
  notes: "Best is subjective and impossible to determine definitively."
- query: "A wine from the year 1200"
  expected_pass: false
  reason_code: "impossible_vintage"
  notes: "No wine from that year would exist today for consumption or data."
- query: "Chardonnay from Antarctica"
  expected_pass: false
  reason_code: "impossible_location"
  notes: "Grapes cannot be grown in Antarctica."
- query: "A wine with 100% alcohol content"
  expected_pass: false
  reason_code: "impossible_attribute"
  notes: "Ethanol is not wine."
- query: "What was Julius Caesar's favorite wine?"
  expected_pass: false
  reason_code: "unverifiable_historical_fact"
  notes: "Impossible to know or verify."
- query: "A wine that is blue in color"
  expected_pass: false
  reason_code: "impossible_attribute"
  notes: "Wine is not naturally blue."
- query: "Find me a wine that has no taste"
  expected_pass: false
  reason_code: "nonsensical_request"
  notes: "A contradictory and nonsensical query."
- query: "A wine made from the 'Unicorn' grape"
  expected_pass: false
  reason_code: "nonexistent_grape"
  notes: "This grape variety does not exist."
- query: "A wine that is both hot and cold at the same time"
  expected_pass: false
  reason_code: "impossible_physical_state"
  notes: "Violates laws of physics."
- query: "What is the secret ingredient in Coca-Cola?"
  expected_pass: false
  reason_code: "off_topic"
  notes: "Not related to wine."
- query: "A wine produced on the International Space Station"
  expected_pass: false
  reason_code: "impossible_location"
  notes: "No wine is commercially produced in space."
- query: "A wine that can predict the future"
  expected_pass: false
  reason_code: "impossible_request"
  notes: "Supernatural claims are not valid."
- query: "A wine with negative calories"
  expected_pass: false
  reason_code: "impossible_attribute"
  notes: "Alcohol has calories; this is impossible."
- query: "A wine that has been aged for 1,000 years"
  expected_pass: false
  reason_code: "impossible_vintage"
  notes: "No wine would survive this long in a drinkable state."
- query: "Can you sell me a bottle of Screaming Eagle?"
  expected_pass: false
  reason_code: "transactional_request"
  notes: "The agent is for research, not sales."
- query: "A wine that tastes like the color purple"
  expected_pass: false
  reason_code: "synesthesia_request"
  notes: "A subjective, synesthetic experience is not a searchable attribute."
- query: "A wine from the lost city of Atlantis"
  expected_pass: false
  reason_code: "fictional_location"
  notes: "Location is fictional."
- query: "asdfghjkl"
  expected_pass: false
  reason_code: "gibberish_query"
  notes: "The query is nonsensical and contains no valid terms."
```
