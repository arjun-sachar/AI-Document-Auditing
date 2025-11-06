'use client'

import React, { useCallback, useState, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Card, CardContent } from '@/components/ui/Card'
import { Progress } from '@/components/ui/Progress'
import { cn, formatFileSize } from '@/lib/utils'
import { FileUpload as FileUploadType } from '@/types'

interface FileUploadProps {
  onFilesSelected: (files: File[]) => void
  onFileRemove: (fileId: string) => void
  onCreateKnowledgeBase: (name: string, description?: string) => void
  uploads: FileUploadType[]
  maxFiles?: number
  maxSize?: number // in bytes
  acceptedTypes?: string[] // MIME types
  className?: string
  isCreatingKB?: boolean
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onFilesSelected,
  onFileRemove,
  onCreateKnowledgeBase,
  uploads,
  maxFiles = 50, // Increased from 10 to 50
  maxSize = 200 * 1024 * 1024, // Increased to 200MB for video files
  acceptedTypes = [
    'application/pdf',
    'text/plain',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/markdown',
    'application/msword',
    'application/vnd.oasis.opendocument.text',
    'application/rtf',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'video/mp4',
    'video/quicktime',
    'video/x-msvideo',
    'audio/mpeg',
    'audio/wav',
    'audio/mp4',
    'audio/m4a',
    'audio/x-m4a',
    'application/zip',
    'application/x-zip-compressed',
    'application/x-rar-compressed',
    'application/x-7z-compressed'
  ],
  className,
  isCreatingKB = false,
}) => {
  console.log('FileUpload component received uploads:', uploads)
  const [isDragActive, setIsDragActive] = useState(false)
  const [uploadMode, setUploadMode] = useState<'files' | 'folder'>('files')
  const [kbName, setKbName] = useState('')
  const [kbDescription, setKbDescription] = useState('')
  const [showCreateForm, setShowCreateForm] = useState(false)

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        onFilesSelected(acceptedFiles)
      }
    },
    [onFilesSelected]
  )

  const handleFolderUpload = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const files = event.target.files
      if (files && files.length > 0) {
        const fileArray = Array.from(files)
        onFilesSelected(fileArray)
      }
    },
    [onFilesSelected]
  )

  const { getRootProps, getInputProps, isDragReject } = useDropzone({
    onDrop,
    onDragEnter: () => setIsDragActive(true),
    onDragLeave: () => setIsDragActive(false),
    maxFiles,
    maxSize,
    accept: acceptedTypes.reduce((acc, mimeType) => {
      acc[mimeType] = []
      return acc
    }, {} as Record<string, string[]>),
    multiple: true,
  })

  const getFileIcon = (fileType: string) => {
    if (fileType.includes('pdf')) return '📄'
    if (fileType.includes('word') || fileType.includes('document')) return '📝'
    if (fileType.includes('text')) return '📃'
    if (fileType.includes('presentation') || fileType.includes('powerpoint')) return '📊'
    if (fileType.includes('video')) return '🎥'
    if (fileType.includes('audio')) return '🎵'
    if (fileType.includes('zip') || fileType.includes('rar') || fileType.includes('7z')) return '📦'
    return '📁'
  }

  const getStatusIcon = (status: FileUploadType['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      case 'uploading':
      case 'processing':
        return <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
      default:
        return <File className="h-4 w-4 text-gray-500" />
    }
  }

  const canCreateKB = uploads.length > 0 && uploads.every(upload => upload.status === 'completed')
  
  useEffect(() => {
    if (!isCreatingKB && uploads.length === 0) {
      setKbName('')
      setKbDescription('')
      setShowCreateForm(false)
    }
  }, [isCreatingKB, uploads.length])

  const handleCreateKnowledgeBase = () => {
    if (!kbName.trim()) {
      return
    }

    onCreateKnowledgeBase(kbName.trim(), kbDescription.trim() || undefined)
  }

  return (
    <div className={cn('w-full', className)}>
      {/* Upload Mode Selection */}
      <div className="flex space-x-2 mb-4">
        <Button
          variant={uploadMode === 'files' ? 'default' : 'outline'}
          onClick={() => setUploadMode('files')}
          className="flex-1"
        >
          📁 Individual Files
        </Button>
        <Button
          variant={uploadMode === 'folder' ? 'default' : 'outline'}
          onClick={() => setUploadMode('folder')}
          className="flex-1"
        >
          📦 Folder/ZIP Upload
        </Button>
      </div>

      {uploadMode === 'files' ? (
        <div
          {...getRootProps()}
          className={cn(
            'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
            isDragActive && !isDragReject
              ? 'border-blue-500 bg-blue-50'
              : isDragReject
              ? 'border-red-500 bg-red-50'
              : 'border-gray-300 hover:border-gray-400'
          )}
        >
          <input {...getInputProps()} />
          <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <p className="text-lg font-medium text-gray-900 mb-2">
            {isDragActive
              ? 'Drop files here...'
              : 'Drag & drop files here, or click to select'}
          </p>
          <p className="text-sm text-gray-500 mb-4">
            Upload up to {maxFiles} files (max {formatFileSize(maxSize)} each)
          </p>
          <p className="text-xs text-gray-400">
            Supported formats: PDF, TXT, DOCX, MD, DOC, ODT, RTF, PPTX, MP4, MOV, AVI, MP3, WAV, M4A, ZIP, RAR, 7Z
          </p>
          <Button variant="outline" className="mt-4">
            Choose Files
          </Button>
        </div>
      ) : (
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <div className="mb-4">
            <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <p className="text-lg font-medium text-gray-900 mb-2">
              Upload Folder or ZIP Archive
            </p>
            <p className="text-sm text-gray-500 mb-4">
              Select an entire folder or ZIP file containing documents
            </p>
            <p className="text-xs text-gray-400 mb-4">
              Supports: ZIP, RAR, 7Z archives and folder uploads
            </p>
          </div>
          
          <div className="space-y-3">
            <div>
              <input
                type="file"
                {...({ webkitdirectory: '', directory: '' } as any)}
                multiple
                onChange={handleFolderUpload}
                className="hidden"
                id="folder-upload"
              />
              <Button
                variant="outline"
                onClick={() => document.getElementById('folder-upload')?.click()}
                className="w-full"
              >
                📁 Choose Folder
              </Button>
            </div>
            
            <div>
              <input
                type="file"
                accept=".zip,.rar,.7z"
                onChange={handleFolderUpload}
                className="hidden"
                id="archive-upload"
              />
              <Button
                variant="outline"
                onClick={() => document.getElementById('archive-upload')?.click()}
                className="w-full"
              >
                📦 Choose ZIP/RAR/7Z Archive
              </Button>
            </div>
          </div>
        </div>
      )}

      {uploads.length > 0 && (
        <div className="mt-6 space-y-3">
          <h3 className="text-lg font-medium text-gray-900">Uploaded Files ({uploads.length})</h3>
          {uploads.map((upload) => (
            <Card key={upload.id} className="p-4">
              <CardContent className="p-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">
                      {getFileIcon(upload.type)}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {upload.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(upload.size)}
                      </p>
                      <p className="text-xs text-blue-600">
                        Status: {upload.status} | Progress: {upload.progress}%
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(upload.status)}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onFileRemove(upload.id)}
                      className="h-8 w-8 p-0"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                
                {(upload.status === 'uploading' || upload.status === 'processing') && (
                  <div className="mt-3">
                    <Progress
                      value={upload.progress}
                      size="sm"
                      color={
                        upload.status === 'uploading' ? 'default' : 'warning'
                      }
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {upload.status === 'uploading' ? 'Uploading...' : 'Processing...'}
                    </p>
                  </div>
                )}
                
                {upload.status === 'error' && upload.error && (
                  <p className="text-xs text-red-500 mt-2">{upload.error}</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {canCreateKB && (
        <div className="mt-6">
          <Card>
            <CardContent className="p-6">
              {isCreatingKB ? (
                <div className="text-center">
                  <div className="flex flex-col items-center justify-center space-y-4">
                    <div className="h-12 w-12 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">
                        Creating Knowledge Base
                      </h3>
                      <p className="text-sm text-gray-600">
                        Processing {uploads.length} files... Please wait.
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div>
                  <div className="text-center">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      Ready to Create Knowledge Base
                    </h3>
                    <p className="text-sm text-gray-600 mb-4">
                      {uploads.length} files uploaded successfully. Provide a name and optional description to continue.
                    </p>
                  </div>

                  {!showCreateForm ? (
                    <Button
                      onClick={() => setShowCreateForm(true)}
                      className="w-full"
                    >
                      Create Knowledge Base
                    </Button>
                  ) : (
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Knowledge Base Name *
                        </label>
                        <input
                          type="text"
                          value={kbName}
                          onChange={(event) => setKbName(event.target.value)}
                          placeholder="Enter knowledge base name..."
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Description (Optional)
                        </label>
                        <textarea
                          value={kbDescription}
                          onChange={(event) => setKbDescription(event.target.value)}
                          placeholder="Enter a description for your knowledge base..."
                          rows={3}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>

                      <div className="flex space-x-3">
                        <Button
                          onClick={handleCreateKnowledgeBase}
                          disabled={!kbName.trim() || isCreatingKB}
                          loading={isCreatingKB}
                          className="flex-1"
                        >
                          {isCreatingKB ? 'Creating...' : 'Create Knowledge Base'}
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => {
                            setShowCreateForm(false)
                            setKbName('')
                            setKbDescription('')
                          }}
                          className="flex-1"
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
