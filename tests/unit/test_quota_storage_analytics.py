from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from app.services.quota_service import _WindowStore


class TestWindowStore:
    def test_add_and_prune(self):
        store = _WindowStore()
        now = time.time()
        store.add("k", now - 100)
        store.add("k", now - 1)
        store.add("k", now)
        # prune entries older than now-10s: only 2 remain
        count = store.prune("k", now - 10)
        assert count == 2

    def test_prune_missing_key(self):
        store = _WindowStore()
        assert store.prune("ghost", time.time()) == 0

    def test_pop_one(self):
        store = _WindowStore()
        store.add("k", time.time())
        store.add("k", time.time())
        assert store.pop_one("k") is True
        assert store.prune("k", 0) == 1

    def test_pop_one_missing(self):
        store = _WindowStore()
        assert store.pop_one("ghost") is False

    def test_pop_one_empty_deque(self):
        store = _WindowStore()
        # add then prune all
        store.add("k", 1.0)
        store.prune("k", 10.0)
        assert store.pop_one("k") is False

    def test_isolation_between_keys(self):
        store = _WindowStore()
        store.add("a", time.time())
        store.add("b", time.time())
        store.prune("a", time.time() + 100)  # remove all from a
        assert store.prune("b", 0) == 1  # b still has one


class TestCheckRateLimitMemory:
    @pytest.mark.asyncio
    async def test_allows_under_limit(self):
        from app.services import quota_service

        quota_service._mem._windows.clear()
        with patch.object(quota_service, "_redis_client", return_value=None):
            ok, remaining = await quota_service.check_rate_limit("test-id", 60, 5)
            assert ok is True
            assert remaining == 4

    @pytest.mark.asyncio
    async def test_blocks_over_limit(self):
        from app.services import quota_service

        quota_service._mem._windows.clear()
        with patch.object(quota_service, "_redis_client", return_value=None):
            for _ in range(3):
                await quota_service.check_rate_limit("rl-test", 60, 3)
            ok, remaining = await quota_service.check_rate_limit("rl-test", 60, 3)
            # 4th request exceeds limit 3
            assert ok is False
            assert remaining == 0

    @pytest.mark.asyncio
    async def test_redis_fallback_on_exception(self):
        from app.services import quota_service

        quota_service._mem._windows.clear()
        mock_redis = MagicMock()
        mock_redis.pipeline.side_effect = Exception("redis down")
        with patch.object(quota_service, "_redis_client", return_value=mock_redis):
            ok, _ = await quota_service.check_rate_limit("redis-fail", 60, 5)
            # falls back to memory, should allow
            assert ok is True


class TestDailyQuotaMemory:
    @pytest.mark.asyncio
    async def test_increment_and_read(self):
        from app.services import quota_service

        quota_service._mem._windows.clear()
        with patch.object(quota_service, "_redis_client", return_value=None):
            ok, remaining = await quota_service.increment_daily("daily-test")
            assert ok is True
            count = await quota_service.read_daily("daily-test")
            assert count == 1

    @pytest.mark.asyncio
    async def test_read_empty(self):
        from app.services import quota_service

        quota_service._mem._windows.clear()
        with patch.object(quota_service, "_redis_client", return_value=None):
            assert await quota_service.read_daily("ghost-daily") == 0

    @pytest.mark.asyncio
    async def test_decrement(self):
        from app.services import quota_service

        quota_service._mem._windows.clear()
        with patch.object(quota_service, "_redis_client", return_value=None):
            await quota_service.increment_daily("decr-test")
            await quota_service.increment_daily("decr-test")
            quota_service.decrement_daily("decr-test")
            assert await quota_service.read_daily("decr-test") == 1

    @pytest.mark.asyncio
    async def test_redis_daily_fallback(self):
        from app.services import quota_service

        quota_service._mem._windows.clear()
        mock_redis = MagicMock()
        mock_redis.pipeline.side_effect = Exception("redis down")
        mock_redis.get.side_effect = Exception("redis down")
        with patch.object(quota_service, "_redis_client", return_value=mock_redis):
            ok, _ = await quota_service.increment_daily("redis-daily-fail")
            assert ok is True
            count = await quota_service.read_daily("redis-daily-fail")
            assert count == 1


class TestLocalStorage:
    def test_put_get_delete_exists(self, tmp_path):
        from app.services.storage_service import LocalStorage

        store = LocalStorage(str(tmp_path))
        store.put_bytes("a/b/file.bin", b"hello world")
        assert store.exists("a/b/file.bin") is True
        assert store.get_bytes("a/b/file.bin") == b"hello world"
        assert list(store.iter_bytes("a/b/file.bin")) == [b"hello world"]
        store.delete("a/b/file.bin")
        assert store.exists("a/b/file.bin") is False

    def test_delete_nonexistent_no_error(self, tmp_path):
        from app.services.storage_service import LocalStorage

        store = LocalStorage(str(tmp_path))
        store.delete("ghost/file.bin")  # should not raise

    def test_exists_false_for_missing(self, tmp_path):
        from app.services.storage_service import LocalStorage

        store = LocalStorage(str(tmp_path))
        assert store.exists("missing.bin") is False

    def test_iter_bytes_chunked(self, tmp_path):
        from app.services.storage_service import LocalStorage

        store = LocalStorage(str(tmp_path))
        data = b"a" * 200 * 1024  # 200KB
        store.put_bytes("big.bin", data)
        chunks = list(store.iter_bytes("big.bin", chunk_size=64 * 1024))
        assert b"".join(chunks) == data
        assert len(chunks) == 4  # 200/64 ceil = 4

    def test_open_write_context_manager(self, tmp_path):
        from app.services.storage_service import LocalStorage

        store = LocalStorage(str(tmp_path))
        with store.open_write("x/y.txt") as f:
            f.write(b"streamed")
        assert store.get_bytes("x/y.txt") == b"streamed"

    def test_get_storage_returns_local(self):
        from app.core.config import settings
        from app.services.storage_service import LocalStorage, get_storage

        # In test env storage_backend is "local"
        assert settings.storage_backend == "local"
        assert isinstance(get_storage(), LocalStorage)


class TestAnalytics:
    def test_track_event_allowed(self, caplog):
        from app.core.analytics import track_event
        import logging

        with caplog.at_level(logging.INFO, logger="convert.analytics"):
            track_event("file_uploaded", source_format="pdf", size_bytes=123)
        assert any("file_uploaded" in r.message for r in caplog.records)

    def test_track_event_unknown_dropped(self, caplog):
        from app.core.analytics import track_event
        import logging

        with caplog.at_level(logging.WARNING, logger="convert.analytics"):
            track_event("unknown_event_xyz", foo="bar")
        assert any("dropped unknown" in r.message for r in caplog.records)

    def test_track_event_never_raises(self):
        from app.core import analytics

        with patch.object(analytics._logger, "info", side_effect=Exception("log fail")):
            # should not raise
            analytics.track_event("file_uploaded", source_format="pdf")


class TestClock:
    def test_utcnow_is_naive(self):
        from app.core.clock import utcnow

        dt = utcnow()
        assert dt.tzinfo is None

    def test_iso_now_contains_tz(self):
        from app.core.clock import iso_now

        s = iso_now()
        assert "T" in s  # ISO format

    def test_utcnow_recent(self):
        from datetime import datetime, timezone

        from app.core.clock import utcnow

        before = datetime.now(timezone.utc).replace(tzinfo=None)
        dt = utcnow()
        after = datetime.now(timezone.utc).replace(tzinfo=None)
        assert before <= dt <= after


class TestConfig:
    def test_is_prod_false_by_default(self):
        from app.core.config import settings

        assert settings.is_prod is False
        assert settings.env == "development"

    def test_upload_secret_is_default(self):
        from app.core.config import settings

        assert settings.upload_secret_is_default is True

    def test_use_turso_false_without_creds(self):
        from app.core.config import settings

        assert settings.use_turso is False

    def test_anon_limits(self):
        from app.core.config import settings

        assert settings.anon_conversions_per_day == 5
        assert settings.anon_req_per_min == 60


class TestRateLimitHelpers:
    def test_sign_deterministic(self):
        from app.api.dependencies.rate_limit import _sign

        assert _sign("hello") == _sign("hello")
        assert _sign("hello") != _sign("world")

    def test_anonymous_identity_deterministic(self):
        from unittest.mock import MagicMock

        from app.api.dependencies.rate_limit import _anonymous_identity

        req = MagicMock()
        req.client.host = "1.2.3.4"
        req.headers.get.return_value = "TestAgent/1.0"
        a = _anonymous_identity(req)
        b = _anonymous_identity(req)
        assert a == b
        assert a.startswith("anon-")

    def test_anonymous_identity_varies_by_ip(self):
        from unittest.mock import MagicMock

        from app.api.dependencies.rate_limit import _anonymous_identity

        req1 = MagicMock()
        req1.client.host = "1.1.1.1"
        req1.headers.get.return_value = "Agent"
        req2 = MagicMock()
        req2.client.host = "2.2.2.2"
        req2.headers.get.return_value = "Agent"
        assert _anonymous_identity(req1) != _anonymous_identity(req2)

    def test_anonymous_identity_no_client(self):
        from unittest.mock import MagicMock

        from app.api.dependencies.rate_limit import _anonymous_identity

        req = MagicMock()
        req.client = None
        req.headers.get.return_value = ""
        result = _anonymous_identity(req)
        assert result.startswith("anon-")


class TestExceptions:
    def test_app_error_fields(self):
        from app.core.exceptions import AppError

        e = AppError("MY_CODE", "my message", 418)
        assert e.code == "MY_CODE"
        assert e.message == "my message"
        assert e.status_code == 418

    def test_not_found(self):
        from app.core.exceptions import NotFoundError

        e = NotFoundError("missing")
        assert e.status_code == 404
        assert e.code == "NOT_FOUND"

    def test_unsupported_format(self):
        from app.core.exceptions import UnsupportedFormatError

        e = UnsupportedFormatError("bad format")
        assert e.status_code == 415

    def test_unsupported_conversion(self):
        from app.core.exceptions import UnsupportedConversionError

        e = UnsupportedConversionError("no conv")
        assert e.status_code == 422

    def test_conflict_state(self):
        from app.core.exceptions import ConflictStateError

        e = ConflictStateError("conflict")
        assert e.status_code == 409

    def test_invalid_data(self):
        from app.core.exceptions import InvalidDataError

        e = InvalidDataError("bad")
        assert e.status_code == 422

    def test_office_error(self):
        from app.core.exceptions import OfficeError

        e = OfficeError("fail", "MY_CODE")
        assert e.code == "MY_CODE"
        assert str(e) == "fail"

    def test_office_error_default_code(self):
        from app.core.exceptions import OfficeError

        e = OfficeError("fail")
        assert e.code == "CONVERSION_FAILED"
