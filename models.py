from pydantic import BaseModel, Field, validator
from typing import Optional
import re

# Модель для задания А.3
class Movietop(BaseModel):
    name: str
    id: int
    cost: int
    director: str

# Модель для задания Б
class Movie(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    genre: str = Field(..., min_length=1, max_length=50)
    rating: float = Field(..., ge=0, le=10)
    comment: str = Field(..., min_length=1, max_length=500)
    image_filename: Optional[str] = None

    @validator('genre')
    def validate_genre(cls, v):
        if any(char.isdigit() for char in v):
            raise ValueError('Genre should not contain numbers')
        if not re.match(r'^[a-zA-Zа-яА-Я\s\-]+$', v):
            raise ValueError('Genre should contain only letters, spaces and hyphens')
        return v