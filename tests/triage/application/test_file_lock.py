from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from genome_toolkit.triage.application.file_lock import FileLock, LockError


class TestFileLock:
    """Tests for advisory file locking."""

    def test_lock_acquire_and_release(self, tmp_path: Path) -> None:
        lock_path = tmp_path / ".triage.lock"
        with FileLock(lock_path):
            assert lock_path.exists()
        # After exit, should be able to reacquire
        with FileLock(lock_path):
            pass

    def test_lock_blocks_concurrent_access(self, tmp_path: Path) -> None:
        lock_path = tmp_path / ".triage.lock"
        barrier = threading.Barrier(2, timeout=5)
        results: list[str] = []

        def holder() -> None:
            with FileLock(lock_path, timeout=5.0):
                results.append("holder_acquired")
                barrier.wait()  # signal that lock is held
                time.sleep(0.5)  # hold the lock
                results.append("holder_released")

        def waiter() -> None:
            barrier.wait()  # wait until holder has the lock
            time.sleep(0.05)  # small delay to ensure ordering
            with FileLock(lock_path, timeout=5.0):
                results.append("waiter_acquired")

        t1 = threading.Thread(target=holder)
        t2 = threading.Thread(target=waiter)
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        # Waiter must acquire after holder releases
        assert results.index("holder_released") < results.index("waiter_acquired")

    def test_lock_raises_after_timeout(self, tmp_path: Path) -> None:
        lock_path = tmp_path / ".triage.lock"
        acquired = threading.Event()

        def holder() -> None:
            with FileLock(lock_path, timeout=5.0):
                acquired.set()
                time.sleep(2.0)  # hold longer than waiter timeout

        t = threading.Thread(target=holder)
        t.start()
        acquired.wait(timeout=5)

        with pytest.raises(LockError, match="another triage session is active"):
            with FileLock(lock_path, timeout=0.2):
                pass

        t.join(timeout=10)

    def test_lock_creates_parent_directories(self, tmp_path: Path) -> None:
        lock_path = tmp_path / "nested" / "dir" / ".triage.lock"
        with FileLock(lock_path):
            assert lock_path.parent.exists()

    def test_reentrant_different_paths(self, tmp_path: Path) -> None:
        lock_a = tmp_path / "a.lock"
        lock_b = tmp_path / "b.lock"
        with FileLock(lock_a):
            with FileLock(lock_b):
                pass  # no deadlock
