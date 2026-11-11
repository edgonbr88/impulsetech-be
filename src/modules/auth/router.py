from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.core.security import create_access_token
from src.core.dependencies import get_current_user
from src.modules.users.models import Usuario
from src.modules.users.schemas import UserResponse
from src.modules.auth.schemas import LoginRequest, TokenResponse
from src.modules.users.service import authenticate_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    login_in: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, email=login_in.email, password=login_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo electrónico o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generar token JWT con claims
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "rol": user.rol,
        "nombre": user.nombre
    }
    token = create_access_token(data=token_data)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Usuario = Depends(get_current_user)
):
    return UserResponse.model_validate(current_user)
