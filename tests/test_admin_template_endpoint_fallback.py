"""
Regression tests for template endpoint fallback between admin route layouts.
"""


def test_admin_dashboard_template_renders_in_monolith_layout(auth_client, database):
    response = auth_client.get('/admin/dashboard')
    assert response.status_code == 200
    assert b'Dashboard' in response.data


def test_admin_projects_template_renders_modular_links_in_monolith(auth_client, database):
    response = auth_client.get('/admin/projects')
    assert response.status_code == 200
    assert b'Back to Dashboard' in response.data


def test_owner_profile_template_resolves_upload_popup_endpoint(auth_client, database):
    response = auth_client.get('/admin/owner-profile')
    assert response.status_code == 200
    assert b'Upload' in response.data
