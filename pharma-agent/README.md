# 🏥 PharmaAgent - Agentic AI Pharmacy System

An autonomous, agent-driven pharmacy ecosystem that behaves like an expert pharmacist, understands natural conversation, enforces medical safety rules, predicts refills, and autonomously executes backend actions with minimal human intervention.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![React](https://img.shields.io/badge/react-18+-61DAFB.svg)

## ✨ Features

### 🤖 Multi-Agent Architecture
- **Conversation Agent**: Natural language understanding with entity extraction (medicine, dosage, quantity)
- **Safety Agent**: Policy enforcement, stock validation, prescription verification
- **Refill Agent**: Predictive analytics for proactive refill alerts
- **Action Agent**: Automated order execution, webhook triggers, notifications

### 💬 Conversational Ordering
- Natural language order processing
- Voice input support (Web Speech API)
- Conversation memory per session
- Clarification questions for low-confidence extractions

### 🔒 Safety & Compliance
- Stock availability validation
- Prescription requirement enforcement
- Customer verification profiles
- Detailed rejection reasons

### 📊 Predictive Intelligence
- Order history analysis
- Refill date predictions
- Proactive customer notifications
- Automated alert generation

### 🎨 Modern UI
- Dark theme with glassmorphism
- Real-time chat interface
- Admin dashboard with inventory management
- Mobile responsive design

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Chat View   │  │ Admin View   │  │ Voice Input  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                 Agent Orchestrator                    │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │   │
│  │  │  Conv  │→│ Safety │→│ Action │ │ Refill │        │   │
│  │  │ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │        │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘        │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Observability (Langfuse)                 │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    SQLite Database                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Medicines │ │ Orders   │ │Customers │ │ Alerts   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
# Navigate to backend directory
cd pharma-agent/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000` with docs at `http://localhost:8000/docs`.

### Frontend Setup

```bash
# Navigate to frontend directory
cd pharma-agent/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The UI will be available at `http://localhost:5173`.

## 📖 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chat` | POST | Send message to agent |
| `/medicines` | GET | List all medicines |
| `/medicines/inventory/{id}` | PATCH | Update stock |
| `/orders` | GET/POST | Manage orders |
| `/customer/{id}/history` | GET | Order history |
| `/alerts` | GET | Refill alerts |
| `/webhook/fulfillment` | POST | Trigger fulfillment |
| `/refill-check` | POST | Run refill predictions |

## 🎯 Demo Flow

1. **Open Chat Interface** at `http://localhost:5173`

2. **Place an Order**:
   - Type: "I need 30 Paracetamol tablets"
   - Agent extracts: medicine, quantity
   - Confirm when prompted

3. **Prescription Required**:
   - Type: "I need Amoxicillin"
   - System requests prescription upload
   - Upload image and continue

4. **Voice Order**:
   - Click microphone button
   - Speak your order
   - Text is extracted and processed

5. **Admin Dashboard** at `http://localhost:5173/admin`:
   - View inventory with stock levels
   - See refill alerts
   - Monitor recent orders

## 🔍 Observability

### Console Logging (Default)
All agent interactions are logged to the console with color-coded traces:
- 🟢 Trace start/end
- 🔵 Span start/end
- 🟡 Decisions
- 🔵 Agent communications

### Langfuse Integration (Optional)
Create a `.env` file in the backend directory:

```env
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com
```

Access traces at your Langfuse dashboard.

## 📁 Project Structure

```
pharma-agent/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── database.py          # DB connection
│   │   ├── routes/              # API endpoints
│   │   └── services/            # Business logic
│   ├── data/
│   │   ├── medicines.csv        # Sample medicines
│   │   └── order_history.csv    # Sample orders
│   └── requirements.txt
├── agents/
│   ├── orchestrator.py          # Central coordinator
│   ├── conversation_agent.py    # NLU agent
│   ├── safety_agent.py          # Policy agent
│   ├── refill_agent.py          # Prediction agent
│   ├── action_agent.py          # Execution agent
│   └── observability.py         # Langfuse integration
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── pages/               # Views
│   │   ├── services/            # API client
│   │   └── App.jsx
│   └── package.json
└── README.md
```

## 🧪 Testing

### Manual Test Scenarios

1. **Basic Order**: "I want 20 ibuprofen tablets"
2. **Prescription Required**: "Order Metformin for me"
3. **Out of Stock**: (Set stock to 0 in admin, then order)
4. **Large Quantity**: "I need 100 Paracetamol"
5. **Voice Input**: Use microphone button

### API Testing

```bash
# Health check
curl http://localhost:8000/health

# Get medicines
curl http://localhost:8000/medicines

# Send chat message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I need 30 paracetamol tablets"}'
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLite/PostgreSQL URL | `sqlite:///./pharma_agent.db` |
| `LANGFUSE_PUBLIC_KEY` | Langfuse public key | None |
| `LANGFUSE_SECRET_KEY` | Langfuse secret key | None |
| `LANGFUSE_HOST` | Langfuse host URL | `https://cloud.langfuse.com` |

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

Built with ❤️ using FastAPI, React, and Multi-Agent AI
