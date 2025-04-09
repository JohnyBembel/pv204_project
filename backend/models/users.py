from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    age: Optional[int] = None
    active: bool = False