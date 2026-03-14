import asyncio
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from app.config import settings
from app.crud import delete_expired_links
from app.database import engine, Base, SessionLocal
from app.models.models import User
from app.routers import links, stats, auth_users
from app.utils import get_password_hash


async def create_admin():
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
    from sqlalchemy import select

    async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        try:
            result = await db.execute(
                select(User).where(User.username == settings.admin_username)
            )
            admin = result.scalar_one_or_none()
            if not admin:
                admin = User(
                    username=settings.admin_username,
                    email=settings.admin_email,
                    hashed_password=get_password_hash(settings.admin_password),
                    role="admin"
                )
                db.add(admin)
                await db.commit()
                await db.refresh(admin)
                print("Admin user created")
            else:
                print("Admin user already exists")
        except Exception as e:
            await db.rollback()
            print(f"Error creating admin: {e}")
            raise


# Асинхронная функция для удаления просроченных ссылок
async def delete_expired_links_job():
    async with SessionLocal() as db:
        await delete_expired_links(db)


# Функция для запуска планировщика в фоне
def run_scheduler():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(delete_expired_links_job())


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")

    # Создаем таблицы асинхронно
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Создаем администратора (синхронно)
    await create_admin()

    # Настраиваем планировщик
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_scheduler,
        'interval',
        hours=1,
        id='delete_expired_links',
        replace_existing=True
    )
    scheduler.start()
    yield
    scheduler.shutdown()
    await engine.dispose()



app = FastAPI(lifespan=lifespan)

app.include_router(auth_users.router, prefix="/auth_users", tags=["auth_users"])
app.include_router(links.router, prefix="/links", tags=["links"])
app.include_router(stats.router, prefix="/stats", tags=["stats"])

@app.get("/")
async def root():
    return {"message": "URL Shortener API", "status": "running"}