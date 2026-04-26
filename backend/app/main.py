from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.feedback import router as feedback_router
from app.api.mcp_bridge import router as mcp_bridge_router
from app.api.rubric import router as rubric_router
from app.api.upload import router as upload_router
from app.core.config import settings

app = FastAPI(title="AI Assignment Feedback API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api")
app.include_router(rubric_router, prefix="/api")
app.include_router(feedback_router, prefix="/api")
app.include_router(mcp_bridge_router, prefix="/api")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
