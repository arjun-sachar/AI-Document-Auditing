'use client'

import React, { useState, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { FileUpload } from '@/components/features/FileUpload'
import { FileUpload as FileUploadType } from '@/types'
import { generateId } from '@/lib/utils'
import { apiClient, validateFiles } from '@/lib/api'
import Link from 'next/link'
import { Home } from 'lucide-react'

export default function UploadPage() {
  const [uploads, setUploads] = useState<FileUploadType[]>([])
  const [isCreatingKB, setIsCreatingKB] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [notifications, setNotifications] = useState<{ id: string, message: string, type: 'success' | 'error' | 'info' }[]>([])

  const addNotification = useCallback((message: string, type: 'success' | 'error' | 'info' = 'info') => {
    const id = generateId()
    setNotifications(prev => [...prev, { id, message, type }])
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id))
    }, 5000)
  }, [])

  const handleFilesSelected = useCallback(async (files: File[]) => {
    console.log('Files selected:', files)
    setIsUploading(true)
    
    // Validate files first
    const acceptedTypes = [
      'application/pdf', 
      'text/plain', 
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
      'text/markdown',
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
    ]
    
    const maxSize = 200 * 1024 * 1024 // 200MB
    const { valid, invalid } = validateFiles(files, acceptedTypes, maxSize)
    
    // Show validation errors
    if (invalid.length > 0) {
      const errorMessages = invalid.map(({ file, reason }) => `${file.name}: ${reason}`).join('\n')
      addNotification(`Some files were rejected:\n${errorMessages}`, 'error')
    }
    
    if (valid.length === 0) {
      setIsUploading(false)
      return
    }
    
    // Create upload entries for each valid file
    const newUploads: FileUploadType[] = valid.map(file => ({
      id: generateId(),
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'uploading',
      progress: 0,
      knowledgeBaseId: undefined
    }))

    // Add new uploads to the list
    setUploads(prev => [...prev, ...newUploads])
    console.log('Added uploads:', newUploads)

    try {
      // Try to use real API first
      console.log('Attempting real API upload for files:', valid.map(f => f.name))
      const uploadResponses = await apiClient.uploadFiles(valid)
      console.log('API upload responses:', uploadResponses)
      
      // Update uploads with real API responses
      setUploads(prev => prev.map(upload => {
        const response = uploadResponses.find(r => r.fileName === upload.name)
        if (response) {
          console.log('Updating upload with response:', response)
          return {
            ...upload,
            status: response.status,
            progress: response.progress,
            error: response.error,
            fileId: response.fileId  // Store the file ID for knowledge base creation
          }
        }
        return upload
      }))
      
      addNotification(`${valid.length} files uploaded successfully!`, 'success')
      
    } catch (error) {
      console.error('API upload failed:', error)
      console.warn('API upload failed, falling back to simulation:', error)
      
      // Fallback to simulation if API is not available
      for (let i = 0; i < newUploads.length; i++) {
        const upload = newUploads[i]
        
        // Simulate upload progress
        for (let progress = 0; progress <= 100; progress += 10) {
          await new Promise(resolve => setTimeout(resolve, 100))
          
          console.log(`Updating progress for ${upload.name}: ${progress}%`)
          setUploads(prev => prev.map(u => 
            u.id === upload.id 
              ? { ...u, progress }
              : u
          ))
        }

        // Mark as completed
        setUploads(prev => prev.map(u => 
          u.id === upload.id 
            ? { ...u, status: 'completed', progress: 100 }
            : u
        ))
      }
      
      addNotification(`${valid.length} files uploaded successfully! (Simulation)`, 'success')
    }

    setIsUploading(false)
  }, [addNotification])

  const handleFileRemove = useCallback((fileId: string) => {
    setUploads(prev => prev.filter(upload => upload.id !== fileId))
  }, [])

  const handleCreateKnowledgeBase = useCallback(async (name: string, description?: string) => {
    setIsCreatingKB(true)
    
    try {
      // Get file IDs from completed uploads
      const fileIds = uploads
        .filter(upload => upload.status === 'completed' && upload.fileId)
        .map(upload => upload.fileId!)
      
      // Try to use real API first
      const kbResponse = await apiClient.createKnowledgeBase(name, description, fileIds)
      
      addNotification(`Knowledge base "${kbResponse.name}" created successfully!`, 'success')
      
      // Store the knowledge base ID for navigation
      const kbId = kbResponse.id
      
      // Clear uploads after successful creation
      setUploads([])
      
      // Navigate to generate page with knowledge base pre-selected
      window.location.href = `/generate?kb=${kbId}`
      
    } catch (error) {
      console.warn('API knowledge base creation failed, falling back to simulation:', error)
      
      // Fallback to simulation if API is not available
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      console.log('Creating knowledge base:', { name, description })
      
      addNotification(`Knowledge base "${name}" created successfully! (Simulation)`, 'success')
      
      // Clear uploads after successful creation
      setUploads([])
    } finally {
      setIsCreatingKB(false)
    }
  }, [uploads, addNotification])

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
              Upload Knowledge Base
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-300">
              Upload your documents to create a knowledge base for article generation
            </p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Upload Documents</CardTitle>
            </CardHeader>
            <CardContent>
              <FileUpload
                onFilesSelected={handleFilesSelected}
                onFileRemove={handleFileRemove}
                onCreateKnowledgeBase={handleCreateKnowledgeBase}
                uploads={uploads}
                maxFiles={50}
                maxSize={200 * 1024 * 1024} // 200MB for video files
                acceptedTypes={[
                  'application/pdf', 
                  'text/plain', 
                  'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                  'text/markdown',
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
                ]}
                isCreatingKB={isCreatingKB}
              />
            </CardContent>
          </Card>

          {/* Upload Status */}
          {isUploading && (
            <Card>
              <CardHeader>
                <CardTitle>Uploading Files</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Processing uploaded files... Please wait.
                </p>
              </CardContent>
            </Card>
          )}

          {/* Success Message */}
          {uploads.length > 0 && uploads.every(u => u.status === 'completed') && !isCreatingKB && (
            <Card className="border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20">
              <CardHeader>
                <CardTitle className="text-green-800 dark:text-green-200">
                  ✅ Files Uploaded Successfully
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-green-700 dark:text-green-300">
                  {uploads.length} files have been uploaded and are ready to be added to a knowledge base.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Notifications */}
      {notifications.length > 0 && (
        <div className="fixed top-4 right-4 z-50 space-y-2">
          {notifications.map(notification => (
            <div
              key={notification.id}
              className={`p-4 rounded-lg shadow-lg max-w-sm ${
                notification.type === 'success' 
                  ? 'bg-green-100 border border-green-300 text-green-800'
                  : notification.type === 'error'
                  ? 'bg-red-100 border border-red-300 text-red-800'
                  : 'bg-blue-100 border border-blue-300 text-blue-800'
              }`}
            >
              <div className="flex justify-between items-start">
                <p className="text-sm font-medium">{notification.message}</p>
                <button
                  onClick={() => setNotifications(prev => prev.filter(n => n.id !== notification.id))}
                  className="ml-2 text-gray-500 hover:text-gray-700"
                >
                  ×
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
