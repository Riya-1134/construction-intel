import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Tests never hit the network: force demo mode before settings are cached.
os.environ["DEMO_MODE"] = "true"
os.environ["GROQ_API_KEY"] = ""

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


# 1x1 PNG and JPEG byte strings for upload tests
PNG_1x1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415478"
    "9c63f8ffff3f0005fe02fea7c1d7cc0000000049454e44ae426082"
)
JPEG_HEAD = b"\xff\xd8\xff\xe0" + b"\x00" * 64 + b"\xff\xd9"


@pytest.fixture
def png_bytes():
    return PNG_1x1


@pytest.fixture
def jpeg_bytes():
    return JPEG_HEAD
