## CSV File Lifecycle and Metadata Flow

```mermaid
flowchart TD
  A[User uploads CSV<br/>via frontend] --> B[/api/files upload endpoint]
  B --> C[Save CSV to disk<br/>(filesystem path)]
  C --> D[add_csv_file<br/>in database.py]
  D --> E[INSERT row into<br/>SQLite csv_files table]
  E --> F[Return file id<br/>to API/frontend]

  subgraph Metadata Table [SQLite: csv_files]
    E
  end

  %% Listing and selection
  G[Sidebar / file list view] --> H[/api/files list endpoint]
  H --> I[get_all_files<br/>in database.py]
  I --> J[SELECT rows ordered by uploaded_at]
  J --> G

  G --> K[User toggles selection<br/>checkbox]
  K --> L[/api/files/{id}/selection]
  L --> M[update_file_selection<br/>in database.py]
  M --> N[UPDATE is_selected<br/>for given id]

  %% Deletion
  G --> O[User deletes file]
  O --> P[/api/files/{id} DELETE]
  P --> Q[delete_file<br/>in database.py]
  Q --> R[SELECT file_path<br/>for given id]
  R --> S{CSV exists on disk?}
  S -->|Yes| T[os.remove(file_path)]
  S -->|No| U[Skip file removal]
  T --> V[DELETE row from csv_files]
  U --> V

  style Metadata\ Table fill:#e3f2fd,stroke:#90caf9
  style A fill:#e8f5e9
  style B fill:#e8f5e9
  style C fill:#fff3e0
  style D fill:#fff3e0
  style E fill:#e3f2fd
  style F fill:#e8f5e9
  style G fill:#e8f5e9
  style H fill:#e8f5e9
  style I fill:#fff3e0
  style J fill:#e3f2fd
  style K fill:#e8f5e9
  style L fill:#e8f5e9
  style M fill:#fff3e0
  style N fill:#e3f2fd
  style O fill:#e8f5e9
  style P fill:#e8f5e9
  style Q fill:#fff3e0
  style R fill:#fff3e0
  style S fill:#f3e5f5
  style T fill:#ffe0b2
  style U fill:#ffe0b2
  style V fill:#e3f2fd
```

