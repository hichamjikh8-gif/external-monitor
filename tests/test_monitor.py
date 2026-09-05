"""Unit tests for the monitor core logic."""

import pytest
from unittest.mock import patch, MagicMock
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from monitor import check_site


class TestCheckSite:

    def test_returns_ok_on_200(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("monitor.requests.get", return_value=mock_resp):
            ok, code, err = check_site("https://example.com", 10)
        assert ok is True
        assert code == 200
        assert err == ""

    def test_returns_ok_on_301(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 301
        with patch("monitor.requests.get", return_value=mock_resp):
            ok, code, err = check_site("https://example.com", 10)
        assert ok is True

    def test_returns_fail_on_500(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        with patch("monitor.requests.get", return_value=mock_resp):
            ok, code, err = check_site("https://example.com", 10)
        assert ok is False
        assert code == 500

    def test_returns_fail_on_timeout(self):
        import requests as req
        with patch("monitor.requests.get", side_effect=req.exceptions.Timeout):
            ok, code, err = check_site("https://example.com", 1)
        assert ok is False
        assert code == 0
        assert "Timeout" in err

    def test_returns_fail_on_connection_error(self):
        import requests as req
        with patch("monitor.requests.get", side_effect=req.exceptions.ConnectionError("refused")):
            ok, code, err = check_site("https://example.com", 5)
        assert ok is False
        assert "ConnectionError" in err
