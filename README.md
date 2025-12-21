# LifeOS: The Personal PKM and AI Agent

LifeOS is a application designed to merge Personal Knowledge Management (PKM) with **goal-oriented gamification** and **autonomous research**. It acts as a centralized digital layer that integrates into your life—serving as a library, a proactive researcher, and a personalised productivity coach.

**Status**: *Active Development*

## Repository Structure

The project follows a decoupled, service-oriented architecture, splitting the "Brain" (Python Backend) from the "Body" (Multi-platform Frontends).

```text
life-os/
├── backend/                       # THE BRAIN (Python/FastAPI)
│   ├── app/                       # Application entry point & middleware
│   ├── api/                       # REST API Routes (Auth, Chat, Watcher)
│   ├── core/                      # Configuration, Security, & Environment
│   ├── db/                        # Database (Postgres & Weaviate Models)
│   ├── agents/                    # AI Logic (Orchestrator, Research Agent, Tools)
│   ├── pkm/                       # Knowledge Engine (RAG, Connectors, Ingestion)
│   └── services/                  # Background Services (Crawler, Watcher, Sandbox)
│
├── frontend/                      # THE BODY (UI Layer)
│   ├── apple-native/              # Deep OS Integration (Swift)
│   │   ├── iOS/                   # Screen Time Shield, Widgets
│   │   └── macOS/                 # Floating Butler, File Watcher
│   ├── web-dashboard/             # Main Control Center (React/Next.js)
│   │   ├── src/components/        # Chat Interface, Source Manager
│   │   └── src/lib/               # API Clients
│   └── browser-extension/         # Chrome/Edge Extension (Site Blocking & Overlay)
│
├── docs/                          # Architecture Diagrams & Specifications
└── tests/                         # End-to-end (E2E) & Integration tests
```

# Project Objectives 

LifeOS shifts focus from passive knowledge storage to **active behavioral change** and **autonomous intelligence**.

* **Unified Intelligence**: Connects dispersed data (Cloud Drives, Web Bookmarks, Local Files) into a single, queryable Vector Database.

* **Proactive Research**: Moves beyond simple Q&A. The agent plans research, crawls the web, and builds its own knowledge base in the background.

* **Behavioural Nudging**: Combines a digital "Butler" character with a token economy to gamify focus and reduce distraction.

## Core Features

| Feature Component | Functionality | Description |
| :--- | :--- | :--- |
| **🧠 Advanced PKM & RAG Engine** | Multi-Source Ingestion | Automatically syncs with Google Drive, OneDrive, and local iCloud folders. |
| | Hybrid Search | Uses Weaviate to combine Vector Search (Semantic) with Keyword Search (BM25) for high-precision retrieval. |
| | Atomic Notes | AI automatically summarises raw documents into structured "Atomic Notes" (Essence + Core Ideas) while preserving raw text chunks for citation. |
| **🤖 Autonomous AI Agent** | Orchestrator Pattern | A Router LLM intelligently directs queries to specialized agents. Personalised LLM uses RAG first, then web search as a fallback. | 
| | Deep Research Mode | Mimics "OpenAI Deep Research." The agent generates a search plan, executes parallel queries, scrapes web content, and synthesizes a comprehensive report. |
| | Sandboxed Execution | Capable of running Python code securely in Docker containers for data analysis and math. |
| **🎮 "The Butler" & Gamification** | Digital Presence | AI analyses goals, breaks them into executable steps, and suggests measurable metrics. A floating character overlay on macOS/Windows/Web that reacts to your productivity state. |
| | Focus Shield | Native integration with iOS Screen Time API and Browser Extensions to block distracting sites/apps. |
| | Token Economy | "Doom scrolling" or skipping task costs tokens. |
| **🖥️ The "Shared Knowledge" Engine** | Background Watcher | A scheduler that monitors user-selected websites and domains, re-crawling them automatically when content updates. |
| | Global vs. Private Scope | Distinguishes between knowledge private to the user and "Global" knowledge sources shared across the LifeOS ecosystem.

## High-Level Architecture

The system relies on a Python Backend handling heavy logic, communicating with lightweight Native Frontends.

### Backend Tech Stack 

 - Framework: FastAPI (Async Python)
 - Database (Relational): PostgreSQL (User Data, Auth, Gamification State)
 - Database (Vector): Weaviate (Hybrid Search, Multi-Tenancy)
 - AI Orchestration: LangChain (LCEL), Pydantic, OpenAI/Anthropic/Google APIs
 - Crawling: Firecrawl (Markdown Extraction)
 - Task Queue: APScheduler & FastAPI BackgroundTasks

### Frontend Tech Stack 

 - Web: React, Next.js, TailwindCSS
 - macOS/iOS: Swift (SwiftUI, FamilyControls, DeviceActivity)
 - Browser: Manifest V3 (Chrome/Edge)