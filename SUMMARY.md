# Tana Helper - Project Summary

## Overview
**Tana Helper** is a sophisticated service that extends [Tana](https://tana.inc) (a knowledge management/PKM application) with AI-powered integrations, data processing, and visualization capabilities. It acts as a bridge between Tana and external services, transforming Tana from a standalone tool into an AI-enhanced ecosystem.

## Architecture

### Backend Service (`/service/`)
- **Framework**: FastAPI with Python 3.11+
- **Main Entry**: `service/main.py` - FastAPI application with middleware for request logging, settings refresh
- **Package Management**: uv (modern Python package manager)
- **Key Dependencies**: 
  - OpenAI API, FastAPI, Uvicorn
  - ChromaDB, Weaviate (vector databases)
  - httpx, Rich, PyQt6

### Frontend Web Application (`/webapp/`)
- **Framework**: React 18 + TypeScript with Vite
- **Package Management**: pnpm
- **UI Stack**: Tailwind CSS + Radix UI components
- **State Management**: Zustand
- **Key Features**: SPA with collapsible sidebar, multiple specialized views

## Core Functionality

### 1. AI-Powered Webhooks (`/endpoints/webhooks.py`)
- Upload Tana supertag schemas to create custom webhook endpoints
- Process unstructured text → structured Tana nodes via OpenAI
- Integration with Zapier, Cloudmailin for automated data ingestion
- Template-based prompt system using Jinja2

### 2. Knowledge Graph Visualization
- Interactive 2D/3D force graphs of Tana data relationships
- Configurable visualization options (nodes, tags, references, schema links)
- React Force Graph components for rendering

### 3. RAG (Retrieval-Augmented Generation)
- Index Tana content for semantic search
- Multiple vector database backends (ChromaDB, Weaviate)
- AI-powered research and content discovery capabilities

### 4. Data Processing Pipeline
- Tana-specific data types and parsers (`tana_types.py`, `tanaparser.py`)
- JSON conversion utilities (`json2tana.py`)
- Calendar integration (macOS only via AppleScript/Swift)
- Bulk operations and data cleanups

## Key Endpoints Structure
- `/ui/` - React web application
- `/webhook/{schema}` - Dynamic webhook endpoints
- `/template/{schema}` - Template management
- Various specialized endpoints: calendar, chroma, class_diagram, graph_view, etc.

## Development Practices

### Code Quality
- **Python**: Ruff for linting + formatting (88 char line length)
- **TypeScript**: Prettier + ESLint (100 char line length, single quotes)
- **Standards**: Minimal surgical changes, preserve comments, proper documentation

### Project Structure
- Scripts defined in `pyproject.toml` [project.scripts] (not Makefile)
- Cross-platform build system with PyInstaller
- Comprehensive test suite with pytest

### Deployment
- Desktop application packaging for macOS/Windows
- DMG creation for macOS distribution
- Ngrok support for local webhook testing
- Environment-based configuration (`.env` files)

## Technology Integrations

### AI/ML Services
- OpenAI API (primary AI provider)
- Ollama support for local models
- Llama Index for RAG capabilities

### Vector Databases
- ChromaDB (primary)
- Weaviate 
- Pinecone (legacy/experimental)

### Visualization
- Mermaid diagrams
- React Force Graph (2D/3D)
- Custom class diagram rendering

## Configuration & Auth
- Tana API Token required for all Tana operations
- OpenAI API Key for AI processing
- Header-based auth override support (`x-tana-api-token`, `x-openai-api-key`)
- Settings refresh middleware for multi-worker deployments

## Notable Design Patterns
- Middleware-based request logging with snowflake IDs
- Template-driven webhook processing
- Settings injection via headers for flexibility
- Reverse proxy capabilities for Tana.pub content
- Rich logging with structured output

## Development Context
- Active development on "batching" branch
- Modern Python/Node.js toolchain (uv, pnpm)
- Emphasis on cross-platform compatibility
- Focus on extending Tana's capabilities rather than replacing them 