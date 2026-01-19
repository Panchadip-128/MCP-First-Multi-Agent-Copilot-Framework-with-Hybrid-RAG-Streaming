"""Project management endpoints."""

from fastapi import APIRouter, Request, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
from pathlib import Path
from loguru import logger

from app.services.code_indexer import CodeIndexer

router = APIRouter()


class Project(BaseModel):
    """Project information."""
    id: str
    name: str
    description: Optional[str] = None
    language: str
    created_at: str


class ProjectCreate(BaseModel):
    """Request to create a project."""
    name: str
    description: Optional[str] = None
    language: str = "python"
    path: Optional[str] = None  # Optional path to index immediately


class IndexRequest(BaseModel):
    """Request to index a directory."""
    directory_path: str
    extensions: Optional[List[str]] = None  # e.g. [".py", ".js"]


class ProjectStats(BaseModel):
    """Project statistics."""
    project_id: str
    name: str
    total_chunks: int
    total_files: int


# In-memory storage (replace with database in production)
projects_db: Dict[str, Project] = {}


@router.post("/", response_model=Project)
async def create_project(request: Request, project: ProjectCreate) -> Project:
    """Create a new project."""
    from datetime import datetime
    
    project_id = str(uuid.uuid4())
    
    new_project = Project(
        id=project_id,
        name=project.name,
        description=project.description,
        language=project.language,
        created_at=datetime.utcnow().isoformat(),
    )
    
    projects_db[project_id] = new_project
    
    return new_project


@router.get("/", response_model=List[Project])
async def list_projects() -> List[Project]:
    """List all projects."""
    return list(projects_db.values())


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str) -> Project:
    """Get project by ID."""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return projects_db[project_id]


@router.delete("/{project_id}")
async def delete_project(request: Request, project_id: str) -> Dict[str, Any]:
    """Delete a project and all its data."""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Delete from memory
    rag = request.app.state.rag_memory
    deleted_chunks = await rag.delete_project(project_id)
    
    # Delete project
    del projects_db[project_id]
    
    return {
        "success": True,
        "project_id": project_id,
        "deleted_chunks": deleted_chunks,
    }


@router.get("/{project_id}/stats", response_model=ProjectStats)
async def get_project_stats(request: Request, project_id: str) -> ProjectStats:
    """Get project statistics."""
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_db[project_id]
    rag = request.app.state.rag_memory
    
    stats = await rag.get_project_stats(project_id)
    
    return ProjectStats(
        project_id=project_id,
        name=project.name,
        total_chunks=stats["total_chunks"],
        total_files=0,  # TODO: Track file count
    )


@router.post("/{project_id}/index")
async def index_code(
    request: Request,
    project_id: str,
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    """
    Index a code file for RAG memory.
    
    Chunks the file and stores embeddings in vector DB.
    """
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = projects_db[project_id]
    rag = request.app.state.rag_memory
    
    # Read file content
    content = await file.read()
    code_text = content.decode("utf-8")
    
    # Simple chunking (TODO: Use smarter AST-based chunking)
    lines = code_text.split("\n")
    chunk_size = 50  # lines per chunk
    
    chunks_added = 0
    for i in range(0, len(lines), chunk_size):
        chunk_lines = lines[i:i + chunk_size]
        chunk_content = "\n".join(chunk_lines)
        
        if chunk_content.strip():
            await rag.add_document(
                content=chunk_content,
                file_path=file.filename or "unknown",
                language=project.language,
                project_id=project_id,
                start_line=i + 1,
                end_line=i + len(chunk_lines),
                chunk_type="code",
            )
            chunks_added += 1
    
    return {
        "success": True,
        "project_id": project_id,
        "file": file.filename,
        "chunks_added": chunks_added,
    }


@router.post("/{project_id}/index-directory")
async def index_directory(
    request: Request,
    project_id: str,
    index_req: IndexRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Index an entire directory for RAG memory.
    
    Uses AST-based chunking for supported languages.
    Processing happens in background.
    """
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    
    directory_path = Path(index_req.directory_path)
    if not directory_path.exists():
        raise HTTPException(status_code=400, detail=f"Directory not found: {index_req.directory_path}")
    
    if not directory_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {index_req.directory_path}")
    
    # Start indexing in background
    background_tasks.add_task(
        _index_directory_task,
        request.app.state.rag_memory,
        project_id,
        str(directory_path),
        index_req.extensions
    )
    
    return {
        "success": True,
        "project_id": project_id,
        "directory": str(directory_path),
        "status": "indexing_started",
        "message": "Indexing started in background. Check project stats for progress."
    }


async def _index_directory_task(
    rag_memory,
    project_id: str,
    directory: str,
    extensions: Optional[List[str]]
):
    """Background task to index a directory."""
    try:
        logger.info(f"Starting directory indexing for project {project_id}: {directory}")
        
        indexer = CodeIndexer(max_chunk_size=1000)
        chunks = indexer.index_directory(directory, project_id, extensions)
        
        # Add all chunks to RAG memory
        added_count = 0
        for chunk in chunks:
            try:
                await rag_memory.add_document(
                    content=chunk.content,
                    file_path=chunk.file_path,
                    language=chunk.language,
                    project_id=project_id,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    chunk_type=chunk.chunk_type,
                )
                added_count += 1
            except Exception as e:
                logger.error(f"Failed to add chunk: {e}")
        
        logger.info(f"✅ Indexed {added_count} chunks for project {project_id}")
        
    except Exception as e:
        logger.error(f"Failed to index directory: {e}")
