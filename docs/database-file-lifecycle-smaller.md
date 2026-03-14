## CSV File Lifecycle and Metadata Flow Smaller

```flowchart LR

A["Upload CSV"] --> B["API upload"]
B --> C["Save file + store metadata"]
C --> D["Return file id"]

subgraph DB["SQLite: csv_files"]
C
F
H
end

%% List / Select
E["File list"] --> F["Read metadata"]
E --> G["Toggle selection"]
G --> H["Update is_selected"]

%% Delete
E --> I["Delete file"]
I --> J{"File on disk?"}
J -->|Yes| K["Remove file"]
J -->|No| L["Skip"]
K --> M["Delete metadata"]
L --> M

%% Colors
style A fill:#e8f5e9
style B fill:#e8f5e9
style D fill:#e8f5e9
style E fill:#e8f5e9
style G fill:#e8f5e9
style I fill:#e8f5e9

style C fill:#fff3e0
style F fill:#fff3e0
style H fill:#fff3e0

style J fill:#f3e5f5

style K fill:#ffe0b2
style L fill:#ffe0b2

style DB fill:#e3f2fd,stroke:#90caf9
```

