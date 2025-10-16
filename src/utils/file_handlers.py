"""File handling utilities."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import yaml
from .document_parser import DocumentParser


logger = logging.getLogger(__name__)


class FileHandler:
    """Handles file I/O operations for the system."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize file handler.
        
        Args:
            base_path: Base path for file operations
        """
        self.base_path = base_path or Path.cwd()
        self.document_parser = DocumentParser()
    
    def load_json(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load JSON data from file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Loaded JSON data
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded JSON data from {path}")
            return data
        except Exception as e:
            logger.error(f"Error loading JSON from {path}: {e}")
            raise
    
    def save_json(
        self,
        data: Dict[str, Any],
        file_path: Union[str, Path],
        indent: int = 2
    ) -> None:
        """Save data as JSON file.
        
        Args:
            data: Data to save
            file_path: Path to save file
            indent: JSON indentation
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path
        
        # Create directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            logger.info(f"Saved JSON data to {path}")
        except Exception as e:
            logger.error(f"Error saving JSON to {path}: {e}")
            raise
    
    def load_yaml(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load YAML data from file.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Loaded YAML data
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            logger.info(f"Loaded YAML data from {path}")
            return data
        except Exception as e:
            logger.error(f"Error loading YAML from {path}: {e}")
            raise
    
    def save_yaml(
        self,
        data: Dict[str, Any],
        file_path: Union[str, Path]
    ) -> None:
        """Save data as YAML file.
        
        Args:
            data: Data to save
            file_path: Path to save file
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path
        
        # Create directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
            logger.info(f"Saved YAML data to {path}")
        except Exception as e:
            logger.error(f"Error saving YAML to {path}: {e}")
            raise
    
    def load_text(self, file_path: Union[str, Path]) -> str:
        """Load text from file.
        
        Args:
            file_path: Path to text file
            
        Returns:
            File content as string
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Loaded text from {path}")
            return content
        except Exception as e:
            logger.error(f"Error loading text from {path}: {e}")
            raise
    
    def save_text(
        self,
        content: str,
        file_path: Union[str, Path]
    ) -> None:
        """Save text to file.
        
        Args:
            content: Text content to save
            file_path: Path to save file
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path
        
        # Create directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Saved text to {path}")
        except Exception as e:
            logger.error(f"Error saving text to {path}: {e}")
            raise
    
    def file_exists(self, file_path: Union[str, Path]) -> bool:
        """Check if file exists.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file exists, False otherwise
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path
        
        return path.exists()
    
    def create_directory(self, dir_path: Union[str, Path]) -> None:
        """Create directory if it doesn't exist.
        
        Args:
            dir_path: Path to directory
        """
        path = Path(dir_path)
        if not path.is_absolute():
            path = self.base_path / path
        
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {path}")
    
    def list_files(
        self,
        dir_path: Union[str, Path],
        pattern: str = "*",
        recursive: bool = False
    ) -> List[Path]:
        """List files in directory.
        
        Args:
            dir_path: Directory path
            pattern: File pattern to match
            recursive: Whether to search recursively
            
        Returns:
            List of matching file paths
        """
        path = Path(dir_path)
        if not path.is_absolute():
            path = self.base_path / path
        
        if not path.exists():
            logger.warning(f"Directory does not exist: {path}")
            return []
        
        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))
        
        # Filter to only include files (not directories)
        files = [f for f in files if f.is_file()]
        
        logger.info(f"Found {len(files)} files matching pattern '{pattern}' in {path}")
        return files
    
    def get_file_size(self, file_path: Union[str, Path]) -> int:
        """Get file size in bytes.
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in bytes
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path
        
        if not path.exists():
            logger.warning(f"File does not exist: {path}")
            return 0
        
        return path.stat().st_size
    
    def backup_file(self, file_path: Union[str, Path]) -> Path:
        """Create backup of file.
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            Path to backup file
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path
        
        if not path.exists():
            raise FileNotFoundError(f"File does not exist: {path}")
        
        # Create backup filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.with_suffix(f".backup_{timestamp}{path.suffix}")
        
        # Copy file
        import shutil
        shutil.copy2(path, backup_path)
        
        logger.info(f"Created backup: {backup_path}")
        return backup_path
    
    def load_document(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load document and extract text content.
        
        Args:
            file_path: Path to document file
            
        Returns:
            Dictionary with parsed content and metadata
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path
        
        try:
            result = self.document_parser.parse_document(path)
            logger.info(f"Loaded document from {path}")
            return result
        except Exception as e:
            logger.error(f"Error loading document from {path}: {e}")
            raise
    
    def extract_text_from_document(self, file_path: Union[str, Path]) -> str:
        """Extract text content from document.
        
        Args:
            file_path: Path to document file
            
        Returns:
            Extracted text content
        """
        document_data = self.load_document(file_path)
        return document_data.get('content', '')
    
    def extract_citations_from_document(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Extract citations from document with location information.
        
        Args:
            file_path: Path to document file
            
        Returns:
            List of citations with location data
        """
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path
        
        try:
            citations = self.document_parser.extract_citations_from_document(path)
            logger.info(f"Extracted {len(citations)} citations from {path}")
            return citations
        except Exception as e:
            logger.error(f"Error extracting citations from {path}: {e}")
            raise
    
    def is_document_supported(self, file_path: Union[str, Path]) -> bool:
        """Check if document format is supported.
        
        Args:
            file_path: Path to document file
            
        Returns:
            True if format is supported
        """
        return self.document_parser.is_supported(file_path)
    
    def get_supported_document_formats(self) -> List[str]:
        """Get list of supported document formats.
        
        Returns:
            List of supported file extensions
        """
        return self.document_parser.get_supported_formats()


# Convenience functions
def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Load JSON data from file (convenience function)."""
    handler = FileHandler()
    return handler.load_json(file_path)


def save_json(
    data: Dict[str, Any],
    file_path: Union[str, Path],
    indent: int = 2
) -> None:
    """Save data as JSON file (convenience function)."""
    handler = FileHandler()
    handler.save_json(data, file_path, indent)


def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Load YAML data from file (convenience function)."""
    handler = FileHandler()
    return handler.load_yaml(file_path)


def save_yaml(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """Save data as YAML file (convenience function)."""
    handler = FileHandler()
    handler.save_yaml(data, file_path)


def load_text(file_path: Union[str, Path]) -> str:
    """Load text from file (convenience function)."""
    handler = FileHandler()
    return handler.load_text(file_path)


def save_text(content: str, file_path: Union[str, Path]) -> None:
    """Save text to file (convenience function)."""
    handler = FileHandler()
    handler.save_text(content, file_path)


def load_document(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Load document and extract content (convenience function)."""
    handler = FileHandler()
    return handler.load_document(file_path)


def extract_text_from_document(file_path: Union[str, Path]) -> str:
    """Extract text from document (convenience function)."""
    handler = FileHandler()
    return handler.extract_text_from_document(file_path)


def extract_citations_from_document(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Extract citations from document (convenience function)."""
    handler = FileHandler()
    return handler.extract_citations_from_document(file_path)
