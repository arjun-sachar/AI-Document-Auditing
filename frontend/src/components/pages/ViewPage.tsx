'use client'

import React, { useState, useMemo, useEffect } from 'react'
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
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null)
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

  const truncateSnippet = (text: string, maxLength: number) => {
    if (!text) return ''
    if (text.length <= maxLength) return text
    return `${text.slice(0, maxLength - 3)}...`
  }

  const getArticleSnippet = (citation: Citation, window = 220) => {
    if ((citation as any).article_excerpt || citation.articleExcerpt) {
      return truncateSnippet((citation as any).article_excerpt || citation.articleExcerpt || '', 800)
    }

    const content = article.content || ''
    if (!content) return ''

    const { start, end } = citation.position || {}
    if (typeof start === 'number' && typeof end === 'number' && start >= 0 && end <= content.length) {
      const snippetStart = Math.max(0, start - window)
      const snippetEnd = Math.min(content.length, end + window)
      return truncateSnippet(content.slice(snippetStart, snippetEnd).trim(), 480)
    }

    const citationText = (citation.text || '').toLowerCase().trim()
    if (!citationText) return ''

    const matchIndex = content.toLowerCase().indexOf(citationText)
    if (matchIndex !== -1) {
      const snippetStart = Math.max(0, matchIndex - window)
      const snippetEnd = Math.min(content.length, matchIndex + citationText.length + window)
      return truncateSnippet(content.slice(snippetStart, snippetEnd).trim(), 480)
    }

    return ''
  }

  const getSourceSnippet = (citation: Citation, window = 220) => {
    if ((citation as any).source_excerpt || citation.sourceExcerpt) {
      return truncateSnippet((citation as any).source_excerpt || citation.sourceExcerpt || '', 800)
    }

    const sourceNumber = citation.sourceNumber || (citation as any).source_number
    if (!sourceNumber) return ''

    const source = sources.find(s => s.sourceNumber === sourceNumber)
    const content = source?.content || ''
    if (!content) return ''

    const citationText = (citation.text || '').toLowerCase().trim()
    if (!citationText) return truncateSnippet(content.trim(), 800)

    const matchIndex = content.toLowerCase().indexOf(citationText)
    if (matchIndex !== -1) {
      const snippetStart = Math.max(0, matchIndex - window)
      const snippetEnd = Math.min(content.length, matchIndex + citationText.length + window)
      return truncateSnippet(content.slice(snippetStart, snippetEnd).trim(), 800)
    }

    return truncateSnippet(content.trim(), 480)
  }

  useEffect(() => {
    if (!activeCitation) return

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setActiveCitation(null)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [activeCitation])

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
      let citationEnd = citation.position?.end ?? citationStart + citation.text.length
      
      // Get the actual text from article at citation position
      let rawCitationText = content.slice(citationStart, citationEnd)
      
      // Check if the article content after the citation contains a [Source X] marker
      // We need to include it in the citationEnd to avoid duplicating it
      const textAfterCitation = content.slice(citationEnd, citationEnd + 20)
      const sourceMarkerAfter = textAfterCitation.match(/^\s*\[Source\s+\d+\]/i)
      
      if (sourceMarkerAfter) {
        // Extend citationEnd to include the source marker so it's not rendered separately
        citationEnd += sourceMarkerAfter[0].length
        rawCitationText = content.slice(citationStart, citationEnd)
      }
      
      if (lastIndex < citationStart) {
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

      // Get source number separately (not from the text)
      const sourceNumber = citation.sourceNumber || (citation as any).source_number
      
      // Use the actual text from the article at this position (with source marker removed)
      let displayContent = rawCitationText
      // Remove the [Source X] marker from the display if present
      displayContent = displayContent.replace(/\s*\[Source\s+\d+\]\s*$/gi, '').trim()
      
      // Only render if we have actual text to display
      if (displayContent && displayContent !== '""' && displayContent !== '') {
        const citationType = (citation as any).type || ''
        const normalisedType = typeof citationType === 'string' ? citationType.toLowerCase() : ''
        const shouldHighlight =
          normalisedType === 'quoted_text' ||
          normalisedType === 'direct_quote' ||
          normalisedType === 'quote' ||
          normalisedType.includes('quote')
        const isLowConfidence = overallConfidence < 0.6

        const baseStyle: React.CSSProperties = shouldHighlight
          ? {
              backgroundColor: validationBgColor,
              color: validationTextColor,
              borderBottom: `2px solid ${validationColor}`,
              padding: '3px 8px',
              borderRadius: '6px',
              margin: '0 3px',
              fontWeight: 500,
              boxShadow: `0 0 0 1px ${validationColor} inset`,
              transition: 'background-color 0.15s ease, color 0.15s ease, box-shadow 0.15s ease',
            }
          : {
              color: validationColor,
              borderBottom: `1px dashed ${validationColor}`,
              padding: '1px 4px',
              borderRadius: '4px',
              margin: '0 2px',
              backgroundColor: isLowConfidence ? validationBgColor : 'transparent',
              transition: 'border-color 0.15s ease, color 0.15s ease, background-color 0.15s ease',
            }

        elements.push(
          <React.Fragment key={`citation-fragment-${index}`}>
            <span
              className="relative inline-block cursor-pointer group focus:outline-none"
              style={baseStyle}
              title={`Source ${sourceNumber || 'N/A'} - Confidence: ${Math.round(overallConfidence * 100)}%`}
              onClick={() => setActiveCitation(citation)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault()
                  setActiveCitation(citation)
                }
              }}
              role="button"
              tabIndex={0}
            >
              {displayContent}
              {/* Hover tooltip */}
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none z-10 max-w-xs shadow-lg whitespace-nowrap">
                <div className="text-center">
                  <div className="font-medium">Source {sourceNumber || 'N/A'}</div>
                  <div className="text-gray-300 mt-1">Confidence: {Math.round(overallConfidence * 100)}%</div>
                </div>
                <div className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
              </div>
            </span>
            {/* Add source marker after the citation as a superscript */}
            {sourceNumber && (
              <sup className="text-xs font-medium text-gray-500 ml-0.5">
                [{sourceNumber}]
              </sup>
            )}
          </React.Fragment>
        )
      }

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
                      ((article as any).overallContextRating || 0) >= 0.8 ? 'bg-green-100 text-green-800' :
                      ((article as any).overallContextRating || 0) >= 0.6 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {Math.round(((article as any).overallContextRating || 0) * 100)}%
                    </div>
                    
                    {/* Context Rating Details Tooltip */}
                    {(article as any).contextRatingDetails && (
                      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-4 py-3 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-20 w-96">
                        <div className="font-semibold mb-3 text-base">Context Rating Breakdown</div>
                        <div className="grid grid-cols-2 gap-3">
                          {/* Overall Rating */}
                          <div className="col-span-2 border-b border-gray-600 pb-2">
                            <div className="flex items-center justify-between">
                              <span className="font-medium">Overall Rating:</span>
                              <span className="font-bold text-blue-400">{Math.round(((article as any).contextRatingDetails.overall_rating || 0) * 100)}%</span>
                            </div>
                          </div>
                          
                          {/* Direct Quotations */}
                          {(article as any).contextRatingDetails.detailed_breakdown?.direct_quotations && (
                            <div className="col-span-1">
                              <div className="font-medium text-xs mb-1">Direct Quotations</div>
                              <div className="text-gray-300 text-xs leading-tight">
                                {(article as any).contextRatingDetails.detailed_breakdown.direct_quotations.explanation}
                              </div>
                            </div>
                          )}
                          
                          {/* Context Citations */}
                          {(article as any).contextRatingDetails.detailed_breakdown?.context_citations && (
                            <div className="col-span-1">
                              <div className="font-medium text-xs mb-1">Context Citations</div>
                              <div className="text-gray-300 text-xs leading-tight">
                                {(article as any).contextRatingDetails.detailed_breakdown.context_citations.explanation}
                              </div>
                            </div>
                          )}
                          
                          {/* Source Coverage */}
                          {(article as any).contextRatingDetails.detailed_breakdown?.source_coverage && (
                            <div className="col-span-1">
                              <div className="font-medium text-xs mb-1">Source Coverage</div>
                              <div className="text-gray-300 text-xs leading-tight">
                                {(article as any).contextRatingDetails.detailed_breakdown.source_coverage.explanation}
                              </div>
                            </div>
                          )}
                          
                          {/* Content Alignment */}
                          {(article as any).contextRatingDetails.detailed_breakdown?.content_alignment && (
                            <div className="col-span-1">
                              <div className="font-medium text-xs mb-1">Content Alignment</div>
                              <div className="text-gray-300 text-xs leading-tight">
                                {(article as any).contextRatingDetails.detailed_breakdown.content_alignment.explanation}
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
              <strong>Citation Legend:</strong> Click (or hover) on highlighted citations to see validation details. 
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
      {activeCitation && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setActiveCitation(null)}
        >
          <div
            className="bg-white rounded-lg shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-y-auto"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="p-6 space-y-5">
              <div className="flex items-start justify-between">
                <div>
                  <h4 className="text-lg font-semibold text-gray-900">Citation Details</h4>
                  <p className="text-xs text-gray-500 mt-1">Click outside this panel or press Escape to close.</p>
                </div>
                <button
                  onClick={() => setActiveCitation(null)}
                  className="text-gray-400 hover:text-gray-600 text-xl"
                  aria-label="Close citation details"
                >
                  ×
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <p className="text-sm text-gray-600">Citation Text</p>
                  <p className="text-sm font-medium bg-gray-50 border border-gray-100 p-3 rounded leading-relaxed">
                    “{activeCitation.text}”
                  </p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-gray-600">Source</p>
                  <p className="text-sm font-medium">
                    {sources.find(s => s.sourceNumber === activeCitation.sourceNumber)?.title || 'Unknown'}
                  </p>
                  <p className="text-xs text-gray-500">
                    Source #{activeCitation.sourceNumber || (activeCitation as any).source_number || 'N/A'}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-50 border border-gray-100 rounded-lg p-3">
                  <p className="text-xs text-gray-500 mb-1">Confidence</p>
                  {(() => {
                    const citationValidation = getCitationValidation(activeCitation)
                    const contextValidation = getContextValidation(activeCitation)
                    const citationConfidence = activeCitation.confidence || 0
                    const overallConfidence = citationConfidence > 0
                      ? citationConfidence
                      : (citationValidation && contextValidation
                        ? (citationValidation.confidence + contextValidation.confidence) / 2
                        : citationValidation?.confidence || contextValidation?.confidence || 0.5)

                    return (
                      <div className="flex items-center space-x-2">
                        <div className={`w-3 h-3 rounded-full ${
                          overallConfidence >= 0.8 ? 'bg-green-500' :
                          overallConfidence >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}></div>
                        <p className="text-sm font-medium text-gray-900">
                          {Math.round(overallConfidence * 100)}% ({overallConfidence >= 0.8 ? 'High' : overallConfidence >= 0.6 ? 'Medium' : 'Low'})
                        </p>
                      </div>
                    )
                  })()}
                </div>

                <div className="bg-gray-50 border border-gray-100 rounded-lg p-3">
                  <p className="text-xs text-gray-500 mb-1">Validation Status</p>
                  <p className="text-sm">
                    {(activeCitation as any).source_found ? '✅ Source Found' : '❌ Source Not Found'}
                  </p>
                </div>

                <div className="bg-gray-50 border border-gray-100 rounded-lg p-3 space-y-1">
                  <p className="text-xs text-gray-500">Quote Insights</p>
                  <p className="text-sm">
                    <span className="font-medium">Type:</span> {(activeCitation as any).type || 'Not specified'}
                  </p>
                  {typeof activeCitation.contextAlignment === 'number' && (
                    <p className="text-sm">
                      <span className="font-medium">Context Alignment:</span> {Math.round((activeCitation.contextAlignment || 0) * 100)}%
                    </p>
                  )}
                  {typeof (activeCitation as any).quote_verbatim !== 'undefined' && (
                    <p className="text-sm">
                      <span className="font-medium">Verbatim:</span> {(activeCitation as any).quote_verbatim ? 'Yes' : 'Needs review'}
                    </p>
                  )}
                </div>
              </div>

              {(() => {
                const citationValidation = getCitationValidation(activeCitation)
                const contextValidation = getContextValidation(activeCitation)

                if (!citationValidation && !contextValidation) return null

                return (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {citationValidation && (
                      <div className="flex items-center space-x-2 bg-gray-50 border border-gray-100 rounded-lg p-3">
                        {getValidationIcon(citationValidation.confidence)}
                        <span className="text-sm">
                          Citation Accuracy: {getValidationLabel(citationValidation.confidence)} ({Math.round(citationValidation.confidence * 100)}%)
                        </span>
                      </div>
                    )}

                    {contextValidation && (
                      <div className="flex items-center space-x-2 bg-gray-50 border border-gray-100 rounded-lg p-3">
                        {getValidationIcon(contextValidation.confidence)}
                        <span className="text-sm">
                          Context Preservation: {getValidationLabel(contextValidation.confidence)} ({Math.round(contextValidation.confidence * 100)}%)
                        </span>
                      </div>
                    )}
                  </div>
                )
              })()}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-gray-200 pt-4">
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                    <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                    Article Context
                  </p>
                  <div className="text-xs bg-blue-50 border border-blue-100 p-3 rounded leading-relaxed">
                    {getArticleSnippet(activeCitation) || (
                      <span className="text-gray-400 italic">Context unavailable</span>
                    )}
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                    <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                    Source Excerpt
                    {((activeCitation as any).source_excerpt || activeCitation.sourceExcerpt) && (
                      <span className="ml-2 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">Verified</span>
                    )}
                  </p>
                  <div className="text-xs bg-green-50 border border-green-100 p-3 rounded leading-relaxed">
                    {getSourceSnippet(activeCitation) || (
                      <span className="text-gray-400 italic">Source excerpt unavailable</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

