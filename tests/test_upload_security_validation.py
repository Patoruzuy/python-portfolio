"""
Unit tests for upload content validation.
"""

import io

from werkzeug.datastructures import FileStorage

from app.utils.upload_security import validate_uploaded_image


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

def test_executable_file_upload_rejection():
    """Test that executable files are rejected."""
    upload = _file('malicious.exe', b'MZ\x90\x00\x03\x00\x00\x00', 'application/x-msdownload')
    is_valid, error = validate_uploaded_image(upload, {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'})
    assert is_valid is False
    
def test_php_file_upload_rejection():
    """Test that PHP files are rejected."""
    upload = _file('shell.php', b'<?php system($_GET["cmd"]); ?>', 'application/x-httpd-php')
    is_valid, error = validate_uploaded_image(upload, {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'})
    assert is_valid is False

def test_double_extension_attacks():
    """Test rejection of double extensions."""
    upload = _file('image.jpg.php', b'<?php system($_GET["cmd"]); ?>', 'image/jpeg')
    is_valid, error = validate_uploaded_image(upload, {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'})
    assert is_valid is False

def test_null_byte_injection():
    """Test rejection of null byte in filename."""
    upload = _file('image.jpg\x00.php', b'fake image data', 'image/jpeg')
    is_valid, error = validate_uploaded_image(upload, {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'})
    assert is_valid is False

def test_file_size_limits_enforced(app):
    """Test that file size limits are enforced."""
    # This is typically handled by Flask's MAX_CONTENT_LENGTH
    # We can verify the config is set
    assert 'MAX_CONTENT_LENGTH' in app.config
    assert app.config['MAX_CONTENT_LENGTH'] > 0

def test_zip_bomb_prevention():
    """Test prevention of zip bombs (often disguised as other formats)."""
    # A tiny valid gzip file header
    zip_payload = b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03'
    upload = _file('bomb.png', zip_payload, 'image/png')
    is_valid, error = validate_uploaded_image(upload, {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'})
    assert is_valid is False
