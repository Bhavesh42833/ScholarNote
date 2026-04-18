<div align="center">

# 📚 ScholarNote

### Intelligent RAG-Powered Document Chat

**Chat with any PDF, webpage, or YouTube video — and get cited, verified answers in under a second.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-scholarnote.studio-blue?style=for-the-badge)](https://www.scholarnote.studio)
[![GitHub](https://img.shields.io/badge/GitHub-Bhavesh42833-black?style=for-the-badge&logo=github)](https://github.com/Bhavesh42833)

</div>

---

## 📖 Overview

ScholarNote is a production-grade, serverless **Retrieval-Augmented Generation (RAG)** system that lets you have intelligent conversations with your documents. Upload a PDF, paste a URL, or drop a YouTube link — and within seconds you can ask questions, get inline-cited answers, and trace every response back to its exact source.

Built without any LangChain wrappers, ScholarNote uses a fully custom async Python backend orchestrating **LlamaIndex**, **Groq**, **Pinecone**, and **AWS** — delivering sub-second responses even over 40+ page documents.

### Why ScholarNote?

| Problem | ScholarNote's Solution |
|---|---|
| Slow document ingestion | Async pipeline cuts ingestion from 30s → **5s** |
| Unreliable retrieval | 6-stage pipeline cuts latency from 15s → **sub-second** |
| Hallucinated answers | Inline citations `[1][2]` with jump-to-source |
| Poor chunking quality | Markdown-aware per-source chunking + Voyage AI embeddings |
| Exam prep friction | Auto-classified question paper upload & analysis |

---

## ✨ Features

- 🗂️ **Multi-source ingestion** — PDFs, webpages (Firecrawl), YouTube transcripts
- ⚡ **Sub-second responses** — Groq inferencing engine with parallel async processing
- 📌 **Inline citations** — Every answer includes `[1]`, `[2]` references with jump-to-source
- 📝 **Question paper analysis** — Upload exam papers, auto-classify questions, retrieve answers per group
- 🔍 **6-stage retrieval pipeline** — Query expansion → deduplication → reranking → diversity filtering → RRF
- 🧩 **Markdown-aware chunking** — Per-source chunking strategies preserving document structure
- 🚫 **No framework wrappers** — Custom orchestration, full control over every pipeline stage
- 📊 **Multi-stage logging** — Per-stage timing metrics and status tracking throughout
- ☁️ **Serverless AWS deployment** — Zero idle compute, horizontal scaling via Lambda

---

## 🛠️ Tech Stack

### Frontend
<p>
  <img src="https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white"/>
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white"/>
  <img src="https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white"/>
</p>

### Backend
<p>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/LlamaIndex-6B21A8?style=for-the-badge&logo=llama&logoColor=white"/>
  <img src="https://img.shields.io/badge/Groq-F55036?style=for-the-badge&logo=groq&logoColor=white"/>
  <img src="https://img.shields.io/badge/Voyage_AI-5B21B6?style=for-the-badge&logoColor=white"/>
  <img src="https://img.shields.io/badge/LlamaParse-7C3AED?style=for-the-badge&logoColor=white"/>
  <img src="https://img.shields.io/badge/Firecrawl-FF4500?style=for-the-badge&logoColor=white"/>
</p>

### Infrastructure
<p>
  <img src="https://img.shields.io/badge/AWS_S3-FF9900?style=for-the-badge&logo=amazons3&logoColor=white"/>
  <img src="https://img.shields.io/badge/AWS_SQS-FF9900?style=for-the-badge&logo=amazonsqs&logoColor=white"/>
  <img src="https://img.shields.io/badge/AWS_Lambda-FF9900?style=for-the-badge&logo=awslambda&logoColor=white"/>
  <img src="https://img.shields.io/badge/DynamoDB-4053D6?style=for-the-badge&logo=amazondynamodb&logoColor=white"/>
  <img src="https://img.shields.io/badge/Pinecone-00C389?style=for-the-badge&logoColor=white"/>
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white"/>
</p>

---

## 📁 File Structure

```
ScholarNote/
├── 📁 api/
│   └── routes.py              # FastAPI route definitions
├── 📁 ingestion/
│   ├── pipeline.py            # Staged ingestion orchestrator
│   ├── loader.py              # PDF, webpage, YouTube loaders
│   ├── tranformers.py         # Chunking & question classification
│   └── query.py              # Question paper parsing pipeline
├── 📁 retrieval/
│   ├── pipeline.py            # Retrieval orchestrator
│   ├── retrievers.py          # Parallel multi-query retrievers
│   ├── fusion.py              # RRF + citation mapping
│   └── generation.py         # Answer generation with inline citations
├── 📁 core/
│   ├── llm.py                 # AsyncGroq LLM client
│   ├── aws.py                 # S3, SQS, DynamoDB clients
│   ├── database.py            # DynamoDB job lifecycle management
│   ├── model.py               # Data models & schemas
│   ├── resources.py           # Pinecone & embedding clients
│   ├── utils.py               # Shared utilities
│   ├── logger.py              # Stage-based structured logging
│   ├── exceptions.py          # Custom exception types
│   └── exceptionHandler.py   # Global exception handling
├── ingestion_handler.py       # Lambda ingestion entry point
├── routes_handler.py          # Lambda routes entry point
├── dockerfile                 # Multi-stage Docker build
├── requirements.txt           # Python dependencies
└── README.md
```

---

## 🔄 Ingestion Pipeline

The ingestion pipeline is fully asynchronous and staged. Each source flows through **Load → Transform → Embed → Store**.

```mermaid
flowchart LR
    A([👤 User Upload]) --> B[🌐 API Gateway]
    B --> C[📨 SQS Queue]
    C --> D[⚡ AWS Lambda]

    D --> E{Source Type}

    E -->|PDF| F[📄 S3 Download\nLlamaParse]
    E -->|Webpage| G[🌍 Firecrawl\nMarkdown Scrape]
    E -->|YouTube| H[🎬 Transcript\n+ Metadata]

    F --> I[SentenceSplitter\nchunks + overlap]
    G --> J[MarkdownNodeParser\n→ SentenceSplitter]
    H --> I

    I --> K[🧠 Voyage AI\nEmbeddings]
    J --> K

    K --> L[(🗄️ Pinecone\nVector Store)]
    L --> M[(📋 DynamoDB\nStatus: Complete)]
    M --> N([✅ Frontend\nStatus Poll Done])

    style A fill:#4F46E5,color:#fff,stroke:#4F46E5
    style N fill:#059669,color:#fff,stroke:#059669
    style K fill:#7C3AED,color:#fff,stroke:#7C3AED
    style L fill:#DC2626,color:#fff,stroke:#DC2626
    style C fill:#FF9900,color:#fff,stroke:#FF9900
    style D fill:#FF9900,color:#fff,stroke:#FF9900
    style M fill:#4053D6,color:#fff,stroke:#4053D6
```

> ⚡ `asyncio.gather` fans out parallel embedding calls and concurrent document streams — cutting ingestion from **30s → 5s**

### Stage Breakdown

| Stage | What happens |
|-------|-------------|
| **Load** | PDFs pulled from S3, webpages scraped via Firecrawl, YouTube converted from transcript + metadata |
| **Transform** | PDFs → `SentenceSplitter` with overlap · Webpages → `MarkdownNodeParser` then `SentenceSplitter` · YouTube → `SentenceSplitter` with timestamps |
| **Embed** | All chunks embedded via **Voyage AI** — ~75% accuracy improvement over naive baselines |
| **Store** | Vectors upserted to Pinecone with metadata · DynamoDB updated to `complete` · Frontend stops polling |

---

## 🔍 Retrieval Pipeline

A 6-stage pipeline optimized for accuracy, speed, and full source traceability.

```mermaid
flowchart LR
    A([💬 User Query]) --> B

    subgraph PIPELINE["  6-Stage Retrieval Pipeline  "]
        direction LR
        B[1️⃣ Query\nExpansion] --> C[2️⃣ Multi-Query\nRetrieval]
        C --> D[3️⃣ Deduplica-\ntion]
        D --> E[4️⃣ Reranking]
        E --> F[5️⃣ Diversity\nFiltering]
        F --> G[6️⃣ RRF\nFusion]
    end

    G --> H[🏗️ Context\nBuilder]
    H --> I[⚡ AsyncGroq\nGeneration]
    I --> J([📌 Answer +\nInline Citations])

    style A fill:#4F46E5,color:#fff,stroke:#4F46E5
    style J fill:#059669,color:#fff,stroke:#059669
    style G fill:#7C3AED,color:#fff,stroke:#7C3AED
    style I fill:#DC2626,color:#fff,stroke:#DC2626
    style PIPELINE fill:#1e1e2e,color:#fff,stroke:#7C3AED
```

> ⚡ Response latency reduced from **15s → sub-second (95% reduction)**

### Stage Breakdown

| Stage | What happens |
|-------|-------------|
| **1. Query Expansion** | AsyncGroq generates multiple semantic query variants to compensate for vocabulary mismatch |
| **2. Multi-Query Retrieval** | All variants hit Pinecone in parallel via `asyncio.gather`, retrieving top-k chunks each |
| **3. Deduplication** | Duplicate chunks across query variants removed by content hash |
| **4. Reranking** | Chunks scored against original query for semantic relevance |
| **5. Diversity Filtering** | Ensures context covers multiple source sections, not just one region |
| **6. RRF Fusion** | Reciprocal Rank Fusion merges results — rewards chunks ranked highly across multiple queries |

**Answer Generation:** Fused context passed to AsyncGroq with citation-forcing prompt → `[1]`, `[2]`... inline citations. Context builder returns reference map with file name, page, timestamps, URL for jump-to-source in UI.

---

## 📋 Question Paper Pipeline

```mermaid
flowchart LR
    A([📄 Upload\nQuestion Paper]) --> B[LlamaParse\nExtraction]
    B --> C[Question\nExtraction]
    C --> D[AsyncGroq\nClassification]
    D --> E[Group by\nTopic]
    E --> F[⚡ Parallel\nRetrieval per Group]
    F --> G([📌 Structured Answers\nwith Citations])

    style A fill:#4F46E5,color:#fff,stroke:#4F46E5
    style G fill:#059669,color:#fff,stroke:#059669
    style F fill:#7C3AED,color:#fff,stroke:#7C3AED
```

---

## 🏗️ Architecture Overview

```mermaid
flowchart TB
    subgraph FE["🖥️ Frontend — Vercel"]
        UI[Next.js + Tailwind]
    end

    subgraph AWS["☁️ AWS"]
        direction LR
        AG[API Gateway] --> LR[Routes Lambda]
        AG --> SQS[SQS Queue]
        SQS --> LI[Ingestion Lambda]
        LI --> S3[S3]
        LI --> DDB[(DynamoDB)]
        LR --> DDB
    end

    subgraph AI["🤖 AI Layer"]
        direction LR
        PC[(Pinecone)] 
        GR[Groq LLM]
        VA[Voyage AI]
        LP[LlamaParse]
        FC[Firecrawl]
    end

    UI -->|query / upload| AG
    UI -->|poll job status| AG
    LI --> LP & FC & VA & PC
    LR --> GR & PC

    style FE fill:#1e293b,color:#fff,stroke:#4F46E5
    style AWS fill:#1e293b,color:#fff,stroke:#FF9900
    style AI fill:#1e293b,color:#fff,stroke:#7C3AED
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.11+, Node.js 18+, Docker
- AWS account (S3, SQS, DynamoDB, Lambda)
- Pinecone, Groq, Voyage AI, LlamaCloud, Firecrawl API keys

### Backend

```bash
git clone https://github.com/Bhavesh42833/scholarnote-backend
cd scholarnote-backend
pip install -r requirements.txt
cp .env.example .env        # fill in keys
uvicorn api.routes:app --reload --port 8000
```

### Frontend

```bash
git clone https://github.com/Bhavesh42833/scholarnote-frontend
cd scholarnote-frontend
npm install
cp .env.example .env.local  # fill in API URL
npm run dev
```

---

## 🔐 Environment Variables

### Backend `.env`

```env
# AWS
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
AWS_S3_BUCKET=your_s3_bucket
AWS_SQS_QUEUE_URL=your_sqs_queue_url
AWS_DYNAMODB_TABLE=your_dynamodb_table

# Vector Store
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=scholarnote

# LLM & Embeddings
GROQ_API_KEY=your_groq_key
VOYAGE_API_KEY=your_voyage_key
LLAMA_CLOUD_API_KEY=your_llamacloud_key
FIRECRAWL_API_KEY=your_firecrawl_key
```

### Frontend `.env.local`

```env
NEXT_PUBLIC_API_URL=https://your-api-gateway-url.amazonaws.com
```

---

## 🚀 Deployment

### Backend — AWS Lambda

```bash
# Build and push to ECR
docker build -t scholarnote-backend .
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag scholarnote-backend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/scholarnote-backend:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/scholarnote-backend:latest

# Lambda entry points
# ingestion_handler.py → triggered by SQS
# routes_handler.py   → triggered by API Gateway
```

### Frontend — Vercel

```bash
npm install -g vercel
vercel --prod
```

---

## 📊 Performance

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Ingestion time | 30s | 5s | **83% faster** |
| Response latency | 15s | sub-second | **95% faster** |
| Retrieval accuracy | baseline | +75% | vs naive chunking |
| Infrastructure overhead | traditional server | serverless | **60% lower** |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ by [Bhavesh Agrawal](https://www.linkedin.com/in/gameron42)

[![LinkedIn](https://img.shields.io/badge/LinkedIn-gameron42-0077B5?style=for-the-badge&logo=linkedin)](https://www.linkedin.com/in/gameron42)
[![GitHub](https://img.shields.io/badge/GitHub-Bhavesh42833-181717?style=for-the-badge&logo=github)](https://github.com/Bhavesh42833)
[![Live](https://img.shields.io/badge/Live-scholarnote.studio-00C389?style=for-the-badge)](https://www.scholarnote.studio)

⭐ **Star this repo if you found it useful!**

</div>
