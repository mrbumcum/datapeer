flowchart LR

  Layout --> Sidebar
  Layout --> ChatPanel

  ChatPanel --> ChatMessages
  ChatPanel --> ChatBar
  ChatPanel --> QuantitativeInsights

  QuantitativeInsights --> CodeBlock
  QuantitativeInsights --> DataOutputPanel
  QuantitativeInsights --> CsvPreviewPanel