from typing import Literal

from pydantic import BaseModel, Field


ComfyCloudWorkflow = Literal["text-to-image", "text-to-video", "image-to-video", "image-edit"]


class ComfyCloudWorkflowInputs(BaseModel):
    prompt: str = Field(...)
    image_url: str | None = Field(None)


class ComfyCloudGenerateRequest(BaseModel):
    workflow: ComfyCloudWorkflow = Field(...)
    inputs: ComfyCloudWorkflowInputs = Field(...)


class ComfyCloudGenerateResponse(BaseModel):
    task_id: str = Field(...)
    status: str = Field(...)
    polling_url: str = Field(...)
    cancel_url: str = Field(...)


class ComfyCloudStatusResponse(BaseModel):
    task_id: str = Field(...)
    status: str = Field(...)
    progress: float | None = Field(None)
    output_url: str | None = Field(None)
    error: str | None = Field(None)
