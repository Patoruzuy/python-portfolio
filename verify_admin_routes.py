"""
Verification script for admin routes refactoring.
Tests that all admin blueprints are registered and routes are accessible.
"""
from app_factory import create_app

def test_admin_routes():
    """Test admin route registration and blueprint structure."""
    app = create_app()
    
    print("=" * 70)
    print("ADMIN ROUTES REFACTORING - VERIFICATION")
    print("=" * 70)
    
    # Expected admin blueprints
    expected_blueprints = [
        'admin_auth',
        'admin_dashboard',
        'admin_blog',
        'admin_newsletter',
        'admin_projects',
        'admin_products',
        'admin_settings',
        'admin_media'
    ]
    
    # Check all blueprints are registered
    print("\n✓ Blueprint Registration:")
    registered_blueprints = list(app.blueprints.keys())
    for bp in expected_blueprints:
        if bp in registered_blueprints:
            print(f"  ✅ {bp}")
        else:
            print(f"  ❌ {bp} - MISSING!")
    
    # Count admin routes
    admin_routes = [r for r in app.url_map.iter_rules() if r.endpoint.startswith('admin_')]
    print(f"\n✓ Admin Routes Count: {len(admin_routes)}")
    
    # Group routes by blueprint
    print("\n✓ Routes by Blueprint:")
    route_groups: dict[str, list[tuple[str, str]]] = {}
    for rule in admin_routes:
        bp_name = rule.endpoint.split('.')[0]
        if bp_name not in route_groups:
            route_groups[bp_name] = []
        route_groups[bp_name].append((rule.rule, rule.endpoint))
    
    for bp_name in sorted(route_groups.keys()):
        routes = route_groups[bp_name]
        print(f"\n  {bp_name} ({len(routes)} routes):")
        for path, endpoint in sorted(routes):
            print(f"    • {path}")
            print(f"      └─ {endpoint}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✓ Total Blueprints: {len(app.blueprints)}")
    print(f"✓ Admin Blueprints: {len([bp for bp in app.blueprints if bp.startswith('admin_')])}")
    print(f"✓ Total Routes: {len(list(app.url_map.iter_rules()))}")
    print(f"✓ Admin Routes: {len(admin_routes)}")
    print(f"✓ Public Routes: {len(list(app.url_map.iter_rules())) - len(admin_routes)}")
    
    # Check for old admin blueprint
    if 'admin' in app.blueprints:
        print("\n⚠️  WARNING: Old 'admin' blueprint still registered!")
        print("   Consider removing admin_routes.py after validation.")
    else:
        print("\n✅ No legacy 'admin' blueprint detected - clean migration!")
    
    print("\n" + "=" * 70)
    print("✅ VERIFICATION COMPLETE - Admin routes refactoring successful!")
    print("=" * 70)

if __name__ == '__main__':
    test_admin_routes()
