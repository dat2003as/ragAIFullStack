# backend/services/image_service.py
"""
Image processing service for handling uploaded images
"""
from PIL import Image
import io
import base64
from pathlib import Path
import logging
from monitoring.metrics import (
    image_processing_duration,
    image_dimensions_histogram,
    track_duration
)
from monitoring.tracing import create_span

logger = logging.getLogger(__name__)


class ImageService:
    """Service for processing and handling images"""
    
    ALLOWED_FORMATS = {'PNG', 'JPEG', 'JPG', 'WEBP'}
    MAX_SIZE_MB = 10
    MAX_DIMENSION = 4096
    
    @staticmethod
    @track_duration(image_processing_duration)
    def validate_image(file_path: str) -> dict:
        """
        Validate uploaded image
        
        Args:
            file_path: Path to the image file
            
        Returns:
            dict: Image metadata (format, size, dimensions)
            
        Raises:
            ValueError: If image is invalid
        """
        with create_span("validate_image") as span:
            try:
                with Image.open(file_path) as img:
                    # Check format
                    if img.format not in ImageService.ALLOWED_FORMATS:
                        raise ValueError(
                            f"Unsupported format: {img.format}. "
                            f"Allowed: {ImageService.ALLOWED_FORMATS}"
                        )
                    
                    # Check dimensions
                    width, height = img.size
                    if width > ImageService.MAX_DIMENSION or height > ImageService.MAX_DIMENSION:
                        raise ValueError(
                            f"Image too large: {width}x{height}. "
                            f"Max dimension: {ImageService.MAX_DIMENSION}"
                        )
                    
                    # Check file size
                    file_size = Path(file_path).stat().st_size
                    size_mb = file_size / (1024 * 1024)
                    if size_mb > ImageService.MAX_SIZE_MB:
                        raise ValueError(
                            f"File too large: {size_mb:.2f}MB. "
                            f"Max: {ImageService.MAX_SIZE_MB}MB"
                        )
                    
                    # Track metrics
                    total_pixels = width * height
                    image_dimensions_histogram.observe(total_pixels)
                    
                    # Set span attributes
                    span.set_attribute("image.format", img.format)
                    span.set_attribute("image.width", width)
                    span.set_attribute("image.height", height)
                    span.set_attribute("image.size_bytes", file_size)
                    
                    metadata = {
                        "format": img.format,
                        "width": width,
                        "height": height,
                        "size_bytes": file_size,
                        "size_mb": round(size_mb, 2),
                        "mode": img.mode
                    }
                    
                    logger.info(f"✅ Image validated: {metadata}")
                    return metadata
                    
            except Exception as e:
                logger.error(f"❌ Image validation failed: {e}")
                span.set_attribute("error", True)
                span.set_attribute("error.message", str(e))
                raise
    
    @staticmethod
    def resize_if_needed(file_path: str, max_dimension: int = 2048) -> str:
        """
        Resize image if it exceeds max dimension (preserve aspect ratio)
        
        Args:
            file_path: Path to the image
            max_dimension: Maximum width or height
            
        Returns:
            str: Path to resized image (or original if no resize needed)
        """
        with create_span("resize_image"):
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
                    
                    # Check if resize needed
                    if width <= max_dimension and height <= max_dimension:
                        logger.info(f"No resize needed: {width}x{height}")
                        return file_path
                    
                    # Calculate new dimensions (preserve aspect ratio)
                    if width > height:
                        new_width = max_dimension
                        new_height = int(height * (max_dimension / width))
                    else:
                        new_height = max_dimension
                        new_width = int(width * (max_dimension / height))
                    
                    # Resize
                    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Save resized image
                    resized_path = file_path.replace('.', '_resized.')
                    resized.save(resized_path, quality=85, optimize=True)
                    
                    logger.info(f"✅ Resized: {width}x{height} → {new_width}x{new_height}")
                    return resized_path
                    
            except Exception as e:
                logger.error(f"❌ Resize failed: {e}")
                return file_path  # Return original on error
    
    @staticmethod
    def to_base64(file_path: str) -> str:
        """
        Convert image to base64 string
        
        Args:
            file_path: Path to the image
            
        Returns:
            str: Base64 encoded string
        """
        try:
            with open(file_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"❌ Base64 encoding failed: {e}")
            raise
    
    @staticmethod
    def get_image_for_gemini(file_path: str) -> Image.Image:
        """
        Prepare image for Gemini API (PIL Image object)
        
        Args:
            file_path: Path to the image
            
        Returns:
            PIL.Image: Image object ready for Gemini
        """
        with create_span("prepare_image_for_gemini"):
            try:
                # Resize if needed (Gemini has limits)
                resized_path = ImageService.resize_if_needed(file_path, max_dimension=2048)
                
                # Open and return PIL Image
                img = Image.open(resized_path)
                logger.info(f"✅ Image prepared for Gemini: {img.size}")
                return img
                
            except Exception as e:
                logger.error(f"❌ Failed to prepare image for Gemini: {e}")
                raise
    
    @staticmethod
    def extract_text_from_image(file_path: str) -> str:
        """
        Extract text from image using OCR (optional feature)
        Requires pytesseract - not implemented in basic version
        
        Args:
            file_path: Path to the image
            
        Returns:
            str: Extracted text
        """
        # TODO: Implement OCR if needed
        logger.warning("OCR not implemented yet")
        return ""


# Create singleton instance
image_service = ImageService()