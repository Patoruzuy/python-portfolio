"""
Security validation helpers for image uploads.
"""

from __future__ import annotations

from io import SEEK_SET
from typing import Optional, Set, Tuple
from xml.etree import ElementTree

from werkzeug.datastructures import FileStorage

# MIME map by normalized extension.
ALLOWED_MIME_TYPES = {
    'png': {'image/png'},
    'jpg': {'image/jpeg', 'image/pjpeg'},
    'gif': {'image/gif'},
    'webp': {'image/webp'},
    'svg': {'image/svg+xml', 'application/svg+xml', 'text/svg+xml', 'text/svg'},
}

_BLOCKED_SVG_TAGS = {
    'script',
    'foreignobject',
    'iframe',
    'object',
    'embed',
    'audio',
    'video',
}

_SAFE_SVG_TAGS = {
    'svg',
    'g',
    'path',
    'circle',
    'ellipse',
    'line',
    'polyline',
    'polygon',
    'rect',
    'text',
    'tspan',
    'defs',
    'lineargradient',
    'radialgradient',
    'stop',
    'title',
    'desc',
    'clippath',
    'mask',
    'pattern',
    'symbol',
    'use',
}

_BLOCKED_SVG_PATTERNS = (
    '<!doctype',
    '<!entity',
    'javascript:',
    'data:text/html',
)


def normalize_image_extension(extension: str) -> str:
    """Normalize image extension aliases."""
    normalized = extension.strip().lower().lstrip('.')
    if normalized == 'jpeg':
        return 'jpg'
    return normalized


def _get_local_name(tag: str) -> str:
    if not isinstance(tag, str):
        return ''
    return tag.split('}', 1)[-1].lower()


def _read_uploaded_bytes(file_storage: FileStorage) -> bytes:
    """
    Read file bytes for validation and rewind stream for later save().
    """
    stream = file_storage.stream
    try:
        stream.seek(0, SEEK_SET)
        payload = stream.read()
        stream.seek(0, SEEK_SET)
    except Exception:
        payload = b''
    return payload


def detect_image_type(payload: bytes) -> Optional[str]:
    """Detect image type by file signature/content."""
    if not payload:
        return None

    if payload.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    if payload.startswith(b'\xff\xd8\xff'):
        return 'jpg'
    if payload.startswith(b'GIF87a') or payload.startswith(b'GIF89a'):
        return 'gif'
    if len(payload) >= 12 and payload[:4] == b'RIFF' and payload[8:12] == b'WEBP':
        return 'webp'

    head = payload[:4096].lstrip(b'\xef\xbb\xbf \t\r\n').lower()
    if head.startswith(b'<?xml') or b'<svg' in head:
        return 'svg'

    return None


def validate_svg_payload(payload: bytes) -> Tuple[bool, str]:
    """Validate SVG payload against scriptable/malicious constructs."""
    try:
        svg_text = payload.decode('utf-8-sig')
    except UnicodeDecodeError:
        return False, 'SVG must be valid UTF-8 text.'

    lowered = svg_text.lower()
    for pattern in _BLOCKED_SVG_PATTERNS:
        if pattern in lowered:
            return False, 'SVG contains blocked executable content.'

    try:
        root = ElementTree.fromstring(svg_text)
    except ElementTree.ParseError:
        return False, 'SVG markup is invalid.'

    if _get_local_name(root.tag) != 'svg':
        return False, 'SVG root element is invalid.'

    for element in root.iter():
        tag_name = _get_local_name(element.tag)
        if tag_name in _BLOCKED_SVG_TAGS:
            return False, f'SVG tag <{tag_name}> is not allowed.'
        if tag_name not in _SAFE_SVG_TAGS:
            return False, f'SVG tag <{tag_name}> is not allowed.'

        for attr_name, attr_value in element.attrib.items():
            normalized_attr = _get_local_name(attr_name)
            attr_text = str(attr_value).strip()
            attr_text_lower = attr_text.lower()

            if normalized_attr.startswith('on'):
                return False, 'SVG event handler attributes are not allowed.'

            if normalized_attr == 'style':
                return False, 'Inline SVG styles are not allowed.'

            if 'javascript:' in attr_text_lower or 'data:text/html' in attr_text_lower:
                return False, 'SVG attribute contains unsafe URI.'

            if normalized_attr in {'href', 'xlink:href'}:
                # Only permit internal document fragment references.
                if attr_text and not attr_text.startswith('#'):
                    return False, 'SVG external references are not allowed.'

            if 'url(' in attr_text_lower and not attr_text_lower.startswith('url(#'):
                return False, 'SVG URL references must be internal fragment links.'

    return True, ''


def validate_uploaded_image(
    file_storage: FileStorage,
    allowed_extensions: Set[str]
) -> Tuple[bool, str]:
    """
    Validate uploaded image by extension, MIME hint, and file content.
    """
    filename = file_storage.filename or ''
    if '.' not in filename:
        return False, 'File extension is required.'

    extension = normalize_image_extension(filename.rsplit('.', 1)[1])
    normalized_allowed = {normalize_image_extension(ext) for ext in allowed_extensions}
    if extension not in normalized_allowed:
        return False, 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp, svg'

    payload = _read_uploaded_bytes(file_storage)
    if not payload:
        return False, 'Uploaded file is empty.'

    detected_type = detect_image_type(payload)
    if detected_type is None:
        return False, 'File content is not a valid supported image format.'

    if detected_type != extension:
        return False, 'File extension does not match file content.'

    declared_mime = (file_storage.mimetype or '').strip().lower()
    allowed_mimes = ALLOWED_MIME_TYPES.get(extension, set())
    if (
        declared_mime
        and declared_mime not in allowed_mimes
        and declared_mime != 'application/octet-stream'
    ):
        return False, 'MIME type does not match the uploaded image format.'

    if extension == 'svg':
        is_safe, reason = validate_svg_payload(payload)
        if not is_safe:
            return False, reason

    return True, ''
