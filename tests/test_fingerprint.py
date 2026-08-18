"""Dataset fingerprint tests."""

from app.data.fingerprint import compute_fingerprint


def test_same_content_same_fingerprint():
    data = b"col1,col2\n1,2\n"
    fp1 = compute_fingerprint(data, source_name="test.csv")
    fp2 = compute_fingerprint(data, source_name="test.csv")
    assert fp1 == fp2


def test_different_content_different_fingerprint():
    a = compute_fingerprint(b"a,b\n1,2", source_name="a.csv")
    b = compute_fingerprint(b"a,b\n3,4", source_name="a.csv")
    assert a != b


def test_different_source_name_different_fingerprint():
    data = b"same,content"
    a = compute_fingerprint(data, source_name="file1.csv")
    b = compute_fingerprint(data, source_name="file2.csv")
    assert a != b


def test_different_size_different_fingerprint():
    a = compute_fingerprint(b"short", source_name="x")
    b = compute_fingerprint(b"longer content", source_name="x")
    assert a != b
