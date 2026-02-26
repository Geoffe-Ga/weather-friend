"""Tests for weather_friend.main module."""

from weather_friend.main import main


def test_main_runs() -> None:
    """Test that main() runs without error."""
    main()  # Should print "Hello from weather-friend!"
