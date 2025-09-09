from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
import regex as re


def username_validator(value: str) -> str:
    if not re.match(r"^[a-zA-Z0-9_]+$", value):
        raise ValueError("Must be alphanumeric or underscore")
    if re.match(r"^[0-9]", value):
        raise ValueError("Must start with a letter")
    return value


def password_validator(value: str) -> str:
    if not re.match(r"^(?=.*[a-zA-Z])(?=.*\d)(?=.*[@$!%*?&])", value):
        raise ValueError("Must contain letter, number and special character")
    return value


def name_validator(value: str) -> str:
    if not re.match(r"^[\p{L}]+$", value):
        raise ValueError("Only letters allowed")
    return value


class UpdateUserDTO(BaseModel):
    user_name: Optional[str] = Field(None, min_length=5, max_length=30)
    password: Optional[str] = Field(None, min_length=5, max_length=30)
    password_confirm: Optional[str] = Field(None, min_length=5, max_length=30)
    first_name: Optional[str] = Field(None, min_length=1, max_length=30)
    last_name: Optional[str] = Field(None, min_length=1, max_length=30)

    @field_validator("user_name")
    def validate_username(cls, v):
        return username_validator(v)

    @field_validator("password")
    def validate_password(cls, v):
        return password_validator(v)

    @field_validator("password_confirm")
    def validate_password_confirm(cls, v):
        return password_validator(v)

    @field_validator("first_name")
    def validate_first_name(cls, v):
        return name_validator(v)

    @field_validator("last_name")
    def validate_last_name(cls, v):
        return name_validator(v)

    @model_validator(mode="after")
    def check_passwords_match(self):
        if (self.password or self.password_confirm) and self.password != self.password_confirm:
            raise ValueError("Passwords must match")
        return self


class ReadUserDTO(BaseModel):
    id: int
    user_name: str
    first_name: Optional[str]
    last_name: Optional[str]
    status: int

    class Config:
        from_attributes = True