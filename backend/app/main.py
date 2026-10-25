import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import security
from .database import Base, engine
from .routers import auth, bookings, providers, quotes, reviews, service_requests, services

STATIC_DIR = Path(__file__).parent / "static"
WEB_DIR = Path(__file__).parent / "web"   # built React app (vite build)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Fieldly API",
    version="0.1.0",
    description="Local services & equipment marketplace — MVP backend (borewell drilling first).",
)

# CORS: the frontend is deployed as a separate Render Static Site (see
# DEPLOYMENT_GUIDE.md), so it calls this API cross-origin. Set
# ALLOWED_ORIGINS to your static site's URL in production instead of "*".
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*" if security.IS_LOCAL else "")  # UI is served from this same app, so CORS is normally not needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(services.router)
app.include_router(providers.router)
app.include_router(service_requests.router)
app.include_router(quotes.router)
app.include_router(bookings.router)
app.include_router(reviews.router)


@app.get("/", include_in_schema=False)
def root():
    if (WEB_DIR / "index.html").exists():
        return FileResponse(WEB_DIR / "index.html")
    return {
        "service": "fieldly-api",
        "status": "ok",
        "docs": "/docs",
        "provider_test_tool": "/provider-dashboard.html",
    }


@app.get("/provider-dashboard.html")
def provider_dashboard():
    return FileResponse(STATIC_DIR / "provider-dashboard.html")


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}


if (WEB_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIR / "assets"), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
def spa(full_path: str):
    """Serve the React app; unknown paths fall back to index.html."""
    target = (WEB_DIR / full_path).resolve()
    if full_path and target.is_file() and WEB_DIR.resolve() in target.parents:
        return FileResponse(target)
    index = WEB_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"detail": "Frontend not built. Run: cd frontend && npm install && npm run build"}
