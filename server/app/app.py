from __future__ import annotations

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import csv
import time
from pathlib import Path
from typing import Optional, Literal, List
import asyncio
from pydantic import BaseModel
from . import database
from . import llm_analysis


class SelectionUpdate(BaseModel):
    is_selected: bool


class ChatMessage(BaseModel):
    message: str
    analysis_type: str  # 'qualitative' or 'quantitative'
    selected_file_ids: list[int] = []
    provider: Optional[str] = None
    model: Optional[str] = None


class BenchmarkVariant(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    context_mode: Literal["none", "light", "rich"] = "none"


class BenchmarkRequest(BaseModel):
    message: str
    analysis_type: Literal["qualitative", "quantitative"]
    selected_file_ids: list[int]
    runs: int = 1
    variants: List[BenchmarkVariant]


class BenchmarkRun(BaseModel):
    timestamp: float
    run_index: int
    analysis_type: str
    provider: Optional[str]
    model: Optional[str]
    context_mode: str
    latency_ms: float
    files_analyzed: list[str]
    response: Optional[str] = None
    code: Optional[str] = None
    code_explanation: Optional[str] = None
    data_output: Optional[str] = None
    code_success: Optional[bool] = None
    code_error: Optional[str] = None

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await database.init_db()


@app.get("/hello-world")
def hello_word():
    return {"message": "Hello World"}


@app.post("/api/files/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV file"""
    # Validate file extension
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    # Save file
    file_path = UPLOAD_DIR / file.filename
    
    # Handle duplicate filenames
    counter = 1
    original_path = file_path
    while file_path.exists():
        stem = original_path.stem
        suffix = original_path.suffix
        file_path = UPLOAD_DIR / f"{stem}_{counter}{suffix}"
        counter += 1
    
    try:
        contents = await file.read()
        file_size = len(contents)
        
        # Write file to disk
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Save metadata to database
        file_id = await database.add_csv_file(
            filename=file_path.name,
            file_size=file_size,
            file_path=str(file_path)
        )
        
        return {
            "id": file_id,
            "filename": file_path.name,
            "file_size": file_size,
            "message": "File uploaded successfully"
        }
    except Exception as e:
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@app.get("/api/files")
async def get_files():
    """Get all uploaded CSV files"""
    try:
        files = await database.get_all_files()
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching files: {str(e)}")


@app.put("/api/files/{file_id}/selection")
async def update_selection(file_id: int, selection: SelectionUpdate):
    """Update the selection status of a file"""
    try:
        await database.update_file_selection(file_id, selection.is_selected)
        return {"message": "Selection updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating selection: {str(e)}")


@app.delete("/api/files/{file_id}")
async def delete_file(file_id: int):
    """Delete a file"""
    try:
        success = await database.delete_file(file_id)
        if not success:
            raise HTTPException(status_code=404, detail="File not found")
        return {"message": "File deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")


@app.get("/api/files/selected")
async def get_selected_files():
    """Get all selected files for LLM processing"""
    try:
        all_files = await database.get_all_files()
        selected = [f for f in all_files if f["is_selected"] == 1]
        return {"files": selected}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching selected files: {str(e)}")


@app.get("/api/files/{file_id}/preview")
async def preview_csv_file(file_id: int, rows: int = Query(default=20, ge=1, le=100)):
    """Preview CSV file content (first N rows)"""
    try:
        all_files = await database.get_all_files()
        file_record = next((f for f in all_files if f["id"] == file_id), None)
        
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = Path(file_record["file_path"])
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        # Read and parse CSV
        preview_data = []
        total_rows = 0
        headers = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                
                for i, row in enumerate(reader):
                    total_rows += 1
                    if i < rows:
                        preview_data.append(row)
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            with open(file_path, 'r', encoding='latin-1') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []
                
                for i, row in enumerate(reader):
                    total_rows += 1
                    if i < rows:
                        preview_data.append(row)
        
        return {
            "id": file_record["id"],
            "filename": file_record["filename"],
            "headers": headers,
            "rows": preview_data,
            "total_rows": total_rows,
            "previewed_rows": len(preview_data)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error previewing file: {str(e)}")


@app.post("/api/chat")
async def chat_with_llm(chat_request: ChatMessage):
    """Process user message with LLM analysis based on selected datasets"""
    try:
        # Validate analysis type
        if chat_request.analysis_type not in ['qualitative', 'quantitative']:
            raise HTTPException(status_code=400, detail="analysis_type must be 'qualitative' or 'quantitative'")
        
        # Get selected files
        if not chat_request.selected_file_ids:
            raise HTTPException(status_code=400, detail="No files selected. Please select at least one dataset.")
        
        # Fetch file records from database
        all_files = await database.get_all_files()
        selected_files = [
            f for f in all_files 
            if f["id"] in chat_request.selected_file_ids
        ]
        
        if not selected_files:
            raise HTTPException(status_code=404, detail="Selected files not found")
        
        # Validate files exist on disk
        file_paths = []
        file_names = []
        for file_record in selected_files:
            file_path = Path(file_record["file_path"])
            if not file_path.exists():
                raise HTTPException(status_code=404, detail=f"File {file_record['filename']} not found on disk")
            file_paths.append(str(file_path))
            file_names.append(file_record["filename"])
        
        # Perform analysis per requested type
        if chat_request.analysis_type == 'qualitative':
            response_text = await llm_analysis.analyze_with_llm_qualitative(
                user_message=chat_request.message,
                file_paths=file_paths,
                file_names=file_names,
                provider=chat_request.provider,
                model=chat_request.model,
            )
            
            return {
                "response": response_text,
                "analysis_type": chat_request.analysis_type,
                "files_analyzed": file_names
            }
        else:
            quant_result = await llm_analysis.analyze_with_llm_quantitative(
                user_message=chat_request.message,
                file_paths=file_paths,
                file_names=file_names,
                provider=chat_request.provider,
                model=chat_request.model,
            )
            
            return {
                "response": quant_result.get("response"),
                "analysis_type": chat_request.analysis_type,
                "files_analyzed": file_names,
                "code": quant_result.get("code"),
                "code_explanation": quant_result.get("code_explanation"),
                "data_output": quant_result.get("data_output"),
                "code_success": quant_result.get("code_success"),
                "code_error": quant_result.get("code_error")
            }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat request: {str(e)}")


@app.post("/api/benchmark")
async def run_benchmark(request: BenchmarkRequest):
    """Run timed EDA analyses across multiple provider/model/context variants."""
    try:
        if request.runs < 1:
            raise HTTPException(status_code=400, detail="runs must be at least 1")

        if not request.selected_file_ids:
            raise HTTPException(status_code=400, detail="No files selected. Please select at least one dataset.")

        # Fetch file records from database
        all_files = await database.get_all_files()
        selected_files = [
            f for f in all_files
            if f["id"] in request.selected_file_ids
        ]

        if not selected_files:
            raise HTTPException(status_code=404, detail="Selected files not found")

        # Validate files exist on disk
        file_paths: list[str] = []
        file_names: list[str] = []
        for file_record in selected_files:
            file_path = Path(file_record["file_path"])
            if not file_path.exists():
                raise HTTPException(status_code=404, detail=f"File {file_record['filename']} not found on disk")
            file_paths.append(str(file_path))
            file_names.append(file_record["filename"])

        now = time.time()

        tasks = []
        meta: list[tuple[int, BenchmarkVariant]] = []
        for variant_index, variant in enumerate(request.variants):
            for run_index in range(request.runs):
                tasks.append(
                    llm_analysis.run_timed_analysis(
                        analysis_type=request.analysis_type,
                        user_message=request.message,
                        file_paths=file_paths,
                        file_names=file_names,
                        provider=variant.provider,
                        model=variant.model,
                        context_mode=variant.context_mode,
                    )
                )
                meta.append((run_index, variant))

        analyses = await asyncio.gather(*tasks)

        results: list[BenchmarkRun] = []
        for (run_index, variant), analysis in zip(meta, analyses):
            run = BenchmarkRun(
                timestamp=now,
                run_index=run_index,
                analysis_type=analysis.get("analysis_type", request.analysis_type),
                provider=analysis.get("provider", variant.provider),
                model=analysis.get("model", variant.model),
                context_mode=analysis.get("context_mode", variant.context_mode),
                latency_ms=float(analysis.get("latency_ms", 0.0)),
                files_analyzed=analysis.get("files_analyzed", file_names),
                response=analysis.get("response"),
                code=analysis.get("code"),
                code_explanation=analysis.get("code_explanation"),
                data_output=analysis.get("data_output"),
                code_success=analysis.get("code_success"),
                code_error=analysis.get("code_error"),
            )
            results.append(run)

        return {"results": [r.model_dump() for r in results]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running benchmark: {str(e)}")
