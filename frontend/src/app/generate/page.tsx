'use client'

import React, { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useSearchParams } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Progress } from '@/components/ui/Progress'
import { GenerationForm, KnowledgeBase } from '@/types'
import { ApiClient } from '@/lib/api'
import Link from 'next/link'
import { Home } from 'lucide-react'

const generationSchema = z.object({
  topic: z.string().min(10, 'Topic must be at least 10 characters'),
  knowledgeBaseId: z.string().min(1, 'Please select a knowledge base'),
  maxSources: z.number().min(1).max(50),
  length: z.enum(['short', 'medium', 'long']),
  style: z.enum(['academic', 'journalistic', 'technical']),
  includeCitations: z.boolean(),
})

type GenerationFormData = z.infer<typeof generationSchema>

export default function GeneratePage() {
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([])
  const [isLoadingKB, setIsLoadingKB] = useState(true)
  const apiClient = new ApiClient()

  // Fetch knowledge bases from API
  useEffect(() => {
    const fetchKnowledgeBases = async () => {
      try {
        console.log('Fetching knowledge bases from API...')
        const kbs = await apiClient.getKnowledgeBases()
        console.log('Fetched knowledge bases:', kbs)
        console.log('Available knowledge base IDs:', kbs.map(kb => ({ id: kb.id, name: kb.name, sources: kb.sourceCount })))
        setKnowledgeBases(kbs)
      } catch (error) {
        console.error('Failed to fetch knowledge bases:', error)
        // No fallback to mock data - only show real knowledge bases
        setKnowledgeBases([])
      } finally {
        setIsLoadingKB(false)
      }
    }

    fetchKnowledgeBases()
  }, [])
  
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

  // Handle URL parameter for pre-selected knowledge base
  const searchParams = useSearchParams()
  const kbParam = searchParams.get('kb')
  
  useEffect(() => {
    if (kbParam && knowledgeBases.length > 0) {
      // Only set the knowledge base ID if it exists in the loaded knowledge bases
      const kbExists = knowledgeBases.some(kb => kb.id === kbParam)
      if (kbExists) {
        console.log('Setting knowledge base from URL parameter:', kbParam)
        setValue('knowledgeBaseId', kbParam)
      } else {
        console.warn('Knowledge base ID from URL parameter not found:', kbParam)
        console.log('Available knowledge base IDs:', knowledgeBases.map(kb => kb.id))
      }
    }
  }, [kbParam, knowledgeBases, setValue])

  const watchedMaxSources = watch('maxSources')
  const watchedLength = watch('length')

  const onSubmit = async (data: GenerationFormData) => {
    setIsGenerating(true)
    console.log('Generating article with:', data)
    console.log('Selected knowledge base ID:', data.knowledgeBaseId)
    console.log('Available knowledge bases:', knowledgeBases.map(kb => ({ id: kb.id, name: kb.name })))
    
    // Validate that the selected knowledge base exists
    const selectedKB = knowledgeBases.find(kb => kb.id === data.knowledgeBaseId)
    if (!selectedKB) {
      alert(`Error: Selected knowledge base ID "${data.knowledgeBaseId}" not found in available knowledge bases.`)
      setIsGenerating(false)
      return
    }
    
    console.log('Selected knowledge base:', selectedKB)
    
    try {
      // Call the real API to generate article
      const result = await apiClient.generateArticle({
        topic: data.topic,
        knowledgeBaseId: data.knowledgeBaseId,
        maxSources: data.maxSources,
        length: data.length,
        style: data.style,
        includeCitations: data.includeCitations
      })
      
      console.log('Article generation result:', result)
      
      if (result.success) {
        alert(`Article generated successfully! Title: ${result.data.title}`)
        // Optionally redirect to validation page or show the article
        window.location.href = `/validate?article=${result.data.id}`
      } else {
        alert('Failed to generate article. Please try again.')
      }
    } catch (error) {
      console.error('Error generating article:', error)
      alert('Error generating article. Please check the console for details.')
    } finally {
      setIsGenerating(false)
    }
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto space-y-6">
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
              Generate Article
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-300">
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
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Knowledge Base *
                  </label>
                  <select
                    {...register('knowledgeBaseId')}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
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
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Article Topic *
                  </label>
                  <textarea
                    {...register('topic')}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
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
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Article Length
                    </label>
                    <select
                      {...register('length')}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    >
                      <option value="short">Short ({getLengthDescription('short')})</option>
                      <option value="medium">Medium ({getLengthDescription('medium')})</option>
                      <option value="long">Long ({getLengthDescription('long')})</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Writing Style
                    </label>
                    <select
                      {...register('style')}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
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
                    <div className="space-y-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-md">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Max Sources: {watchedMaxSources}
                        </label>
                        <input
                          type="range"
                          min="5"
                          max="50"
                          {...register('maxSources', { valueAsNumber: true })}
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
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
                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
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
                  value={75}
                  className="mb-4"
                />
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Processing knowledge base and generating content...
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Stage: Content Generation
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
