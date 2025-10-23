# backend/utils/text_splitter.py
"""
Text chunking utilities for RAG
"""
from typing import List
import re


class TextSplitter:
    """Split text into chunks for embedding"""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separator: str = "\n\n"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Input text
            
        Returns:
            List of text chunks
        """
        # Split by separator
        splits = text.split(self.separator)
        
        # Merge small splits and create chunks
        chunks = []
        current_chunk = ""
        
        for split in splits:
            # If adding this split exceeds chunk size
            if len(current_chunk) + len(split) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # Keep overlap
                    current_chunk = current_chunk[-self.chunk_overlap:] if self.chunk_overlap > 0 else ""
                
                # If single split is larger than chunk size, split it further
                if len(split) > self.chunk_size:
                    # Split by sentences
                    sentences = re.split(r'(?<=[.!?])\s+', split)
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) > self.chunk_size:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                                current_chunk = sentence
                        else:
                            current_chunk += " " + sentence
                else:
                    current_chunk = split
            else:
                current_chunk += self.separator + split
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return [c for c in chunks if c]  # Remove empty chunks


class RecursiveTextSplitter(TextSplitter):
    """
    Split text recursively with multiple separators
    Useful for structured documents
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        super().__init__(chunk_size, chunk_overlap)
        # Try separators in order: paragraphs, sentences, words
        self.separators = ["\n\n", "\n", ". ", " "]
    
    def split_text(self, text: str) -> List[str]:
        """Split text recursively"""
        return self._split_recursive(text, self.separators)
    
    def _split_recursive(self, text: str, separators: List[str]) -> List[str]:
        """Recursive splitting logic"""
        if not separators or len(text) <= self.chunk_size:
            return [text] if text else []
        
        separator = separators[0]
        remaining_separators = separators[1:]
        
        splits = text.split(separator)
        chunks = []
        current_chunk = ""
        
        for split in splits:
            if len(current_chunk) + len(split) + len(separator) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # Keep overlap
                    if self.chunk_overlap > 0:
                        overlap_text = current_chunk[-self.chunk_overlap:]
                        current_chunk = overlap_text + separator + split
                    else:
                        current_chunk = split
                else:
                    # Split is too large, use next separator
                    if len(split) > self.chunk_size:
                        sub_chunks = self._split_recursive(split, remaining_separators)
                        chunks.extend(sub_chunks)
                    else:
                        current_chunk = split
            else:
                if current_chunk:
                    current_chunk += separator + split
                else:
                    current_chunk = split
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks