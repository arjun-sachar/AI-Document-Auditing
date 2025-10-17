"""Knowledge base integration and management."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re


logger = logging.getLogger(__name__)


@dataclass
class KnowledgeEntry:
    """Represents a single knowledge base entry."""
    id: str
    title: str
    content: str
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class KnowledgeBase:
    """Manages knowledge base operations and search functionality."""
    
    def __init__(self, knowledge_base_path: Path):
        """Initialize knowledge base from file.
        
        Args:
            knowledge_base_path: Path to knowledge base JSON file
        """
        self.knowledge_base_path = knowledge_base_path
        self.entries: List[KnowledgeEntry] = []
        self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> None:
        """Load knowledge base entries from file."""
        if not self.knowledge_base_path.exists():
            logger.warning(f"Knowledge base file not found: {self.knowledge_base_path}")
            return
        
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                # List of entries
                for entry_data in data:
                    entry = KnowledgeEntry(
                        id=entry_data.get('id', ''),
                        title=entry_data.get('title', ''),
                        content=entry_data.get('content', ''),
                        url=entry_data.get('url'),
                        metadata=entry_data.get('metadata', {})
                    )
                    self.entries.append(entry)
            elif isinstance(data, dict) and 'entries' in data:
                # Structured format with entries key
                for entry_data in data['entries']:
                    entry = KnowledgeEntry(
                        id=entry_data.get('id', ''),
                        title=entry_data.get('title', ''),
                        content=entry_data.get('content', ''),
                        url=entry_data.get('url'),
                        metadata=entry_data.get('metadata', {})
                    )
                    self.entries.append(entry)
            
            logger.info(f"Loaded {len(self.entries)} knowledge base entries")
            
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            raise
    
    def search(
        self,
        query: str,
        max_results: int = 10,
        min_relevance: float = 0.1
    ) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant entries.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            min_relevance: Minimum relevance score threshold
            
        Returns:
            List of relevant entries with relevance scores
        """
        logger.debug(f"Searching knowledge base for query: {query}")
        if not self.entries:
            logger.warning("No entries in knowledge base")
            return []
        
        # Simple keyword-based search (in a real implementation, this would use
        # more sophisticated techniques like TF-IDF, embeddings, etc.)
        query_lower = query.lower()
        query_words = set(query_lower.split())

        if not query_words:
            logger.warning("Empty query provided - returning all entries")
            results = [
                {
                    'id': entry.id,
                    'title': entry.title,
                    'content': entry.content,
                    'url': entry.url,
                    'metadata': entry.metadata,
                    'relevance_score': 1.0
                }
                for entry in self.entries[:max_results]
            ]
            return results
        
        scored_entries = []
        
        for entry in self.entries:
            # Calculate relevance score based on keyword matches
            logger.debug(f"Calculating relevance score for entry: {entry.title}")
            title_matches = sum(1 for word in query_words if word in entry.title.lower())
            logger.debug(f"Title matches: {title_matches}")
            content_matches = sum(1 for word in query_words if word in entry.content.lower())
            logger.debug(f"Content matches: {content_matches}")
            # Weight title matches more heavily
            logger.debug(f"Query words: {query_words}")
            relevance_score = (title_matches * 3 + content_matches) / len(query_words)
            
            if relevance_score >= min_relevance:
                entry_dict = {
                    'id': entry.id,
                    'title': entry.title,
                    'content': entry.content,
                    'url': entry.url,
                    'metadata': entry.metadata,
                    'relevance_score': relevance_score
                }
                scored_entries.append(entry_dict)
        
        # Sort by relevance score (descending)
        scored_entries.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Return top results
        results = scored_entries[:max_results]
        logger.info(f"Found {len(results)} relevant entries for query: {query}")
        
        return results
    
    def get_entry_by_id(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Get a specific entry by ID.
        
        Args:
            entry_id: Entry identifier
            
        Returns:
            Knowledge entry or None if not found
        """
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None
    
    def add_entry(
        self,
        title: str,
        content: str,
        url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a new entry to the knowledge base.
        
        Args:
            title: Entry title
            content: Entry content
            url: Optional URL
            metadata: Optional metadata
            
        Returns:
            Generated entry ID
        """
        # Generate unique ID
        entry_id = f"entry_{len(self.entries) + 1}_{hash(title) % 10000}"
        
        entry = KnowledgeEntry(
            id=entry_id,
            title=title,
            content=content,
            url=url,
            metadata=metadata or {}
        )
        
        self.entries.append(entry)
        logger.info(f"Added new entry: {title}")
        
        return entry_id
    
    def save_knowledge_base(self, output_path: Optional[Path] = None) -> None:
        """Save knowledge base to file.
        
        Args:
            output_path: Optional output path (uses original path if not provided)
        """
        save_path = output_path or self.knowledge_base_path
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert entries to dictionary format
        entries_data = []
        for entry in self.entries:
            entry_dict = {
                'id': entry.id,
                'title': entry.title,
                'content': entry.content,
                'url': entry.url,
                'metadata': entry.metadata
            }
            entries_data.append(entry_dict)
        
        knowledge_base_data = {
            'metadata': {
                'total_entries': len(self.entries),
                'created_at': '2024-01-01T00:00:00Z',  # Would be actual timestamp
                'version': '1.0'
            },
            'entries': entries_data
        }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(knowledge_base_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved knowledge base to {save_path}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_entries = len(self.entries)
        total_content_length = sum(len(entry.content) for entry in self.entries)
        entries_with_urls = sum(1 for entry in self.entries if entry.url)
        
        return {
            'total_entries': total_entries,
            'total_content_length': total_content_length,
            'entries_with_urls': entries_with_urls,
            'average_content_length': total_content_length / total_entries if total_entries > 0 else 0
        }
