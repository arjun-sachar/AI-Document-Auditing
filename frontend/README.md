# AI Document Auditing Tool - Frontend

A modern, user-friendly frontend for the AI Document Auditing Tool built with Next.js 14, React 18, and Tailwind CSS.

## Features

- **📁 File Upload**: Drag & drop folder upload for knowledge bases
- **🤖 Article Generation**: AI-powered article generation with real-time progress
- **📊 Citation Validation**: Visual validation with color-coded confidence scores
- **🎯 Hover Citations**: Interactive citations with source information on hover
- **📈 Real-time Progress**: Live updates during generation and validation
- **📱 Responsive Design**: Works on desktop, tablet, and mobile devices

## Technology Stack

- **Framework**: Next.js 14 with App Router
- **UI Library**: React 18 with TypeScript
- **Styling**: Tailwind CSS with custom design system
- **State Management**: Zustand for global state
- **Forms**: React Hook Form with Zod validation
- **Icons**: Lucide React
- **Animations**: Framer Motion

## Getting Started

### Prerequisites

- Node.js 18+ (installed via conda)
- Python 3.11+ (in ai-doc-env conda environment)
- All Python dependencies installed

### Installation

1. **Activate the conda environment**:
   ```bash
   conda activate ai-doc-env
   ```

2. **Install frontend dependencies**:
   ```bash
   cd frontend
   npm install
   ```

3. **Start the development servers**:
   ```bash
   # From the project root directory
   ./start_dev.sh
   ```

   This will start both the FastAPI backend (port 8000) and Next.js frontend (port 3000).

### Manual Setup

If you prefer to run the servers separately:

1. **Start the backend**:
   ```bash
   python backend_server.py
   ```

2. **Start the frontend** (in a new terminal):
   ```bash
   cd frontend
   npm run dev
   ```

## Usage

1. **Upload Knowledge Base**: Drag and drop files or click to select
2. **Configure Article**: Set topic, length, style, and advanced options
3. **Generate Article**: Click generate and watch real-time progress
4. **View Results**: See the article with color-coded citation validation
5. **Hover Citations**: Hover over highlighted citations to see validation details
6. **Export**: Download the article as a Markdown file

## Color Coding System

- **🟢 Green**: High confidence (80%+)
- **🟡 Yellow**: Medium confidence (60-79%)
- **🔴 Red**: Low confidence (<60%)

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js 14 App Router
│   │   ├── page.tsx           # Main page
│   │   ├── layout.tsx         # Root layout
│   │   └── globals.css        # Global styles
│   ├── components/            # React components
│   │   ├── ui/               # Base UI components
│   │   └── features/         # Feature components
│   ├── lib/                  # Utilities and configurations
│   ├── stores/               # Zustand stores
│   ├── types/                # TypeScript types
│   └── hooks/                # Custom React hooks
├── public/                   # Static assets
└── package.json             # Dependencies
```

## API Integration

The frontend communicates with the Python backend via FastAPI:

- **Base URL**: `http://localhost:8000`
- **Endpoints**: See `src/lib/api.ts` for all available endpoints
- **CORS**: Configured for localhost:3000

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Key Components

- **ArticleGenerator**: Main form for article configuration
- **ArticleViewer**: Displays generated articles with validation
- **FileUpload**: Handles file uploads with progress tracking
- **Progress**: Real-time progress indicator

## Customization

### Design System

Edit `src/lib/design-system.ts` to customize:
- Colors
- Typography
- Spacing
- Validation color mapping

### API Configuration

Update `src/lib/api.ts` to change:
- API base URL
- Request/response handling
- Error handling

## Troubleshooting

### Common Issues

1. **Port already in use**: Change ports in the startup script
2. **CORS errors**: Ensure backend is running on port 8000
3. **File upload fails**: Check file size limits and types
4. **Generation fails**: Verify API keys and backend connectivity

### Debug Mode

Set `NODE_ENV=development` for additional logging and debugging information.

## Contributing

1. Follow the existing code style
2. Use TypeScript for all new components
3. Add proper error handling
4. Include loading states
5. Test on multiple screen sizes

## License

This project is part of the AI Document Auditing Tool.