from app import app, db
from app.models import OwnerProfile, SiteConfig, Project

app.config['TESTING'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['PREFERRED_URL_SCHEME'] = 'http'

with app.app_context():
    db.create_all()
    
    # Create minimal test data
    owner = OwnerProfile(
        name='Test',
        title='Dev',
        email='test@test.com'
    )
    config = SiteConfig(
        site_name='Test'
    )
    project = Project(
        title='Test Project',
        description='Test',
        technologies='Python',
        category='web',
        featured=True
    )
    db.session.add_all([owner, config, project])
    db.session.commit()

client = app.test_client()
response = client.get('/')
print(f'Status: {response.status_code}')
print(f'Location: {response.location if response.status_code == 302 else "N/A"}')
print(f'Data preview: {response.data[:200]}')
