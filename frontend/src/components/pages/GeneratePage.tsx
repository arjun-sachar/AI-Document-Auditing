'use client'

import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Progress } from '@/components/ui/Progress'
import { GenerationForm, KnowledgeBase } from '@/types'

const generationSchema = z.object({
  topic: z.string().min(10, 'Topic must be at least 10 characters'),
  knowledgeBaseId: z.string().min(1, 'Please select a knowledge base'),
  maxSources: z.number().min(1).max(50),
  length: z.enum(['short', 'medium', 'long']),
  style: z.enum(['academic', 'journalistic', 'technical']),
  includeCitations: z.boolean(),
})

type GenerationFormData = z.infer<typeof generationSchema>

interface GeneratePageProps {
  onGenerate: (form: GenerationForm) => void
  knowledgeBases: KnowledgeBase[]
  isGenerating: boolean
  progress: {
    stage: string
    percentage: number
    currentStep: string
  }
}

export const GeneratePage: React.FC<GeneratePageProps> = ({
  onGenerate,
  knowledgeBases,
  isGenerating,
  progress,
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false)
  
  const {
    register,
    handleSubmit,
    watch,
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

  const getLengthDescription = (length: string) => {
    switch (length) {
      case 'short': return '500-800 words'
      case 'medium': return '1000-1500 words'
      case 'long': return '2000-3000 words'
      default: return ''
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Generate Article
        </h1>
        <p className="text-lg text-gray-600">
          Configure your article settings and generate content from your knowledge base
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Article Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Knowledge Base Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Knowledge Base *
              </label>
              <select
                {...register('knowledgeBaseId')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select a knowledge base...</option>
                {knowledgeBases.map((kb) => (
                  <option key={kb.id} value={kb.id}>
                    {kb.name} ({kb.sourceCount} sources)
                  </option>
                ))}
              </select>
              {errors.knowledgeBaseId && (
                <p className="text-red-500 text-sm mt-1">
                  {errors.knowledgeBaseId.message}
                </p>
              )}
            </div>

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
                      max="50"
                      {...register('maxSources', { valueAsNumber: true })}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>5 sources</span>
                      <span>50 sources</span>
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

