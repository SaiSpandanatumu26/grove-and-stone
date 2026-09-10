"""Serve an optional Expo web export beside the API on Azure App Service."""
from pathlib import Path

from flask import abort, send_from_directory


def install_web(app):
    directory = app.config.get("WEB_DIST_DIR")
    if not directory:
        return
    root = (Path(app.root_path).parent / directory).resolve()
    if not (root / "index.html").is_file():
        raise RuntimeError("WEB_DIST_DIR must contain an exported Expo index.html.")

    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def web_page(path):
        target = (root / path).resolve()
        if path == "api" or path.startswith("api/") or not target.is_relative_to(root) or any(part.startswith(".") for part in Path(path).parts):
            abort(404)
        if target.is_file():
            return send_from_directory(root, path)
        if Path(path).suffix or path.startswith(("assets/", "_expo/")):
            abort(404)
        return send_from_directory(root, "index.html")
