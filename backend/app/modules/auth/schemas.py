"""Auth wire contracts (G1). JSON camelCase via PulseSchema."""

from uuid import UUID

from pydantic import EmailStr, Field

from app.core.authz import Role
from app.core.schema import PulseSchema

PASSWORD_MIN = 10
PASSWORD_MAX = 128


class RegisterRequest(PulseSchema):
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN, max_length=PASSWORD_MAX)
    role: Role


class RegisterResponse(PulseSchema):
    user_id: UUID


class ResendVerificationRequest(PulseSchema):
    email: EmailStr


class VerifyRequest(PulseSchema):
    challenge_id: str
    token: str


class LoginRequest(PulseSchema):
    email: EmailStr
    password: str = Field(min_length=1, max_length=PASSWORD_MAX)


class StepUpRequest(PulseSchema):
    password: str = Field(min_length=1, max_length=PASSWORD_MAX)


class MeResponse(PulseSchema):
    user_id: UUID
    role: Role
    email: EmailStr
    email_verified: bool
