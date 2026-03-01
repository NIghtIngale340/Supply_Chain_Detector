from unittest.mock import MagicMock, patch
from fetcher.npm_fetcher import fetch_npm_metadata


@patch("fetcher.npm_fetcher.requests.get")
def test_npm_fetch_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "name": "lodash",
        "dist-tags": {"latest": "4.17.21"},
        "versions": {
            "4.17.21": {
                "dependencies": {},
                "dist": {"tarball": "https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz"}
            }
        },
        "description": "Lodash modular utilities",
        "author": {"name": "John-David Dalton"},
        "license": "MIT",
        "repository": {"url": "git+https://github.com/lodash/lodash.git"},
        "homepage": "https://lodash.com/",
    }
    mock_get.return_value = mock_response

    result = fetch_npm_metadata("lodash")

    assert result.registry == "npm"
    assert result.status_code == 200
    assert result.metadata["name"] == "lodash"


@patch("fetcher.npm_fetcher.requests.get")
def test_npm_fetch_not_found(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    result = fetch_npm_metadata("nonexistent-npm-pkg-xyz")

    assert result.status_code == 404
    assert result.metadata == {}


def test_npm_fetch_empty_name():
    import pytest
    with pytest.raises(ValueError):
        fetch_npm_metadata("")
