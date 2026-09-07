"""Modal burst compute for parsing / API (optional). App is not locked to Modal."""

import modal

image = modal.Image.debian_slim(python_version="3.12").pip_install(
    "fastapi", "uvicorn", "sqlalchemy", "nbformat", "httpx", "pydantic"
)
app = modal.App("llm-twin-academy-api", image=image)


@app.function()
@modal.asgi_app()
def fastapi_app():
    import sys

    sys.path.append("/root/api")
    from app.main import app as fa

    return fa
