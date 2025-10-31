'use client'

import React, { useState, useMemo, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { GeneratedArticle, Citation, ValidationResults, Source } from '@/types'
import { getValidationColor, getValidationBgColor, getValidationTextColor } from '@/lib/design-system'
import { CheckCircle, AlertCircle, XCircle, Info, Download, RotateCcw } from 'lucide-react'

interface ViewPageProps {
  article: GeneratedArticle
  validationResults?: ValidationResults
  sources: Source[]
  onExport?: () => void
  onValidate?: () => void
  onGenerateNew?: () => void
}

export const ViewPage: React.FC<ViewPageProps> = ({
  article,
  validationResults,
  sources,
  onExport,
  onValidate,
  onGenerateNew,
}) => {
  const [hoveredCitation, setHoveredCitation] = useState<Citation | null>(null)
  const hoverTimeoutRef = useRef<NodeJS.Timeout | null>(null)
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

    // Sort citations by position for proper rendering (with fallback for missing position data)
    const sortedCitations = [...article.citations].sort((a, b) => {
      // Handle cases where position data might be missing
      const aStart = a.position?.start ?? 0
      const bStart = b.position?.start ?? 0
      return aStart - bStart
    })

    sortedCitations.forEach((citation, index) => {
      // Add text before citation (with fallback for missing position data)
      const citationStart = citation.position?.start ?? 0
      const citationEnd = citation.position?.end ?? citationStart + citation.text.length
      
      if (citationStart > lastIndex) {
        elements.push(
          <span key={`text-${index}`}>
            {content.slice(lastIndex, citationStart)}
          </span>
        )
      }

      // Add citation with validation styling
      const citationValidation = getCitationValidation(citation)
      const contextValidation = getContextValidation(citation)
      
      // Calculate overall confidence (use citation's own confidence if available, otherwise calculate from validation)
      const citationConfidence = citation.confidence || 0
      const overallConfidence = citationConfidence > 0 
        ? citationConfidence 
        : (citationValidation && contextValidation
          ? (citationValidation.confidence + contextValidation.confidence) / 2
          : citationValidation?.confidence || contextValidation?.confidence || 0.5) // Default to 0.5 (medium) if no confidence

      const validationColor = getValidationColor(overallConfidence)
      const validationBgColor = getValidationBgColor(overallConfidence)
      const validationTextColor = getValidationTextColor(overallConfidence)

      elements.push(
        <span
          key={`citation-${index}`}
          className="relative inline-block cursor-pointer group"
          style={{
            backgroundColor: validationBgColor,
            color: validationTextColor,
            borderBottom: `2px solid ${validationColor}`,
            padding: '2px 6px',
            borderRadius: '4px',
            margin: '0 2px',
            transition: 'background-color 0.15s ease, color 0.15s ease',
          }}
          onMouseEnter={() => {
            // Clear any existing timeout
            if (hoverTimeoutRef.current) {
              clearTimeout(hoverTimeoutRef.current)
            }
            // Set citation immediately for better UX
            setHoveredCitation(citation)
          }}
          onMouseLeave={() => {
            // Clear any existing timeout
            if (hoverTimeoutRef.current) {
              clearTimeout(hoverTimeoutRef.current)
            }
            // Add longer delay to allow reading the tooltip
            hoverTimeoutRef.current = setTimeout(() => {
              setHoveredCitation(null)
            }, 1000) // Increased from 200ms to 1000ms
          }}
          title={`Confidence: ${Math.round(overallConfidence * 100)}%`}
        >
          {citation.text}
          <span className="ml-1 text-xs font-bold">
            [{citation.source_number || citation.sourceNumber || '?'}]
          </span>
          
          {/* Hover tooltip */}
          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none z-10 max-w-xs">
            Confidence: {Math.round(overallConfidence * 100)}%
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
          </div>
        </span>
      )

      lastIndex = citationEnd
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
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Article Header */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-3xl mb-2">{article.title}</CardTitle>
              <div className="flex items-center space-x-6 mt-2 text-sm text-gray-500">
                <span className="flex items-center">
                  <span className="font-medium">Words:</span> {article.wordCount}
                </span>
                <span className="flex items-center">
                  <span className="font-medium">Citations:</span> {article.citationCount}
                </span>
                <span className="flex items-center">
                  <span className="font-medium">Sources:</span> {article.sourcesUsed}
                </span>
                <span className="flex items-center">
                  <span className="font-medium">Generated:</span> {new Date(article.generatedAt).toLocaleDateString()}
                </span>
                <span className="flex items-center">
                  <span className="font-medium">Context Rating:</span>
                  <div className="relative group">
                    <div className={`ml-1 px-2 py-1 rounded text-xs font-medium cursor-help ${
                      (article.overallContextRating || 0) >= 0.8 ? 'bg-green-100 text-green-800' :
                      (article.overallContextRating || 0) >= 0.6 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {Math.round((article.overallContextRating || 0) * 100)}%
                    </div>
                    
                    {/* Context Rating Details Tooltip */}
                    {article.contextRatingDetails && (
                      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-4 py-3 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-20 max-w-md">
                        <div className="font-semibold mb-2">Context Rating Breakdown:</div>
                        <div className="space-y-2">
                          {/* Overall Rating */}
                          <div className="border-b border-gray-600 pb-2">
                            <div className="font-medium">Overall Context Rating: {Math.round((article.contextRatingDetails.overall_rating || 0) * 100)}%</div>
                            <div className="text-gray-300 text-xs mt-1">{article.contextRatingDetails.explanation || 'No explanation available'}</div>
                          </div>
                          
                          {/* Direct Quotations */}
                          {article.contextRatingDetails.detailed_breakdown?.direct_quotations && (
                            <div className="border-b border-gray-600 pb-2">
                              <div className="font-medium">Direct Quotations:</div>
                              <div className="text-gray-300 text-xs mt-1">
                                {article.contextRatingDetails.detailed_breakdown.direct_quotations.explanation}
                              </div>
                            </div>
                          )}
                          
                          {/* Context Citations */}
                          {article.contextRatingDetails.detailed_breakdown?.context_citations && (
                            <div className="border-b border-gray-600 pb-2">
                              <div className="font-medium">Context Citations:</div>
                              <div className="text-gray-300 text-xs mt-1">
                                {article.contextRatingDetails.detailed_breakdown.context_citations.explanation}
                              </div>
                            </div>
                          )}
                          
                          {/* Source Coverage */}
                          {article.contextRatingDetails.detailed_breakdown?.source_coverage && (
                            <div className="border-b border-gray-600 pb-2">
                              <div className="font-medium">Source Coverage:</div>
                              <div className="text-gray-300 text-xs mt-1">
                                {article.contextRatingDetails.detailed_breakdown.source_coverage.explanation}
                              </div>
                            </div>
                          )}
                          
                          {/* Content Alignment */}
                          {article.contextRatingDetails.detailed_breakdown?.content_alignment && (
                            <div>
                              <div className="font-medium">Content Alignment:</div>
                              <div className="text-gray-300 text-xs mt-1">
                                {article.contextRatingDetails.detailed_breakdown.content_alignment.explanation}
                              </div>
                            </div>
                          )}
                        </div>
                        <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
                      </div>
                    )}
                  </div>
                </span>
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
                  <Download className="h-4 w-4 mr-2" />
                  Export Article
                </Button>
              )}
              {onGenerateNew && (
                <Button variant="outline" onClick={onGenerateNew}>
                  <RotateCcw className="h-4 w-4 mr-2" />
                  Generate New
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
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
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
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">
                  {validationResults.citationResults.length}
                </div>
                <div className="text-sm text-gray-600">Total Citations</div>
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
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              <strong>Citation Legend:</strong> Hover over highlighted citations to see validation details. 
              Colors indicate confidence levels:
              <span className="ml-2">
                <span className="inline-block w-3 h-3 bg-green-100 border border-green-500 rounded mr-1"></span>
                High confidence (80%+)
                <span className="inline-block w-3 h-3 bg-yellow-100 border border-yellow-500 rounded mx-2"></span>
                Medium confidence (60-79%)
                <span className="inline-block w-3 h-3 bg-red-100 border border-red-500 rounded ml-1"></span>
                Low confidence (&lt;60%)
              </span>
            </p>
          </div>
        </CardHeader>
        <CardContent>
          <div className="prose prose-lg max-w-none">
            <div className="text-gray-800 leading-relaxed">
              {renderArticleContent()}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Citation Details Modal */}
      {hoveredCitation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-96 overflow-y-auto">
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <h4 className="font-medium text-gray-900">Citation Details</h4>
                <button
                  onClick={() => setHoveredCitation(null)}
                  className="text-gray-400 hover:text-gray-600 text-xl"
                >
                  ×
                </button>
              </div>
              
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Citation Text:</p>
                  <p className="text-sm font-medium bg-gray-50 p-2 rounded">"{hoveredCitation.text}"</p>
                </div>
                
                <div>
                  <p className="text-sm text-gray-600 mb-1">Source:</p>
                  <p className="text-sm">
                    {sources.find(s => s.sourceNumber === hoveredCitation.sourceNumber)?.title || 'Unknown'}
                  </p>
                </div>
                
                <div>
                  <p className="text-sm text-gray-600 mb-1">Confidence Score:</p>
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${
                      hoveredCitation.confidence >= 0.8 ? 'bg-green-500' :
                      hoveredCitation.confidence >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}></div>
                    <p className="text-sm font-medium">
                      {Math.round((hoveredCitation.confidence || 0) * 100)}% 
                      ({hoveredCitation.confidence >= 0.8 ? 'High' : 
                        hoveredCitation.confidence >= 0.6 ? 'Medium' : 'Low'} confidence)
                    </p>
                  </div>
                </div>
                
                <div>
                  <p className="text-sm text-gray-600 mb-1">Validation Status:</p>
                  <p className="text-sm">
                    {hoveredCitation.source_found ? '✅ Source Found' : '❌ Source Not Found'}
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
          </div>
        </div>
      )}
    </div>
  )
}

