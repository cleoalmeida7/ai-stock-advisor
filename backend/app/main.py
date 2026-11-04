from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analysis, instruments, portfolio
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="AI Stock Advisor API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(portfolio.router)
    app.include_router(instruments.router)
    app.include_router(analysis.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
