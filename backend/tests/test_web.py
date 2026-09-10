import pytest

from backend import create_app


def test_web_export_routes_keep_api_and_private_files_separate(tmp_path):
    (tmp_path / "index.html").write_text("<h1>Grove & Stone</h1>")
    (tmp_path / "app.js").write_text("console.log('shop')")
    (tmp_path / ".env").write_text("DO_NOT_SERVE")
    app = create_app({"TESTING": True, "WEB_DIST_DIR": str(tmp_path)})
    client = app.test_client()
    for path in ["/", "/Home/Landing", "/Account/Landing"]:
        response = client.get(path)
        assert response.status_code == 200 and b"Grove & Stone" in response.data
    assert client.get("/app.js").mimetype in {"text/javascript", "application/javascript"}
    for path in ["/api", "/api/v1/missing", "/missing.js", "/assets/missing", "/.env", "/%2e%2e/requirements.txt"]:
        response = client.get(path)
        assert response.status_code == 404 and response.is_json
        assert b"DO_NOT_SERVE" not in response.data
    assert client.post("/Home/Landing").status_code == 405


def test_web_export_is_optional_and_fails_fast_when_missing(tmp_path):
    assert create_app({"TESTING": True, "WEB_DIST_DIR": None}).test_client().get("/").status_code == 404
    with pytest.raises(RuntimeError, match="index.html"):
        create_app({"TESTING": True, "WEB_DIST_DIR": str(tmp_path)})
