from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str
    status: str = "PENDING"
    priority: str = "MED"
    deadline: str

class TransactionCreate(BaseModel):
    date: str
    description: str
    category: str
    amount: float

class ChatRequest(BaseModel):
    message: str
    context: list = []
    session_id: str | None = None

class ToolStep(BaseModel):
    tool: str
    input: str
    output: str
    status: str = "success" # success, error

class ChatResponse(BaseModel):
    response: str
    steps: list[ToolStep] = []
    usage: dict = {}

class ScrapeRequest(BaseModel):
    url: str
    task: str = "extract all text"

class CalendarEventCreate(BaseModel):
    title: str
    start: str
    end: str | None = None
    description: str | None = None
    location: str | None = None

class CalendarEventUpdate(BaseModel):
    title: str | None = None
    start: str | None = None
    end: str | None = None
    description: str | None = None
    location: str | None = None

class CryptoBalanceRequest(BaseModel):
    address: str

class CryptoTransferRequest(BaseModel):
    from_address: str
    to_address: str
    amount: float
