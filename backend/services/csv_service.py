# backend/services/csv_service.py
"""CSV processing service with monitoring"""
import io
import urllib
import pandas as pd
from pathlib import Path
import logging
from typing import Dict, Any
from opentelemetry import trace
import requests

from monitoring.metrics import csv_rows_processed

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class CSVService:
    """Service for processing CSV files"""
    
    def __init__(self, upload_dir: str = "./uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
    
    async def parse_csv(self, file_path: str) -> pd.DataFrame:
        """Parse CSV file with basic tracking"""
        with tracer.start_as_current_span("parse_csv") as span:
            df = pd.read_csv(file_path)
            
            # Track metrics
            csv_rows_processed.inc(len(df))
            
            # Add basic span info
            span.set_attribute("rows", len(df))
            span.set_attribute("columns", len(df.columns))
            
            logger.info(f"Parsed CSV: {len(df)} rows, {len(df.columns)} cols")
            return df
    
    async def load_from_url(self, url: str) -> pd.DataFrame:
        """Load CSV from URL with automatic encoding detection and GitHub fix"""
        with tracer.start_as_current_span("load_csv_url") as span:
            if "github.com" in url and "blob" in url:
                url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
                logger.info(f"🪄 Converted GitHub URL to raw: {url}")

            span.set_attribute("url", url)

            try:
                df = pd.read_csv(url)
            except UnicodeDecodeError:
                logger.warning("⚠️ UTF-8 failed, retrying with latin1 encoding")
                df = pd.read_csv(url, encoding="latin1")

            csv_rows_processed.inc(len(df))
            span.set_attribute("rows", len(df))
            logger.info(f"✅ Loaded CSV: {len(df)} rows, {len(df.columns)} cols")
            return df


    
    async def analyze_csv(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get basic CSV statistics"""
        with tracer.start_as_current_span("analyze_csv"):
            return {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "dtypes": df.dtypes.astype(str).to_dict(),
                "missing_values": df.isnull().sum().to_dict(),
            }
    
    async def filter_csv(self, df: pd.DataFrame, conditions: Dict) -> pd.DataFrame:
        """Filter DataFrame based on conditions"""
        with tracer.start_as_current_span("filter_csv") as span:
            original_rows = len(df)
            filtered_df = df.copy()
            
            for column, value in conditions.items():
                if column in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df[column] == value]
            
            span.set_attribute("original_rows", original_rows)
            span.set_attribute("filtered_rows", len(filtered_df))
            
            csv_rows_processed.inc(len(filtered_df), {"operation": "filter"})
            return filtered_df


csv_service = CSVService()