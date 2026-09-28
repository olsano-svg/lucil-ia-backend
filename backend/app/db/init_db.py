import asyncio
import logging
from sqlalchemy.future import select
from app.db.database import engine, Base, AsyncSessionLocal
from app.models.user import User
from app.models.project import Project
from app.models.conversation import Conversation, Message
from app.models.memory import MemoryItem
from app.core.security import get_password_hash
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_admin_user():
    """Asegura que el usuario administrador inicial exista con hash seguro."""
    admin_username = settings.ADMIN_USERNAME
    admin_pass = settings.ADMIN_PASSWORD

    async with AsyncSessionLocal() as db:
        res = await db.execute(
            select(User).filter(
                (User.email == admin_username) | (User.email == f"{admin_username}@lucil.ai")
            )
        )
        user = res.scalars().first()
        if not user:
            user = User(
                email=admin_username,
                hashed_password=get_password_hash(admin_pass),
                is_active=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info("Usuario administrador 'admin' creado exitosamente.")
        else:
            user.hashed_password = get_password_hash(admin_pass)
            user.is_active = True
            await db.commit()
            logger.info("Credenciales del usuario 'admin' actualizadas exitosamente.")

        # Asegurar que tenga un proyecto predeterminado
        proj_res = await db.execute(select(Project).filter(Project.user_id == user.id))
        if not proj_res.scalars().first():
            default_project = Project(name="Proyecto Principal Lucil", user_id=user.id)
            db.add(default_project)
            await db.commit()

async def init_tables():
    """Inicializa todas las tablas en la base de datos local SQLite y el usuario admin."""
    async with engine.begin() as conn:
        logger.info("Verificando y creando tablas de SQLite...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Tablas creadas y verificadas con éxito.")
    await init_admin_user()

if __name__ == "__main__":
    asyncio.run(init_tables())

