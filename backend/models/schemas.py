from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = Field(default=None, max_length=128)
    session_token: str | None = Field(default=None, max_length=128)
    language: str | None = Field(default=None, pattern="^(en|ar)$")


class SourceChunk(BaseModel):
    source_url: str | None = None
    title: str | None = None
    similarity: float | None = None


class ChatResponse(BaseModel):
    session_id: str
    session_token: str | None = None
    answer: str
    language: str
    sources: list[SourceChunk] = []
    show_lead_form: bool = False
    lead_prompt: str | None = None


class VoiceRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1500)
    language: str = Field(default="en", pattern="^(en|ar)$")
    session_id: str | None = None
    session_token: str | None = None


class VoiceResponse(BaseModel):
    audio_url: str
    language: str
    voice_id: str


class LeadRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=40)
    company: str | None = Field(default=None, max_length=160)
    requirements: str | None = Field(default=None, max_length=4000)
    session_id: str | None = Field(default=None, max_length=128)
    session_token: str | None = Field(default=None, max_length=128)
    language: str | None = Field(default=None, pattern="^(en|ar)$")
    website: str | None = Field(default=None, max_length=200)


class LeadResponse(BaseModel):
    id: str
    status: str = "saved"


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
