# EDA LLM Benchmark — Methodology (flowchart)

High-level methodology for benchmarking the EDA LLM tool: what we vary, what we measure, and how we use the results.

```mermaid
flowchart TB
  subgraph Setup["1. Setup"]
    DS[Select datasets]
    PR[Define analysis prompt]
    AT[Choose analysis type: qualitative or quantitative]
  end

  subgraph Design["2. Experiment design"]
    MOD[Pick models to compare]
    CTX[Choose context given to LLM: none, light, or rich]
    REP[Set number of runs per configuration]
    VAR[Variants = models × context mode × runs]
  end

  subgraph Run["3. Execute"]
    EX[For each variant, run EDA analysis]
    EX --> IN[LLM receives prompt + optional dataset context]
    IN --> OUT[LLM returns analysis and, if quantitative, generated code]
  end

  subgraph Measure["4. Measure"]
    LAT[Latency: time from request to response]
    QUAL[Quality: for quantitative, whether generated code runs successfully]
    OPT[Optional: manual ratings for correctness and usefulness]
  end

  subgraph Results["5. Compare & export"]
    AGG[Aggregate by model and context: avg latency, code success rate]
    INSPECT[Inspect individual responses and code]
    CSV[Export runs to CSV for offline analysis]
  end

  Setup --> Design
  Design --> Run
  Run --> Measure
  Measure --> Results
```

See **benchmark-page-flow.md** for a short narrative.
