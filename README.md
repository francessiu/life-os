# LifeOS: The Personal PKM and AI Agent

LifeOS is a application designed to merge Personal Knowledge Management (PKM) with goal-oriented gamification, supported by a personalised AI agent. My goal is to shift the user's focus from mere knowledge, task management to more strategic behavioral plan.

Status: In Early Development

```text
life-os/
├── .github/                       # GitHub actions
├── .vscode/                       # VSCode settings
├── backend/                       # Shared logic (Python)
│   ├── app/                       # FastAPI application entry point
│   ├── core/                      # Main business logic
│   ├── db/                        # Database connections, models (Postgres/VectorDB)
│   └── agents/                    # LLM orchestration, RAG pipeline, prompt templates
├── frontend/                      # UI code
│   ├── apple-native/              # MacOS and iOS specific (SwiftUI)
│   │   ├── iOS/                   # iOS (Screen Time API, Widgets)
│   │   └── macOS/                 # macOS (Floating Window, native blocking logic)
│   ├── core-flutter/              # Shared Flutter codebase
│   │   ├── lib/                   # Flutter source code
│   │   └── test/                  # Unit and Widget tests
│   └── web-dashboard/             # Separate web dashboard (React/Next.js)
│       ├── public/
│       └── src/
├── docs/
│   ├── architecture/              # Diagrams (UML, Data flow, API interactions)
│   └── specs/                     # Feature specifications (e.g., Token Economy Logic)
├── assets/
├── tests/                         # End-to-end (E2E) tests
└── README.md                      # Project overview 
```

# Project Objectives 

The objective of LifeOS is to create a centralised digital layer that integrates into the user's life, acting as a library, a personalised coach for productivity.

* **Digital Integration**: Unify knowledge and workflow across all major platforms (Web, MacOS, iOS, Linux, Android).

* **Personalised Intelligence**: Prioritise user-specific data (PKM) over generalised pre-trained knowledge.

* **Behavioural Nudging**: Implement a unique token economy and a Digital Butler or Pet character to encourage focus and prevent distraction.

## Core Features

| Feature Component | Functionality | Key Technology |
| :--- | :--- | :--- |
| **🧠 PKM Database & RAG** | Connects to Google Drive, OneDrive, and iCloud. Converts documents into a searchable Vector Database for contextual Q&A with LLMs. | Python/FastAPI, Vector Database (Weaviate/Pinecone), Cloud Storage APIs |
| **🤖 AI Agent** | Personalised LLM that uses RAG first, then web search as a fallback. Summarises information from multiple models (e.g., Gemini, ChatGPT, Claude). | LangChain/LlamaIndex, OpenAI, Anthropic (Claude 3.5) |
| **🎮 Task Gamification** | AI analyses goals, breaks them into executable steps, and suggests measurable metrics. Implements a **token economy** for skipping tasks. | Python Agents, PostgreSQL (Token/Habit Tracking), SwiftUI/Kotlin (Platform Channels) |
| **🖥️ Digital Butler or Pet** | A character that "lives" on the user's screen (floating window on desktop, overlay on Android). Remind user of tasks or interrupts media scrolling during focus sessions. | SwiftUI (MacOS), Flutter/Kotlin (Android), Screen Time API (iOS) |

## High-Level Architecture

The LifeOS application follows a **Decoupled Service Architecture**:

#### 1. Frontend Layer
* **Web Dashboard (React/Next.js):** Primary interface for deep PKM browsing and goal setting.
* **Apple Native (SwiftUI/Swift):** Provides native performance and is required for accessing restrictive operating system APIs (e.g., MacOS Floating Window, iOS Screen Time/DeviceActivity).
* **Multi-Platform Mobile/Desktop (Flutter):** Serves as the base UI for Android, Linux, and shares logic with the Web and Apple platforms.

#### 2. Backend Layer (Python/FastAPI)
The backend is the brain of the operation, designed as a set of stateless microservices orchestrated by FastAPI.

* **API Gateway:** Handles authentication, routing, and ensures security (OAuth2).
* **RAG Service:** Manages indexing, embedding generation, and vector retrieval.
* **Gamification Service:** Contains the token logic, habit trackers, and goal decomposition algorithms.

Communication between the Frontend and Backend is exclusively handled via **RESTful APIs** and **WebSockets** for real-time chat and progress updates.
