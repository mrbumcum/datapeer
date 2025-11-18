import { CodeBlock } from './CodeBlock'
import { DataOutputPanel } from './DataOutputPanel'
import { CsvPreviewPanel } from './CsvPreviewPanel'

export function QuantitativeInsights({
  quantAnalysis,
  selectedFiles,
  isLoading
}) {
  const {
    code,
    explanation,
    dataOutput,
    summary,
    files,
    codeSuccess,
    codeError,
    updatedAt
  } = quantAnalysis || {}

  return (
    <div className="w-full lg:w-5/12 flex flex-col gap-4 min-h-0 overflow-hidden">
      <CodeBlock
        code={code}
        explanation={explanation}
        isLoading={isLoading}
        updatedAt={updatedAt}
      />

      <DataOutputPanel
        responseText={summary}
        dataOutput={dataOutput}
        files={files}
        codeSuccess={codeSuccess}
        codeError={codeError}
        isLoading={isLoading}
      />

      <div className="flex-1 overflow-hidden">
        <CsvPreviewPanel selectedFiles={selectedFiles} />
      </div>
    </div>
  )
}

