# <div align="center"> Vortex AI Core: Full Architecture </div>
<div align="center">
  <img src="../docs/assets/vortex_rag_logo.png" alt="Vortex RAG Logo" width="200"/>
  <br>
  <strong>High-Performance Retrieval-Augmented Generation (RAG) Service</strong>
  <br>
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-Framework-teal.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vector%20DB-Qdrant-orange.svg" alt="Qdrant">
  <img src="https://img.shields.io/badge/ML%20Core-Llama%203.2-purple.svg" alt="Llama">
</div>

---

## 🧬 Full Architecture Overview

The **Vortex AI Core** is designed for high-concurrency, low-latency AI interactions. The architecture is split into two primary asynchronous pipelines: the **Knowledge Ingestion Pipeline** and the **RAG Query Pipeline**.

### 🏗️ Global System Diagram

```mermaid
graph TD
    subgraph "Clients & Gateway"
        User((User)) -->|HTTPS| Frontend[React UI]
        Frontend -->|API| Gateway[Express Gateway]
    end

    subgraph "AI Core (FastAPI)"
        Gateway -->|Internal RPC| Router[Ingestion/Query Routers]
        
        subgraph "Ingestion Pipeline"
            Router -->|POST /upload| Validator[Sync Validator]
            Validator -->|Background| Worker[Job Worker]
            Worker -->|PDF/DOCX| DocLoader[Document Loader]
            Worker -->|URL| Scraper[Recursive Web Crawler]
            DocLoader & Scraper -->|Raw Text| Chunker[Semantic Chunker]
            Chunker -->|Raw Chunks| Refiner["AI Refinement Layer (Llama 3.2)"]
            Refiner -->|Structured JSON| Embedder[Sentence-Transformers]
            Embedder -->|Vectors + Metadata| VectorDB[(Qdrant Vector Store)]
        end

        subgraph "RAG Query Pipeline"
            Router -->|POST /query| CacheCheck{Redis Cache Hit?}
            CacheCheck -->|Yes| FastPath[Return Cached Answer]
            CacheCheck -->|No| Retriever[Context Retriever]
            Retriever -->|Embed Query| Embedder
            Retriever -->|Search Top-K| VectorDB
            Retriever -->|Context Chunks| PromptEngine[Prompt Construction]
            PromptEngine -->|System + Context + Query| LLM[Inference (Llama 3.2 3B)]
            LLM -->|Stream/JSON| Output[Response Generator]
            Output -->|Background| CacheSet[Update Redis]
            Output -->|Final| User
        end
    end

    subgraph "Infrastructure"
        Redis[(Redis Cache)]
        Qdrant[(Qdrant Vector DB)]
        LLM_CPP[Llama-cpp Engine]
    end

    CacheCheck -.-> Redis
    CacheSet -.-> Redis
    LLM -.-> LLM_CPP
```

---

## 📥 1. AI-Driven Ingestion Lifecycle

Unlike standard RAG systems, Vortex employs an **AI Refinement Layer** before vectorization. This ensures that the vector database contains high-quality, education-centric knowledge rather than raw noise.

### The Metadata Distillation Process:
Every text chunk passes through a specialized **System Instruction** for **Llama 3.2 3B**:
1.  **Noise Removal**: Boilerplate, ads, and repetitions are stripped.
2.  **Classification**: Chunks are tagged by `framework` (React, Node, etc.), `topic`, and `subtopic`.
3.  **Educational Scaling**: Each chunk is assigned a `difficulty` level (beginner | intermediate | advanced).
4.  **Keyword Extraction**: Distilling core concepts into a `keywords` array to enhance dense retrieval.

**Example Structured Storage:**
```json
{
  "framework": "react",
  "topic": "hooks",
  "subtopic": "useState",
  "cleaned_text": "useState is a Hook that lets you add React state to function components...",
  "keywords": ["react", "useState", "state", "hook"],
  "difficulty": "beginner"
}
```

---

## 💬 2. RAG Query Execution (Sub-15s Target)

The query pipeline is optimized for performance using **Asynchronous I/O** and **Thread-Pool Offloading**.

### Step-by-Step Flow:
1.  **SSRF & Prompt Sanitization**: Synchronous validation to prevent injection attacks and illegal URL access.
2.  **Distributed Caching**: Redis-backed fast-path for query results. If a query hash exists, the response is returned in `< 50ms`.
3.  **Semantic Retrieval**:
    *   Query is vectorized using `Sentence-Transformers`.
    *   Qdrant performs a similarity search, returning the **Top-K** (default 3-5) most relevant context chunks.
4.  **Prompt Engineering**:
    *   System Prompt forces "AI Tutor" behavior (concise, code-first, theory-backed).
    *   Context is injected into a specialized **Llama 3.2 Chat Template**.
5.  **Non-Blocking Inference**: The heavy LLM generation call is executed in a `ThreadPoolExecutor` to ensure the FastAPI event loop remains responsive to other users.

---

## 🛠️ Technical Specifications

### AI Models & Engines
*   **Main LLM**: `Llama 3.2 3B` (GGUF 4-bit Quantized)
*   **Embedding Model**: `all-MiniLM-L6-v2` (Fast & Efficient)
*   **Inference Engine**: `llama-cpp-python` (Optimized for CPU/GPU threading)

### Storage & Performance
*   **Vector Database**: `Qdrant` (Indexing: HNSW, Distance: Cosine)
*   **Caching Layer**: `Redis` (Atomic query-context mapping)
*   **Concurrency**: 4+ Workers with `uvicorn` (Multi-user concurrency support)

### Infrastructure Layer
*   **Orchestration**: `Docker Compose`
*   **Internal Network**: `rag-net` (Subnet: 172.x.x.x)
*   **Volumes**: Persistent storage for Qdrant (`qdrant_storage`) and models.

---
<p>
<strong>Under Development...</strong>
</p>

<p>
  Developed by <strong>Vennilavan Manoharan</strong> • 2026
</p>

<p align="center">
<strong>Vortex AI Core </strong> — Powering the Future of Agentic Learning.
</p>