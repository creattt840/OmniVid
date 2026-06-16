"""分析历史 API 单元测试。"""
import time

from tests.conftest import register_and_login


def _register_and_login(client, email: str, password: str = "test1234"):
    return register_and_login(client, email, password)


def _save_payload(url: str, title: str = "Test Video", **extra):
    payload = {
        "url": url,
        "source": "url",
        "title": title,
        "platform": "YouTube",
        "thumbnail": "https://example.com/thumb.jpg",
        "summary": {"summary": "hello", "highlights": [], "chapters": [], "terms": []},
        "mindmap": "# root",
        "segments": [{"start": 0, "end": 5, "text": "hello world"}],
        "article": "# Article\n\nContent here",
        "chatHistory": [{"role": "user", "content": "Q?"}, {"role": "assistant", "content": "A."}],
        "transcriptSource": "subtitle",
    }
    payload.update(extra)
    return payload


def test_history_requires_auth(client):
    res = client.get("/api/analysis-history")
    assert res.status_code == 401


def test_save_and_list_history(client):
    headers = _register_and_login(client, "history1@example.com")
    payload = _save_payload("https://youtube.com/watch?v=abc")
    save = client.post("/api/analysis-history", json=payload, headers=headers)
    assert save.status_code == 200
    assert save.json()["success"] is True
    assert save.json()["data"]["title"] == "Test Video"

    listing = client.get("/api/analysis-history", headers=headers)
    assert listing.status_code == 200
    items = listing.json()["data"]
    assert len(items) == 1
    assert items[0]["url"] == payload["url"]
    assert items[0]["summary"]["summary"] == "hello"


def test_save_extended_fields(client):
    headers = _register_and_login(client, "history_ext@example.com")
    payload = _save_payload("https://youtube.com/watch?v=ext")
    save = client.post("/api/analysis-history", json=payload, headers=headers)
    assert save.status_code == 200
    data = save.json()["data"]
    assert len(data["segments"]) == 1
    assert data["article"].startswith("# Article")
    assert len(data["chatHistory"]) == 2
    assert data["transcriptSource"] == "subtitle"


def test_partial_sync_preserves_order(client):
    headers = _register_and_login(client, "history_partial@example.com")
    url = "https://youtube.com/watch?v=partial"
    client.post("/api/analysis-history", json=_save_payload(url, title="First"), headers=headers)
    time.sleep(0.02)
    client.post(
        "/api/analysis-history",
        json=_save_payload("https://youtube.com/watch?v=other", title="Second"),
        headers=headers,
    )
    items_before = client.get("/api/analysis-history", headers=headers).json()["data"]
    assert items_before[0]["title"] == "Second"

    client.post(
        "/api/analysis-history",
        json={
            "url": url,
            "partial": True,
            "article": "Updated article",
            "chatHistory": [{"role": "user", "content": "hi"}],
        },
        headers=headers,
    )
    items_after = client.get("/api/analysis-history", headers=headers).json()["data"]
    assert items_after[0]["title"] == "Second"
    first = next(i for i in items_after if i["url"] == url)
    assert first["article"] == "Updated article"
    assert first["chatHistory"][0]["content"] == "hi"


def test_history_chat_not_found(client):
    headers = _register_and_login(client, "history_chat404@example.com")
    res = client.post(
        "/api/analysis-history/99999/chat",
        json={"message": "hello"},
        headers=headers,
    )
    assert res.status_code == 404


def test_history_rewrite_not_found(client):
    headers = _register_and_login(client, "history_rewrite404@example.com")
    res = client.get("/api/analysis-history/99999/rewrite", headers=headers)
    assert res.status_code == 404


def test_user_isolation(client):
    headers_a = _register_and_login(client, "history_a@example.com")
    headers_b = _register_and_login(client, "history_b@example.com")

    client.post(
        "/api/analysis-history",
        json=_save_payload("https://youtube.com/watch?v=a-only"),
        headers=headers_a,
    )
    client.post(
        "/api/analysis-history",
        json=_save_payload("https://youtube.com/watch?v=b-only"),
        headers=headers_b,
    )

    list_a = client.get("/api/analysis-history", headers=headers_a).json()["data"]
    list_b = client.get("/api/analysis-history", headers=headers_b).json()["data"]

    assert len(list_a) == 1
    assert len(list_b) == 1
    assert list_a[0]["url"].endswith("a-only")
    assert list_b[0]["url"].endswith("b-only")


def test_max_10_trim_oldest(client):
    headers = _register_and_login(client, "history_trim@example.com")
    for i in range(11):
        client.post(
            "/api/analysis-history",
            json=_save_payload(f"https://youtube.com/watch?v=vid{i}", title=f"Video {i}"),
            headers=headers,
        )
        time.sleep(0.01)

    items = client.get("/api/analysis-history", headers=headers).json()["data"]
    assert len(items) == 10
    titles = {item["title"] for item in items}
    assert "Video 0" not in titles
    assert "Video 10" in titles


def test_dedup_same_url(client):
    headers = _register_and_login(client, "history_dedup@example.com")
    url = "https://youtube.com/watch?v=dedup"
    client.post(
        "/api/analysis-history",
        json=_save_payload(url, title="First"),
        headers=headers,
    )
    client.post(
        "/api/analysis-history",
        json=_save_payload(url, title="Updated"),
        headers=headers,
    )

    items = client.get("/api/analysis-history", headers=headers).json()["data"]
    assert len(items) == 1
    assert items[0]["title"] == "Updated"


def test_delete_single_and_clear(client):
    headers = _register_and_login(client, "history_delete@example.com")
    save1 = client.post(
        "/api/analysis-history",
        json=_save_payload("https://youtube.com/watch?v=del1"),
        headers=headers,
    ).json()["data"]
    client.post(
        "/api/analysis-history",
        json=_save_payload("https://youtube.com/watch?v=del2"),
        headers=headers,
    )

    delete = client.delete(f"/api/analysis-history/{save1['id']}", headers=headers)
    assert delete.status_code == 200
    items = client.get("/api/analysis-history", headers=headers).json()["data"]
    assert len(items) == 1

    clear = client.delete("/api/analysis-history", headers=headers)
    assert clear.status_code == 200
    assert clear.json()["data"]["deleted"] == 1
    assert client.get("/api/analysis-history", headers=headers).json()["data"] == []


def test_delete_other_user_forbidden(client):
    headers_a = _register_and_login(client, "history_owner@example.com")
    headers_b = _register_and_login(client, "history_other@example.com")
    item = client.post(
        "/api/analysis-history",
        json=_save_payload("https://youtube.com/watch?v=owned"),
        headers=headers_a,
    ).json()["data"]

    res = client.delete(f"/api/analysis-history/{item['id']}", headers=headers_b)
    assert res.status_code == 404

    still = client.get("/api/analysis-history", headers=headers_a).json()["data"]
    assert len(still) == 1
