// Core Types for AI Document Auditing Tool

export interface KnowledgeBase {
  id: string
  name: string
  description?: string
  filePath: string
  createdAt: Date
  updatedAt: Date
  sourceCount: number
}

export interface Source {
  id: string
  title: string
  content: string
  url?: string
  metadata?: Record<string, any>
  sourceNumber?: number
}

export interface GenerationForm {
  topic: string
  knowledgeBaseId: string
  maxSources: number
  length: 'short' | 'medium' | 'long'
  style: 'academic' | 'journalistic' | 'technical'
  includeCitations: boolean
}

export interface GenerationProgress {
  stage: 'idle' | 'uploading' | 'processing' | 'generating' | 'validating' | 'completed' | 'error'
  percentage: number
  currentStep: string
  estimatedTime: number
  error?: string
}

export interface GeneratedArticle {
  id: string
  title: string
  content: string
  wordCount: number
  citationCount: number
  sourcesUsed: number
  generatedAt: Date
  knowledgeBaseId: string
  citations: Citation[]
  validationResults?: ValidationResults
}

export interface Citation {
  id: string
  text: string
  sourceId: string
  sourceNumber: number
  position: {
    start: number
    end: number
  }
  confidence?: number
  isAccurate?: boolean
  issues?: string[]
}

export interface ValidationResults {
  citationResults: CitationValidationResult[]
  contextResults: ContextValidationResult[]
  confidenceScore: number
  riskFactors: string[]
  recommendations: string[]
  validatedAt: Date
}

export interface CitationValidationResult {
  citationText: string
  isAccurate: boolean
  accuracyScore: number
  exactMatch: boolean
  fuzzyMatchScore: number
  sourceFound: boolean
  sourceId?: string
  issues: string[]
  confidence: number
}

export interface ContextValidationResult {
  citationText: string
  originalContext: string
  articleContext: string
  contextPreserved: boolean
  contextSimilarityScore: number
  semanticSimilarityScore: number
  meaningPreserved: boolean
  issues: string[]
  confidence: number
  detailedAnalysis: string
}

export interface FileUpload {
  id: string
  name: string
  size: number
  type: string
  status: 'uploading' | 'processing' | 'completed' | 'error'
  progress: number
  error?: string
  knowledgeBaseId?: string
  fileId?: string  // Backend file ID for API calls
}

export interface ValidationScore {
  score: number
  color: string
  bgColor: string
  textColor: string
  label: 'Excellent' | 'Good' | 'Fair' | 'Poor'
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface GenerationResponse {
  articleId: string
  article: GeneratedArticle
  progress: GenerationProgress
}

export interface ValidationResponse {
  validationId: string
  results: ValidationResults
}

// WebSocket Event Types
export interface WebSocketEvent {
  type: 'progress' | 'completion' | 'error'
  data: any
}

export interface ProgressEvent {
  articleId: string
  stage: GenerationProgress['stage']
  percentage: number
  currentStep: string
  estimatedTime: number
}

export interface CompletionEvent {
  articleId: string
  article: GeneratedArticle
  validationResults: ValidationResults
}

export interface ErrorEvent {
  articleId: string
  error: string
  stage: GenerationProgress['stage']
}

