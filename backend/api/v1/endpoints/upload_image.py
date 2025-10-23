from typing import Optional
from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.params import Form
from services.image_service import image_service
from monitoring.metrics import file_upload_counter, file_size_histogram
from opentelemetry import trace
import shutil
from pathlib import Path
import uuid
import time

router = APIRouter()
tracer = trace.get_tracer(__name__)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

from typing import Optional
from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.params import Form
from services.image_service import image_service
from monitoring.metrics import file_upload_counter, file_size_histogram
from opentelemetry import trace
import shutil
from pathlib import Path
import uuid
import time
from datetime import datetime

router = APIRouter()
tracer = trace.get_tracer(__name__)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("")
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """Upload image file - supports multiple images per session"""    
    if not session_id:
        session_id = str(uuid.uuid4())

    with tracer.start_as_current_span("upload_image_endpoint") as span:
        span.set_attribute("session_id", session_id)
        span.set_attribute("filename", file.filename)
        span.set_attribute("content_type", file.content_type)

        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(400, "File phải là ảnh hợp lệ")

        file_upload_counter.labels(file_type="image").inc()

        # Tạo đường dẫn lưu file
        file_id = str(uuid.uuid4())[:8]
        file_path = UPLOAD_DIR / "images" / f"{session_id}_{file_id}_{file.filename}"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            metadata = image_service.validate_image(str(file_path))
            file_size_histogram.labels(file_type="image").observe(metadata["size_bytes"])
            resized_path = image_service.resize_if_needed(str(file_path), max_dimension=2048)

            span.set_attribute("validation.success", True)
            span.set_attribute("image.format", metadata["format"])
            span.set_attribute("image.dimensions", f"{metadata['width']}x{metadata['height']}")
            span.set_attribute("file.size_mb", metadata["size_mb"])
            span.set_attribute("resized", resized_path != str(file_path))
            span.set_attribute("file_id", file_id)

            session = request.app.state.sessions.setdefault(session_id, {
                "images": {},
                "csvs": {},
                "documents": {},
                "created_at": time.time(),
                "last_activity": time.time()
            })

            session["images"][file_id] = {
                "path": str(file_path),
                "resized_path": resized_path if resized_path != str(file_path) else None,
                "filename": file.filename,
                "metadata": metadata,
                "ready_for_gemini": True,
                "uploaded_at": time.time()
            }

            session["last_activity"] = time.time()

            return {
                "status": "uploaded",
                "session_id": session_id,
                "file_id": file_id,
                "filename": file.filename,
                "format": metadata["format"],
                "dimensions": {
                    "width": metadata["width"],
                    "height": metadata["height"]
                },
                "size_mb": metadata["size_mb"],
                "resized": resized_path != str(file_path),
                "preview_url": f"/uploads/images/{session_id}_{file_id}_{file.filename}",
                "total_images": len(session["images"])
            }

        except ValueError as e:
            span.set_attribute("validation.success", False)
            span.record_exception(e)
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(400, detail=str(e))

        except Exception as e:
            span.set_attribute("validation.success", False)
            span.record_exception(e)
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(500, detail=f"Lỗi khi upload ảnh: {str(e)}")

@router.delete("/{session_id}")
async def delete_all_images(request: Request, session_id: str):
    """Delete all uploaded images for a session and clear chat history"""
    with tracer.start_as_current_span("delete_all_images") as span:
        span.set_attribute("session_id", session_id)
        
        if session_id in request.app.state.sessions:
            images = request.app.state.sessions[session_id]["images"]
            deleted_count = 0
            
            for file_id, image_info in images.items():
                try:
                    Path(image_info["path"]).unlink(missing_ok=True)
                    deleted_count += 1
                    span.add_event(f"Deleted image file: {image_info['filename']}")
                except Exception as e:
                    span.record_exception(e)
                
                if image_info.get("resized_path"):
                    try:
                        Path(image_info["resized_path"]).unlink(missing_ok=True)
                        span.add_event(f"Deleted resized image: {image_info['filename']}")
                    except Exception as e:
                        span.record_exception(e)
            
            # Clear images dict
            request.app.state.sessions[session_id]["images"].clear()
            
            # Clear chat history if no files remain
            if (not request.app.state.sessions[session_id]["csvs"] and 
                not request.app.state.sessions[session_id]["documents"]):
                if session_id in request.app.state.chat_history:
                    del request.app.state.chat_history[session_id]
                    span.add_event("Cleared chat history - no files remaining")
            
            return {"status": "deleted", "count": deleted_count, "history_cleared": True}
        
        return {"status": "not_found", "count": 0}


@router.delete("/{session_id}/{file_id}")
async def delete_single_image(request: Request, session_id: str, file_id: str):
    """Delete a specific image by file_id"""
    with tracer.start_as_current_span("delete_single_image") as span:
        span.set_attribute("session_id", session_id)
        span.set_attribute("file_id", file_id)
        
        if (session_id in request.app.state.sessions and 
            file_id in request.app.state.sessions[session_id]["images"]):
            
            image_info = request.app.state.sessions[session_id]["images"][file_id]
            
            try:
                Path(image_info["path"]).unlink(missing_ok=True)
                span.add_event(f"Deleted image file: {image_info['filename']}")
            except Exception as e:
                span.record_exception(e)
            
            if image_info.get("resized_path"):
                try:
                    Path(image_info["resized_path"]).unlink(missing_ok=True)
                    span.add_event(f"Deleted resized image: {image_info['filename']}")
                except Exception as e:
                    span.record_exception(e)
            
            del request.app.state.sessions[session_id]["images"][file_id]
            
            # Clear history if no files remain
            if (not request.app.state.sessions[session_id]["images"] and
                not request.app.state.sessions[session_id]["csvs"] and
                not request.app.state.sessions[session_id]["documents"]):
                if session_id in request.app.state.chat_history:
                    del request.app.state.chat_history[session_id]
                    span.add_event("Cleared chat history - no files remaining")
            
            return {"status": "deleted", "file_id": file_id}
        
        raise HTTPException(404, "Image not found")


@router.get("/{session_id}")
async def list_images(request: Request, session_id: str):
    """List all uploaded images for a session"""
    if session_id in request.app.state.sessions:
        images = request.app.state.sessions[session_id]["images"]
        sorted_images = sorted(
            images.items(),
            key=lambda x: x[1].get("uploaded_at", 0)
        )
        return {
            "session_id": session_id,
            "count": len(sorted_images),
            "images": [
                {
                    "file_id": file_id,
                    "filename": info["filename"],
                    "format": info["metadata"]["format"],
                    "dimensions": f"{info['metadata']['width']}x{info['metadata']['height']}",
                    "size_mb": info["metadata"]["size_mb"],
                    "uploaded_at": info.get("uploaded_at")
                }
                for file_id, info in sorted_images
            ]
        }
    
    return {"session_id": session_id, "count": 0, "images": []}

