from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import json

db = SQLAlchemy()


class Project(db.Model):
    """Portfolio projects showcase"""
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    technologies = db.Column(db.String(200), nullable=False)  # Comma-separated
    category = db.Column(db.String(50), nullable=False, index=True)
    github_url = db.Column(db.String(200))
    demo_url = db.Column(db.String(200))
    image_url = db.Column(
        db.String(200),
        default='/static/images/placeholder.jpg')
    featured = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(
            timezone.utc))


class Product(db.Model):
    """Digital/physical products for sale"""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    price = db.Column(db.Float, nullable=False)
    # digital, physical, service
    type = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    features_json = db.Column(db.Text, default='[]')  # Array of strings
    technologies = db.Column(db.String(200))  # Comma-separated

    # Payment Configuration
    # stripe, paypal, external, none
    payment_type = db.Column(db.String(20), default='external')
    # External payment link (eBay, Etsy, Stripe checkout, etc.)
    payment_url = db.Column(db.String(300))
    # Legacy field, use payment_url instead
    purchase_link = db.Column(db.String(200))

    demo_link = db.Column(db.String(200))
    image_url = db.Column(
        db.String(200),
        default='/static/images/placeholder.jpg')
    available = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(
            timezone.utc))

    @property
    def features(self):
        try:
            return json.loads(self.features_json) if self.features_json else []
        except (json.JSONDecodeError, TypeError):
            return []


class RaspberryPiProject(db.Model):
    """Raspberry Pi specific projects"""
    __tablename__ = 'raspberry_pi_projects'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    # Array of hardware components
    hardware_json = db.Column(db.Text, default='[]')
    technologies = db.Column(db.String(200), nullable=False)  # Comma-separated
    features_json = db.Column(db.Text, default='[]')  # Array of features
    github_url = db.Column(db.String(200))
    image_url = db.Column(
        db.String(200),
        default='/static/images/placeholder.jpg')
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(
            timezone.utc))

    @property
    def hardware(self):
        try:
            return json.loads(self.hardware_json) if self.hardware_json else []
        except (json.JSONDecodeError, TypeError):
            return []

    @property
    def features(self):
        try:
            return json.loads(self.features_json) if self.features_json else []
        except (json.JSONDecodeError, TypeError):
            return []

    @property
    def technologies_list(self):
        """Return technologies as a list"""
        if self.technologies:
            return [tech.strip() for tech in self.technologies.split(',')]
        return []


class BlogPost(db.Model):
    """Blog posts with markdown content"""
    __tablename__ = 'blog_posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    excerpt = db.Column(db.String(500))
    author = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Markdown content
    category = db.Column(db.String(50), index=True)
    tags = db.Column(db.String(200))  # Comma-separated
    image_url = db.Column(
        db.String(200),
        default='/static/images/blog-placeholder.jpg')
    read_time = db.Column(db.Integer)  # Minutes
    published = db.Column(db.Boolean, default=False, index=True)
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(
            timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        onupdate=lambda: datetime.now(
            timezone.utc))

    @property
    def date(self):
        """Alias for created_at for template compatibility"""
        return self.created_at

    @property
    def tags_list(self):
        """Return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []

    @property
    def content_html(self):
        """Convert markdown content to HTML"""
        import markdown
        from markdown.extensions.codehilite import CodeHiliteExtension  # noqa: F401
        from markdown.extensions.fenced_code import FencedCodeExtension  # noqa: F401

        md = markdown.Markdown(extensions=[
            'extra',
            'codehilite',
            'fenced_code',
            'tables',
            'nl2br',
            'sane_lists'
        ])
        return md.convert(self.content)


class OwnerProfile(db.Model):
    """Portfolio owner's complete profile"""
    __tablename__ = 'owner_profile'

    id = db.Column(db.Integer, primary_key=True)

    # Personal Info
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200))  # e.g., "Python Software Developer"
    bio = db.Column(db.Text)  # Short bio/intro
    profile_image = db.Column(
        db.String(200),
        default='/static/images/profile.jpg')

    # Contact & Social
    email = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    github = db.Column(db.String(100))
    linkedin = db.Column(db.String(100))
    twitter = db.Column(db.String(100))
    location = db.Column(db.String(100))

    # About Page Content
    intro = db.Column(db.String(200))  # Headline
    summary = db.Column(db.Text)  # Professional summary paragraph
    journey = db.Column(db.Text)  # Journey paragraph
    interests = db.Column(db.Text)  # Interests paragraph

    # Statistics
    years_experience = db.Column(db.Integer, default=0)
    projects_completed = db.Column(db.Integer, default=0)
    contributions = db.Column(db.Integer, default=0)
    clients_served = db.Column(db.Integer, default=0)
    certifications = db.Column(db.Integer, default=0)

    # Structured Data (JSON)
    # Technical skills with percentages
    skills_json = db.Column(db.Text, default='[]')
    # Professional experience timeline
    experience_json = db.Column(db.Text, default='[]')
    # Technical expertise cards (for homepage)
    expertise_json = db.Column(db.Text, default='[]')

    @property
    def skills(self):
        try:
            return json.loads(self.skills_json) if self.skills_json else []
        except (json.JSONDecodeError, TypeError):
            return []

    @property
    def experience(self):
        try:
            return json.loads(
                self.experience_json) if self.experience_json else []
        except (json.JSONDecodeError, TypeError):
            return []

    @property
    def expertise(self):
        try:
            return json.loads(
                self.expertise_json) if self.expertise_json else []
        except (json.JSONDecodeError, TypeError):
            return []


class SiteConfig(db.Model):
    """Global site configuration"""
    __tablename__ = 'site_config'

    id = db.Column(db.Integer, primary_key=True)

    # Site Identity
    site_name = db.Column(db.String(100), default='Python Portfolio')
    tagline = db.Column(db.String(200))
    favicon_url = db.Column(
        db.String(200),
        default='/static/images/favicon.ico')

    # Email Configuration (password stored in .env only)
    mail_server = db.Column(db.String(100), default='smtp.gmail.com')
    mail_port = db.Column(db.Integer, default=587)
    mail_use_tls = db.Column(db.Boolean, default=True)
    mail_username = db.Column(db.String(100))
    mail_default_sender = db.Column(db.String(100))
    mail_recipient = db.Column(db.String(100))

    # Features
    blog_enabled = db.Column(db.Boolean, default=True)
    products_enabled = db.Column(db.Boolean, default=True)
    analytics_enabled = db.Column(db.Boolean, default=True)


class PageView(db.Model):
    """Analytics for page views and time tracking"""
    __tablename__ = 'page_views'

    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(200), nullable=False, index=True)
    title = db.Column(db.String(200))
    referrer = db.Column(db.String(200))
    user_agent = db.Column(db.String(300))
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    session_id = db.Column(db.String(100), index=True)
    time_spent = db.Column(db.Integer, default=0)  # Seconds
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(
            timezone.utc),
        index=True)


class Newsletter(db.Model):
    """Blog newsletter subscriptions"""
    __tablename__ = 'newsletter'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100))
    active = db.Column(db.Boolean, default=True, index=True)
    confirmed = db.Column(db.Boolean, default=False)
    confirmation_token = db.Column(db.String(100), unique=True)
    subscribed_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(
            timezone.utc))
    unsubscribed_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Newsletter {self.email}>'


class User(db.Model):
    """Admin users with authentication and password recovery"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False,
        index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    # Profile
    full_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_superuser = db.Column(db.Boolean, default=False)

    # Password Recovery
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiry = db.Column(db.DateTime)

    # Tracking
    last_login = db.Column(db.DateTime)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(
            timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        onupdate=lambda: datetime.now(
            timezone.utc))

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Hash and set password"""
        import bcrypt
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        """Verify password against hash"""
        import bcrypt
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8'))

    def generate_reset_token(self):
        """Generate password reset token"""
        import secrets
        from datetime import timedelta
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.now(
            timezone.utc) + timedelta(hours=24)
        return self.reset_token

    def verify_reset_token(self, token):
        """Check if reset token is valid and not expired"""
        if not self.reset_token or not self.reset_token_expiry:
            return False
        if self.reset_token != token:
            return False
        if datetime.now(timezone.utc) > self.reset_token_expiry:
            return False
        return True
