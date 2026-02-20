"""
Regression tests for admin upload URL/path resolution.
"""

import io
import os

import pytest

from admin_routes import build_uploaded_image_url
from routes.admin.utils import build_uploaded_image_url as modular_build_uploaded_image_url


def test_upload_url_derives_from_static_subfolder(app):
    with app.app_context():
        app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads', 'projects')
        app.config['UPLOAD_URL_PREFIX'] = ''

        url = build_uploaded_image_url('hero.png')
        assert url == '/static/uploads/projects/hero.png'


def test_upload_url_uses_explicit_prefix_for_non_static_folder(app, tmp_path):
    with app.app_context():
        app.config['UPLOAD_FOLDER'] = str(tmp_path / 'external-uploads')
        app.config['UPLOAD_URL_PREFIX'] = '/media/uploads'

        url = build_uploaded_image_url('avatar.png')
        assert url == '/media/uploads/avatar.png'


def test_upload_url_requires_prefix_for_non_static_folder(app, tmp_path):
    with app.app_context():
        app.config['UPLOAD_FOLDER'] = str(tmp_path / 'external-uploads')
        app.config['UPLOAD_URL_PREFIX'] = ''

        with pytest.raises(ValueError):
            build_uploaded_image_url('avatar.png')


def test_modular_upload_url_matches_monolith(app):
    with app.app_context():
        app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'images')
        app.config['UPLOAD_URL_PREFIX'] = ''

        expected = '/static/images/check.png'
        assert build_uploaded_image_url('check.png') == expected
        assert modular_build_uploaded_image_url('check.png') == expected


def test_upload_route_returns_derived_custom_prefix(auth_client, app, tmp_path):
    with app.app_context():
        app.config['UPLOAD_FOLDER'] = str(tmp_path / 'admin-uploads')
        app.config['UPLOAD_URL_PREFIX'] = '/media/uploads'

    png_payload = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    response = auth_client.post(
        '/admin/upload-image?popup=true',
        data={
            'popup': 'true',
            'image': (io.BytesIO(png_payload), 'team-photo.png')
        },
        content_type='multipart/form-data'
    )

    assert response.status_code == 200
    assert b'/media/uploads/team-photo_' in response.data

    uploaded_files = list((tmp_path / 'admin-uploads').glob('team-photo_*.png'))
    assert len(uploaded_files) == 1
