'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Progress } from '@/components/ui/Progress'
import { ViewPage } from '@/components/pages/ViewPage'
import { FileUpload } from '@/components/features/FileUpload'
import { GeneratedArticle, ValidationResults, Source, FileUpload as FileUploadType } from '@/types'
import { ApiClient, ArticleApiClient } from '@/lib/api'
import Link from 'next/link'
import { Home } from 'lucide-react'

export default function ValidatePage() {
  const [isValidating, setIsValidating] = useState(false)
  const [validationResults, setValidationResults] = useState<ValidationResults | null>(null)
  const [articles, setArticles] = useState<GeneratedArticle[]>([])
  const [selectedArticle, setSelectedArticle] = useState<GeneratedArticle | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [uploadedArticles, setUploadedArticles] = useState<GeneratedArticle[]>([])
  const [activeTab, setActiveTab] = useState<'generated' | 'uploaded'>('generated')
  const apiClient = new ArticleApiClient()
  const fileApiClient = new ApiClient()

  // Fetch generated articles
  useEffect(() => {
    const fetchArticles = async () => {
      try {
        const articlesData = await apiClient.getArticles()
        setArticles(articlesData)
        if (articlesData.length > 0) {
          setSelectedArticle(articlesData[0])
        }
      } catch (error) {
        console.error('Failed to fetch articles:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchArticles()
  }, [])

  const handleValidate = async () => {
    if (!selectedArticle) return
    
    setIsValidating(true)
    try {
      const results = await apiClient.validateArticle(selectedArticle.id)
      setValidationResults(results)
    } catch (error) {
      console.error('Validation failed:', error)
    } finally {
      setIsValidating(false)
    }
  }

  const handleFileUpload = async (files: FileUploadType[]) => {
    try {
      // Process uploaded files and convert to GeneratedArticle format
      const newArticles: GeneratedArticle[] = []
      
      for (const fileUpload of files) {
        if (fileUpload.status === 'completed') {
          // For now, create a placeholder article - in a real implementation,
          // you would read the actual file content
          const article: GeneratedArticle = {
            id: `uploaded_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            title: fileUpload.name.replace(/\.[^/.]+$/, ""), // Remove extension
            content: `# ${fileUpload.name.replace(/\.[^/.]+$/, "")}\n\nThis is a placeholder for the uploaded article content. In a real implementation, the file content would be read and processed here.\n\nFile: ${fileUpload.name}\nSize: ${(fileUpload.size / 1024).toFixed(2)} KB\nType: ${fileUpload.type}`,
            sources: [], // No sources for uploaded articles
            citations: [],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            metadata: {
              type: 'uploaded',
              fileName: fileUpload.name,
              fileSize: fileUpload.size,
              fileType: fileUpload.type
            }
          }
          
          newArticles.push(article)
        }
      }
      
      setUploadedArticles(prev => [...prev, ...newArticles])
      
      // Auto-select the first uploaded article
      if (newArticles.length > 0) {
        setSelectedArticle(newArticles[0])
        setActiveTab('uploaded')
      }
      
    } catch (error) {
      console.error('File upload processing failed:', error)
    }
  }

  const handleFileRemove = (fileId: string) => {
    setUploadedArticles(prev => {
      const filtered = prev.filter(article => article.id !== fileId)
      if (selectedArticle?.id === fileId) {
        setSelectedArticle(filtered.length > 0 ? filtered[0] : null)
      }
      return filtered
    })
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-8">
            <div className="flex justify-between items-center mb-4">
              <Link href="/">
                <Button variant="outline" size="sm" className="flex items-center gap-2">
                  <Home className="w-4 h-4" />
                  Home
                </Button>
              </Link>
              <div className="flex-1"></div>
            </div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              Article Validation
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Validate generated articles or upload your own articles for validation
            </p>
          </div>
          
          <div className="flex items-center justify-center">
            <div className="text-center">
              <Progress className="w-64 mb-4" />
              <p className="text-gray-600 dark:text-gray-400">Loading articles...</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (articles.length === 0 && uploadedArticles.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-8">
            <div className="flex justify-between items-center mb-4">
              <Link href="/">
                <Button variant="outline" size="sm" className="flex items-center gap-2">
                  <Home className="w-4 h-4" />
                  Home
                </Button>
              </Link>
              <div className="flex-1"></div>
            </div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              Article Validation
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Validate generated articles or upload your own articles for validation
            </p>
          </div>
          
          <div className="flex items-center justify-center">
            <Card className="w-full max-w-md mx-auto">
              <CardHeader>
                <CardTitle className="text-center">No Articles Found</CardTitle>
              </CardHeader>
              <CardContent className="text-center">
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  No articles available for validation. Generate an article or upload one to get started.
                </p>
                <div className="space-y-2">
                  <Button 
                    onClick={() => window.location.href = '/generate'}
                    className="w-full"
                  >
                    Generate Article
                  </Button>
                  <Button 
                    onClick={() => setActiveTab('uploaded')}
                    variant="outline"
                    className="w-full"
                  >
                    Upload Article
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-8">
          <div className="flex justify-between items-center mb-4">
            <Link href="/">
              <Button variant="outline" size="sm" className="flex items-center gap-2">
                <Home className="w-4 h-4" />
                Home
              </Button>
            </Link>
            <div className="flex-1"></div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Article Validation
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Validate generated articles or upload your own articles for validation
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex justify-center mb-6">
          <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => setActiveTab('generated')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'generated'
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              Generated Articles ({articles.length})
            </button>
            <button
              onClick={() => setActiveTab('uploaded')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === 'uploaded'
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              Uploaded Articles ({uploadedArticles.length})
            </button>
          </div>
        </div>

        {/* File Upload Section */}
        {activeTab === 'uploaded' && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Upload Articles for Validation</CardTitle>
            </CardHeader>
            <CardContent>
              <FileUpload
                onFilesSelected={handleFileUpload}
                onFileRemove={handleFileRemove}
                uploads={uploadedArticles.map(article => ({
                  id: article.id,
                  name: article.metadata?.fileName || article.title,
                  size: article.metadata?.fileSize || 0,
                  type: article.metadata?.fileType || 'text/plain',
                  status: 'completed' as const,
                  progress: 100,
                  fileId: article.id
                }))}
                acceptedTypes={{
                  'text/plain': ['.txt'],
                  'text/markdown': ['.md'],
                  'application/pdf': ['.pdf'],
                  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
                  'application/msword': ['.doc']
                }}
                maxSize={10 * 1024 * 1024} // 10MB
                uploadMode="files"
              />
            </CardContent>
          </Card>
        )}

        {/* Article Selection */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>
              Select Article to Validate
              {activeTab === 'generated' && ' (AI Generated)'}
              {activeTab === 'uploaded' && ' (Uploaded)'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <select
              value={selectedArticle?.id || ''}
              onChange={(e) => {
                const allArticles = activeTab === 'generated' ? articles : uploadedArticles
                const article = allArticles.find(a => a.id === e.target.value)
                setSelectedArticle(article || null)
              }}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            >
              <option value="">Select an article...</option>
              {(activeTab === 'generated' ? articles : uploadedArticles).map((article) => (
                <option key={article.id} value={article.id}>
                  {article.title} - {new Date(article.generatedAt || article.createdAt).toLocaleDateString()}
                  {article.metadata?.type === 'uploaded' && ' (Uploaded)'}
                </option>
              ))}
            </select>
          </CardContent>
        </Card>

        {/* Article Display and Validation */}
        {selectedArticle && (
          <ViewPage
            article={selectedArticle}
            validationResults={validationResults}
            sources={selectedArticle.sources || []}
            onValidate={handleValidate}
            onExport={() => {
              // Export functionality
              const blob = new Blob([selectedArticle.content], { type: 'text/markdown' })
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = `${selectedArticle.title}.md`
              a.click()
              URL.revokeObjectURL(url)
            }}
            onGenerateNew={() => window.location.href = '/generate'}
          />
        )}
      </div>
    </div>
  )
}