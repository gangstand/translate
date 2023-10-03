from pydantic import BaseModel, Field, field_validator
from typing import Annotated, List

SOURCE_LANGUAGES: List[str] = ["en-US", "it-IT", "es-MX", "ru-RU", "de-DE", "ja-JP", "pt-BR"]
TARGET_LANGUAGES: List[str] = ["en", "it", "es", "ru", "de", "ja", "pt"]

source_language_annotated = Annotated[str, Field(validate_default=True)]
target_language_annotated = Annotated[str, Field(validate_default=True)]


class VideoProcessorInput(BaseModel):
    input_directory: str
    source_language: str = Field(default="en-US", description="Исходный язык")
    target_language: str = Field(default="ru", description="Язык перевода")
    output_directory: str
    workers: int

    @field_validator('source_language')
    @classmethod
    def check_source_language(cls, v):
        if v not in SOURCE_LANGUAGES:
            raise ValueError(f"Недопустимый значения '{v}'. Допустимые значения: {', '.join(SOURCE_LANGUAGES)}")
        return v

    @field_validator('target_language')
    @classmethod
    def check_target_language(cls, v):
        if v not in TARGET_LANGUAGES:
            raise ValueError(f"Недопустимый значения '{v}'. Допустимые значения: {', '.join(TARGET_LANGUAGES)}")
        return v
