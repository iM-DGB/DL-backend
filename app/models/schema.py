from pydantic import BaseModel
from typing import Optional

class UserRequest(BaseModel):
    utterance: str

class ActionParams(BaseModel):
    category: Optional[str]
    product_name: Optional[str]

class Action(BaseModel):
    params: ActionParams

class KakaoRequest(BaseModel):
    action: Action
    userRequest: UserRequest
