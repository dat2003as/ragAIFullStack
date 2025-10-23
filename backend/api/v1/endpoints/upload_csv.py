from typing import Optional
from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Form, logger
from services.csv_service import csv_service
from monitoring.metrics import file_upload_counter, file_size_histogram
from opentelemetry import trace
from pathlib import Path
import shutil
import uuid
import time
import asyncio
from pydantic import BaseModel

class CSVUrlRequest(BaseModel):
    url: str
    session_id: Optional[str] = None

router = APIRouter()
tracer = trace.get_tracer(__name__)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("")
async def upload_csv(
    request: Request,
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """Upload CSV file - supports multiple CSVs per session"""
    if not session_id:
        session_id = str(uuid.uuid4())

    with tracer.start_as_current_span("upload_csv") as span:
        span.set_attribute("session_id", session_id)
        span.set_attribute("filename", file.filename)
        span.set_attribute("file_type", "csv")

        if not file.content_type or not file.content_type.startswith("text/"):
            raise HTTPException(400, "File must be a CSV or text file")

        file_upload_counter.labels(file_type="csv").inc()

        file_id = str(uuid.uuid4())[:8]
        file_path = UPLOAD_DIR / "csv" / f"{session_id}_{file_id}_{file.filename}"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            await asyncio.to_thread(lambda: shutil.copyfileobj(file.file, open(file_path, "wb")))

            file_size = file_path.stat().st_size
            file_size_histogram.labels(file_type="csv").observe(file_size)
            span.set_attribute("file_size_bytes", file_size)

            df = await csv_service.parse_csv(str(file_path))

            # Initialize session if not exists
            if session_id not in request.app.state.sessions:
                request.app.state.sessions[session_id] = {
                    "images": {},
                    "csvs": {},
                    "documents": {},
                    "created_at": time.time(),
                    "last_activity": time.time()
                }

            request.app.state.sessions[session_id]["csvs"][file_id] = {
                "path": str(file_path),
                "filename": file.filename,
                "df": df,
                "shape": df.shape,
                "uploaded_at": time.time()
            }

            request.app.state.sessions[session_id]["last_activity"] = time.time()

            preview_data = df.head(5).to_dict(orient="records")

            return {
                "status": "uploaded",
                "session_id": session_id,
                "file_id": file_id,
                "filename": file.filename,
                "rows": df.shape[0],
                "columns": list(df.columns),
                "preview": preview_data,
                "uploaded_at": time.time(),
                "total_csvs": len(request.app.state.sessions[session_id]["csvs"])
            }

        except Exception as e:
            if file_path.exists():
                file_path.unlink(missing_ok=True)
            span.record_exception(e)
            raise HTTPException(400, f"Failed to process CSV: {str(e)}")

@router.post("/url")
async def upload_csv_url(request: Request, body: CSVUrlRequest):
    """Load CSV directly from a URL (no query params, JSON body only)"""
    url = body.url
    session_id = body.session_id or str(uuid.uuid4())

    with tracer.start_as_current_span("upload_csv_url") as span:
        span.set_attribute("session_id", session_id)
        span.set_attribute("url_input", url)
        span.set_attribute("file_type", "csv-url")

        file_upload_counter.labels(file_type="csv-url").inc()

        try:
            df = await csv_service.load_from_url(url)
            file_id = str(uuid.uuid4())[:8]

            sessions = request.app.state.sessions
            if session_id not in sessions:
                sessions[session_id] = {
                    "images": {},
                    "csvs": {},
                    "documents": {},
                    "created_at": time.time(),
                    "last_activity": time.time(),
                }

            filename = url.split("/")[-1] or f"csv_{file_id}.csv"
            sessions[session_id]["csvs"][file_id] = {
                "url": url,
                "filename": filename,
                "rows": len(df),
                "columns": list(df.columns),
                "shape": df.shape,
                "uploaded_at": time.time(),
                "df": df,
            }

            sessions[session_id]["last_activity"] = time.time()

            return {
                "status": "loaded",
                "session_id": session_id,
                "file_id": file_id,
                "filename": filename,
                "rows": len(df),
                "columns": list(df.columns),
                "shape": df.shape,
                "total_csvs": len(sessions[session_id]['csvs']),
            }

        except Exception as e:
            span.record_exception(e)
            logger.error(f"❌ Failed to load CSV from URL: {url} — {e}")
            raise HTTPException(status_code=400, detail=f"Failed to load CSV: {str(e)}")


@router.delete("/{session_id}")
async def delete_all_csvs(request: Request, session_id: str):
    """Delete all uploaded CSVs for a session"""
    with tracer.start_as_current_span("delete_all_csvs") as span:
        span.set_attribute("session_id", session_id)

        if session_id in request.app.state.sessions:
            csvs = request.app.state.sessions[session_id]["csvs"]
            deleted_count = 0

            for file_id, csv_info in csvs.items():
                if "path" in csv_info:
                    try:
                        Path(csv_info["path"]).unlink(missing_ok=True)
                        deleted_count += 1
                        span.add_event(f"Deleted CSV file: {csv_info['filename']}")
                    except Exception as e:
                        span.record_exception(e)

            request.app.state.sessions[session_id]["csvs"].clear()

            # Clear chat history if no files remain
            if (not request.app.state.sessions[session_id]["images"] and
                not request.app.state.sessions[session_id]["documents"]):
                if session_id in request.app.state.chat_history:
                    del request.app.state.chat_history[session_id]
                    span.add_event("Cleared chat history due to CSV deletion")

            return {"status": "deleted", "count": deleted_count, "history_cleared": True}

        return {"status": "not_found", "count": 0}


@router.delete("/{session_id}/{file_id}")
async def delete_single_csv(request: Request, session_id: str, file_id: str):
    """Delete a specific CSV by file_id"""
    with tracer.start_as_current_span("delete_single_csv") as span:
        span.set_attribute("session_id", session_id)
        span.set_attribute("file_id", file_id)

        if (session_id in request.app.state.sessions and
            file_id in request.app.state.sessions[session_id]["csvs"]):

            csv_info = request.app.state.sessions[session_id]["csvs"][file_id]

            if "path" in csv_info:
                try:
                    Path(csv_info["path"]).unlink(missing_ok=True)
                    span.add_event(f"Deleted CSV file: {csv_info['filename']}")
                except Exception as e:
                    span.record_exception(e)

            del request.app.state.sessions[session_id]["csvs"][file_id]

            # Clear history if no fisession les remain
            if (not request.app.state.sessions[session_id]["images"] and
                not request.app.state.sessions[session_id]["csvs"] and
                not request.app.state.sessions[session_id]["documents"]):
                if session_id in request.app.state.chat_history:
                    del request.app.state.chat_history[session_id]

            return {"status": "deleted", "file_id": file_id}

        raise HTTPException(404, "CSV not found")


@router.get("/{session_id}")
async def list_csvs(request: Request, session_id: str):
    """List all uploaded CSVs for a session"""
    if session_id in request.app.state.sessions:
        csvs = request.app.state.sessions[session_id]["csvs"]
        return {
            "session_id": session_id,
            "count": len(csvs),
            "csvs": [
                {
                    "file_id": file_id,
                    "filename": csv_info["filename"],
                    "rows": csv_info["shape"][0],
                    "columns": csv_info["shape"][1],
                    "column_names": list(csv_info["df"].columns),
                    "uploaded_at": csv_info["uploaded_at"]
                }
                for file_id, csv_info in csvs.items()
            ]
        }

    return {"session_id": session_id, "count": 0, "csvs": []}