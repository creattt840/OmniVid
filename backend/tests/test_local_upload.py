"""Quick integration tests for local upload feature."""

SRT = """1
00:00:01,000 --> 00:00:03,000
Test subtitle line
"""


def _register_and_login(client, email: str = "upload_test@example.com", password: str = "test1234"):
    client.post("/api/auth/register", json={"email": email, "password": password})
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    token = res.json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def test_upload_with_subtitle_and_analyze(client):
    fake_mp4 = b"\x00" * 100
    r = client.post(
        "/api/upload",
        files={
            "media": ("demo.mp4", fake_mp4, "video/mp4"),
            "subtitle": ("demo.srt", SRT.encode("utf-8"), "application/x-subrip"),
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["file_id"]
    assert data["has_subtitle_file"] is True
    assert data["platform"] == "本地文件"

    r2 = client.get(f"/api/upload/{data['file_id']}/stream")
    assert r2.status_code == 200

    headers = _register_and_login(client)
    r3 = client.post("/api/analyze", json={"file_id": data["file_id"]}, headers=headers)
    assert r3.status_code == 200, r3.text
    assert r3.json()["data"]["transcript_source"] == "subtitle"
