from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.core.dependencies import get_current_user, require_admin
from src.modules.users.models import Usuario
from src.modules.users.schemas import UserCreate, UserResponse
from src.modules.users.service import (
    get_all_users,
    get_active_ejecutivos,
    get_user_by_email,
    create_user,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/ejecutivos", response_model=list[UserResponse])
async def list_ejecutivos(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista los ejecutivos activos disponibles para asignación de clientes."""
    ejecutivos = await get_active_ejecutivos(db)
    return [UserResponse.model_validate(e) for e in ejecutivos]


@router.get("", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    admin_user: Usuario = Depends(require_admin)
):
    """Lista completa de usuarios del sistema (Acceso exclusivo Administrador)."""
    users = await get_all_users(db)
    return [UserResponse.model_validate(u) for u in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: Usuario = Depends(require_admin)
):
    """Crea un nuevo usuario en la plataforma (Acceso exclusivo Administrador)."""
    existing = await get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un usuario registrado con el email '{user_in.email}'."
        )

    user = await create_user(db, user_in)
    return UserResponse.model_validate(user)
