flowchart TB

  subgraph Setup [1. Setup]
    DS[Select datasets]
    PR[Define analysis prompt]
    AT[Choose analysis type: qualitative or quantitative]
  end

  subgraph Design [2. Experiment design]
    MOD[Pick models to compare]
    CTX[Choose context given to LLM: none, light, or rich]
    REP[Set number of runs per configuration]
    VAR[Variants = models x context mode x runs]
  end

  subgraph Run [3. Execute]
    EX[For each variant, run EDA analysis]
    IN[LLM receives prompt plus optional dataset context]
    OUT[LLM returns analysis and generated code if quantitative]
  end

  subgraph Measure [4. Measure]
    LAT[Latency: time from request to response]
    QUAL[Quality: whether generated code runs successfully]
    OPT[Optional manual ratings for correctness and usefulness]
  end

  subgraph Results [5. Compare and export]
    AGG[Aggregate metrics by model and context]
    INSPECT[Inspect individual responses and code]
    CSV[Export runs to CSV for offline analysis]
  end

  Setup --> Design
  Design --> Run
  Run --> Measure
  Measure --> Results

  EX --> IN --> OUT

  %% Color classes with darker text
  classDef setup fill:#E3F2FD,stroke:#1E88E5,stroke-width:2px,color:#000;
  classDef design fill:#E8F5E9,stroke:#43A047,stroke-width:2px,color:#000;
  classDef run fill:#FFF3E0,stroke:#FB8C00,stroke-width:2px,color:#000;
  classDef measure fill:#F3E5F5,stroke:#8E24AA,stroke-width:2px,color:#000;
  classDef results fill:#E0F2F1,stroke:#00897B,stroke-width:2px,color:#000;

  class DS,PR,AT setup
  class MOD,CTX,REP,VAR design
  class EX,IN,OUT run
  class LAT,QUAL,OPT measure
  class AGG,INSPECT,CSV results