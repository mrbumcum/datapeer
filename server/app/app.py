from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import csv
from pathlib import Path
from pydantic import BaseModel
from . import database


class SelectionUpdate(BaseModel):
    is_selected: bool

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
