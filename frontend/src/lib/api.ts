// API utilities for file upload and knowledge base management

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface UploadResponse {
  fileId: string
  fileName: string
  fileSize: number
  status: 'uploading' | 'processing' | 'completed' | 'error'
  progress: number
  error?: string
}

export interface KnowledgeBaseResponse {
  id: string
  name: string
  description?: string
  filePath: string
  createdAt: string
  updatedAt: string
  sourceCount: number
}

export class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${this.baseUrl}/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const result = await response.json()
      return result.data
    } catch (error) {
      console.error('File upload error:', error)
      throw error
    }
  }

  async uploadFiles(files: File[]): Promise<UploadResponse[]> {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })

    console.log('API Client: Uploading files to:', `${this.baseUrl}/upload`)
    console.log('API Client: Files to upload:', files.map(f => f.name))

    try {
      const response = await fetch(`${this.baseUrl}/upload`, {
        method: 'POST',
        body: formData,
      })

      console.log('API Client: Upload response status:', response.status)
      
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const result = await response.json()
      console.log('API Client: Upload result:', result)
      return result.data
    } catch (error) {
      console.error('API Client: Files upload error:', error)
      throw error
    }
  }

  async createKnowledgeBase(name: string, description?: string, fileIds?: string[]): Promise<KnowledgeBaseResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/knowledge-bases`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          description,
          fileIds,
        }),
      })

      if (!response.ok) {
        throw new Error(`Knowledge base creation failed: ${response.statusText}`)
      }

      const result = await response.json()
      return result.data
    } catch (error) {
      console.error('Knowledge base creation error:', error)
      throw error
    }
  }

  async getKnowledgeBases(): Promise<KnowledgeBaseResponse[]> {
    try {
      const response = await fetch(`${this.baseUrl}/knowledge-bases`)

      if (!response.ok) {
        throw new Error(`Failed to fetch knowledge bases: ${response.statusText}`)
      }

      const result = await response.json()
      return result.data
    } catch (error) {
      console.error('Get knowledge bases error:', error)
      throw error
    }
  }

  async uploadToKnowledgeBase(kbId: string, files: File[]): Promise<UploadResponse[]> {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })

    try {
      const response = await fetch(`${this.baseUrl}/knowledge-bases/${kbId}/upload`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Upload to knowledge base failed: ${response.statusText}`)
      }

      const result = await response.json()
      return result.data
    } catch (error) {
      console.error('Upload to knowledge base error:', error)
      throw error
    }
  }

  async getFileStatus(fileId: string): Promise<UploadResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/files/${fileId}/status`)

      if (!response.ok) {
        throw new Error(`Failed to get file status: ${response.statusText}`)
      }

      const result = await response.json()
      return result.data
    } catch (error) {
      console.error('Get file status error:', error)
      throw error
    }
  }
}

// Export a default instance
export const apiClient = new ApiClient()

// Utility functions for file handling
export const validateFileType = (file: File, acceptedTypes: string[]): boolean => {
  return acceptedTypes.includes(file.type)
}

export const validateFileSize = (file: File, maxSize: number): boolean => {
  return file.size <= maxSize
}

export const validateFiles = (files: File[], acceptedTypes: string[], maxSize: number): { valid: File[], invalid: { file: File, reason: string }[] } => {
  const valid: File[] = []
  const invalid: { file: File, reason: string }[] = []

  files.forEach(file => {
    if (!validateFileType(file, acceptedTypes)) {
      invalid.push({ file, reason: 'File type not supported' })
    } else if (!validateFileSize(file, maxSize)) {
      invalid.push({ file, reason: `File too large (max ${maxSize} bytes)` })
    } else {
      valid.push(file)
    }
  })

  return { valid, invalid }
}

// Add generateArticle method to ApiClient
ApiClient.prototype.generateArticle = async function(request: {
  topic: string
  knowledgeBaseId: string
  maxSources: number
  length: string
  style: string
  includeCitations: boolean
}): Promise<{ success: boolean; data: any }> {
  try {
    console.log('API: Generating article with request:', request)
    
    const response = await fetch(`${this.baseUrl}/generate/article`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    console.log('API: Generate article response status:', response.status)

    if (!response.ok) {
      const errorText = await response.text()
      console.error('API: Generate article error response:', errorText)
      throw new Error(`Article generation failed: ${response.statusText}`)
    }

    const result = await response.json()
    console.log('API: Generate article success:', result)
    return result
  } catch (error) {
    console.error('API: Generate article error:', error)
    throw error
  }
}

// Additional API methods for articles and validation
export class ArticleApiClient {
  private baseUrl: string

  constructor() {
    this.baseUrl = API_BASE_URL
  }

  async getArticles(): Promise<GeneratedArticle[]> {
    try {
      const response = await fetch(`${this.baseUrl}/articles`)

      if (!response.ok) {
        throw new Error(`Failed to fetch articles: ${response.statusText}`)
      }

      const result = await response.json()
      return result.data || []
    } catch (error) {
      console.error('Get articles error:', error)
      throw error
    }
  }

  async validateArticle(articleId: string): Promise<ValidationResults> {
    try {
      const response = await fetch(`${this.baseUrl}/validate/results/${articleId}`)

      if (!response.ok) {
        throw new Error(`Failed to validate article: ${response.statusText}`)
      }

      const result = await response.json()
      return result.data
    } catch (error) {
      console.error('Validate article error:', error)
      throw error
    }
  }
}