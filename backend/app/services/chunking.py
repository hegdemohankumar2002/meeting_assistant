"""
Intelligent text chunking service for processing long transcripts.
Provides multiple chunking strategies optimized for different use cases.
"""

import re
from typing import List, Dict, Tuple
import tiktoken


class TextChunker:
    """Handles intelligent text chunking with multiple strategies."""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """
        Initialize the text chunker.
        
        Args:
            model_name: Model name for token counting (default: gpt-3.5-turbo)
        """
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except Exception:
            # Fallback to cl100k_base encoding if model not found
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.
        
        Args:
            text: Input text
            
        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))
    
    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using regex.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting - handles most cases
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def chunk_by_tokens(
        self, 
        text: str, 
        max_tokens: int = 1000, 
        overlap_tokens: int = 100
    ) -> List[Dict[str, any]]:
        """
        Chunk text by token count with overlap for context preservation.
        
        Args:
            text: Input text to chunk
            max_tokens: Maximum tokens per chunk
            overlap_tokens: Number of tokens to overlap between chunks
            
        Returns:
            List of chunk dictionaries with 'text', 'start_idx', 'end_idx', 'token_count'
        """
        sentences = self.split_into_sentences(text)
        chunks = []
        current_chunk = []
        current_tokens = 0
        start_idx = 0
        
        for i, sentence in enumerate(sentences):
            sentence_tokens = self.count_tokens(sentence)
            
            # If single sentence exceeds max_tokens, split it further
            if sentence_tokens > max_tokens:
                # Save current chunk if it exists
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunks.append({
                        "text": chunk_text,
                        "start_idx": start_idx,
                        "end_idx": i - 1,
                        "token_count": current_tokens
                    })
                    current_chunk = []
                    current_tokens = 0
                
                # Split long sentence by words
                words = sentence.split()
                word_chunk = []
                word_tokens = 0
                
                for word in words:
                    word_token_count = self.count_tokens(word + " ")
                    if word_tokens + word_token_count > max_tokens and word_chunk:
                        chunk_text = " ".join(word_chunk)
                        chunks.append({
                            "text": chunk_text,
                            "start_idx": i,
                            "end_idx": i,
                            "token_count": word_tokens
                        })
                        word_chunk = []
                        word_tokens = 0
                    
                    word_chunk.append(word)
                    word_tokens += word_token_count
                
                if word_chunk:
                    chunk_text = " ".join(word_chunk)
                    chunks.append({
                        "text": chunk_text,
                        "start_idx": i,
                        "end_idx": i,
                        "token_count": word_tokens
                    })
                
                start_idx = i + 1
                continue
            
            # Check if adding this sentence exceeds max_tokens
            if current_tokens + sentence_tokens > max_tokens and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "start_idx": start_idx,
                    "end_idx": i - 1,
                    "token_count": current_tokens
                })
                
                # Start new chunk with overlap
                # Keep last few sentences for context
                overlap_sentences = []
                overlap_token_count = 0
                for j in range(len(current_chunk) - 1, -1, -1):
                    sent_tokens = self.count_tokens(current_chunk[j])
                    if overlap_token_count + sent_tokens <= overlap_tokens:
                        overlap_sentences.insert(0, current_chunk[j])
                        overlap_token_count += sent_tokens
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_tokens = overlap_token_count
                start_idx = i - len(overlap_sentences)
            
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "start_idx": start_idx,
                "end_idx": len(sentences) - 1,
                "token_count": current_tokens
            })
        
        return chunks
    
    def chunk_by_words(
        self, 
        text: str, 
        max_words: int = 1000, 
        overlap_words: int = 100
    ) -> List[Dict[str, any]]:
        """
        Chunk text by word count (simpler, faster than token-based).
        
        Args:
            text: Input text to chunk
            max_words: Maximum words per chunk
            overlap_words: Number of words to overlap between chunks
            
        Returns:
            List of chunk dictionaries with 'text', 'word_count'
        """
        words = text.split()
        chunks = []
        
        i = 0
        while i < len(words):
            # Get chunk of max_words
            chunk_words = words[i:i + max_words]
            chunk_text = " ".join(chunk_words)
            
            chunks.append({
                "text": chunk_text,
                "word_count": len(chunk_words),
                "token_count": self.count_tokens(chunk_text)
            })
            
            # Move forward by (max_words - overlap_words)
            i += max_words - overlap_words
            
            # Prevent infinite loop
            if max_words <= overlap_words:
                break
        
        return chunks
    
    def smart_chunk(
        self, 
        text: str, 
        max_tokens: int = 1000,
        strategy: str = "token"
    ) -> List[str]:
        """
        Smart chunking that respects sentence boundaries.
        
        Args:
            text: Input text
            max_tokens: Maximum tokens per chunk
            strategy: "token" or "word" based chunking
            
        Returns:
            List of text chunks
        """
        if strategy == "token":
            chunks = self.chunk_by_tokens(text, max_tokens=max_tokens)
        else:
            # Convert max_tokens to approximate words (1 token ≈ 0.75 words)
            max_words = int(max_tokens * 0.75)
            overlap_words = int(max_words * 0.1)  # 10% overlap
            chunks = self.chunk_by_words(text, max_words=max_words, overlap_words=overlap_words)
        
        return [chunk["text"] for chunk in chunks]


# Singleton instance for reuse
_chunker_instance = None

def get_chunker(model_name: str = "gpt-3.5-turbo") -> TextChunker:
    """Get or create a TextChunker instance."""
    global _chunker_instance
    if _chunker_instance is None:
        _chunker_instance = TextChunker(model_name)
    return _chunker_instance
