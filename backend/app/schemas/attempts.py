"""Attempt request/response DTOs (api-contract §5.9–§5.10).

Only the shape is checked here (processing step 1). The item rules (option belongs to the
current item, fill_blank length after normalization) need the mission content, so the attempts
service checks them before taking any lock.
"""

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import RequestModel
from app.schemas.state import StateView

NODE_ID_MAX = 64
RAW_TEXT_MAX = 200  # the 1-80 characters rule is applied after normalization, in the service


class AdvanceRequest(RequestModel):
    node_id: str = Field(min_length=1, max_length=NODE_ID_MAX)


class AnswerRequest(RequestModel):
    node_id: str = Field(min_length=1, max_length=NODE_ID_MAX)
    option_id: str | None = Field(default=None, pattern=r"^[a-z0-9]{1,8}$")
    text: str | None = Field(default=None, max_length=RAW_TEXT_MAX)

    @model_validator(mode="after")
    def exactly_one_answer(self) -> "AnswerRequest":
        if (self.option_id is None) == (self.text is None):
            raise ValueError("Send exactly one of option_id or text.")
        return self


class AnswerResponse(BaseModel):
    """No outcome / is_correct field (F-01): the story carries what happened."""

    maya_line: str | None
    state: StateView
