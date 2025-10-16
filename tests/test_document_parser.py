"""Tests for document parsing functionality."""

import pytest
from pathlib import Path
from src.utils.document_parser import DocumentParser
from src.utils.file_handlers import FileHandler


class TestDocumentParser:
    """Test document parsing functionality."""
    
    def test_supported_formats(self):
        """Test supported file formats."""
        parser = DocumentParser()
        formats = parser.get_supported_formats()
        
        assert '.pdf' in formats
        assert '.docx' in formats
        assert '.doc' in formats
        assert '.txt' in formats
        assert '.md' in formats
        assert '.rtf' in formats
    
    def test_is_supported(self):
        """Test format support checking."""
        parser = DocumentParser()
        
        assert parser.is_supported("test.pdf")
        assert parser.is_supported("test.docx")
        assert parser.is_supported("test.doc")
        assert parser.is_supported("test.txt")
        assert parser.is_supported("test.md")
        assert parser.is_supported("test.rtf")
        
        assert not parser.is_supported("test.xyz")
        assert not parser.is_supported("test")
    
    def test_parse_text_file(self):
        """Test parsing of text files."""
        parser = DocumentParser()
        
        # Create a temporary text file
        test_content = "This is a test document.\nIt has multiple lines.\nWith some content."
        test_file = Path("test_document.txt")
        
        try:
            test_file.write_text(test_content)
            
            result = parser.parse_document(test_file)
            
            assert result['content'] == test_content
            assert result['file_extension'] == '.txt'
            assert result['total_words'] > 0
            assert result['parsing_method'] == 'direct_read'
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_extract_citations_from_text(self):
        """Test citation extraction from text document."""
        parser = DocumentParser()
        
        test_content = """
        According to research [Source 1], the findings show that 'climate change is real' [2].
        The study found that temperatures are rising [Source 3].
        """
        
        test_file = Path("test_citations.txt")
        
        try:
            test_file.write_text(test_content)
            
            citations = parser.extract_citations_from_document(test_file)
            
            assert len(citations) >= 3  # Should find at least 3 citations
            assert any("[Source 1]" in citation['text'] for citation in citations)
            assert any("[2]" in citation['text'] for citation in citations)
            assert any("[Source 3]" in citation['text'] for citation in citations)
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_context_extraction(self):
        """Test context extraction around citations."""
        parser = DocumentParser()
        
        test_content = "This is some context before the citation [Source 1] and some context after."
        test_file = Path("test_context.txt")
        
        try:
            test_file.write_text(test_content)
            
            citations = parser.extract_citations_from_document(test_file)
            
            assert len(citations) == 1
            citation = citations[0]
            assert "[Source 1]" in citation['text']
            assert "context before" in citation['context']
            assert "context after" in citation['context']
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_unsupported_format_error(self):
        """Test error handling for unsupported formats."""
        parser = DocumentParser()
        
        test_file = Path("test.unsupported")
        
        with pytest.raises(ValueError, match="Unsupported file format"):
            parser.parse_document(test_file)
    
    def test_nonexistent_file_error(self):
        """Test error handling for nonexistent files."""
        parser = DocumentParser()
        
        test_file = Path("nonexistent_file.txt")
        
        with pytest.raises(FileNotFoundError):
            parser.parse_document(test_file)


class TestFileHandlerDocumentSupport:
    """Test file handler document support."""
    
    def test_load_document_text(self):
        """Test loading text document through file handler."""
        handler = FileHandler()
        
        test_content = "This is a test document with some content."
        test_file = Path("test_handler.txt")
        
        try:
            test_file.write_text(test_content)
            
            result = handler.load_document(test_file)
            
            assert result['content'] == test_content
            assert result['file_extension'] == '.txt'
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_extract_text_from_document(self):
        """Test text extraction from document."""
        handler = FileHandler()
        
        test_content = "Simple test content for extraction."
        test_file = Path("test_extract.txt")
        
        try:
            test_file.write_text(test_content)
            
            extracted_text = handler.extract_text_from_document(test_file)
            
            assert extracted_text == test_content
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_extract_citations_from_document(self):
        """Test citation extraction from document."""
        handler = FileHandler()
        
        test_content = "Research shows [Source 1] that this is true [2]."
        test_file = Path("test_citations_handler.txt")
        
        try:
            test_file.write_text(test_content)
            
            citations = handler.extract_citations_from_document(test_file)
            
            assert len(citations) == 2
            assert any("[Source 1]" in citation['text'] for citation in citations)
            assert any("[2]" in citation['text'] for citation in citations)
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_is_document_supported(self):
        """Test document format support checking."""
        handler = FileHandler()
        
        assert handler.is_document_supported("test.pdf")
        assert handler.is_document_supported("test.docx")
        assert handler.is_document_supported("test.txt")
        assert not handler.is_document_supported("test.xyz")
    
    def test_get_supported_document_formats(self):
        """Test getting supported document formats."""
        handler = FileHandler()
        
        formats = handler.get_supported_document_formats()
        
        assert '.pdf' in formats
        assert '.docx' in formats
        assert '.txt' in formats
        assert '.md' in formats


# Note: Tests for PDF and DOCX parsing would require actual test files
# or mocking of the respective libraries. These tests focus on the
# text parsing functionality and the overall structure.
