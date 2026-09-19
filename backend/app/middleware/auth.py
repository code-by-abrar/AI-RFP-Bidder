# backend/app/middleware/auth.py
from fastapi import Header, HTTPException
from typing import Optional
from uuid import UUID

class MockUser:
    def __init__(self):
        # Deterministic UUIDs for mock development
        self.id = UUID("00000000-0000-0000-0000-000000000001")
        self.company_id = UUID("00000000-0000-0000-0000-000000000002")

async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Get the current user from the authorization header.
    Currently stubbed for local testing. In production, decode the JWT here.
    """
    # Simply return a mock user so the endpoints function
    return MockUser()
