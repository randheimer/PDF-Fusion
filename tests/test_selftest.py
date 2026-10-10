"""Tests for the version number and the smoke test that the release build runs."""

import re

from pdf_fusion import __version__
from pdf_fusion.selftest import run_smoke_test


def test_version_is_semantic():
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__)


def test_smoke_test_passes():
    assert run_smoke_test() == 0
