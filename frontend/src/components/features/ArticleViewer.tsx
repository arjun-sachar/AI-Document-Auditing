'use client'

import React, { useState, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { GeneratedArticle, Citation, ValidationResults, Source } from '@/types'
import { getValidationColor, getValidationBgColor, getValidationTextColor } from '@/lib/design-system'
import { CheckCircle, AlertCircle, XCircle, Info } from 'lucide-react'

interface ArticleViewerProps {
  article: GeneratedArticle
  validationResults?: ValidationResults
  sources: Source[]
  onExport?: () => void
  onValidate?: () => void
}

export const ArticleViewer: React.FC<ArticleViewerProps> = ({
  article,
  validationResults,
  sources,
  onExport,
  onValidate,
}) => {
  const [hoveredCitation, setHoveredCitation] = useState<Citation | null>(null)
  const [showValidationDetails, setShowValidationDetails] = useState(false)

  // Create citation map for quick lookup
  const citationMap = useMemo(() => {
    const map = new Map<number, Citation>()
    article.citations.forEach(citation => {
      map.set(citation.sourceNumber, citation)
    })
    return map
  }, [article.citations])

  // Get validation result for a citation
  const getCitationValidation = (citation: Citation) => {
    if (!validationResults) return null
    return validationResults.citationResults.find(
      result => result.citationText === citation.text
    )
  }

  // Get context validation result for a citation
  const getContextValidation = (citation: Citation) => {
    if (!validationResults) return null
    return validationResults.contextResults.find(
      result => result.citationText === citation.text
    )
  }

  // Render article content with highlighted citations
  const renderArticleContent = () => {
    let content = article.content
    let lastIndex = 0
    const elements: React.ReactNode[] = []

    // Sort citations by position for proper rendering
    const sortedCitations = [...article.citations].sort((a, b) => a.position.start - b.position.start)

    sortedCitations.forEach((citation, index) => {
      // Add text before citation
      if (citation.position.start > lastIndex) {
        elements.push(
          <span key={`text-${index}`}>
            {content.slice(lastIndex, citation.position.start)}
          </span>
        )
      }

      // Add citation with validation styling
      const citationValidation = getCitationValidation(citation)
      const contextValidation = getContextValidation(citation)
      
      // Calculate overall confidence (average of citation and context confidence)
      const overallConfidence = citationValidation && contextValidation
        ? (citationValidation.confidence + contextValidation.confidence) / 2
        : citationValidation?.confidence || contextValidation?.confidence || 0

      const validationColor = getValidationColor(overallConfidence)
      const validationBgColor = getValidationBgColor(overallConfidence)
      const validationTextColor = getValidationTextColor(overallConfidence)

      elements.push(
        <span
          key={`citation-${index}`}
          className="relative inline-block cursor-pointer"
          style={{
            backgroundColor: validationBgColor,
            color: validationTextColor,
            borderBottom: `2px solid ${validationColor}`,
            padding: '2px 4px',
            borderRadius: '4px',
            margin: '0 2px',
          }}
          onMouseEnter={() => setHoveredCitation(citation)}
          onMouseLeave={() => setHoveredCitation(null)}
          title={`Confidence: ${Math.round(overallConfidence * 100)}%`}
        >
          {citation.text}
          <span className="ml-1 text-xs font-bold">
            [{citation.sourceNumber}]
          </span>
        </span>
      )

      lastIndex = citation.position.end
    })

    // Add remaining text
    if (lastIndex < content.length) {
      elements.push(
        <span key="text-end">
          {content.slice(lastIndex)}
        </span>
      )
    }

    return elements
  }

  // Get validation icon
  const getValidationIcon = (confidence: number) => {
    if (confidence >= 0.8) return <CheckCircle className="h-4 w-4 text-green-500" />
    if (confidence >= 0.6) return <AlertCircle className="h-4 w-4 text-yellow-500" />
    return <XCircle className="h-4 w-4 text-red-500" />
  }

  // Get validation label
  const getValidationLabel = (confidence: number) => {
    if (confidence >= 0.8) return 'Excellent'
    if (confidence >= 0.6) return 'Good'
    if (confidence >= 0.4) return 'Fair'
    return 'Poor'
  }

  return (
    <div className="space-y-6">
      {/* Article Header */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-2xl">{article.title}</CardTitle>
              <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                <span>{article.wordCount} words</span>
                <span>{article.citationCount} citations</span>
                <span>{article.sourcesUsed} sources</span>
                <span>{new Date(article.generatedAt).toLocaleDateString()}</span>
              </div>
            </div>
            <div className="flex space-x-2">
              {onValidate && (
                <Button variant="outline" onClick={onValidate}>
                  Validate Citations
                </Button>
              )}
              {onExport && (
                <Button onClick={onExport}>
                  Export Article
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Validation Summary */}
      {validationResults && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Info className="h-5 w-5" />
              <span>Validation Summary</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">
                  {Math.round(validationResults.confidenceScore * 100)}%
                </div>
                <div className="text-sm text-gray-600">Overall Confidence</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">
                  {validationResults.citationResults.filter(r => r.isAccurate).length}
                </div>
                <div className="text-sm text-gray-600">Accurate Citations</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">
                  {validationResults.contextResults.filter(r => r.contextPreserved).length}
                </div>
                <div className="text-sm text-gray-600">Context Preserved</div>
              </div>
            </div>

            <Button
              variant="outline"
              onClick={() => setShowValidationDetails(!showValidationDetails)}
              className="w-full"
            >
              {showValidationDetails ? 'Hide' : 'Show'} Detailed Validation Results
            </Button>

            {showValidationDetails && (
              <div className="mt-4 space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Risk Factors</h4>
                  <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                    {validationResults.riskFactors.map((factor, index) => (
                      <li key={index}>{factor}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Recommendations</h4>
                  <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                    {validationResults.recommendations.map((rec, index) => (
                      <li key={index}>{rec}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Article Content */}
      <Card>
        <CardHeader>
          <CardTitle>Article Content</CardTitle>
          <p className="text-sm text-gray-600">
            Hover over highlighted citations to see validation details. Colors indicate confidence levels:
            <span className="ml-2">
              <span className="inline-block w-3 h-3 bg-green-100 border border-green-500 rounded mr-1"></span>
              High confidence
              <span className="inline-block w-3 h-3 bg-yellow-100 border border-yellow-500 rounded mx-2"></span>
              Medium confidence
              <span className="inline-block w-3 h-3 bg-red-100 border border-red-500 rounded ml-1"></span>
              Low confidence
            </span>
          </p>
        </CardHeader>
        <CardContent>
          <div className="prose max-w-none">
            {renderArticleContent()}
          </div>
        </CardContent>
      </Card>

      {/* Citation Tooltip */}
      {hoveredCitation && (
        <div className="fixed z-50 bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-w-md">
          <div className="flex items-start justify-between mb-2">
            <h4 className="font-medium text-gray-900">Citation Details</h4>
            <button
              onClick={() => setHoveredCitation(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>
          
          <div className="space-y-2">
            <div>
              <p className="text-sm text-gray-600 mb-1">Citation Text:</p>
              <p className="text-sm font-medium">"{hoveredCitation.text}"</p>
            </div>
            
            <div>
              <p className="text-sm text-gray-600 mb-1">Source:</p>
              <p className="text-sm">
                {sources.find(s => s.sourceNumber === hoveredCitation.sourceNumber)?.title || 'Unknown'}
              </p>
            </div>

            {(() => {
              const citationValidation = getCitationValidation(hoveredCitation)
              const contextValidation = getContextValidation(hoveredCitation)
              
              if (!citationValidation && !contextValidation) return null

              return (
                <div className="space-y-2">
                  {citationValidation && (
                    <div className="flex items-center space-x-2">
                      {getValidationIcon(citationValidation.confidence)}
                      <span className="text-sm">
                        Citation Accuracy: {getValidationLabel(citationValidation.confidence)} ({Math.round(citationValidation.confidence * 100)}%)
                      </span>
                    </div>
                  )}
                  
                  {contextValidation && (
                    <div className="flex items-center space-x-2">
                      {getValidationIcon(contextValidation.confidence)}
                      <span className="text-sm">
                        Context Preservation: {getValidationLabel(contextValidation.confidence)} ({Math.round(contextValidation.confidence * 100)}%)
                      </span>
                    </div>
                  )}
                </div>
              )
            })()}
          </div>
        </div>
      )}
    </div>
  )
}

