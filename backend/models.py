from pydantic import BaseModel
from typing import Dict, Any

class Presentation(BaseModel):
    id: str
    token: str
    tmp_path: str
    main_markdown_path: str
    state: Dict[str, Any] = {"indexh": 0, "indexv": 0, "indexf": 0}
