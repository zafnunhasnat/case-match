# backend/app/api/auth.py (or backend/app/services/audit.py)

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

SECRET_KEY = "super-secret-clinical-key-change-in-prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

router = APIRouter(prefix="/auth", tags=["Authentication & Audit"])

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    role = "doctor" if "admin" not in form_data.username else "admin"
    if "reviewer" in form_data.username:
        role = "reviewer"
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username, "role": role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": role}

def verify_role(required_roles: list):
    def role_verifier(token: str = Depends(oauth2_scheme)):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            role: str = payload.get("role")
            if username is None or role not in required_roles:
                raise HTTPException(status_code=403, detail="Insufficient privileges")
            return {"username": username, "role": role}
        except JWTError:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
    return role_verifier

def log_audit_event(db: Session, username: str, action: str, details: str, ip_address: str):
    audit_sql = text("""
        INSERT INTO search_audit_logs (username, action, details, ip_address, timestamp)
        VALUES (:username, :action, :details, :ip_address, NOW())
    """)
    db.execute(audit_sql, {"username": username, "action": action, "details": details, "ip_address": ip_address})
    db.commit()