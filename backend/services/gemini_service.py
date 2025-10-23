import logging
import google.generativeai as genai
from PIL import Image
import pandas as pd
import time
from typing import Optional, Dict, List

from core.config.settings import APP_SETTINGS
from monitoring.metrics import (
    gemini_api_duration,
    chat_requests_counter,
    chat_errors_counter,
    message_length_histogram
)

logger = logging.getLogger(__name__)

genai.configure(api_key=APP_SETTINGS.GEMINI_API_KEY)

async def chat(
    message: str,
    history: list,
    images: Optional[Dict[str, dict]] = None,
    csvs: Optional[Dict[str, dict]] = None,
    documents: Optional[Dict[str, dict]] = None,
    ordered_files: Optional[list] = None,
    ordered_context: Optional[str] = None
):
    """
    Chat with Gemini with multi-turn history and optional multi-file context
    
    Args:
        message: User's current message
        history: List of previous chat messages
        images: Dict of {file_id: image_info}
        csvs: Dict of {file_id: csv_info}
        documents: Dict of {file_id: doc_info}
        ordered_files: List of uploaded files in chronological order
        ordered_context: Text summary of upload order to include in prompt
    """
    # Track message length
    message_length_histogram.observe(len(message))
    
    start_time = time.time()
    
    try:
        model = genai.GenerativeModel(APP_SETTINGS.GEMINI_MODEL)
        context_parts = []

        # 1️⃣ Add conversation history
        if history:
            history_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in history[:-1]
            ])
            if history_text:
                context_parts.append(f"Previous conversation:\n{history_text}\n")

        # 2️⃣ Add ordered file context if available
        if ordered_context:
            context_parts.append(
                f"File upload order (earliest first):\n{ordered_context}\n"
                "Please refer to files in this order when answering.\n"
            )
            logger.info("🗂️ Added ordered file context to prompt")

        # 3️⃣ Add CSV context
        if csvs:
            csv_context = ["CSV Data Context:"]
            for file_id, csv_info in csvs.items():
                df = csv_info['df']
                filename = csv_info['filename']
                csv_context.append(f"\n--- CSV File: {filename} (file_id: {file_id}) ---")
                csv_context.append(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
                csv_context.append(f"Columns: {', '.join(df.columns.tolist())}")
                csv_context.append(f"\nFirst 5 rows:\n{df.head().to_string()}")
                csv_context.append(f"\nSummary statistics:\n{df.describe().to_string()}")
            context_parts.append("\n".join(csv_context))
            logger.info(f"📊 Added {len(csvs)} CSV file(s) to context")

        # 4️⃣ Add document context
        if documents:
            doc_context = ["Document Context:"]
            total_chars = 0
            max_chars_per_doc = 15000
            max_total_chars = 50000
            for file_id, doc_info in documents.items():
                filename = doc_info['filename']
                text = doc_info['text']
                truncated_text = text[:max_chars_per_doc] + (
                    "\n\n[Document truncated...]" if len(text) > max_chars_per_doc else ""
                )
                if total_chars + len(truncated_text) > max_total_chars:
                    remaining = max_total_chars - total_chars
                    if remaining > 1000:
                        truncated_text = truncated_text[:remaining] + "\n\n[Remaining documents truncated...]"
                        doc_context.append(f"\n--- Document: {filename} (file_id: {file_id}) ---")
                        doc_context.append(truncated_text)
                    logger.warning(f"⚠️  Reached total document limit ({max_total_chars} chars)")
                    break
                doc_context.append(f"\n--- Document: {filename} (file_id: {file_id}) ---")
                doc_context.append(truncated_text)
                total_chars += len(truncated_text)
            context_parts.append("\n".join(doc_context))
            logger.info(f"📄 Added {len(documents)} document(s) to context")

        # 5️⃣ Add image context
        if images:
            for file_id, image_info in images.items():
                filename = image_info['filename']
                image_path = image_info.get('resized_path') or image_info['path']
                try:
                    img = Image.open(image_path)
                    context_parts.append(img)
                    context_parts.append(f"[Image: {filename} (file_id: {file_id})]")
                    logger.info(f"🖼️ Added image: {filename}")
                except Exception as e:
                    logger.error(f"❌ Failed to load image {filename}: {e}")
                    context_parts.append(f"[Failed to load image: {filename}]")
            if len(images) > 1:
                context_parts.append(
                    f"\nNote: {len(images)} images have been uploaded. "
                    f"Please refer to them by filename when answering."
                )

        # 6️⃣ Add user message
        context_parts.append(f"\nUser question: {message}")

        # Generate response
        response = model.generate_content(context_parts)
        
        duration = time.time() - start_time
        gemini_api_duration.observe(duration)
        chat_requests_counter.labels(status="success").inc()
        logger.info(f"✅ Gemini response generated in {duration:.2f}s")
        return response.text

    except Exception as e:
        duration = time.time() - start_time
        gemini_api_duration.observe(duration)
        chat_requests_counter.labels(status="error").inc()
        chat_errors_counter.labels(error_type=type(e).__name__).inc()
        logger.error(f"❌ Gemini API error: {e}")
        raise

async def chat_with_session(
    message: str,
    history: list,
    session_data: dict,
    ordered_files: Optional[list] = None,
    ordered_context: Optional[str] = None
):
    return await chat(
        message=message,
        history=history,
        images=session_data.get("images"),
        csvs=session_data.get("csvs"),
        documents=session_data.get("documents"),
        ordered_files=ordered_files,
        ordered_context=ordered_context
    )

