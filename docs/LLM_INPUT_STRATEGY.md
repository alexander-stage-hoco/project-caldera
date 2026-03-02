# LLM Input Size Management Strategies

## Context

Caldera's LLM layer (NarrativeEnricher, BaseJudge, LLMSynthesisRule) has no input size management. Prompts are constructed by `json.dumps(data)` and sent raw. This document surveys approaches to handle large inputs, with recommendations specific to Caldera's structured-metrics use case.

## The Seven Approaches

### 1. Chunking

Split large inputs into fixed-size or semantically-bounded pieces.

| Variant | How it works | Best for |
|---------|-------------|----------|
| Fixed-size | Split at N tokens with overlap | Uniform text (docs, logs) |
| Recursive | Split at delimiters (`}`, `]`, `\n\n`), fall back to smaller delimiters | Structured data, code |
| Semantic | Embed sentences, split at similarity drops | Narrative text |
| Late chunking (Jina AI) | Embed full doc first, then chunk embeddings | Preserving long-range context |

**Recommended default:** 400-512 tokens, 10-20% overlap, recursive splitting.

**For structured JSON data:** Recursive chunking respecting delimiters works well. Semantic chunking adds little since structure is already explicit.

**Tradeoffs:** Simple to implement, but each chunk loses global context. Overlap helps but increases total tokens processed.

### 2. Map-Reduce / Hierarchical

Process chunks independently ("map"), then consolidate results ("reduce").

| Pattern | Parallel? | Cross-chunk context | LLM calls | Best for |
|---------|-----------|-------------------|-----------|----------|
| **Map-Reduce** | Yes | No | N+1 | Independent items (file-level metrics) |
| **Refine** | No | Yes (sequential) | N | Narrative continuity |
| **Tree-of-Summaries** | Partially | Pairwise | O(N log N) | Very large inputs, hierarchical data |

**Key insight:** Tree-Oriented MapReduce (EMNLP 2025) follows the document's inherent hierarchy rather than flat chunking — directly applicable to Caldera's file → directory → repo structure.

**Tradeoffs:** Higher latency and cost (multiple LLM calls). Map-Reduce loses cross-chunk relationships. Refine has sequential bottleneck.

### 3. Extract-then-Synthesize (Hybrid Deterministic + LLM)

Pre-extract key information deterministically, send only the distilled version to the LLM.

**Pattern:**
1. SQL/code computes all numbers (counts, averages, rankings, deltas)
2. Filter to top-N most significant findings
3. LLM receives only pre-computed aggregations for narrative interpretation

**Why this is strongest for structured analytical data:**
- LLMs are unreliable at arithmetic — let each tool do what it does best
- Pre-aggregation can compress data by 80%+ while preserving signal
- The LLM focuses purely on interpretation, not computation
- Deterministic steps are reproducible and testable

**Tradeoffs:** Requires upfront investment in aggregation logic. Risk of filtering out something the LLM would have found interesting.

### 4. RAG (Retrieval-Augmented Generation)

Index content, retrieve only relevant chunks per query.

**When it fits:** Query-specific retrieval from large knowledge bases (e.g., "what security issues affect module X?").

**When it doesn't fit:** Holistic summarization, trend analysis, overall metrics — you need the whole dataset, not a subset. **Not ideal for Caldera's reporting use case.**

**Tradeoffs:** Requires embedding infrastructure, retrieval quality directly limits output quality.

### 5. Prompt Compression

Compress context while preserving meaning.

| Technique | Compression | Quality loss | Risk for structured data |
|-----------|------------|-------------|------------------------|
| LLMLingua (Microsoft) | Up to 20x | <1.5% on reasoning | **High** — can break JSON structure |
| Deduplication/grouping | 2-5x | Near zero | **Low** — safe for structured data |
| Schema stripping | 1.5-3x | Near zero | **Low** — remove verbose keys |

**Safest for Caldera:** Deduplication ("N occurrences of pattern X" instead of N records) and schema stripping (compact JSON keys, remove null fields).

### 6. Token Budgeting

Allocate token budgets across prompt sections.

**Rules of thumb:**
- Reserve 25-50% of context window for output
- System prompt: 5-15%, context data: 40-60%, examples: 5-10%
- ACL 2025: including a budget hint in the prompt achieves 68% token reduction with <5% accuracy loss

**Tiered detail levels** (most to least compact):
1. Aggregate stats only (repo-level counts)
2. Category breakdowns (by tool, by severity)
3. Top-N items with details
4. Full detail

Use the most compact tier that fits the budget.

### 7. Iterative Refinement / Progressive Summarization

Build summaries bottom-up through the data hierarchy.

**Pattern for analytical data:**
```
file-level findings → directory-level summaries → repo-level synthesis
```

Each pass operates on progressively smaller, higher-signal data. Multi-pass processing (extract facts → identify patterns → generate narrative) produces higher quality than single-pass.

**Tradeoffs:** Multiple LLM calls increase latency and cost. Each compression step risks information loss.

## Anthropic-Specific Best Practices

From official Claude documentation:

1. **Document placement:** Long documents at the TOP of the prompt, instructions at the bottom (up to 30% quality improvement)
2. **XML tags:** Use consistent naming (`<document>`, `<metrics>`, `<evidence>`)
3. **Ground first:** Ask Claude to extract relevant quotes before reasoning
4. **Lost-in-the-middle effect:** U-shaped recall curve — put critical info at start or end, not middle
5. **Context awareness:** Claude 4.5/4.6 can track remaining context budget

## Recommendation for Caldera

Given that Caldera produces **structured metrics data** (JSON from 18 tools → DuckDB → dbt marts), the optimal strategy is **Extract-then-Synthesize (approach #3)** combined with **Token Budgeting (#6)**:

### Why this fits

- dbt marts **already pre-aggregate** file-level data into directory/repo summaries
- Run-over-run delta SQL **already computes** regressions deterministically
- The NarrativeEnricher callers **already select** bounded slices (top-3 insights, top-5 risks)
- The LLM is used **only for interpretation**, not computation — this is already the right pattern

### What's missing (the gaps to close)

1. **No input size guard** — add token estimation + truncation before LLM calls
2. **BaseJudge `collect_evidence()` is unbounded** — needs a size contract or truncation
3. **LLMSynthesisRule excerpts have no length cap** — needs per-excerpt truncation
4. **No tiered detail fallback** — if pre-aggregated data exceeds budget, no automatic compression
5. **No token counting** — only character lengths tracked; need at least char-based estimation (1 token ≈ 4 chars for English, ~3 chars for JSON)

### Staged implementation path

| Phase | What | Complexity |
|-------|------|-----------|
| **P0: Guard rails** | Add `max_prompt_chars` to LLMClient, truncate with warning | Low |
| **P1: Excerpt caps** | Cap `EvidenceItem.excerpt` at 500 chars, cap BaseJudge evidence serialization | Low |
| **P2: Token budgeting** | Per-section budgets in NarrativeEnricher, tiered detail levels | Medium |
| **P3: Hierarchical summarization** | Progressive file→dir→repo summarization for BaseJudge evidence | Medium-High |

P0+P1 close the immediate risk. P2+P3 are quality improvements for when repos grow large.

## Sources

- [Anthropic: Long Context Prompting Tips](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/long-context-tips)
- [Tree-Oriented MapReduce (EMNLP 2025)](https://aclanthology.org/2025.emnlp-main.899.pdf)
- [Token-Budget-Aware LLM Reasoning (ACL 2025)](https://aclanthology.org/2025.findings-acl.1274/)
- [LLMLingua - Microsoft Research](https://www.microsoft.com/en-us/research/blog/llmlingua-innovating-llm-efficiency-with-prompt-compression/)
- [Hierarchical Repository-Level Code Summarization](https://arxiv.org/html/2501.07857v1)
- [Meta-RAG on Large Codebases](https://arxiv.org/html/2508.02611v1)
- [Lost in the Middle (Stanford/UW)](https://arxiv.org/abs/2307.03172)
- [Best Chunking Strategies for RAG 2026 - Firecrawl](https://www.firecrawl.dev/blog/best-chunking-strategies-rag)
- [Context Window Management - Maxim AI](https://www.getmaxim.ai/articles/context-window-management-strategies-for-long-context-ai-agents-and-chatbots/)
