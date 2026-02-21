"""
Admin projects and Raspberry Pi management routes.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.wrappers.response import Response as WerkzeugResponse
from typing import Union
import json
from app.models import db, Project, RaspberryPiProject, Product
from app.utils.video_utils import validate_video_url
from app.routes.admin.utils import login_required, is_truthy, parse_optional_int

# Create admin projects blueprint
admin_projects_bp = Blueprint('admin_projects', __name__, url_prefix='/admin')


# ========== PROJECTS ==========

@admin_projects_bp.route('/projects')
@login_required
def projects() -> str:
    """List all projects."""
    all_projects = Project.query.all()
    return render_template('admin/projects.html', projects=all_projects)


@admin_projects_bp.route('/projects/add', methods=['GET', 'POST'])
@login_required
def add_project() -> Union[str, WerkzeugResponse]:
    """Add a new project."""
    if request.method == 'POST':
        new_project = Project(
            title=request.form.get('title'),
            description=request.form.get('description'),
            technologies=request.form.get('technologies'),
            category=request.form.get('category'),
            github_url=request.form.get('github') or None,
            demo_url=request.form.get('demo') or None,
            image_url=request.form.get('image'),
            featured=request.form.get('featured') == 'on'
        )

        db.session.add(new_project)
        db.session.commit()

        flash('Project added successfully!', 'success')
        return redirect(url_for('admin_projects.projects'))

    return render_template('admin/project_form.html', project=None)


@admin_projects_bp.route('/projects/edit/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id: int) -> Union[str, WerkzeugResponse]:
    """Edit an existing project."""
    project = Project.query.get_or_404(project_id)

    if request.method == 'POST':
        project.title = request.form.get('title')
        project.description = request.form.get('description')
        project.technologies = request.form.get('technologies')
        project.category = request.form.get('category')
        project.github_url = request.form.get('github') or None
        project.demo_url = request.form.get('demo') or None
        project.image_url = request.form.get('image')
        project.featured = request.form.get('featured') == 'on'

        db.session.commit()

        flash('Project updated successfully!', 'success')
        return redirect(url_for('admin_projects.projects'))

    return render_template('admin/project_form.html', project=project)


@admin_projects_bp.route('/projects/delete/<int:project_id>', methods=['POST'])
@login_required
def delete_project(project_id: int) -> WerkzeugResponse:
    """Delete a project."""
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted successfully!', 'success')
    return redirect(url_for('admin_projects.projects'))


# ========== RASPBERRY PI ==========

@admin_projects_bp.route('/raspberry-pi')
@login_required
def raspberry_pi() -> str:
    """List all Raspberry Pi projects."""
    projects = RaspberryPiProject.query.order_by(RaspberryPiProject.id).all()
    return render_template('admin/raspberry_pi.html', projects=projects)


@admin_projects_bp.route('/raspberry-pi/add', methods=['GET', 'POST'])
@login_required
def add_rpi_project() -> Union[str, WerkzeugResponse]:
    """Create a new Raspberry Pi project."""
    products = Product.query.order_by(Product.name).all()
    
    if request.method == 'POST':
        # Process documentation links
        doc_titles = request.form.getlist('doc_title[]')
        doc_urls = request.form.getlist('doc_url[]')
        doc_types = request.form.getlist('doc_type[]')
        documentation = []
        for title, url, doc_type in zip(doc_titles, doc_urls, doc_types):
            if title and url:
                documentation.append({'title': title, 'url': url, 'type': doc_type})
        
        # Process circuit diagrams
        diagram_titles = request.form.getlist('diagram_title[]')
        diagram_urls = request.form.getlist('diagram_url[]')
        diagram_types = request.form.getlist('diagram_type[]')
        circuit_diagrams = []
        for title, url, diagram_type in zip(diagram_titles, diagram_urls, diagram_types):
            if title and url:
                circuit_diagrams.append({'title': title, 'url': url, 'type': diagram_type})
        
        # Process parts list
        part_names = request.form.getlist('part_name[]')
        part_urls = request.form.getlist('part_url[]')
        part_is_own_product = request.form.getlist('part_is_own_product[]')
        part_product_ids = request.form.getlist('part_product_id[]')
        parts_list = []
        for i, (name, url) in enumerate(zip(part_names, part_urls)):
            if name:
                is_own = i < len(part_is_own_product) and is_truthy(part_is_own_product[i])
                raw_product_id = part_product_ids[i] if i < len(part_product_ids) else None
                product_id = parse_optional_int(raw_product_id) if is_own else None
                parts_list.append({
                    'name': name,
                    'url': url or None,
                    'is_own_product': is_own,
                    'product_id': product_id
                })
        
        # Process video tutorials (with validation)
        video_titles = request.form.getlist('video_title[]')
        video_urls = request.form.getlist('video_url[]')
        videos = []
        for title, url in zip(video_titles, video_urls):
            if title and url:
                is_valid, embed_url, platform, error = validate_video_url(url)
                if is_valid:
                    videos.append({'title': title, 'url': url, 'embed_url': embed_url})
                else:
                    flash(f'Video "{title}" has invalid URL: {error}', 'warning')
        
        project = RaspberryPiProject(
            title=request.form.get('title'),
            description=request.form.get('description'),
            hardware_json=json.dumps([h.strip() for h in request.form.get('hardware', '').split(',') if h.strip()]),
            technologies=request.form.get('technologies', ''),
            features_json=json.dumps([f.strip() for f in request.form.get('features', '').split('\n') if f.strip()]),
            github_url=request.form.get('github') or None,
            image_url=request.form.get('image') or '/static/images/placeholder.jpg',
            documentation_json=json.dumps(documentation),
            circuit_diagrams_json=json.dumps(circuit_diagrams),
            parts_list_json=json.dumps(parts_list),
            videos_json=json.dumps(videos)
        )

        db.session.add(project)
        db.session.commit()

        flash('Raspberry Pi project added successfully!', 'success')
        return redirect(url_for('admin_projects.raspberry_pi'))

    return render_template('admin/rpi_form.html', project=None, products=products)


@admin_projects_bp.route('/raspberry-pi/edit/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_rpi_project(project_id: int) -> Union[str, WerkzeugResponse]:
    """Edit an existing Raspberry Pi project."""
    project = RaspberryPiProject.query.get_or_404(project_id)
    products = Product.query.order_by(Product.name).all()

    if request.method == 'POST':
        project.title = request.form.get('title')
        project.description = request.form.get('description')
        project.hardware_json = json.dumps(
            [h.strip() for h in request.form.get('hardware', '').split(',') if h.strip()])
        project.technologies = request.form.get('technologies', '')
        project.features_json = json.dumps(
            [f.strip() for f in request.form.get('features', '').split('\n') if f.strip()])
        project.github_url = request.form.get('github') or None
        project.image_url = request.form.get('image') or project.image_url
        
        # Process documentation, circuit diagrams, parts list, videos (same as add)
        doc_titles = request.form.getlist('doc_title[]')
        doc_urls = request.form.getlist('doc_url[]')
        doc_types = request.form.getlist('doc_type[]')
        documentation = []
        for title, url, doc_type in zip(doc_titles, doc_urls, doc_types):
            if title and url:
                documentation.append({'title': title, 'url': url, 'type': doc_type})
        project.documentation_json = json.dumps(documentation)
        
        diagram_titles = request.form.getlist('diagram_title[]')
        diagram_urls = request.form.getlist('diagram_url[]')
        diagram_types = request.form.getlist('diagram_type[]')
        circuit_diagrams = []
        for title, url, diagram_type in zip(diagram_titles, diagram_urls, diagram_types):
            if title and url:
                circuit_diagrams.append({'title': title, 'url': url, 'type': diagram_type})
        project.circuit_diagrams_json = json.dumps(circuit_diagrams)
        
        part_names = request.form.getlist('part_name[]')
        part_urls = request.form.getlist('part_url[]')
        part_is_own_product = request.form.getlist('part_is_own_product[]')
        part_product_ids = request.form.getlist('part_product_id[]')
        parts_list = []
        for i, (name, url) in enumerate(zip(part_names, part_urls)):
            if name:
                is_own = i < len(part_is_own_product) and is_truthy(part_is_own_product[i])
                raw_product_id = part_product_ids[i] if i < len(part_product_ids) else None
                product_id = parse_optional_int(raw_product_id) if is_own else None
                parts_list.append({
                    'name': name,
                    'url': url or None,
                    'is_own_product': is_own,
                    'product_id': product_id
                })
        project.parts_list_json = json.dumps(parts_list)
        
        video_titles = request.form.getlist('video_title[]')
        video_urls = request.form.getlist('video_url[]')
        videos = []
        for title, url in zip(video_titles, video_urls):
            if title and url:
                is_valid, embed_url, platform, error = validate_video_url(url)
                if is_valid:
                    videos.append({'title': title, 'url': url, 'embed_url': embed_url})
                else:
                    flash(f'Video "{title}" has invalid URL: {error}', 'warning')
        project.videos_json = json.dumps(videos)

        db.session.commit()

        flash('Raspberry Pi project updated successfully!', 'success')
        return redirect(url_for('admin_projects.raspberry_pi'))

    return render_template('admin/rpi_form.html', project=project, products=products)


@admin_projects_bp.route('/raspberry-pi/delete/<int:project_id>', methods=['POST'])
@login_required
def delete_rpi_project(project_id: int) -> WerkzeugResponse:
    """Delete a Raspberry Pi project."""
    project = RaspberryPiProject.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()

    flash('Raspberry Pi project deleted successfully!', 'success')
    return redirect(url_for('admin_projects.raspberry_pi'))
