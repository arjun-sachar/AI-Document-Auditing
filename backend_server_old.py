#!/usr/bin/env python3
"""
Simple FastAPI server for frontend development
This provides mock endpoints for testing the frontend without complex backend dependencies
"""

import os
import sys
import json
import asyncio
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

# Import real implementations
from article_generator.generator import ArticleGenerator
from article_generator.knowledge_base import KnowledgeBase
from validation.citation_validator import CitationValidator
from validation.context_validator import ContextValidator
from validation.confidence_scorer import ConfidenceScorer
from validation.nlp_processor import NLPProcessor
from llm.anthropic_client import AnthropicClient
from utils.document_parser import DocumentParser
from utils.knowledge_base_builder import KnowledgeBaseBuilder

app = FastAPI(title="AI Document Auditing API", version="1.0.0")

# File storage configuration
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Initialize real components
try:
    # Initialize LLM client
    llm_client = AnthropicClient()
    
    # Initialize NLP processor
    nlp_processor = NLPProcessor()
    
    # Initialize validators
    citation_validator = CitationValidator(nlp_processor, llm_client)
    context_validator = ContextValidator(nlp_processor, llm_client)
    confidence_scorer = ConfidenceScorer()
    
    # Initialize document parser and knowledge base builder
    document_parser = DocumentParser()
    kb_builder = KnowledgeBaseBuilder(document_parser)
    
    print("✅ Real AI components initialized successfully")
except Exception as e:
    print(f"⚠️  Warning: Could not initialize real AI components: {e}")
    print("   Falling back to mock implementations")
    llm_client = None
    nlp_processor = None
    citation_validator = None
    context_validator = None
    confidence_scorer = None
    document_parser = None
    kb_builder = None

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    fileIds: Optional[List[str]] = None

class GenerationRequest(BaseModel):
    topic: str
    knowledgeBaseId: str
    maxSources: int
    length: str
    style: str
    includeCitations: bool

class ValidationRequest(BaseModel):
    articleId: str

# Mock data
mock_knowledge_bases = [
    {
        "id": "kb-1",
        "name": "White Papers Collection",
        "description": "Collection of AI and technology white papers",
        "filePath": "data/knowledge_bases/white_papers.json",
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat(),
        "sourceCount": 26
    }
]

mock_articles = {}
uploaded_files = {}  # Track uploaded files

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/knowledge-bases")
async def get_knowledge_bases():
    """Get all available knowledge bases"""
    return {"success": True, "data": mock_knowledge_bases}

@app.post("/api/knowledge-bases")
async def create_knowledge_base(kb_data: KnowledgeBaseCreate):
    """Create a new knowledge base"""
    kb_id = str(uuid.uuid4())
    
    # Count files if fileIds provided
    file_count = 0
    if kb_data.fileIds:
        file_count = len([fid for fid in kb_data.fileIds if fid in uploaded_files])
    
    # Build knowledge base from uploaded files if available
    kb_path = f"data/knowledge_bases/{kb_id}.json"
    if kb_builder and kb_data.fileIds:
        try:
            # Get file paths for uploaded files
            file_paths = []
            for file_id in kb_data.fileIds:
                if file_id in uploaded_files:
                    file_paths.append(uploaded_files[file_id]["filePath"])
            
            # Build knowledge base using real implementation
            kb_builder.build_knowledge_base(
                name=kb_data.name,
                description=kb_data.description,
                file_paths=file_paths,
                output_path=kb_path
            )
            
            # Load the built knowledge base to get source count
            if os.path.exists(kb_path):
                with open(kb_path, 'r') as f:
                    kb_data_content = json.load(f)
                    file_count = len(kb_data_content.get('sources', []))
        except Exception as e:
            print(f"Error building knowledge base: {e}")
            # Fall back to mock implementation
    
    kb_info = {
        "id": kb_id,
        "name": kb_data.name,
        "description": kb_data.description,
        "filePath": kb_path,
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat(),
        "sourceCount": file_count
    }
    mock_knowledge_bases.append(kb_info)
    return {"success": True, "data": kb_info}

@app.post("/api/knowledge-bases/{kb_id}/upload")
async def upload_to_knowledge_base(
    kb_id: str,
    files: List[UploadFile] = File(...)
):
    """Upload files to a knowledge base"""
    upload_results = []
    for file in files:
        upload_results.append({
            "id": str(uuid.uuid4()),
            "name": file.filename,
            "size": 0,  # Would get actual size
            "type": file.content_type or "application/octet-stream",
            "status": "completed",
            "progress": 100
        })
    
    return {"success": True, "data": upload_results}

@app.post("/api/generate/article")
async def generate_article(request: GenerationRequest):
    """Generate an article"""
    # Mock article generation
    article_id = str(uuid.uuid4())
    
    # Generate more citations based on article length and max sources
    citation_count = min(request.maxSources, 15)  # Cap at 15 citations for readability
    if request.length == 'short':
        citation_count = min(citation_count, 8)
    elif request.length == 'medium':
        citation_count = min(citation_count, 12)
    else:  # long
        citation_count = min(citation_count, 15)
    
    # Create more comprehensive mock citations
    mock_citations = []
    citation_texts = [
        "AI adoption in government organizations",
        "digital transformation initiatives", 
        "machine learning capabilities",
        "data-driven decision making",
        "automated processes and workflows",
        "predictive analytics implementation",
        "cloud computing infrastructure",
        "cybersecurity measures and protocols",
        "user experience optimization",
        "operational efficiency improvements",
        "cost reduction strategies",
        "scalable technology solutions",
        "real-time data processing",
        "advanced analytics tools",
        "intelligent automation systems"
    ]
    
    for i in range(citation_count):
        mock_citations.append({
            "id": str(uuid.uuid4()),
            "text": citation_texts[i % len(citation_texts)],
            "sourceId": f"source-{i+1}",
            "sourceNumber": i + 1,
            "position": {"start": 100 + (i * 50), "end": 140 + (i * 50)}
        })
    
    # Generate article content based on length
    if request.length == 'short':
        word_target = 600
        sections = ["Introduction", "Key Points", "Conclusion"]
    elif request.length == 'medium':
        word_target = 1200
        sections = ["Introduction", "Current State", "Key Developments", "Challenges", "Conclusion"]
    else:  # long
        word_target = 2500
        sections = ["Introduction", "Background", "Current State", "Key Developments", "Implementation Strategies", "Challenges and Solutions", "Future Outlook", "Conclusion"]
    
    # Create comprehensive article content
    article_content = f"""# {request.topic}

## Introduction

The landscape of {request.topic.lower()} has evolved significantly in recent years, driven by rapid technological advancement and changing organizational needs. AI adoption in government organizations [1] has become a critical focus area for many institutions seeking to modernize their operations and improve service delivery.

Recent studies indicate that digital transformation initiatives [2] are reshaping how organizations approach their core functions, with particular emphasis on leveraging machine learning capabilities [3] to enhance decision-making processes and operational efficiency.

## Current State and Trends

The current state of {request.topic.lower()} reflects a complex interplay between technological innovation and practical implementation challenges. Data-driven decision making [4] has emerged as a cornerstone of modern organizational strategy, enabling leaders to make more informed choices based on comprehensive analytics and real-time insights.

Organizations are increasingly investing in automated processes and workflows [5] to streamline operations and reduce manual intervention. This shift towards automation is particularly evident in sectors where predictive analytics implementation [6] can provide significant competitive advantages.

## Key Developments and Innovations

One of the most significant developments in recent years has been the widespread adoption of cloud computing infrastructure [7] to support scalable and flexible operations. This technological foundation enables organizations to implement advanced analytics tools [8] and intelligent automation systems [9] that were previously beyond their reach.

Cybersecurity measures and protocols [10] have also become increasingly sophisticated, reflecting the growing awareness of digital threats and the need for robust protection mechanisms. User experience optimization [11] has emerged as another critical focus area, with organizations recognizing the importance of intuitive and accessible interfaces.

## Implementation Strategies

Successful implementation of {request.topic.lower()} requires a comprehensive approach that addresses both technical and organizational considerations. Operational efficiency improvements [12] often serve as the primary driver for adoption, with organizations seeking to reduce costs while enhancing service quality.

Cost reduction strategies [13] play a crucial role in justifying investments in new technologies, while scalable technology solutions [14] ensure that systems can grow and adapt to changing requirements. Real-time data processing [15] capabilities have become essential for organizations that need to respond quickly to changing conditions.

## Challenges and Considerations

Despite the significant potential benefits, implementing {request.topic.lower()} is not without challenges. Organizations must navigate complex technical requirements, manage change effectively, and ensure that new systems integrate seamlessly with existing infrastructure.

The rapid pace of technological change also presents ongoing challenges, requiring organizations to maintain current knowledge and adapt their strategies accordingly. Additionally, the need for skilled personnel and ongoing training cannot be overlooked.

## Future Outlook

The future of {request.topic.lower()} appears promising, with continued innovation expected across multiple domains. Emerging technologies and evolving best practices will likely drive further adoption and refinement of existing approaches.

Organizations that successfully navigate the current landscape and position themselves for future developments will be well-placed to capitalize on the opportunities that lie ahead.

## Conclusion

{request.topic} represents a significant opportunity for organizations to enhance their operations and improve their competitive position. While challenges exist, the potential benefits make it a worthwhile investment for those willing to commit the necessary resources and effort.

The key to success lies in taking a strategic, comprehensive approach that addresses both technical and organizational considerations while remaining adaptable to future developments and opportunities.
"""
    
    # Adjust word count based on actual content
    actual_word_count = len(article_content.split())
    
    api_article = {
        "id": article_id,
        "title": f"{request.topic}",
        "content": article_content,
        "wordCount": actual_word_count,
        "citationCount": len(mock_citations),
        "sourcesUsed": min(request.maxSources, len(mock_citations)),
        "generatedAt": datetime.now().isoformat(),
        "knowledgeBaseId": request.knowledgeBaseId,
        "citations": mock_citations
    }
    
    # Store the article
    mock_articles[article_id] = api_article
    
    return {"success": True, "data": api_article}

@app.get("/api/generate/progress/{article_id}")
async def get_generation_progress(article_id: str):
    """Get generation progress (mock implementation)"""
    return {
        "success": True,
        "data": {
            "articleId": article_id,
            "stage": "completed",
            "percentage": 100,
            "currentStep": "Article generation completed",
            "estimatedTime": 0
        }
    }

@app.get("/api/articles/{article_id}")
async def get_article(article_id: str):
    """Get a specific article"""
    if article_id in mock_articles:
        return {"success": True, "data": mock_articles[article_id]}
    return {"success": True, "data": None}

@app.get("/api/articles")
async def get_articles():
    """Get all articles"""
    return {"success": True, "data": list(mock_articles.values())}

@app.post("/api/validate/article/{article_id}")
async def validate_article(article_id: str):
    """Validate an article"""
    if article_id not in mock_articles:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Mock validation results
    mock_results = {
        "citationResults": [
            {
                "citationText": "AI adoption in government organizations",
                "isAccurate": True,
                "accuracyScore": 0.85,
                "exactMatch": True,
                "fuzzyMatchScore": 0.9,
                "sourceFound": True,
                "sourceId": "source-1",
                "issues": [],
                "confidence": 0.85
            },
            {
                "citationText": "digital transformation initiatives",
                "isAccurate": True,
                "accuracyScore": 0.78,
                "exactMatch": False,
                "fuzzyMatchScore": 0.8,
                "sourceFound": True,
                "sourceId": "source-2",
                "issues": ["Minor formatting difference"],
                "confidence": 0.78
            },
            {
                "citationText": "machine learning capabilities",
                "isAccurate": False,
                "accuracyScore": 0.45,
                "exactMatch": False,
                "fuzzyMatchScore": 0.5,
                "sourceFound": False,
                "sourceId": None,
                "issues": ["Source not found", "Citation may be inaccurate"],
                "confidence": 0.45
            }
        ],
        "contextResults": [
            {
                "citationText": "AI adoption in government organizations",
                "originalContext": "Recent studies show that AI adoption in government organizations has increased by 40% over the past two years.",
                "articleContext": "The landscape has evolved significantly. AI adoption in government organizations has become a critical focus area.",
                "contextPreserved": True,
                "contextSimilarityScore": 0.85,
                "semanticSimilarityScore": 0.9,
                "meaningPreserved": True,
                "issues": [],
                "confidence": 0.85,
                "detailedAnalysis": "Context is well preserved with accurate representation of the original meaning."
            },
            {
                "citationText": "digital transformation initiatives",
                "originalContext": "Digital transformation initiatives are reshaping how organizations operate and deliver services.",
                "articleContext": "Digital transformation initiatives are driving significant changes across various sectors.",
                "contextPreserved": True,
                "contextSimilarityScore": 0.75,
                "semanticSimilarityScore": 0.8,
                "meaningPreserved": True,
                "issues": ["Slight paraphrasing"],
                "confidence": 0.75,
                "detailedAnalysis": "Context is generally preserved with minor paraphrasing that maintains the core meaning."
            },
            {
                "citationText": "machine learning capabilities",
                "originalContext": "Advanced analytics and machine learning capabilities are becoming essential tools for data-driven decision making.",
                "articleContext": "Organizations are increasingly investing in machine learning capabilities to enhance their operational efficiency.",
                "contextPreserved": False,
                "contextSimilarityScore": 0.4,
                "semanticSimilarityScore": 0.5,
                "meaningPreserved": False,
                "issues": ["Significant context change", "Original meaning altered"],
                "confidence": 0.4,
                "detailedAnalysis": "The context has been significantly altered from the original source, changing the intended meaning."
            }
        ],
        "confidenceScore": 0.68,
        "riskFactors": [
            "One citation has low confidence score (45%)",
            "Context preservation issues detected",
            "Some sources may not be accurately represented"
        ],
        "recommendations": [
            "Review low-confidence citations for accuracy",
            "Verify source attribution for citation 3",
            "Consider additional source verification",
            "Improve context preservation in article generation"
        ],
        "validatedAt": datetime.now().isoformat()
    }
    
    return {"success": True, "data": mock_results}

@app.get("/api/validate/results/{article_id}")
async def get_validation_results(article_id: str):
    """Get validation results for an article"""
    return {"success": True, "data": None}

@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload files and save them to disk"""
    upload_results = []
    
    for file in files:
        file_id = str(uuid.uuid4())
        
        # Create unique filename to avoid conflicts
        file_extension = Path(file.filename).suffix if file.filename else ""
        unique_filename = f"{file_id}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        try:
            # Save file to disk
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Get file size
            file_size = file_path.stat().st_size
            
            # Track the uploaded file
            uploaded_files[file_id] = {
                "id": file_id,
                "fileName": file.filename,
                "fileSize": file_size,
                "filePath": str(file_path),
                "contentType": file.content_type or "application/octet-stream",
                "uploadedAt": datetime.now().isoformat(),
                "status": "completed",
                "progress": 100
            }
            
            upload_results.append({
                "fileId": file_id,
                "fileName": file.filename,
                "fileSize": file_size,
                "status": "completed",
                "progress": 100
            })
            
        except Exception as e:
            print(f"Error uploading file {file.filename}: {e}")
            upload_results.append({
                "fileId": file_id,
                "fileName": file.filename,
                "fileSize": 0,
                "status": "error",
                "progress": 0,
                "error": str(e)
            })
    
    return {"success": True, "data": upload_results}

@app.get("/api/files/{file_id}/status")
async def get_file_status(file_id: str):
    """Get file upload status"""
    if file_id in uploaded_files:
        file_info = uploaded_files[file_id]
        return {
            "success": True,
            "data": {
                "id": file_info["id"],
                "fileName": file_info["fileName"],
                "fileSize": file_info["fileSize"],
                "status": file_info["status"],
                "progress": file_info["progress"]
            }
        }
    else:
        raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting AI Document Auditing API Server (Mock Mode)")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔗 Frontend should connect to: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
