from unittest.mock import patch

from pliparser import run_plip2csv


@patch("pliparser.core.plip2csv_stream")
def test_run_plip2csv_calls_stream(mock_plip2csv_stream):
    run_plip2csv("report.txt", "out")
    mock_plip2csv_stream.assert_called_once()
