https://chatgpt.com/c/68bea989-5fc0-8321-af59-567c4b53762e

You’re right to pause and design this carefully. Below is a deep, structured research + plan for putting evaluations (evals) into your wine agent so it becomes measurably more robust—at each step and across the whole sequence. I’ve also mapped concrete hook points into your codebase (from the repomix-output.xml you shared), and showed how to fold DSPy in as the optimization layer that turns your prompts into trainable programs with metrics as the objective.

⸻

0) Quick diagnosis of your current stack (from your repo)

Key files / where to hook evals:
	•	Agent orchestration: src/deepagents/graph.py (creates the agent; has post_model_hook, checkpointer), src/deepagents/sub_agent.py, src/deepagents/state.py (state schema), src/deepagents/interrupt.py (interrupt hooks for step control).
	•	Model boundary: src/deepagents/model.py (LLM adapters).
	•	Tools: src/deepagents/tools.py (file ops + todo tool), src/deepagents/qdrant/tools.py (RAG sync, Qdrant retrieval paths).
	•	Search providers: src/deepagents/search/base.py (common interface), jina_provider.py, tavily_provider.py.
	•	Wine examples: examples/research/wine_agent.py, wine_models.py.
	•	Existing tests: tests/search/*, tests/export/*, plus test_data/*.

These are ideal anchor points for unit/component/e2e evals without large refactors.

⸻

1) Capability map → what we must measure

For a Wine Agent, split user-facing abilities into measurable buckets:
	1.	Grounded fact Q&A (e.g., “What are Jacquère’s typical aromatics?” “Define ‘Crémant de Savoie’ rules.”)
	2.	Source-backed summaries (producer profiles, appellation summaries) with attribution.
	3.	Recommendation & pairing with constraints (budget, region, style), with rationale and sources.
	4.	Information extraction (structured fields from winery pages or PDFs).
	5.	Search + RAG navigation (finding and citing primary regulations or official databases).
	6.	Multi-step planning (decide which tool/route/sub-agent; recover from failures).
	7.	Safety/compliance (e.g., alcohol health disclaimers when relevant).

We’ll evaluate each and also the sequence as a whole.

⸻

2) Where to put evals in your pipeline (by layer)

Unit / tool level
	•	src/deepagents/search/base.py and providers (jina_provider.py, tavily_provider.py):
Evaluate retrieval quality per query (precision@k, recall@k, context-recall), and log normalized outputs.
	•	src/deepagents/qdrant/tools.py:
Evaluate indexing integrity, deduping, recall@k against labeled “relevant doc” sets, and latency per call.
	•	src/deepagents/tools.py (file ops / todos):
Simple correctness checks (state mutations, idempotency).

Component level
	•	Generator boundary (src/deepagents/model.py):
Score faithfulness-to-context, citation completeness, format adherence (for structured extraction) per LLM call.
	•	Planner / Sub-agent (src/deepagents/graph.py, sub_agent.py):
Score plan validity, tool-call correctness, action minimality (no unnecessary calls), recovery rate after injected failures.

End-to-end
	•	examples/research/wine_agent.py:
Score task success, source support, hallucination (FactScore-style), user-satisfaction proxy (LLM-as-judge with rubrics), latency/cost.

Tracing hooks (for all the above)
	•	Use OpenInference/Phoenix or LangSmith to capture traces + online/out-of-band evaluators; both support LangChain/LangGraph/DSPy instrumentations.  ￼ ￼

⸻

3) Metrics that matter (by layer) + credible frameworks

Retrieval (Search + Vector DB)
	•	Precision@k, Recall@k, MAP over labeled “relevant passages”; Context Precision/Recall for RAG. Tools like RAGAS offer these out-of-the-box (context precision/recall, utilization).  ￼ ￼
	•	Qdrant-focused best-practice guides discuss top‑k tuning and reranking impacts—use when optimizing retriever.  ￼

Generation (faithfulness & relevance)
	•	Faithfulness (is the answer supported by retrieved context?) using RAGAS or LlamaIndex evaluators.  ￼ ￼
	•	FActScore (decompose text into atomic facts; % supported by gold sources). Good for long-form summaries like appellation/producers.  ￼ ￼
	•	Hallucination detection sanity checks such as SelfCheckGPT (consistency across samples). Use as a signal, not a single gate.  ￼ ￼

Attribution / Citation
	•	Source coverage (all key claims have citations) and Attribution correctness (citations actually support the claim). Can be scored via custom LLM-as-judge rubrics + heuristics (URL overlap and quote matching). See reliability guidance on LLM-as-judge.  ￼

Recommendation & Pairing
	•	Constraint satisfaction (budget/style/region), diversity (no near-duplicates), justification quality (rubric-scored with LLM-as-judge). Pairwise win-rate A/B also works.  ￼

Extraction
	•	Schema accuracy (exact match on required fields), normalized ontology (regions/grapes mapped to canonical sets), strict JSON conformance.

Agentic (planning & tool use)
	•	Task success rate, tool-call success rate, action minimality, branch stability (# of backtracks), recovery from faults (inject 5xx/timeouts).
Agent literature (AgentBench/WebArena/GAIA) uses task success; we emulate that in your domain.  ￼

E2E product / operations
	•	Latency, cost/tokens, defect density (user-visible corrections), SLO attainment.

Frameworks to implement quickly
	•	RAGAS (RAG metrics), TruLens (feedback functions: groundedness, context relevance, answer relevance), LangSmith (offline + online evaluators & traces), Phoenix/OpenInference (vendor-neutral tracing + fast batched evals).  ￼ ￼ ￼ ￼

Why LLM‑as‑judge here? For open‑ended answers (explanations, recommendations), rubric‑based LLM‑as‑judge correlates well with humans when mitigations are used (position randomization, structured rubrics, CoT). Use it to triage; keep small human checkpoints for “gold” sets.  ￼

⸻

4) Wine‑specific ground‑truth sources (for gold evaluation sets)

Favor open/official sources to avoid licensing issues:
	•	VIVC (grape variety catalog; ampelography, synonyms): build Q&A/fact cards for varieties.  ￼
	•	EU eAmbrosia (legal GI register for wine traditional terms/PDO/PGI rules). Great for “what counts as X” regulatory questions.  ￼
	•	US TTB AVA (AVA definitions, official boundary descriptions; UC Davis GeoJSON set for spatial). Useful for AVA facts and extraction tasks.  ￼ ￼ ￼
	•	OIV (global statistics, yearbooks/pressers) for macro wine context tasks.  ￼
	•	Wikipedia for secondary support where licensing is acceptable (CC BY-SA; keep attribution).  ￼

Dataset tiers
	•	Gold: Human‑curated Q/A with exact supporting citations from the above (high‑importance regions/grapes, top PDO/PGI/AVA, core definitions).
	•	Silver: LLM‑generated then human‑verified pairs based on those sources.
	•	Bronze: LLM‑generated without human verification; use only for internal pretests, never for gating.

⸻

5) A minimal schema for your eval datasets

(A) Fact Q&A (RAG)

{
  "id": "q_000123",
  "task": "fact_qa",
  "question": "What grape varieties are permitted in Cr\u00e9mant de Savoie?",
  "expected_key_facts": [
    "Jacqu\u00e8re is permitted", "Altesse is permitted", "Chardonnay is permitted"
  ],
  "gold_sources": [
    {"url": "https://ec.europa.eu/agriculture/eambrosia/...", "support": "Annex X ..."},
    {"url": "https://en.wikipedia.org/wiki/Cr%C3%A9mant_de_Savoie"}
  ],
  "tags": ["Savoie","PDO","sparkling"]
}

(B) Attribution

{
  "id": "attr_045",
  "task": "attribution",
  "claim": "Riesling acreage in Germany declined in 2024 vs 2023.",
  "must_support_from": ["OIV 2024/2025 documents"],
  "gold_sources": [{"url": "https://www.oiv.int/..."}]
}

(C) Recommendation

{
  "id": "rec_210",
  "task": "pairing",
  "constraints": {"budget_eur_max": 25, "style": "high-acid white", "region_hint": "Savoie"},
  "success_criteria": [
    "constraints_met", "gives 2-3 options", "explains pairing rationale",
    "at least one source cited"
  ],
  "judge_rubric": "Score 1-5 for constraint satisfaction, 1-5 for rationale quality, 1-5 for citation relevance."
}

(D) Extraction

{
  "id": "ext_032",
  "task": "extract",
  "input_url": "https://ttb.gov/wine/ava-map-explorer#...Chartreuse",
  "expected": {
    "name": "Jongieux",
    "country": "France",
    "type": "PDO",
    "grapes": ["Jacqu\u00e8re","Altesse"],
    "source": "eAmbrosia"
  }
}


⸻

6) How to run the actual scoring (recommended libraries)
	•	RAGAS for context precision/recall, faithfulness, and answer relevancy; works cleanly with RAG pipelines.  ￼
	•	TruLens feedback functions for groundedness, context relevance, answer relevance; integrates with LangChain/LangGraph and supports vector DBs; includes dashboards.  ￼ ￼
	•	LangSmith to register target functions (your agent or a single LLM call), attach evaluators, and run offline suites plus online (production) evaluators over traces.  ￼
	•	Phoenix / OpenInference for standardized tracing across frameworks + fast batched evals at scale. Useful if you want a self‑hostable OSS path.  ￼ ￼
	•	Promptfoo for cheap, repeatable prompt/LLM A/B matrices, assertions, and CI checks.  ￼ ￼

⸻

7) Folding DSPy in (replacing brittle prompts with trainable modules)

Why DSPy here: You declare modules (Signatures) and let optimizers (formerly “teleprompters”) compile prompts/few-shot examples to maximize your metric. For your wine agent, your metric can be a weighted blend of: faithfulness (RAGAS), attribution coverage, judge score for rationale, and tool‑use success.  ￼
	•	Use MIPROv2 to jointly optimize instructions and few‑shot examples for your key modules (e.g., AnswerWithCitations, ExtractWineFacts, PlanNextStep). You supply a training set + metric, DSPy searches instructions/examples to improve your scores.  ￼
	•	DSPy plays nicely with RAG/agents and has growing instrumentation support via OpenInference.  ￼ ￼

Adoption path (incremental, low risk):
	1.	Wrap a single module boundary (e.g., Answer with citations) as a DSPy program; define a metric that combines RAGAS faithfulness + judge score.
	2.	Compile with MIPROv2 against your gold dev set → produce tuned prompts/examples.
	3.	Swap it into your create_deep_agent call (your graph.py already takes post_model_hook/checkpointer, so keep tracing intact).
	4.	Repeat per module (extraction, pairing), then consider planner optimization.

References / docs: DSPy site & GitHub; optimizer docs for MIPROv2.  ￼ ￼

⸻

8) A metric‑first iteration loop you can run continuously

Tier A — Offline (fast, repeatable)
	•	Unit tests on retriever and extractors (precision/recall@k; exact‑match schema).
	•	Component tests on generator (faithfulness, attribution, JSON schema validity).
	•	E2E tests per task template (success, judge score, latency/cost).

Tier B — Online shadow evals
	•	Run LLM‑as‑judge over a 1–5% sample of production traces with position randomization and pairwise comparisons to last stable build. Track win‑rate, informed by MT‑Bench/Arena insights on judge reliability.  ￼

Tier C — Gates
	•	Only promote a change if:
	•	Retrieval recall@k ↑ or equal;
	•	Faithfulness ↑; attribution coverage ≥ threshold;
	•	Task success ↑; latency/cost within SLOs;
	•	Safety checks pass.

⸻

9) Concrete eval suites to start with (small but high leverage)
	1.	“Appellation facts” (gold): 120 Q&A from eAmbrosia (definitions/terms/rules) → Evaluate faithfulness, citation correctness, and key fact coverage.  ￼
	2.	“Grape variety cards” (gold): 120 Q&A from VIVC → Evaluate factuality & synonym handling; penalize unsupported synonyms.  ￼
	3.	“AVA quick facts” (gold): 60 Q&A from TTB AVA and UC Davis GeoJSON→ Evaluate extraction + location fields.  ￼ ￼
	4.	“Pairing under constraints” (silver): 80 prompts with rubric judge scoring (constraint satisfaction, rationale, diversity).
	5.	“Long-form producer/appellation summaries” (silver): 50 prompts—score with FActScore, attribution, and judge rubric.  ￼

⸻

10) Instrumentation plan mapped to your files
	•	Tracing (all calls): add OpenInference/LangSmith spans in src/deepagents/model.py, search/*, qdrant/tools.py, and at the agent root (graph.py), so every step has inputs/outputs + timing.  ￼ ￼
	•	Retriever eval hook: in search/base.py provider search() return, record retrieved URLs/ids; in tests, compute precision/recall@k vs labeled sets. (Keep an evals/retrieval/ fixture with <query, relevant_urls[]>.)
	•	Qdrant eval: in qdrant/tools.py after sync/query, log top‑k ids/scores; test suite checks recall@k on canned collections. Qdrant’s RAG eval guides are useful references.  ￼
	•	Generator eval: in graph.py post_model_hook, run faithfulness (RAGAS/LlamaIndex), attribution coverage (heuristic + judge), JSON schema checks (when structured).  ￼ ￼
	•	Planner eval: wrap create_react_agent (already used in graph.py) with counters: tool_success_rate, backtracks, invalid tool calls, recovery after injected failures (use interrupt.py).
	•	CI: add promptfoo job for quick regression matrices on hot paths (answers with citations; extraction).  ￼

⸻

11) LLM‑as‑judge: make it reliable, not vibes
	•	Use pairwise comparisons where possible; randomize answer order.
	•	Use structured rubrics (dimensions + definitions + 1–5 anchors).
	•	Ask the judge for explanations (improves stability) and enforce style‑agnostic scoring to reduce verbosity bias. Evidence shows high agreement with humans when mitigations are applied.  ￼
	•	Periodically calibrate: sample 5–10% to humans; track judge‑human agreement.

You can implement judge flows in TruLens or LangSmith; Phoenix also has high‑throughput evals.  ￼ ￼ ￼

⸻

12) How DSPy uses the metrics to self‑improve your modules
	•	Define a composite metric function in Python that:
	•	calls RAGAS faithfulness,
	•	checks attribution coverage,
	•	includes judge score,
	•	(optionally) adds cost/latency penalty.
	•	Run MIPROv2 on your DSPy module(s) over your gold dev set to search improved instructions and exemplars; keep a holdout for honest evaluation.  ￼

This replaces hand‑tuned prompts with compiled, measured programs—exactly what you want for stability.  ￼

⸻

13) Example rubrics (concise, actionable)

Attribution rubric (1–5):
1 = No citations or irrelevant;
3 = Some claims supported but notable gaps;
5 = All key claims supported by correct, authoritative sources; citations placed near claims.

Faithfulness rubric (1–5):
1 = Contradicts provided context;
3 = Mostly aligned, minor unsupported claims;
5 = Fully grounded, no extra-factual claims.

Recommendation rubric (1–5 × 3 dims):
	•	Constraint satisfaction,
	•	Rationale clarity,
	•	Diversity (distinct options).
Total score = average.

⸻

14) First pass of North‑Star metrics (to baseline + track)
	•	E2E success rate on gold tasks (≥ X%).
	•	Faithfulness ≥ Y%, Attribution coverage ≥ Z%.
	•	Retriever recall@k ≥ R% on gold retrieval set.
	•	Pairwise win‑rate vs last stable ≥ W%.
	•	P50 latency and cost/token SLOs.

⸻

15) Risks & mitigations
	•	Judge bias / drift → use pairwise, order randomization, explanations; periodic human calibration.  ￼
	•	Licensing → stick to VIVC, eAmbrosia, TTB, OIV, Wikipedia for gold sets; store full citations and license notes.  ￼ ￼ ￼ ￼
	•	Data leakage → keep train/dev/test splits; never train on test.
	•	Overfitting to judge → rotate judges and keep human spot‑checks.

⸻

16) What to actually create (no execution yet—just the plan)

Repo structure to add:

/evals/
  datasets/
    wine_fact_qa_gold.jsonl
    wine_attribution_gold.jsonl
    wine_pairing_silver.jsonl
    wine_extraction_gold.jsonl
  rubrics/
    attribution.yaml
    faithfulness.yaml
    recommendation.yaml
  suites/
    retrieval.json
    generation.json
    e2e.json
  runners/
    ragas_runner.py
    trulens_runner.py
    judge_runner.py

Checklists:
	•	Connect tracing (Phoenix or LangSmith) at model, search, qdrant, and agent root.  ￼ ￼
	•	Build 40–60 gold Q/A from eAmbrosia and VIVC (balanced by region/grape).  ￼ ￼
	•	Create retrieval labels (query → relevant URLs) to measure precision/recall.
	•	Implement post_model_hook that runs faithfulness + attribution checks.
	•	Add promptfoo matrix for smoke A/B across 5–10 prompts/models (answers-with-citations).  ￼
	•	Wrap AnswerWithCitations as a DSPy program; compile with MIPROv2 on the gold dev set.  ￼

⸻

17) References you can lean on
	•	DSPy overview & optimizers (MIPROv2) – declarative, metric‑driven optimization of prompts/modules.  ￼
	•	RAG evaluation metrics (RAGAS), context precision/recall, faithfulness.  ￼
	•	TruLens feedback functions (groundedness, context relevance) + integrations.  ￼ ￼
	•	LangSmith evaluation/tracing guides (offline & online).  ￼
	•	Phoenix / OpenInference for unified tracing + high‑throughput evals.  ￼ ￼
	•	LLM‑as‑judge reliability (MT‑Bench / Arena).  ￼
	•	Hallucination: FActScore, SelfCheckGPT; RAGTruth dataset (methodology).  ￼
	•	Domain sources: VIVC, eAmbrosia, TTB AVA, OIV.  ￼ ￼ ￼ ￼

⸻

TL;DR (how to start, concretely)
	1.	Instrument tracing + minimal evaluators at the model boundary (post_model_hook) and retriever (providers + qdrant tools).
	2.	Assemble 40–60 gold Q/A from eAmbrosia and VIVC with explicit citations; add a 20‑item attribution set.  ￼
	3.	Run RAGAS + a rubric judge on that gold set; record baseline.  ￼
	4.	Wrap one module in DSPy and compile with MIPROv2 to your metric; re‑run evals and compare.  ￼
	5.	Promote only if faithfulness/attribution/retrieval improve and latency/cost stay within SLOs; otherwise iterate.

If you’d like, I can draft the eval suite skeletons (JSONL and rubric YAML) and the metric function DSPy would optimize against—ready to drop into /evals/.
