'use client'

import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Progress } from '@/components/ui/Progress'
import { FileUpload } from './FileUpload'
import { useGenerationStore } from '@/stores/generationStore'
import { GenerationForm, FileUpload as FileUploadType } from '@/types'
import { generateId } from '@/lib/utils'

const generationSchema = z.object({
  topic: z.string().min(10, 'Topic must be at least 10 characters'),
  knowledgeBaseId: z.string().min(1, 'Please select a knowledge base'),
  maxSources: z.number().min(1).max(30),
  length: z.enum(['short', 'medium', 'long']),
  style: z.enum(['academic', 'journalistic', 'technical']),
  includeCitations: z.boolean(),
})

type GenerationFormData = z.infer<typeof generationSchema>

interface ArticleGeneratorProps {
  onGenerate: (form: GenerationForm) => void
  onUploadFiles: (files: File[]) => void
  onRemoveFile: (fileId: string) => void
  onCreateKnowledgeBase: (name: string, description?: string) => void
  uploads: FileUploadType[]
  knowledgeBases: Array<{ id: string; name: string }>
  isGenerating: boolean
  isCreatingKB: boolean
  progress: {
    stage: string
    percentage: number
    currentStep: string
  }
}

export const ArticleGenerator: React.FC<ArticleGeneratorProps> = ({
  onGenerate,
  onUploadFiles,
  onRemoveFile,
  onCreateKnowledgeBase,
  uploads,
  knowledgeBases,
  isGenerating,
  isCreatingKB,
  progress,
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false)
  
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isValid },
  } = useForm<GenerationFormData>({
    resolver: zodResolver(generationSchema),
    defaultValues: {
      topic: '',
      knowledgeBaseId: '',
      maxSources: 20,
      length: 'medium',
      style: 'academic',
      includeCitations: true,
    },
  })

  const watchedMaxSources = watch('maxSources')
  const watchedLength = watch('length')

  const onSubmit = (data: GenerationFormData) => {
    onGenerate(data as GenerationForm)
  }

  const handleFileUpload = (files: File[]) => {
    // Convert files to FileUploadType objects
    const fileUploads: FileUploadType[] = files.map(file => ({
      id: generateId(),
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'uploading',
      progress: 0,
    }))
    
    // Add to store
    fileUploads.forEach(upload => {
      useGenerationStore.getState().addFileUpload(upload)
    })
    
    // Call parent handler
    onUploadFiles(files)
  }

  const handleFileRemove = (fileId: string) => {
    useGenerationStore.getState().removeFileUpload(fileId)
    onRemoveFile(fileId)
  }

  const getLengthDescription = (length: string) => {
    switch (length) {
      case 'short': return '500-800 words'
      case 'medium': return '1000-1500 words'
      case 'long': return '2000-3000 words'
      default: return ''
    }
  }

  return (
    <div className="space-y-6">
      {/* File Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle>1. Upload Knowledge Base</CardTitle>
        </CardHeader>
        <CardContent>
          <FileUpload
            onFilesSelected={handleFileUpload}
            onFileRemove={handleFileRemove}
            onCreateKnowledgeBase={onCreateKnowledgeBase}
            uploads={uploads}
            maxFiles={50}
            maxSize={50 * 1024 * 1024} // 50MB
            acceptedTypes={['.pdf', '.txt', '.docx', '.md']}
            isCreatingKB={isCreatingKB}
          />
        </CardContent>
      </Card>

      {/* Knowledge Base Selection */}
      <Card>
        <CardHeader>
          <CardTitle>2. Select Knowledge Base</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Knowledge Base
              </label>
              <select
                {...register('knowledgeBaseId')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select a knowledge base...</option>
                {knowledgeBases.map((kb) => (
                  <option key={kb.id} value={kb.id}>
                    {kb.name}
                  </option>
                ))}
              </select>
              {errors.knowledgeBaseId && (
                <p className="text-red-500 text-sm mt-1">
                  {errors.knowledgeBaseId.message}
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Article Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>3. Configure Article</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Topic */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Article Topic *
              </label>
              <textarea
                {...register('topic')}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter a detailed topic for your article..."
              />
              {errors.topic && (
                <p className="text-red-500 text-sm mt-1">
                  {errors.topic.message}
                </p>
              )}
            </div>

            {/* Basic Options */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Article Length
                </label>
                <select
                  {...register('length')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="short">Short ({getLengthDescription('short')})</option>
                  <option value="medium">Medium ({getLengthDescription('medium')})</option>
                  <option value="long">Long ({getLengthDescription('long')})</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Writing Style
                </label>
                <select
                  {...register('style')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="academic">Academic</option>
                  <option value="journalistic">Journalistic</option>
                  <option value="technical">Technical</option>
                </select>
              </div>
            </div>

            {/* Advanced Options */}
            <div>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="mb-4"
              >
                {showAdvanced ? 'Hide' : 'Show'} Advanced Options
              </Button>

              {showAdvanced && (
                <div className="space-y-4 p-4 bg-gray-50 rounded-md">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Max Sources: {watchedMaxSources}
                    </label>
                    <input
                      type="range"
                      min="5"
                      max="30"
                      {...register('maxSources', { valueAsNumber: true })}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>5 sources</span>
                      <span>30 sources</span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      {...register('includeCitations')}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <label className="text-sm font-medium text-gray-700">
                      Include citations in the article
                    </label>
                  </div>
                </div>
              )}
            </div>

            {/* Generate Button */}
            <Button
              type="submit"
              disabled={!isValid || isGenerating}
              loading={isGenerating}
              className="w-full"
            >
              {isGenerating ? 'Generating Article...' : 'Generate Article'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Progress Section */}
      {isGenerating && (
        <Card>
          <CardHeader>
            <CardTitle>Generation Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <Progress
              value={progress.percentage}
              color="default"
              className="mb-4"
            />
            <p className="text-sm text-gray-600">
              {progress.currentStep}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Stage: {progress.stage}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
