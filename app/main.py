from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from app.database import engine, Base, get_db, SessionLocal
from app.routers import links, stats, auth_users
from app.models.models import User
from app.crud import delete_expired_links
from app.utils import get_password_hash
from app.config import settings

Base.metadata.create_all(bind=engine)

app = FastAPI()

scheduler = BackgroundScheduler()
scheduler.add_job(
    lambda: delete_expired_links(next(get_db())),
    'interval',
    hours=1
)
scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

app.include_router(auth_users.router, prefix="/auth_users", tags=["auth_users"])
app.include_router(links.router, prefix="/links", tags=["links"])
app.include_router(stats.router, prefix="/stats", tags=["stats"])

def create_admin():
    db = SessionLocal()
    
    # Проверяем, существует ли уже администратор
    admin = db.query(User).filter(User.username == settings.admin_username).first()
    if not admin:
        admin = User(
            username=settings.admin_username,
            email=settings.admin_email,
            hashed_password=get_password_hash(settings.admin_password),
            role="admin"  # Назначаем роль администратора
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print("Admin user created")
    else:
        print("Admin user already exists")

# Регистрируем create_admin как обработчик события startup
@app.on_event("startup")
def startup_event():
    create_admin()