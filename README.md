<div align="center">
  <img src="https://github.com/Mk3Ang8l/Eveline/blob/main/src/assets/OIP-3162603972.jpg" alt="Description" width="600"/>
</div>

# Eveline

> AI Personal Assistant 

A terminal-themed agentic AI personal assistant with a React frontend and Python/FastAPI backend.

## Features

### Core AI Capabilities
- **Conversational AI** - Powered by Mistral Large with ReAct reasoning loop
- **Tool Calling** - Automatic tool execution (search, scrape, commands, etc.)
- **Semantic Memory (RAG)** - Vector-based recall using FAISS and Sentence Transformers
- **Vision Analysis** - Image understanding via Mistral Pixtral
- **Linux Command Learning** - Remembers and recalls past command executions

### Modules
- **AI Console** - Chat interface with markdown rendering
- **Calendar** - Event management with SQLite persistence
- **Notes** - Note-taking with categories and search
- **Crypto Wallet** - MetaMask integration for ETH balance and transactions
- **OSINT Tools** - Username and domain lookups

### Technical Features
- **Streaming Responses** - Real-time AI output via Server-Sent Events (SSE)
- **Terminal Streaming** - Live command output streaming
- **Docker Deployment** - Full containerized setup
- **Playwright Service** - Browser automation for web scraping

## Architecture

```
lain-de-laine/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── core/           # Database and config
│   │   ├── models/         # SQLAlchemy models
│   │   ├── routers/        # API endpoints
│   │   └── services/       # Business logic
│   └── main.py             # Application entry point
├── src/                    # React frontend
│   ├── App.jsx             # Main component
│   └── App.css             # Styling
├── docker-compose.yml      # Docker orchestration
└── README.md
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)

### Environment Variables
Create a `.env` file in the root directory:
```env
MISTRAL_API_KEY=your_mistral_api_key
OPENROUTER_API_KEY=your_openrouter_key  # Optional
```

### Running with Docker
```bash
# Build and start all services
docker compose up -d --build

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Local Development
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
npm install
npm run dev
```

## API Endpoints

### AI
- `POST /api/chat` - Send message to AI (streaming response)

### Sandbox
- `POST /api/sandbox/run` - Execute code or command
- `GET /api/sandbox/stream?command=...` - Stream command output (SSE)

### Calendar
- `GET /api/calendar` - List all events
- `POST /api/calendar` - Create event

### Notes
- `GET /api/notes` - List all notes
- `POST /api/notes` - Create note
- `PUT /api/notes/{id}` - Update note
- `DELETE /api/notes/{id}` - Delete note

## AI Tool Calling

The AI uses a ReAct (Reason + Act) loop for tool execution:

1. **Parse** - Extract JSON tool calls from AI response using regex
2. **Validate** - Check for loops and validate parameters
3. **Execute** - Call the appropriate Python service
4. **Feedback** - Inject results back into context as "OBSERVATION"
5. **Repeat** - Continue until AI provides final answer

### Available Tools
| Tool | Description |
|------|-------------|
| `search` | Web search via DuckDuckGo |
| `scrape` | Extract text from URL |
| `sandbox` | Execute Python code |
| `command` | Execute shell commands |
| `manage_notes` | CRUD operations for notes |
| `manage_calendar` | Calendar event management |
| `manage_wallet` | Crypto wallet operations |
| `image_search` | Search for images |
| `vision_analyze` | Analyze images with AI |
| `get_time` | Get current time |
| `get_weather` | Get weather for a city |

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Database ORM
- **SQLite** - Local database
- **FAISS** - Vector similarity search
- **Sentence Transformers** - Text embeddings
- **Mistral AI** - LLM provider

### Frontend
- **React 17** - UI framework
- **Vite** - Build tool
- **Lucide React** - Icons
- **React Markdown** - Markdown rendering

### Infrastructure
- **Docker** - Containerization
- **Playwright** - Browser automation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## acknowledgments
I would like to express my gratitude to mistral ai team as they made that project possible  and github team too for offering a large ocean of projects to dive into  ❤️
## License
donate:
-USDT/ETHERIUM ADRESS:
0x1950f711cfcc8a4c9fad6c3af3e440b3d3ee7212
PAYPAL:https://www.paypal.me/MicaPaul138


**Custom License** - See [LICENSE](LICENSE) for full terms.

- ✅ **Free** for personal, non-commercial use
- 💰 **Commercial use** requires a paid license
- 📝 **Attribution required** for derivative works

