# 🧠 LLM Copilot Framework

> Open-source, research-grade framework for developer copilots with MCP orchestration, hybrid RAG, streaming chat, and multi-agent workflows.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61dafb)](https://react.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Tags:** `#mcp` `#multi-agent` `#rag` `#weaviate` `#fastapi` `#react` `#streaming` `#gsoc`

## 🎯 Overview

This project builds an industry-grade copilot platform that combines:
- **MCP protocol** for tool routing and agent messaging
- **Hybrid RAG** (vector + BM25) for robust retrieval
- **Streaming chat** via SSE
- **Multi-agent workflows** (planner → coder → reviewer → tester)
- **Pluggable tools** with JSON-schema validation

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Frontend (React)                      │
│          Chat • Tools • Planner • Multi-Agent UI            │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                      MCP Protocol Layer                     │
│       Message routing • Tool registry • Validation          │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌──────────────┬──────────────┬──────────────┬────────────────┐
│  LLM Router  │  RAG Memory  │ Tool Agents  │ Agents (Meta)  │
│ (Groq/OpenAI)│ (Hybrid)     │ (MCP tools)  │ (Planner, etc.)│
└──────────────┴──────────────┴──────────────┴────────────────┘
```

## ✅ Implemented Features

### MCP & Tools
- Tool registry with JSON‑schema validation
- `/api/v1/tools/specs` for tool discovery
- Advanced tools:
  - `code_search` (regex search across workspace)
  - `file_read` (safe file range reads)
  - `calculator` (simple sanity tool)

### Multi-Agent Orchestration
- Planner → Coder → Reviewer → Tester workflow
- Endpoint: `/api/v1/agents/run`
- Planner with tool orchestration: `/api/v1/agents/plan`

### RAG Memory Engine
- Weaviate v4 client
- Hybrid retrieval (vector + BM25)
- Automatic fallback to BM25 when embeddings fail

### Streaming Chat
- SSE endpoint: `/api/v1/chat/stream`
- UI toggle in Chat page

### LLM Routing
- Groq + OpenAI providers
- Default provider switchable via config

## 🧩 Tech Stack

**Backend**
- FastAPI, Pydantic, Weaviate
- Groq + OpenAI (LLM + embeddings)
- Redis (optional)

**Frontend**
- React + TypeScript + Vite
- TanStack Query + Tailwind

## 🚀 Quick Start

### Backend (WSL)
```bash
cd /mnt/d/proj1/backend
poetry install
nohup poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
```

### Frontend (Windows)
```powershell
cd D:\proj1\frontend
npm install
npm run dev
```

Open the URL Vite prints (e.g., http://localhost:3002).

## 🔑 Environment

Set keys in [backend/.env](backend/.env):

```
GROQ_API_KEY=your_key
OPENAI_API_KEY=optional
EMBEDDING_PROVIDER=groq
```

## 🧪 Test the Advanced Features

### Tool Planner (MCP)
```
POST /api/v1/agents/plan
{"goal":"Find where MCPProtocol is defined and show the first 10 lines"}
```

### Multi-Agent Run
```
POST /api/v1/agents/run
{"goal":"Add a new endpoint to list tools with schemas"}
```

### Streaming Chat (SSE)
```
POST /api/v1/chat/stream
{"messages":[{"role":"user","content":"Say hello in one sentence."}]}
```

### Hybrid RAG Search
```
POST /api/v1/memory/search
{"query":"MCPProtocol","top_k":3,"mode":"hybrid"}
```

## 📌 Roadmap (Next)
- Plugin system (manifest + permissions)
- Evaluation harness (retrieval metrics + regression tests)
- MCP streaming tool traces in UI
- VS Code extension integration

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

MIT — see [LICENSE](LICENSE).
