# AI Document Auditing System

A comprehensive document validation processor that generates articles from knowledge bases and validates citations, quotes, and context using NLP and LLM techniques. This system provides confidence scores for citation accuracy and helps identify potential hallucination in AI-generated content.

## 🎯 Project Overview

The AI Document Auditing System is designed to address the critical need for validating AI-generated content, particularly focusing on:

- **Citation Accuracy**: Verifying that citations are word-for-word accurate with LLM-powered validation
- **Context Validation**: Ensuring quotes are not taken out of context or misused
- **Hallucination Detection**: Identifying when AI models generate false or unsupported claims
- **Confidence Scoring**: Providing quantitative measures of document reliability (0-100%)
- **Multi-Format Support**: Process articles from PDF, Word, PowerPoint, audio (M4A, MP3, WAV), video, and other formats
- **Source Excerpt Extraction**: Automatically extract relevant passages from sources to verify citations
- **Article Quality Control**: Validate prompt separation, quote formatting, word count compliance, and context ratings

## ✨ Key Features

### Smart Citation Validation
- **Direct Quote Focus**: Only validates actual quoted text, ignoring references and attributions for efficiency
- **Intelligent Quote Matching**: Uses multiple strategies (exact match, partial match, key word matching) to find quotes in sources
- **Source Context Extraction**: Automatically extracts 2-4 sentences from sources showing quotes in their original context
- **Visual Confidence Indicators**: Color-coded highlights (green=high, yellow=medium, red=low confidence) in the UI

### Article Generation Quality
- **Strict Word Count Enforcement**: Regenerates articles up to 3 times to meet target word count ranges
- **Minimum Quote Length**: Enforces 20-80 word quotes for substantial context
- **Meta Statement Removal**: Automatically removes "Here is..." and "Word count:" statements
- **Prompt Leakage Detection**: Validates that generated articles don't include prompt instructions
- **Quote Formatting Validation**: Ensures proper quotation marks and source references

### Interactive UI
- **Click-to-View Details**: Click on highlighted citations to see detailed validation information
- **Source Excerpts**: View the original source context alongside article usage
- **Context Rating Breakdown**: Hover over ratings to see detailed scoring breakdown
- **Verified Badges**: See which citations have LLM-verified source excerpts
- **ESC Key Support**: Quick close for citation details panel

## 🏗️ Project Structure

```
AI-Document-Auditing/
├── README.md                          # This file
├── environment.yml                    # Conda environment configuration
├── requirements.txt                   # Python package dependencies
├── backend_server.py                  # FastAPI backend server
├── run_cli.py                         # CLI runner script
├── quick_start.py                     # Quick setup script
├── config/
│   ├── __init__.py
│   ├── settings.py                   # Application settings
│   └── model_config.yaml             # LLM model configurations
├── src/
│   ├── __init__.py
│   ├── article_generator/            # Article generation modules
│   │   ├── __init__.py
│   │   ├── generator.py              # Main article generation logic
│   │   ├── knowledge_base.py         # Knowledge base integration
│   │   └── prompt_templates.py       # Prompt templates for article generation
│   ├── validation/                   # Document validation modules
│   │   ├── __init__.py
│   │   ├── citation_validator.py     # Citation accuracy validation
│   │   ├── context_validator.py      # Context and quote validation
│   │   ├── nlp_processor.py          # NLP preprocessing and analysis
│   │   └── confidence_scorer.py      # Confidence scoring algorithms
│   ├── llm/                          # LLM integration modules
│   │   ├── __init__.py
│   │   ├── anthropic_client.py       # Anthropic API client
│   │   ├── model_selector.py         # Model selection and configuration
│   │   └── response_parser.py        # LLM response parsing and processing
│   ├── utils/                        # Utility modules
│   │   ├── __init__.py
│   │   ├── text_processing.py        # Text preprocessing utilities
│   │   ├── file_handlers.py          # File I/O operations
│   │   ├── document_parser.py        # Document parsing utilities
│   │   ├── knowledge_base_builder.py # Knowledge base building utilities
│   │   └── logging_config.py         # Logging configuration
│   └── cli/                          # Command-line interface
│       ├── __init__.py
│       ├── main.py                   # Main CLI entry point
│       ├── generate_command.py       # Article generation command
│       ├── validate_command.py       # Document validation command
│       └── build_command.py          # Knowledge base building command
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── test_document_parser.py       # Document parsing tests
│   ├── test_validator.py             # Validation tests
│   └── test_llm_integration.py       # LLM integration tests
├── examples/                         # Example usage and sample data
│   ├── sample_knowledge_base.json    # Sample knowledge base
│   ├── sample_article.md             # Sample generated article
│   ├── sample_research_paper.txt     # Sample research paper
│   └── build_knowledge_base_example.py # Knowledge base building example
├── frontend/                         # Next.js frontend application
│   ├── src/
│   │   ├── app/                      # Next.js app directory
│   │   ├── components/               # React components
│   │   ├── lib/                      # Utility libraries
│   │   ├── stores/                   # State management
│   │   └── types/                    # TypeScript type definitions
│   ├── package.json                  # Frontend dependencies
│   └── next.config.ts                # Next.js configuration
├── data/                             # Data directory (ignored in git)
│   ├── knowledge_bases/              # Knowledge base files
│   ├── generated_articles/           # Generated articles (empty)
│   ├── validation_results/           # Validation results (empty)
│   └── logs/                         # Application logs (empty)
└── "White Papers, Studies, POVs, Conference Pres"/ # Sample documents
    └── [various document files]
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- Conda package manager
- Git

### Installation

#### Option 1: Automated Installation (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd AI-Document-Auditing

# Run the automated installation script
python install_dependencies.py
```

#### Option 2: Manual Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd AI-Document-Auditing
   ```

2. **Create and activate conda environment:**
   ```bash
   conda env create -f environment.yml
   conda activate ai-document-auditing
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

5. **Configure the system:**
   ```bash
   cp config/model_config.yaml.example config/model_config.yaml
   # Edit the configuration file with your API keys and preferences
   ```

### Basic Usage

#### Option 1: Web Interface (Recommended)
```bash
# Quick start with automated script
./start_dev.sh

# OR manually start both servers:
# Start the backend server
python backend_server.py

# In another terminal, start the frontend
cd frontend
npm run dev
```
Then visit `http://localhost:3000` to use the web interface.

#### Option 2: Command Line Interface

**Build Knowledge Base from Document Folder:**
```bash
# Build from your White Papers folder
python -m src.cli.main build \
    --folder "White Papers, Studies, POVs, Conference Pres" \
    --output data/knowledge_bases/white_papers.json

# Build only PDF and DOCX files
python -m src.cli.main build \
    --folder documents/ \
    --output knowledge_bases/research.json \
    --extensions pdf,docx
```

**Generate an Article from Knowledge Base:**
```bash
python -m src.cli.main generate \
    --knowledge-base data/knowledge_bases/white_papers.json \
    --topic "AI Research Trends" \
    --output data/generated_articles/research_article.md
```

**Validate Citations and Context:**
```bash
# Validate from various document formats
python -m src.cli.main validate \
    --article data/generated_articles/climate_article.pdf \
    --knowledge-base examples/sample_knowledge_base.json \
    --output data/validation_results/validation_report.json

# Also supports DOCX, DOC, TXT, MD, RTF formats
python -m src.cli.main validate \
    --article research_paper.docx \
    --knowledge-base examples/sample_knowledge_base.json
```

## 📦 Key Dependencies

### Core NLP Libraries
- **spaCy**: Advanced natural language processing for text analysis
- **transformers**: Hugging Face transformers for local LLM integration
- **sentence-transformers**: Semantic similarity calculations for context validation
- **nltk**: Natural language toolkit for text preprocessing

### LLM Integration
- **anthropic**: Anthropic API client (using open-source alternatives via OpenRouter)
- **openai**: Alternative LLM providers
- **requests**: HTTP client for API communications

### Data Processing
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **pydantic**: Data validation and settings management
- **pyyaml**: Configuration file parsing

### Document Parsing
- **PyPDF2**: PDF document parsing and text extraction
- **python-docx**: Microsoft Word document processing
- **python-pptx**: PowerPoint presentation processing and slide extraction
- **striprtf**: RTF document text extraction
- **SpeechRecognition**: Audio transcript extraction from audio files
- **moviepy**: Video processing and audio extraction
- **pydub**: Audio format conversion and processing

### Validation & Scoring
- **scikit-learn**: Machine learning algorithms for confidence scoring
- **fuzzywuzzy**: Fuzzy string matching for citation validation
- **textstat**: Readability and complexity metrics

### CLI & Utilities
- **click**: Command-line interface framework
- **rich**: Rich text and beautiful formatting in terminal
- **loguru**: Advanced logging capabilities

## 🔧 Configuration

The system uses YAML configuration files for flexible setup:

- **Model Configuration**: LLM model selection, API endpoints, and parameters
- **Validation Settings**: Confidence thresholds, validation criteria, and scoring weights
- **Knowledge Base Settings**: Data sources, indexing options, and search parameters

## 🏗️ Knowledge Base Building

### Automatic Document Processing
The system can automatically build knowledge bases from folders containing various document formats:

1. **Multi-Format Support**: Process PDF, DOCX, DOC, TXT, MD, and RTF files
2. **Metadata Extraction**: Extract document titles, authors, creation dates, and other metadata
3. **Content Processing**: Parse and clean document content for optimal search and citation
4. **Smart Filtering**: Exclude drafts, temporary files, and files over size limits
5. **Recursive Search**: Process documents in subdirectories automatically

### Build Options
- **File Type Filtering**: Include only specific file extensions
- **Pattern Exclusion**: Exclude files matching certain patterns (e.g., *draft*, *temp*)
- **Size Limits**: Skip files larger than specified size
- **Update Mode**: Update existing knowledge bases with new documents

## 🧪 Validation Algorithms

### Citation Validation
The system uses a sophisticated **LLM-driven validation pipeline** that focuses on direct quotes:

1. **Direct Quote Filtering**: Only validates direct quotations (quoted_text type), skipping other citation types for efficiency
2. **LLM-Powered Verification**: Uses Claude 3.5 Haiku to validate each quote against source material
3. **Source Excerpt Extraction**: Automatically extracts 2-4 sentences from the source showing the quote in context
4. **Multi-Strategy Quote Matching**:
   - Exact match (case-insensitive)
   - Partial match (first 30 characters)
   - Key word matching for flexible comparison
5. **Context Alignment Scoring**: Evaluates how well the article context aligns with the source's original meaning
6. **Verbatim Validation**: Checks if quotes match source wording exactly (with minor formatting differences allowed)

### Confidence Scoring
- **LLM-Generated Scores**: Confidence scores are generated by the LLM based on quote accuracy, source verification, and context alignment
- **Composite Score Calculation**: Weighted average of:
  - Citation Accuracy (40%): Precision of direct quotes
  - Context Preservation (30%): Maintains original meaning
  - Source Reliability (20%): Source quality and credibility
  - Scholarly Coherence (10%): Logical flow and argumentation
- **Threshold-based Classification**: 
  - High confidence (≥80%): Green indicator
  - Medium confidence (60-79%): Yellow indicator
  - Low confidence (<60%): Red indicator
- **Risk Factor Identification**: Automatic flagging of potential issues like missing sources, low-confidence citations, or context misalignment
- **Detailed Reporting**: Granular breakdown with source excerpts, article context, and validation insights

## 📄 Supported Document Formats

The system can process articles from various document formats:

### Input Formats (for validation and knowledge base building)
- **PDF** (.pdf) - Academic papers, reports, research documents
- **Microsoft Word** (.docx, .doc) - Research papers, articles, documents
- **Microsoft PowerPoint** (.pptx, .ppt) - Presentations, slides, conference materials
- **Plain Text** (.txt) - Simple text documents
- **Markdown** (.md) - Formatted text documents
- **Rich Text Format** (.rtf) - Formatted documents
- **OpenDocument** (.odt) - OpenDocument text files
- **Audio Files** (.mp3, .wav, .m4a) - Audio recordings with transcript extraction
- **Video Files** (.mp4, .mov, .avi) - Video recordings with audio transcript extraction
- **Archive Files** (.zip, .rar, .7z) - Compressed folders containing multiple documents
- **Folder Upload** - Upload entire directories with all contained files

### Output Formats
- **Markdown** (.md) - Generated articles with proper formatting
- **JSON** (.json) - Validation results and metadata
- **Plain Text** (.txt) - Extracted text content

### Document Processing Features
- **Multi-page PDF support** - Extract text from all pages with metadata
- **PowerPoint slide extraction** - Extract text from all slides and shapes
- **Audio transcript extraction** - Convert audio files to text using speech recognition
- **Video transcript extraction** - Extract audio from videos and convert to text
- **Metadata extraction** - Author, title, creation date, etc. from all formats
- **Page/slide/paragraph tracking** - Citations linked to specific locations
- **File type statistics** - Detailed processing statistics for each file type
- **Table extraction** - Process tabular data in documents
- **Format preservation** - Maintain document structure where possible
- **Archive extraction** - Automatically extract and process files from ZIP, RAR, and 7Z archives
- **Folder upload** - Upload entire directories with all contained files
- **Batch processing** - Process multiple files simultaneously for efficient knowledge base building

## 📊 Output Formats

### Validation Reports
- **JSON format** with structured validation results including:
  - Overall confidence score (0.0-1.0)
  - Individual citation validation results with:
    - `source_found`: Whether the source exists
    - `confidence`: LLM-generated confidence score
    - `quote_verbatim`: Whether quote matches source exactly
    - `context_alignment`: How well context aligns (0.0-1.0)
    - `source_excerpt`: 2-4 sentences from source showing quote in context
    - `article_excerpt`: Article context around the citation
  - Risk factors and recommendations
  - Citation accuracy and context preservation scores
  - Article validation report (prompt leakage, quote formatting, word count compliance)

### Article Generation
- **Markdown format** with proper citation formatting:
  - Direct quotes in the format: `"full quote text" [Source X]`
  - Minimum 20-80 word quotes for substantial context
  - Natural integration with transitional phrases
- **Structured metadata** including:
  - Word count (calculated with regex for accuracy)
  - Citation count and sources used
  - Overall context rating and detailed breakdown
  - Generation prompt and validation results
  - Article-level validation (prompt separation, quote formatting, context rating sanity checks)

## 🧪 Testing

Run the test suite:
```bash
pytest tests/ -v
```

Run specific test categories:
```bash
pytest tests/test_validator.py -v
pytest tests/test_llm_integration.py -v
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Anthropic for LLM research and development
- Hugging Face for open-source transformer models
- The open-source NLP community for tools and libraries

## 📞 Support

For questions, issues, or contributions, please:
- Open an issue on GitHub
- Check the documentation in the `docs/` directory
- Review example usage in the `examples/` directory
