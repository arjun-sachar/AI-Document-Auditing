import { create } from 'zustand'
import { 
  GenerationForm, 
  GenerationProgress, 
  GeneratedArticle, 
  ValidationResults,
  KnowledgeBase,
  FileUpload 
} from '@/types'

interface GenerationStore {
  // Current generation state
  currentGeneration: GenerationForm | null
  progress: GenerationProgress
  currentArticle: GeneratedArticle | null
  validationResults: ValidationResults | null
  
  // Knowledge bases
  knowledgeBases: KnowledgeBase[]
  selectedKnowledgeBase: KnowledgeBase | null
  
  // File uploads
  fileUploads: FileUpload[]
  
  // Articles history
  articles: GeneratedArticle[]
  
  // Actions
  setCurrentGeneration: (form: GenerationForm) => void
  updateProgress: (progress: Partial<GenerationProgress>) => void
  setCurrentArticle: (article: GeneratedArticle) => void
  setValidationResults: (results: ValidationResults) => void
  
  // Knowledge base actions
  setKnowledgeBases: (bases: KnowledgeBase[]) => void
  setSelectedKnowledgeBase: (base: KnowledgeBase | null) => void
  addKnowledgeBase: (base: KnowledgeBase) => void
  
  // File upload actions
  addFileUpload: (upload: FileUpload) => void
  updateFileUpload: (id: string, updates: Partial<FileUpload>) => void
  removeFileUpload: (id: string) => void
  
  // Article actions
  addArticle: (article: GeneratedArticle) => void
  updateArticle: (id: string, updates: Partial<GeneratedArticle>) => void
  removeArticle: (id: string) => void
  
  // Reset actions
  resetGeneration: () => void
  resetAll: () => void
}

export const useGenerationStore = create<GenerationStore>((set, get) => ({
  // Initial state
  currentGeneration: null,
  progress: {
    stage: 'idle',
    percentage: 0,
    currentStep: '',
    estimatedTime: 0,
  },
  currentArticle: null,
  validationResults: null,
  knowledgeBases: [],
  selectedKnowledgeBase: null,
  fileUploads: [],
  articles: [],

  // Actions
  setCurrentGeneration: (form) => set({ currentGeneration: form }),
  
  updateProgress: (progress) => set((state) => ({
    progress: { ...state.progress, ...progress }
  })),
  
  setCurrentArticle: (article) => set({ currentArticle: article }),
  
  setValidationResults: (results) => set({ validationResults: results }),
  
  // Knowledge base actions
  setKnowledgeBases: (bases) => set({ knowledgeBases: bases }),
  
  setSelectedKnowledgeBase: (base) => set({ selectedKnowledgeBase: base }),
  
  addKnowledgeBase: (base) => set((state) => ({
    knowledgeBases: [...state.knowledgeBases, base]
  })),
  
  // File upload actions
  addFileUpload: (upload) => set((state) => ({
    fileUploads: [...state.fileUploads, upload]
  })),
  
  updateFileUpload: (id, updates) => set((state) => ({
    fileUploads: state.fileUploads.map(upload =>
      upload.id === id ? { ...upload, ...updates } : upload
    )
  })),
  
  removeFileUpload: (id) => set((state) => ({
    fileUploads: state.fileUploads.filter(upload => upload.id !== id)
  })),
  
  // Article actions
  addArticle: (article) => set((state) => ({
    articles: [article, ...state.articles]
  })),
  
  updateArticle: (id, updates) => set((state) => ({
    articles: state.articles.map(article =>
      article.id === id ? { ...article, ...updates } : article
    )
  })),
  
  removeArticle: (id) => set((state) => ({
    articles: state.articles.filter(article => article.id !== id)
  })),
  
  // Reset actions
  resetGeneration: () => set({
    currentGeneration: null,
    progress: {
      stage: 'idle',
      percentage: 0,
      currentStep: '',
      estimatedTime: 0,
    },
    currentArticle: null,
    validationResults: null,
  }),
  
  resetAll: () => set({
    currentGeneration: null,
    progress: {
      stage: 'idle',
      percentage: 0,
      currentStep: '',
      estimatedTime: 0,
    },
    currentArticle: null,
    validationResults: null,
    knowledgeBases: [],
    selectedKnowledgeBase: null,
    fileUploads: [],
    articles: [],
  }),
}))

