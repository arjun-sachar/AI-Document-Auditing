"""Knowledge base builder from document folders."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import hashlib
import uuid
from datetime import datetime

from .document_parser import DocumentParser
from .file_handlers import FileHandler


logger = logging.getLogger(__name__)


@dataclass
class DocumentEntry:
    """Represents a document entry in the knowledge base."""
    id: str
    title: str
    content: str
    file_path: str
    file_type: str
    file_size: int
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class KnowledgeBaseBuilder:
    """Builds knowledge bases from document folders."""
    
    def __init__(self):
        """Initialize knowledge base builder."""
        self.document_parser = DocumentParser()
        self.file_handler = FileHandler()
    
    def build_from_folder(
        self,
        folder_path: Union[str, Path],
        output_path: Union[str, Path],
        include_extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_file_size: int = 500 * 1024 * 1024,  # 500MB default (increased for large media files)
        recursive: bool = True
    ) -> Dict[str, Any]:
        """Build knowledge base from a folder of documents.
        
        Args:
            folder_path: Path to folder containing documents
            output_path: Path where knowledge base JSON will be saved
            include_extensions: List of file extensions to include (default: all supported)
            exclude_patterns: List of patterns to exclude (e.g., ['*draft*', '*temp*'])
            max_file_size: Maximum file size in bytes
            recursive: Whether to search subdirectories recursively
            
        Returns:
            Dictionary with build statistics and metadata
        """
        folder_path = Path(folder_path)
        output_path = Path(output_path)
        
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        logger.info(f"Building knowledge base from folder: {folder_path}")
        
        # Set default extensions if not provided
        if include_extensions is None:
            include_extensions = self.document_parser.get_supported_formats()
        
        # Find all supported documents
        documents = self._find_documents(
            folder_path, include_extensions, exclude_patterns, max_file_size, recursive
        )
        
        logger.info(f"Found {len(documents)} documents to process")
        
        # Process documents and build entries
        entries = []
        processed_count = 0
        error_count = 0
        file_type_stats = {}
        
        for doc_path in documents:
            try:
                entry = self._process_document(doc_path, folder_path)
                entries.append(entry)
                processed_count += 1
                
                # Track file type statistics
                file_ext = doc_path.suffix.lower()
                if file_ext not in file_type_stats:
                    file_type_stats[file_ext] = {'count': 0, 'total_size': 0, 'successful': 0, 'failed': 0}
                file_type_stats[file_ext]['count'] += 1
                file_type_stats[file_ext]['total_size'] += doc_path.stat().st_size
                file_type_stats[file_ext]['successful'] += 1
                
                logger.info(f"Processed: {doc_path.name} ({file_ext})")
                
            except Exception as e:
                logger.error(f"Error processing {doc_path}: {e}")
                error_count += 1
                
                # Track failed files
                file_ext = doc_path.suffix.lower()
                if file_ext not in file_type_stats:
                    file_type_stats[file_ext] = {'count': 0, 'total_size': 0, 'successful': 0, 'failed': 0}
                file_type_stats[file_ext]['count'] += 1
                file_type_stats[file_ext]['total_size'] += doc_path.stat().st_size
                file_type_stats[file_ext]['failed'] += 1
        
        # Create knowledge base structure
        knowledge_base = {
            'metadata': {
                'title': f"Knowledge Base from {folder_path.name}",
                'description': f"Automatically generated from {folder_path}",
                'total_entries': len(entries),
                'source_folder': str(folder_path),
                'created_at': datetime.now().isoformat(),
                'version': '1.0',
                'build_stats': {
                    'total_documents_found': len(documents),
                    'successfully_processed': processed_count,
                    'errors': error_count,
                    'supported_extensions': include_extensions,
                    'file_type_statistics': file_type_stats
                }
            },
            'entries': [asdict(entry) for entry in entries]
        }
        
        # Save knowledge base
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Knowledge base saved to: {output_path}")
        
        return knowledge_base['metadata']
    
    def _find_documents(
        self,
        folder_path: Path,
        include_extensions: List[str],
        exclude_patterns: Optional[List[str]],
        max_file_size: int,
        recursive: bool
    ) -> List[Path]:
        """Find all supported documents in folder.
        
        Args:
            folder_path: Path to search in
            include_extensions: Extensions to include
            exclude_patterns: Patterns to exclude
            max_file_size: Maximum file size
            recursive: Whether to search recursively
            
        Returns:
            List of document paths
        """
        documents = []
        
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        for file_path in folder_path.glob(pattern):
            if not file_path.is_file():
                continue
            
            # Check extension
            if file_path.suffix.lower() not in include_extensions:
                continue
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > max_file_size:
                size_mb = file_size / (1024 * 1024)
                max_size_mb = max_file_size / (1024 * 1024)
                logger.warning(
                    f"Skipping large file: {file_path.name} "
                    f"({size_mb:.1f} MB > {max_size_mb:.1f} MB limit). "
                    f"Use --max-size {int(file_size * 1.1)} to include this file."
                )
                continue
            
            # Check exclude patterns
            if exclude_patterns:
                should_exclude = False
                for pattern in exclude_patterns:
                    if file_path.match(pattern):
                        should_exclude = True
                        break
                if should_exclude:
                    continue
            
            documents.append(file_path)
        
        return sorted(documents)
    
    def _process_document(self, doc_path: Path, base_folder: Path) -> DocumentEntry:
        """Process a single document and create knowledge base entry.
        
        Args:
            doc_path: Path to document
            base_folder: Base folder for relative paths
            
        Returns:
            DocumentEntry object
        """
        # Parse document
        doc_data = self.document_parser.parse_document(doc_path)
        
        # Generate unique ID based on file path and content hash
        content_hash = hashlib.md5(doc_data['content'].encode()).hexdigest()[:8]
        relative_path = doc_path.relative_to(base_folder)
        entry_id = f"{relative_path.stem}_{content_hash}"
        
        # Extract title from filename or document metadata
        title = self._extract_title(doc_path, doc_data)
        
        # Create entry
        entry = DocumentEntry(
            id=entry_id,
            title=title,
            content=doc_data['content'],
            file_path=str(relative_path),
            file_type=doc_data['file_extension'],
            file_size=doc_data['file_size'],
            url=None,  # Could be set if documents have URLs
            metadata={
                'source_file': str(doc_path),
                'relative_path': str(relative_path),
                'parsing_method': doc_data.get('parsing_method', 'unknown'),
                'total_words': doc_data.get('total_words', 0),
                'document_metadata': doc_data.get('metadata', {}),
                'pages': doc_data.get('total_pages', 1),
                'paragraphs': doc_data.get('total_paragraphs', 0),
                'tables': doc_data.get('total_tables', 0)
            }
        )
        
        return entry
    
    def _extract_title(self, doc_path: Path, doc_data: Dict[str, Any]) -> str:
        """Extract title from document.
        
        Args:
            doc_path: Document path
            doc_data: Parsed document data
            
        Returns:
            Document title
        """
        # Try to get title from document metadata first
        metadata = doc_data.get('metadata', {})
        if metadata.get('title'):
            return metadata['title']
        
        # Try to extract from content (first heading or first line)
        content = doc_data.get('content', '')
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for markdown headers
            if line.startswith('#'):
                return line.lstrip('#').strip()
            
            # Check for all caps (likely title)
            if line.isupper() and len(line) > 10:
                return line.title()
            
            # Use first substantial line as title
            if len(line) > 20 and len(line) < 100:
                return line
        
        # Fall back to filename
        return doc_path.stem.replace('_', ' ').replace('-', ' ').title()
    
    def update_knowledge_base(
        self,
        knowledge_base_path: Union[str, Path],
        folder_path: Union[str, Path],
        force_update: bool = False
    ) -> Dict[str, Any]:
        """Update existing knowledge base with new documents.
        
        Args:
            knowledge_base_path: Path to existing knowledge base
            folder_path: Path to folder with new/updated documents
            force_update: Whether to reprocess all documents
            
        Returns:
            Update statistics
        """
        kb_path = Path(knowledge_base_path)
        folder_path = Path(folder_path)
        
        # Load existing knowledge base
        existing_entries = {}
        if kb_path.exists() and not force_update:
            with open(kb_path, 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
            
            # Index existing entries by file path
            for entry in kb_data.get('entries', []):
                file_path = entry.get('metadata', {}).get('relative_path', '')
                if file_path:
                    existing_entries[file_path] = entry
        
        # Build new knowledge base
        return self.build_from_folder(folder_path, kb_path)
    
    def get_folder_statistics(self, folder_path: Union[str, Path]) -> Dict[str, Any]:
        """Get statistics about documents in a folder.
        
        Args:
            folder_path: Path to folder
            
        Returns:
            Statistics dictionary
        """
        folder_path = Path(folder_path)
        
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        stats = {
            'total_files': 0,
            'supported_files': 0,
            'file_types': {},
            'total_size': 0,
            'supported_size': 0,
            'largest_file': None,
            'largest_file_size': 0
        }
        
        supported_extensions = self.document_parser.get_supported_formats()
        
        for file_path in folder_path.rglob('*'):
            if not file_path.is_file():
                continue
            
            stats['total_files'] += 1
            stats['total_size'] += file_path.stat().st_size
            
            file_ext = file_path.suffix.lower()
            stats['file_types'][file_ext] = stats['file_types'].get(file_ext, 0) + 1
            
            if file_path.stat().st_size > stats['largest_file_size']:
                stats['largest_file_size'] = file_path.stat().st_size
                stats['largest_file'] = str(file_path)
            
            if file_ext in supported_extensions:
                stats['supported_files'] += 1
                stats['supported_size'] += file_path.stat().st_size
        
        return stats
