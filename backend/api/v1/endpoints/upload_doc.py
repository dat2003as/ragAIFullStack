from typing import Optional
from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.params import Form
from services.document_service import document_service
from models.schemas import FileUploadResponse
from monitoring.metrics import (
    file_upload_counter, 
    file_size_histogram,
    document_processing_errors
)
from monitoring.tracing import create_span
from pathlib import Path
import shutil
import os
import logging
import uuid
import time

logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("", response_model=FileUploadResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """Upload document (PDF, DOCX, TXT, MD) - supports multiple documents per session"""
    if not session_id:
        session_id = str(uuid.uuid4())

    with create_span("upload_document", {"session_id": session_id, "filename": file.filename}):
        file_upload_counter.labels(file_type="document").inc()

        try:
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in document_service.ALLOWED_EXTENSIONS:
                raise HTTPException(
                    400,
                    f"Unsupported file type: {file_ext}. Allowed: {document_service.ALLOWED_EXTENSIONS}"
                )

            file_id = str(uuid.uuid4())[:8]
            file_path = UPLOAD_DIR / "documents" / f"{session_id}_{file_id}_{file.filename}"
            file_path.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"📥 Uploading document: {file.filename}")

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            file_size = os.path.getsize(file_path)
            file_size_histogram.labels(file_type="document").observe(file_size)
            logger.info(f"✅ File saved: {file_size} bytes")

            metadata = document_service.validate_document(str(file_path))
            text = document_service.parse_document(str(file_path))

            # Initialize session if not exists
            if session_id not in request.app.state.sessions:
                request.app.state.sessions[session_id] = {
                    "images": {},
                    "csvs": {},
                    "documents": {},
                    "created_at": time.time(),
                    "last_activity": time.time()
                }

            request.app.state.sessions[session_id]["documents"][file_id] = {
                "path": str(file_path),
                "filename": file.filename,
                "text": text,
                "metadata": metadata,
                "char_count": len(text),
                "word_count": len(text.split()),
                "uploaded_at": time.time()
            }

            request.app.state.sessions[session_id]["last_activity"] = time.time()

            return FileUploadResponse(
                status="uploaded",
                session_id=session_id,
                filename=file.filename,
                file_type="document",
                size_bytes=file_size,
                metadata={
                    **metadata,
                    "file_id": file_id,
                    "char_count": len(text),
                    "word_count": len(text.split()),
                    "preview": text[:200] + "..." if len(text) > 200 else text,
                    "total_documents": len(request.app.state.sessions[session_id]["documents"]),
                    "uploaded_at": time.time()
                }
            )

        except ValueError as e:
            logger.error(f"❌ Validation error: {e}")
            document_processing_errors.inc(1, {"file_type": "document", "error_type": "validation"})
            raise HTTPException(400, f"Document validation failed: {str(e)}")

        except Exception as e:
            logger.error(f"❌ Processing error: {e}")
            document_processing_errors.inc(1, {"file_type": "document", "error_type": "processing"})
            raise HTTPException(500, f"Failed to process document: {str(e)}")


@router.delete("/{session_id}")
async def delete_all_documents(request: Request, session_id: str):
    """Delete all uploaded documents for a session"""
    with create_span("delete_all_documents", {"session_id": session_id}):
        if session_id in request.app.state.sessions:
            documents = request.app.state.sessions[session_id]["documents"]
            deleted_count = 0
            
            for file_id, doc_info in documents.items():
                try:
                    Path(doc_info['path']).unlink(missing_ok=True)
                    deleted_count += 1
                    logger.info(f"🗑️  Deleted file: {doc_info['filename']}")
                except Exception as e:
                    logger.warning(f"⚠️  Could not delete file: {e}")
            
            request.app.state.sessions[session_id]["documents"].clear()
            
            # Clear chat history if no files remain
            if (not request.app.state.sessions[session_id]["images"] and
                not request.app.state.sessions[session_id]["csvs"]):
                if session_id in request.app.state.chat_history:
                    del request.app.state.chat_history[session_id]
                    logger.info(f"🗑️  Cleared chat history for session {session_id}")
            
            return {"status": "deleted", "count": deleted_count, "history_cleared": True}
        
        return {"status": "not_found", "count": 0}


@router.delete("/{session_id}/{file_id}")
async def delete_single_document(request: Request, session_id: str, file_id: str):
    """Delete a specific document by file_id"""
    with create_span("delete_single_document", {"session_id": session_id, "file_id": file_id}):
        if (session_id in request.app.state.sessions and
            file_id in request.app.state.sessions[session_id]["documents"]):
            
            doc_info = request.app.state.sessions[session_id]["documents"][file_id]
            
            try:
                Path(doc_info['path']).unlink(missing_ok=True)
                logger.info(f"🗑️  Deleted file: {doc_info['filename']}")
            except Exception as e:
                logger.warning(f"⚠️  Could not delete file: {e}")
            
            del request.app.state.sessions[session_id]["documents"][file_id]
            
            # Clear history if no files remain
            if (not request.app.state.sessions[session_id]["images"] and
                not request.app.state.sessions[session_id]["csvs"] and
                not request.app.state.sessions[session_id]["documents"]):
                if session_id in request.app.state.chat_history:
                    del request.app.state.chat_history[session_id]
            
            return {"status": "deleted", "file_id": file_id}
        
        raise HTTPException(404, "Document not found")


@router.get("/{session_id}")
async def list_documents(request: Request, session_id: str):
    """List all uploaded documents for a session"""
    if session_id in request.app.state.sessions:
        documents = request.app.state.sessions[session_id]["documents"]
        return {
            "session_id": session_id,
            "count": len(documents),
            "documents": [
                {
                    "file_id": file_id,
                    "filename": doc_info["filename"],
                    "char_count": doc_info["char_count"],
                    "word_count": doc_info["word_count"],
                    "uploaded_at": doc_info["uploaded_at"],
                    "preview": doc_info["text"][:100] + "..." if len(doc_info["text"]) > 100 else doc_info["text"]
                }
                for file_id, doc_info in documents.items()
            ]
        }
    return {"session_id": session_id, "count": 0, "documents": []}

@router.get("/{session_id}/{file_id}/info")
async def get_document_info(request: Request, session_id: str, file_id: str):
    """Get specific document information"""
    if (session_id in request.app.state.sessions and
        file_id in request.app.state.sessions[session_id]["documents"]):
        
        doc_info = request.app.state.sessions[session_id]["documents"][file_id]
        
        return {
            "file_id": file_id,
            "filename": doc_info['filename'],
            "char_count": doc_info['char_count'],
            "word_count": doc_info['word_count'],
            "metadata": doc_info['metadata']
        }
    
    raise HTTPException(404, "Document not found")
