from unittest.mock import MagicMock, patch
from fetcher.pypi_fetcher import fetch_pypi_metadata


@patch("fetcher.pypi_fetcher.requests.get")
def test_pypi_fetch_success(mock_get):
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "info": {
            "name": "requests",
            "version": "2.31.0",
            "summary": "HTTP for Humans",
            "author": "Kenneth Reitz",
            "license": "Apache 2.0",
            "project_urls": {"Source": "https://github.com/psf/requests"},
            "requires_dist": ["charset-normalizer"],
        }
    }
    mock_get.return_value = mock_response

   
    result = fetch_pypi_metadata("requests")

    assert result.registry == "pypi"
    assert result.status_code == 200
    assert result.metadata["name"] == "requests"
    assert result.metadata["version"] == "2.31.0"
    assert result.metadata["project_urls"]["Source"] == "https://github.com/psf/requests"


@patch("fetcher.pypi_fetcher.requests.get")
def test_pypi_fetch_not_found(mock_get):
    
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    result = fetch_pypi_metadata("this-package-does-not-exist-xyz")

    assert result.status_code == 404
    assert result.metadata == {}
    assert result.registry == "pypi"

