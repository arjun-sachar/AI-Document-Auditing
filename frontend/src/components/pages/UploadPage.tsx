'use client'

import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { FileUpload } from '@/components/features/FileUpload'
import { FileUpload as FileUploadType } from '@/types'

interface UploadPageProps {
  onFilesSelected: (files: File[]) => void
  onFileRemove: (fileId: string) => void
  onCreateKnowledgeBase: (name: string, description?: string) => void
  uploads: FileUploadType[]
  isCreatingKB: boolean
}

export const UploadPage: React.FC<UploadPageProps> = ({
  onFilesSelected,
  onFileRemove,
  onCreateKnowledgeBase,
  uploads,
  isCreatingKB,
}) => {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Upload Knowledge Base
        </h1>
        <p className="text-lg text-gray-600">
          Upload your documents to create a knowledge base for article generation
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Upload Documents</CardTitle>
        </CardHeader>
        <CardContent>
          <FileUpload
            onFilesSelected={onFilesSelected}
            onFileRemove={onFileRemove}
            onCreateKnowledgeBase={onCreateKnowledgeBase}
            uploads={uploads}
            maxFiles={50}
            maxSize={50 * 1024 * 1024} // 50MB
            acceptedTypes={['.pdf', '.txt', '.docx', '.md']}
            isCreatingKB={isCreatingKB}
          />
        </CardContent>
      </Card>
    </div>
  )
}

