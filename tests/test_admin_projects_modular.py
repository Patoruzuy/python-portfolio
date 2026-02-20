"""
Coverage-focused tests for modular admin projects routes.

These tests target routes/admin/projects.py through app_factory.create_app().
"""

from __future__ import annotations

import json

import pytest

from app_factory import create_app
from models import db, Product, Project, RaspberryPiProject


@pytest.fixture
def modular_app():
    app = create_app('testing')
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        WTF_CSRF_ENABLED=False,
        SECRET_KEY='test-secret-key',
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def modular_client(modular_app):
    return modular_app.test_client()


def login_admin(client) -> None:
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True


def test_projects_list_requires_authentication(modular_client):
    response = modular_client.get('/admin/projects', follow_redirects=False)
    assert response.status_code == 302
    assert '/admin/login' in response.headers.get('Location', '')


def test_projects_list_renders_for_authenticated_admin(modular_client, modular_app):
    login_admin(modular_client)

    with modular_app.app_context():
        db.session.add(
            Project(
                title='Coverage Project',
                description='Route coverage project',
                technologies='Python,Flask',
                category='web',
            )
        )
        db.session.commit()

    response = modular_client.get('/admin/projects')
    assert response.status_code == 200
    assert b'Coverage Project' in response.data


def test_add_project_post_persists_optional_fields(modular_client, modular_app):
    login_admin(modular_client)

    response = modular_client.post(
        '/admin/projects/add',
        data={
            'title': 'Minimal Project',
            'description': 'No optional links',
            'technologies': 'Python',
            'category': 'web',
            'image': '/static/images/minimal.jpg',
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert '/admin/projects' in response.headers.get('Location', '')

    with modular_app.app_context():
        project = Project.query.filter_by(title='Minimal Project').first()
        assert project is not None
        assert project.github_url is None
        assert project.demo_url is None
        assert project.featured is False


def test_edit_project_post_updates_fields(modular_client, modular_app):
    login_admin(modular_client)

    with modular_app.app_context():
        project = Project(
            title='Editable Project',
            description='Before edit',
            technologies='Python',
            category='web',
            github_url='https://example.com/old',
            demo_url='https://example.com/old-demo',
            image_url='/static/images/old.jpg',
            featured=False,
        )
        db.session.add(project)
        db.session.commit()
        project_id = project.id

    response = modular_client.post(
        f'/admin/projects/edit/{project_id}',
        data={
            'title': 'Edited Project',
            'description': 'After edit',
            'technologies': 'Python,Flask',
            'category': 'backend',
            'github': '',
            'demo': 'https://example.com/new-demo',
            'image': '/static/images/new.jpg',
            'featured': 'on',
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    with modular_app.app_context():
        project = Project.query.get(project_id)
        assert project is not None
        assert project.title == 'Edited Project'
        assert project.category == 'backend'
        assert project.github_url is None
        assert project.demo_url == 'https://example.com/new-demo'
        assert project.featured is True


def test_edit_project_unknown_id_returns_404(modular_client):
    login_admin(modular_client)
    response = modular_client.get('/admin/projects/edit/99999')
    assert response.status_code == 404


def test_delete_project_removes_record(modular_client, modular_app):
    login_admin(modular_client)

    with modular_app.app_context():
        project = Project(
            title='Delete Me',
            description='To be deleted',
            technologies='Python',
            category='web',
        )
        db.session.add(project)
        db.session.commit()
        project_id = project.id

    response = modular_client.post(
        f'/admin/projects/delete/{project_id}',
        follow_redirects=False,
    )
    assert response.status_code == 302

    with modular_app.app_context():
        assert Project.query.get(project_id) is None


def test_add_rpi_project_parses_structured_form_data(modular_client, modular_app, monkeypatch):
    login_admin(modular_client)

    with modular_app.app_context():
        product = Product(
            name='Own Sensor Pack',
            description='Product linked from parts list',
            price=19.99,
            type='digital',
            category='hardware',
        )
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    from routes.admin import projects as projects_module

    def fake_validate(url):
        if 'valid-video' in url:
            return True, 'https://youtube.com/embed/abc123', 'youtube', None
        return False, None, None, 'Unsupported video URL'

    monkeypatch.setattr(projects_module, 'validate_video_url', fake_validate)

    response = modular_client.post(
        '/admin/raspberry-pi/add',
        data={
            'title': 'Smart Greenhouse',
            'description': 'Automated greenhouse monitoring',
            'hardware': 'Raspberry Pi 5, DHT22',
            'technologies': 'Python,GPIO',
            'features': 'Monitoring\nAlerts',
            # No image to cover placeholder fallback branch
            'doc_title[]': ['Setup Guide', 'Ignore Missing URL'],
            'doc_url[]': ['https://docs.example.com/setup', ''],
            'doc_type[]': ['github', 'markdown'],
            'diagram_title[]': ['Wiring Diagram'],
            'diagram_url[]': ['https://example.com/wiring.png'],
            'diagram_type[]': ['image'],
            'part_name[]': ['Camera Module', 'Custom Board', 'USB Cable'],
            'part_url[]': ['https://shop.example/camera', '', ''],
            'part_is_own_product[]': ['on', 'on', ''],
            'part_product_id[]': [str(product_id), 'abc', ''],
            'video_title[]': ['Valid Tutorial', 'Bad Tutorial'],
            'video_url[]': [
                'https://youtube.com/watch?v=valid-video',
                'https://invalid.example/video',
            ],
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert '/admin/raspberry-pi' in response.headers.get('Location', '')

    with modular_app.app_context():
        project = RaspberryPiProject.query.filter_by(title='Smart Greenhouse').first()
        assert project is not None
        assert project.image_url == '/static/images/placeholder.jpg'
        assert json.loads(project.hardware_json) == ['Raspberry Pi 5', 'DHT22']
        assert json.loads(project.features_json) == ['Monitoring', 'Alerts']

        docs = json.loads(project.documentation_json)
        assert docs == [
            {
                'title': 'Setup Guide',
                'url': 'https://docs.example.com/setup',
                'type': 'github',
            }
        ]

        diagrams = json.loads(project.circuit_diagrams_json)
        assert diagrams == [
            {
                'title': 'Wiring Diagram',
                'url': 'https://example.com/wiring.png',
                'type': 'image',
            }
        ]

        parts = json.loads(project.parts_list_json)
        assert parts[0]['is_own_product'] is True
        assert parts[0]['product_id'] == product_id
        assert parts[1]['is_own_product'] is True
        assert parts[1]['product_id'] is None
        assert parts[2]['is_own_product'] is False
        assert parts[2]['product_id'] is None

        videos = json.loads(project.videos_json)
        assert len(videos) == 1
        assert videos[0]['title'] == 'Valid Tutorial'
        assert videos[0]['embed_url'] == 'https://youtube.com/embed/abc123'


def test_edit_rpi_project_preserves_image_when_blank(modular_client, modular_app, monkeypatch):
    login_admin(modular_client)

    with modular_app.app_context():
        project = RaspberryPiProject(
            title='Editable RPi',
            description='Before edit',
            hardware_json=json.dumps(['Pi 4']),
            technologies='Python',
            features_json=json.dumps(['Old feature']),
            github_url='https://example.com/old',
            image_url='/static/images/existing-rpi.jpg',
        )
        db.session.add(project)
        db.session.commit()
        project_id = project.id

    from routes.admin import projects as projects_module

    monkeypatch.setattr(
        projects_module,
        'validate_video_url',
        lambda _url: (False, None, None, 'Invalid URL format'),
    )

    response = modular_client.post(
        f'/admin/raspberry-pi/edit/{project_id}',
        data={
            'title': 'Editable RPi Updated',
            'description': 'After edit',
            'hardware': 'Pi 5, Sensor',
            'technologies': 'Python,Flask',
            'features': 'Feature A\nFeature B',
            'github': '',
            'image': '',
            'doc_title[]': ['Doc A'],
            'doc_url[]': ['https://docs.example/a'],
            'doc_type[]': ['github'],
            'diagram_title[]': ['Diagram A'],
            'diagram_url[]': ['https://docs.example/diagram-a'],
            'diagram_type[]': ['link'],
            'part_name[]': ['Bracket'],
            'part_url[]': ['https://shop.example/bracket'],
            'part_is_own_product[]': ['no'],
            'part_product_id[]': [''],
            'video_title[]': ['Invalid Tutorial'],
            'video_url[]': ['https://invalid.example/video'],
        },
        follow_redirects=False,
    )

    assert response.status_code == 302

    with modular_app.app_context():
        project = RaspberryPiProject.query.get(project_id)
        assert project is not None
        assert project.title == 'Editable RPi Updated'
        assert project.github_url is None
        assert project.image_url == '/static/images/existing-rpi.jpg'
        assert json.loads(project.hardware_json) == ['Pi 5', 'Sensor']
        assert json.loads(project.features_json) == ['Feature A', 'Feature B']
        assert json.loads(project.documentation_json)[0]['title'] == 'Doc A'
        assert json.loads(project.videos_json) == []


def test_delete_rpi_project_removes_record(modular_client, modular_app):
    login_admin(modular_client)

    with modular_app.app_context():
        project = RaspberryPiProject(
            title='Delete RPi',
            description='To be deleted',
            hardware_json=json.dumps(['Pi']),
            technologies='Python',
            features_json=json.dumps(['Feature']),
        )
        db.session.add(project)
        db.session.commit()
        project_id = project.id

    response = modular_client.post(
        f'/admin/raspberry-pi/delete/{project_id}',
        follow_redirects=False,
    )

    assert response.status_code == 302

    with modular_app.app_context():
        assert RaspberryPiProject.query.get(project_id) is None


def test_delete_rpi_project_unknown_id_returns_404(modular_client):
    login_admin(modular_client)
    response = modular_client.post('/admin/raspberry-pi/delete/99999')
    assert response.status_code == 404
