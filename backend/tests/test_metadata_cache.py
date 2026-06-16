"""元数据缓存单元测试。"""

from app.services.video import metadata_cache


def test_bilibili_cache_roundtrip():
    metadata_cache._store.clear()
    metadata_cache.put_bilibili(
        "https://www.bilibili.com/video/BV1test",
        view_data={"title": "测试", "duration": 120, "aid": 1},
        cid=100,
        bvid="BV1test",
        aid=1,
        page=1,
    )
    data = metadata_cache.get_bilibili("https://www.bilibili.com/video/BV1test")
    assert data is not None
    assert data["cid"] == 100
    assert data["view_data"]["title"] == "测试"


def test_cache_expires_after_ttl(monkeypatch):
    metadata_cache._store.clear()
    metadata_cache.put_ytdlp_info("https://youtube.com/watch?v=abc", {"id": "abc"})
    key = metadata_cache.normalize_url("https://youtube.com/watch?v=abc")
    ts, payload = metadata_cache._store[key]
    metadata_cache._store[key] = (ts - metadata_cache.TTL_SECONDS - 1, payload)
    assert metadata_cache.get_ytdlp_info("https://youtube.com/watch?v=abc") is None
