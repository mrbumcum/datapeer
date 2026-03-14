## Safe Code Execution Flow (`execute_safe_code`)

```mermaid
flowchart TD
  A[Generated Python Code\n+ DataFrames] --> B[Lowercase + Scan for\nDangerous Patterns]
  B -->|Contains restricted tokens\ne.g. __import__, eval, open| Z[Reject Code\nReturn Error]
  B -->|No restricted tokens| C[Compile Code\n(Syntax Check Only)]
  C -->|SyntaxError| Z2[Return Syntax Error\nwith Line + Message]
  C -->|OK| D[Prepare Restricted Environment]
  D --> E[Restricted Builtins\n(math, iterables, print...)]
  D --> F[Expose Pandas + Numpy\n(pd, np aliases)]
  D --> G[Inject DataFrames\nas Named Variables]
  E --> H[Exec Wrapped Code\n`_result = None` + user code]
  F --> H
  G --> H
  H -->|Exception| Z3[Restore stdout\nReturn Exec Error + Traceback]
  H -->|Success| I[Capture stdout\nand `_result`]
  I --> J[Truncate Very Long\nOutputs / Results]
  J --> K[If No Output:\nSummarize Available DataFrames]
  J --> L[If Output Exists:\nReturn Output + Success Flag]

  style B fill:#fff4e1
  style C fill:#fff4e1
  style D fill:#e3f2fd
  style E fill:#e3f2fd
  style F fill:#e3f2fd
  style G fill:#e3f2fd
  style H fill:#f3e5f5
  style I fill:#e8f5e9
  style J fill:#e8f5e9
  style K fill:#e8f5e9
  style L fill:#e8f5e9
  style Z fill:#ffebee
  style Z2 fill:#ffebee
  style Z3 fill:#ffebee
```

