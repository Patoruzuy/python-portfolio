"""
Unit tests for upload content validation.
"""

import io

from werkzeug.datastructures import FileStorage

from utils.upload_security import validate_uploaded_image


def _file(filename: str, payload: bytes, mimetype: str) -> FileStorage:
    return FileStorage(stream=io.BytesIO(payload), filename=filename, content_type=mimetype)


def test_validate_uploaded_image_accepts_valid_png():
    png_payload = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    upload = _file('safe.png', png_payload, 'image/png')

    is_valid, error = validate_uploaded_image(upload, {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'})
    assert is_valid is True
    assert error == ''


def test_validate_uploaded_image_rejects_extension_content_mismatch():
    png_payload = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    upload = _file('wrong.jpg', png_payload, 'image/jpeg')

    is_valid, error = validate_uploaded_image(upload, {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'})
    assert is_valid is False
    assert 'extension does not match' in error.lower()


def test_validate_uploaded_image_rejects_svg_with_script():
    svg_payload = b"""<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>"""
    upload = _file('bad.svg', svg_payload, 'image/svg+xml')

    is_valid, error = validate_uploaded_image(upload, {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'})
    assert is_valid is False
    assert 'blocked' in error.lower() or 'not allowed' in error.lower()


def test_validate_uploaded_image_rejects_svg_external_reference():
    svg_payload = b"""<svg xmlns="http://www.w3.org/2000/svg"><use href="https://evil.example/a.svg#x"/></svg>"""
    upload = _file('bad-ref.svg', svg_payload, 'image/svg+xml')

    is_valid, error = validate_uploaded_image(upload, {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'})
    assert is_valid is False
    assert 'external references' in error.lower()


def test_validate_uploaded_image_accepts_safe_svg():
    svg_payload = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect x="1" y="1" width="8" height="8" /></svg>"""
    upload = _file('safe.svg', svg_payload, 'image/svg+xml')

    is_valid, error = validate_uploaded_image(upload, {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'})
    assert is_valid is True
    assert error == ''


def test_validate_uploaded_image_rejects_non_image_payload():
    upload = _file('not-image.png', b'not an image', 'image/png')

    is_valid, error = validate_uploaded_image(upload, {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'})
    assert is_valid is False
    assert 'not a valid' in error.lower()
