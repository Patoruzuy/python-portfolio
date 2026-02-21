"""
Admin products management routes.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.wrappers.response import Response as WerkzeugResponse
from typing import Union
import json
from app.models import db, Product
from app.routes.admin.utils import login_required

# Create admin products blueprint
admin_products_bp = Blueprint('admin_products', __name__, url_prefix='/admin')


@admin_products_bp.route('/products')
@login_required
def products() -> str:
    """List all products."""
    all_products = Product.query.order_by(Product.id).all()
    return render_template('admin/products.html', products=all_products)


@admin_products_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product() -> Union[str, WerkzeugResponse]:
    """Create a new product."""
    if request.method == 'POST':
        try:
            product = Product(
                name=request.form.get('name'),
                description=request.form.get('description'),
                price=float(request.form.get('price', 0)),
                type=request.form.get('type'),
                category=request.form.get('category'),
                technologies=request.form.get('technologies') or '',
                features_json=json.dumps(
                    [f.strip() for f in request.form.get('features', '').split('\n') if f.strip()]),
                purchase_link=request.form.get('purchase_link') or None,
                demo_link=request.form.get('demo_link') or None,
                image_url=request.form.get('image') or '/static/images/placeholder.jpg',
                available=request.form.get('available') == 'on')

            db.session.add(product)
            db.session.commit()

            flash('Product added successfully!', 'success')
            return redirect(url_for('admin_products.products'))
        except (ValueError, TypeError) as e:
            flash(f'Invalid input: {str(e)}', 'error')
            return render_template('admin/product_form.html', product=None)
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'error')
            return render_template('admin/product_form.html', product=None)

    return render_template('admin/product_form.html', product=None)


@admin_products_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id: int) -> Union[str, WerkzeugResponse]:
    """Edit an existing product."""
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price', 0))
        product.type = request.form.get('type')
        product.category = request.form.get('category')
        product.technologies = request.form.get('technologies') or ''
        product.features_json = json.dumps(
            [f.strip() for f in request.form.get('features', '').split('\n') if f.strip()])
        product.purchase_link = request.form.get('purchase_link') or None
        product.demo_link = request.form.get('demo_link') or None
        product.image_url = request.form.get('image') or product.image_url
        product.available = request.form.get('available') == 'on'

        db.session.commit()

        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products.products'))

    return render_template('admin/product_form.html', product=product)


@admin_products_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id: int) -> WerkzeugResponse:
    """Delete a product."""
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()

    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin_products.products'))
