from fastapi import FastAPI
from app.core.config import settings
from app.api.router import api_router

app = FastAPI(title=settings.PROJECT_NAME, version="0.1.0")

app.include_router(api_router, prefix="/api/v1")


from fastapi import Request
from fastapi.responses import JSONResponse
from app.utils.exceptions import BaseAppException

@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_response_dict()
    )

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "project": settings.PROJECT_NAME}

