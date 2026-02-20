"""
Admin media upload routes.
"""
from flask import Blueprint, render_template, request, current_app
from werkzeug.utils import secure_filename
from typing import Any
from datetime import datetime
from utils.upload_security import validate_uploaded_image
from routes.admin.utils import (
    login_required,
    get_upload_folder,
    build_uploaded_image_url,
    resolve_upload_filepath,
    get_allowed_extensions,
    get_dashboard_endpoint,
)

# Create admin media blueprint
admin_media_bp = Blueprint('admin_media', __name__, url_prefix='/admin')


@admin_media_bp.route('/upload-image', methods=['GET', 'POST'])
@login_required
def upload_image() -> Any:
    """Handle image uploads with optional popup mode."""
    popup = request.args.get('popup') in {'1', 'true'} or request.form.get('popup') in {'1', 'true'}
    template = 'admin/upload_image_popup.html' if popup else 'admin/upload_image.html'
    dashboard_endpoint = get_dashboard_endpoint()

    if request.method == 'POST':
        uploaded_file = request.files.get('file') or request.files.get('image')
        if uploaded_file is None:
            return render_template(
                template,
                error='No file provided',
                popup=popup,
                dashboard_endpoint=dashboard_endpoint
            ), 400

        file = uploaded_file

        if file.filename == '':
            return render_template(
                template,
                error='No file selected',
                popup=popup,
                dashboard_endpoint=dashboard_endpoint
            ), 400

        if file:
            is_valid, validation_error = validate_uploaded_image(file, get_allowed_extensions())
            if not is_valid:
                return render_template(
                    template,
                    error=validation_error,
                    popup=popup,
                    dashboard_endpoint=dashboard_endpoint
                ), 400

            # Secure the filename and add timestamp
            if not file.filename:
                return render_template(
                    template,
                    error='No filename provided',
                    popup=popup,
                    dashboard_endpoint=dashboard_endpoint
                ), 400
            
            original_name = secure_filename(file.filename)
            if not original_name:
                return render_template(
                    template,
                    error='Invalid file name',
                    popup=popup,
                    dashboard_endpoint=dashboard_endpoint
                ), 400

            name_parts = original_name.rsplit('.', 1)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"

            # Save file and derive URL from configured upload path
            upload_folder = get_upload_folder()
            try:
                filepath = resolve_upload_filepath(upload_folder, filename)
                image_url = build_uploaded_image_url(filename, upload_folder)
                file.save(filepath)
            except (OSError, ValueError) as exc:
                current_app.logger.error("Upload error: %s", exc)
                return render_template(
                    template,
                    error=str(exc),
                    popup=popup,
                    dashboard_endpoint=dashboard_endpoint
                ), 400

            # Render result directly in popup or full page.
            return render_template(
                template,
                uploaded_path=image_url,
                popup=popup,
                dashboard_endpoint=dashboard_endpoint
            )
        else:
            return render_template(
                template,
                error='No file selected',
                popup=popup,
                dashboard_endpoint=dashboard_endpoint
            ), 400

    # GET request - show upload form
    return render_template(
        template,
        popup=popup,
        dashboard_endpoint=dashboard_endpoint
    )
