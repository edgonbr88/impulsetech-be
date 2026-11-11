import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.users.models import Usuario
from src.modules.users.schemas import UserCreate
from src.core.security import hash_password, verify_password


async def get_user_by_email(db: AsyncSession, email: str) -> Usuario | None:
    stmt = select(Usuario).where(Usuario.email == email.lower().strip())
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Usuario | None:
    stmt = select(Usuario).where(Usuario.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_all_users(db: AsyncSession) -> list[Usuario]:
    stmt = select(Usuario).order_by(Usuario.nombre.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_active_ejecutivos(db: AsyncSession) -> list[Usuario]:
    """Retorna usuarios activos habilitados para ser asignados a clientes."""
    stmt = (
        select(Usuario)
        .where(Usuario.activo.is_(True))
        .order_by(Usuario.nombre.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_user(db: AsyncSession, user_in: UserCreate) -> Usuario:
    hashed_password = hash_password(user_in.password)
    new_user = Usuario(
        nombre=user_in.nombre.strip(),
        email=user_in.email.lower().strip(),
        password_hash=hashed_password,
        rol=user_in.rol,
        activo=user_in.activo
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)
    return new_user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Usuario | None:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.activo:
        return None
    return user
