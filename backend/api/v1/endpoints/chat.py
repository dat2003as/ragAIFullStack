from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from models.schemas import ChatRequest, ChatResponse
from services.gemini_service import chat_with_session
from monitoring.metrics import (
    chat_errors_counter,
    message_length_histogram,
)
from monitoring.tracing import create_span
import time
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("", response_model=ChatResponse)
async def chat(request: Request, payload: ChatRequest):
    """
    Handle chat request with multi-file context
    Supports: multiple images, CSVs, documents per session
    """
    with create_span("chat_request", {"session_id": payload.session_id}):
        session_id = payload.session_id
        user_message = payload.message
        
        message_length_histogram.observe(len(user_message))
        
        # Get or create chat history
        if session_id not in request.app.state.chat_history:
            request.app.state.chat_history[session_id] = []
        
        history = request.app.state.chat_history[session_id]
        
        # Get session data
        session_data = request.app.state.sessions.get(session_id, {
            "images": {},
            "csvs": {},
            "documents": {}
        })
        
        # Count files for logging
        images_count = len(session_data.get("images", {}))
        csvs_count = len(session_data.get("csvs", {}))
        documents_count = len(session_data.get("documents", {}))
        
        # Add user message to history
        history.append({
            "role": "user",
            "content": user_message,
            "timestamp": time.time(),
            "context": {
                "images_count": images_count,
                "csvs_count": csvs_count,
                "documents_count": documents_count
            }
        })
        
        try:
            all_files = []
            for ftype in ["images", "csvs", "documents"]:
                for fid, finfo in session_data.get(ftype, {}).items():
                    all_files.append({
                        "type": ftype,
                        "file_id": fid,
                        "filename": finfo.get("filename"),
                        "uploaded_at": finfo.get("uploaded_at", 0),
                        "preview": finfo.get("preview") if ftype == "documents" else None
                    })

            all_files.sort(key=lambda f: f["uploaded_at"])

            ordered_context = "\n".join([
                f"[{i+1}] {f['type'].upper()} → {f['filename']}"
                for i, f in enumerate(all_files)
            ])

            response = await chat_with_session(
                message=user_message,
                history=history[-10:],  
                session_data=session_data,
                ordered_files=all_files,      
                ordered_context=ordered_context 
            )

            history.append({
                "role": "assistant",
                "content": response,
                "timestamp": time.time()
            })

            request.app.state.chat_history[session_id] = history

            if session_id in request.app.state.sessions:
                request.app.state.sessions[session_id]["last_activity"] = time.time()

            logger.info(
                f"✅ Chat response generated for session {session_id} "
                f"(total files: {len(all_files)}, order preserved)"
            )

            return ChatResponse(
                response=response,
                session_id=session_id,
                metadata={
                    "total_files": len(all_files),
                    "images_used": images_count,
                    "csvs_used": csvs_count,
                    "documents_used": documents_count,
                    "file_order": [f["filename"] for f in all_files]
                }
            )
        
        except Exception as e:
            chat_errors_counter.labels(error_type=type(e).__name__).inc()
            logger.error(f"❌ Chat error for session {session_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}/history")
async def clear_chat_history(request: Request, session_id: str):
    """Clear chat history for a session"""
    with create_span("clear_chat_history", {"session_id": session_id}):
        if session_id in request.app.state.chat_history:
            message_count = len(request.app.state.chat_history[session_id])
            del request.app.state.chat_history[session_id]
            logger.info(f"🗑️  Cleared {message_count} messages for session {session_id}")
            return {"status": "cleared", "messages_deleted": message_count}
        
        return {"status": "not_found", "messages_deleted": 0}


@router.get("/{session_id}/history")
async def get_chat_history(request: Request, session_id: str, limit: int = 50):
    """Get chat history for a session"""
    if session_id in request.app.state.chat_history:
        history = request.app.state.chat_history[session_id]
        return {
            "session_id": session_id,
            "total_messages": len(history),
            "messages": history[-limit:] if limit else history
        }
    
    return {"session_id": session_id, "total_messages": 0, "messages": []}


@router.get("/{session_id}/info")
async def get_session_info(request: Request, session_id: str):
    """Get complete session information including all uploaded files"""
    if session_id not in request.app.state.sessions:
        raise HTTPException(404, "Session not found")
    
    session_data = request.app.state.sessions[session_id]
    
    return {
        "session_id": session_id,
        "created_at": session_data.get("created_at"),
        "last_activity": session_data.get("last_activity"),
        "files": {
            "images": {
                "count": len(session_data["images"]),
                "files": [
                    {
                        "file_id": fid,
                        "filename": info["filename"],
                        "size_mb": info["metadata"]["size_mb"]
                    }
                    for fid, info in session_data["images"].items()
                ]
            },
            "csvs": {
                "count": len(session_data["csvs"]),
                "files": [
                    {
                        "file_id": fid,
                        "filename": info["filename"],
                        "rows": info["shape"][0],
                        "columns": info["shape"][1]
                    }
                    for fid, info in session_data["csvs"].items()
                ]
            },
            "documents": {
                "count": len(session_data["documents"]),
                "files": [
                    {
                        "file_id": fid,
                        "filename": info["filename"],
                        "word_count": info["word_count"]
                    }
                    for fid, info in session_data["documents"].items()
                ]
            }
        },
        "chat_messages": len(request.app.state.chat_history.get(session_id, []))
    }


@router.delete("/{session_id}")
async def delete_session(request: Request, session_id: str):
    """Delete entire session including all files and chat history"""
    with create_span("delete_session", {"session_id": session_id}):
        if session_id not in request.app.state.sessions:
            raise HTTPException(404, "Session not found")
        
        session_data = request.app.state.sessions[session_id]
        deleted_files = 0
        
        # Delete all images
        for file_id, image_info in session_data["images"].items():
            try:
                Path(image_info["path"]).unlink(missing_ok=True)
                if image_info.get("resized_path"):
                    Path(image_info["resized_path"]).unlink(missing_ok=True)
                deleted_files += 1
            except Exception as e:
                logger.warning(f"⚠️  Could not delete image: {e}")
        
        # Delete all CSVs
        for file_id, csv_info in session_data["csvs"].items():
            if "path" in csv_info:
                try:
                    Path(csv_info["path"]).unlink(missing_ok=True)
                    deleted_files += 1
                except Exception as e:
                    logger.warning(f"⚠️  Could not delete CSV: {e}")
        
        # Delete all documents
        for file_id, doc_info in session_data["documents"].items():
            try:
                Path(doc_info["path"]).unlink(missing_ok=True)
                deleted_files += 1
            except Exception as e:
                logger.warning(f"⚠️  Could not delete document: {e}")
        
        # Delete session data
        del request.app.state.sessions[session_id]
        
        # Delete chat history
        messages_deleted = 0
        if session_id in request.app.state.chat_history:
            messages_deleted = len(request.app.state.chat_history[session_id])
            del request.app.state.chat_history[session_id]
        
        logger.info(f"🗑️  Deleted session {session_id}: {deleted_files} files, {messages_deleted} messages")
        
        return {
            "status": "deleted",
            "session_id": session_id,
            "files_deleted": deleted_files,
            "messages_deleted": messages_deleted
        }
router.get("/history/{session_id}")
async def get_full_chat_history(request: Request, session_id: str):
    """Get full chat history for a session"""
    if session_id in request.app.state.chat_history:
        history = request.app.state.chat_history[session_id]
        return {
            "session_id": session_id,
            "total_messages": len(history),
            "messages": history
        }
    
    return {"session_id": session_id, "total_messages": 0, "messages": []}