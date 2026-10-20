"""Tests for CLI entrypoint and database seeding."""

import sys
from unittest import mock

import pytest

from hotel_booking.main import main, seed_database


def test_seed_database() -> None:
    """Verify seed_database populates database records without error."""
    seed_database()


def test_cli_version_flag() -> None:
    """Verify --version flag prints version and exits."""
    with mock.patch.object(sys, "argv", ["hotel-booking", "--version"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


def test_cli_seed_only_flag() -> None:
    """Verify --seed-only flag executes seeding and exits cleanly."""
    with mock.patch.object(sys, "argv", ["hotel-booking", "--seed-only"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0
