"""
Coverage-focused tests for modular admin product routes.

These tests target routes/admin/products.py through app_factory.create_app().
"""

from __future__ import annotations

import json

import pytest

from app.app_factory import create_app
from app.models import Product, db


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


def test_products_routes_require_authentication(modular_client):
    list_resp = modular_client.get('/admin/products', follow_redirects=False)
    add_resp = modular_client.get('/admin/products/add', follow_redirects=False)

    assert list_resp.status_code == 302
    assert add_resp.status_code == 302
    assert '/admin/login' in list_resp.headers.get('Location', '')


def test_products_list_renders(modular_client, modular_app):
    login_admin(modular_client)

    with modular_app.app_context():
        db.session.add(
            Product(
                name='Coverage Product',
                description='Product description',
                price=29.99,
                type='digital',
                category='software',
            )
        )
        db.session.commit()

    response = modular_client.get('/admin/products')
    assert response.status_code == 200
    assert b'Coverage Product' in response.data


def test_add_product_get_renders_form(modular_client):
    login_admin(modular_client)

    response = modular_client.get('/admin/products/add')
    assert response.status_code == 200
    assert b'Add Product' in response.data or b'Create Product' in response.data


def test_add_product_success_creates_record(modular_client, modular_app):
    login_admin(modular_client)

    response = modular_client.post(
        '/admin/products/add',
        data={
            'name': 'New Product',
            'description': 'A new product',
            'price': '49.50',
            'type': 'digital',
            'category': 'tools',
            'features': 'Feature 1\nFeature 2',
            'purchase_link': '',
            'demo_link': 'https://demo.example/product',
            'image': '/static/images/new-product.jpg',
            'available': 'on',
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert '/admin/products' in response.headers.get('Location', '')

    with modular_app.app_context():
        product = Product.query.filter_by(name='New Product').first()
        assert product is not None
        assert product.price == 49.50
        assert json.loads(product.features_json) == ['Feature 1', 'Feature 2']
        assert product.purchase_link is None
        assert product.available is True


def test_add_product_invalid_price_returns_form(modular_client, modular_app):
    login_admin(modular_client)

    response = modular_client.post(
        '/admin/products/add',
        data={
            'name': 'Bad Product',
            'description': 'Bad input',
            'price': 'not-a-number',
            'type': 'digital',
            'category': 'tools',
        },
    )

    assert response.status_code == 200
    assert b'Product Form' in response.data or b'Add Product' in response.data

    with modular_app.app_context():
        assert Product.query.filter_by(name='Bad Product').first() is None


def test_add_product_generic_exception_rolls_back(modular_client, modular_app, monkeypatch):
    login_admin(modular_client)

    def raise_add_error(_obj):
        raise RuntimeError('db add failed')

    monkeypatch.setattr(db.session, 'add', raise_add_error)

    response = modular_client.post(
        '/admin/products/add',
        data={
            'name': 'Exploding Product',
            'description': 'Should fail',
            'price': '10',
            'type': 'digital',
            'category': 'tools',
        },
    )

    assert response.status_code == 200
    assert b'Product Form' in response.data or b'Add Product' in response.data


def test_edit_product_get_and_post_update_fields(modular_client, modular_app):
    login_admin(modular_client)

    with modular_app.app_context():
        product = Product(
            name='Editable Product',
            description='Before edit',
            price=20.0,
            type='digital',
            category='tools',
            features_json='["Old"]',
            image_url='/static/images/old.jpg',
            available=True,
        )
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    get_response = modular_client.get(f'/admin/products/edit/{product_id}')
    assert get_response.status_code == 200

    post_response = modular_client.post(
        f'/admin/products/edit/{product_id}',
        data={
            'name': 'Edited Product',
            'description': 'After edit',
            'price': '99.99',
            'type': 'service',
            'category': 'consulting',
            'features': 'One\nTwo',
            'purchase_link': '',
            'demo_link': '',
            'image': '',
            # available omitted => false branch
        },
        follow_redirects=False,
    )

    assert post_response.status_code == 302

    with modular_app.app_context():
        product = Product.query.get(product_id)
        assert product is not None
        assert product.name == 'Edited Product'
        assert product.price == 99.99
        assert product.type == 'service'
        assert product.category == 'consulting'
        assert json.loads(product.features_json) == ['One', 'Two']
        assert product.image_url == '/static/images/old.jpg'
        assert product.available is False


def test_edit_and_delete_unknown_product_return_404(modular_client):
    login_admin(modular_client)

    edit_response = modular_client.get('/admin/products/edit/99999')
    delete_response = modular_client.post('/admin/products/delete/99999')

    assert edit_response.status_code == 404
    assert delete_response.status_code == 404


def test_delete_product_success(modular_client, modular_app):
    login_admin(modular_client)

    with modular_app.app_context():
        product = Product(
            name='Delete Product',
            description='Delete me',
            price=15.0,
            type='digital',
            category='tools',
        )
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    response = modular_client.post(f'/admin/products/delete/{product_id}', follow_redirects=False)
    assert response.status_code == 302

    with modular_app.app_context():
        assert Product.query.get(product_id) is None
