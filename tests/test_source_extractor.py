import tarfile
from fetcher.source_extractor import extract_archive


def test_unsupported_archive_format(tmp_path):
    
    fake_file = tmp_path / "malware.exe"
    fake_file.write_text("hello world")     # create an empty file
    
    import pytest
    with pytest.raises(ValueError):
        extract_archive(fake_file, tmp_path / "output")


def test_missing_archive_file(tmp_path):
    
    import pytest
    with pytest.raises(FileNotFoundError):
        extract_archive(tmp_path / "does_not_exist.tar.gz", tmp_path / "output")


def test_tar_gz_extraction(tmp_path):
    
    archive_path = tmp_path / "test.tar.gz"
    inner_file = tmp_path / "hello.txt"
    inner_file.write_text("hello world")
    
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(inner_file, arcname="hello.txt")

    output_dir = tmp_path / "extracted"
    result = extract_archive(archive_path, output_dir)

    assert result.exists()        
    assert (result / "hello.txt").exists() 


def test_tar_gz_extraction_with_dotted_filename(tmp_path):
    archive_path = tmp_path / "requests-2.32.5.tar.gz"
    inner_file = tmp_path / "main.py"
    inner_file.write_text("print('ok')")

    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(inner_file, arcname="main.py")

    output_dir = tmp_path / "extracted"
    result = extract_archive(archive_path, output_dir)

    assert result.exists()
    assert (result / "main.py").exists()
