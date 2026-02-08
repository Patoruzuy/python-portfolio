# Python Developer Portfolio Website

A professional portfolio website built with Flask, featuring a blog with markdown support, contact form with email functionality, project showcase, and e-commerce capabilities.

## Features

- 🎨 Modern, responsive design
- 📝 Blog system with markdown support
- 📧 Contact form with email notifications
- 🚀 Project showcase with filtering
- 🔌 Raspberry Pi/IoT projects section
- 🛒 E-commerce product listings
- 📱 Mobile-friendly interface

## Tech Stack

- **Backend**: Flask (Python)
- **Email**: Flask-Mail
- **Markdown**: Python-Markdown with syntax highlighting
- **Frontend**: HTML5, CSS3, JavaScript
- **Styling**: Custom CSS with CSS Variables

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A Gmail account (or other SMTP server) for email functionality

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd python-portfolio
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your configuration:
   ```env
   SECRET_KEY=your-secret-key-here
   FLASK_ENV=development
   
   # Email Configuration (Gmail example)
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   MAIL_RECIPIENT=your-email@gmail.com
   
   # Blog Configuration
   BLOG_POSTS_DIR=blog_posts
   ```

5. **Set up Gmail App Password** (if using Gmail)
   
   - Go to your Google Account settings
   - Navigate to Security → 2-Step Verification
   - Scroll down to "App passwords"
   - Generate a new app password for "Mail"
   - Use this password in your `.env` file

6. **Run the application**
   ```bash
   python app.py
   ```
   
   The application will be available at `http://localhost:5000`

## Project Structure

```
python-portfolio/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── README.md                  # This file
├── blog_posts/                # Markdown blog posts
│   ├── 1-building-scalable-python-applications.md
│   ├── 2-getting-started-raspberry-pi-python.md
│   └── 3-async-python-asyncio-concurrency.md
├── static/                    # Static assets
│   ├── css/
│   │   ├── style.css         # Main stylesheet
│   │   └── markdown.css      # Markdown content styling
│   └── js/
│       └── main.js           # JavaScript functionality
└── templates/                 # HTML templates
    ├── base.html             # Base template
    ├── index.html            # Homepage
    ├── about.html            # About page
    ├── projects.html         # Projects listing
    ├── project_detail.html   # Individual project
    ├── raspberry_pi.html     # Raspberry Pi projects
    ├── blog.html             # Blog listing
    ├── blog_post.html        # Individual blog post
    ├── contact.html          # Contact form
    └── products.html         # Products/services
```

## Creating Blog Posts

Blog posts are written in Markdown with YAML frontmatter. Create a new file in the `blog_posts/` directory:

```markdown
---
title: Your Blog Post Title
author: Your Name
date: 2026-01-15
category: Python Development
tags: Python, Flask, Tutorial
read_time: 10 min
image: /static/images/your-image.jpg
excerpt: A brief description of your blog post that appears in listings.
---

# Your Blog Post Title

Your markdown content goes here...

## Section 1

Content with **bold**, *italic*, and `code` formatting.

\`\`\`python
def hello_world():
    print("Hello, World!")
\`\`\`

## Section 2

More content...
```

### Frontmatter Fields

- `title`: Post title (required)
- `author`: Author name (required)
- `date`: Publication date in YYYY-MM-DD format (required)
- `category`: Post category (required)
- `tags`: Comma-separated list of tags (required)
- `read_time`: Estimated reading time (required)
- `image`: Featured image path (required)
- `excerpt`: Short description for listings (required)

### Markdown Features

The blog supports:
- Headers (H1-H6)
- Bold and italic text
- Code blocks with syntax highlighting
- Inline code
- Lists (ordered and unordered)
- Links
- Images
- Tables
- Blockquotes
- Horizontal rules

## Contact Form

The contact form sends emails using Flask-Mail. Make sure to configure your email settings in the `.env` file.

### Testing Email Functionality

1. Fill out the contact form on `/contact`
2. Check your configured recipient email
3. If emails aren't sending, check:
   - SMTP credentials are correct
   - App password is used (for Gmail)
   - Firewall isn't blocking SMTP ports
   - Check Flask console for error messages

## Customization

### Updating Personal Information

Edit the following files to customize with your information:

- `app.py`: Update project data, Raspberry Pi projects, and products
- `templates/about.html`: Update your bio and skills
- `templates/contact.html`: Update contact information
- `static/css/style.css`: Customize colors and styling

### Adding Projects

Add new projects to the `PROJECTS` list in `app.py`:

```python
{
    'id': 5,
    'title': 'Your Project Name',
    'description': 'Project description',
    'technologies': ['Python', 'Flask', 'PostgreSQL'],
    'category': 'Web Development',
    'github': 'https://github.com/username/project',
    'demo': 'https://demo.example.com',
    'image': '/static/images/project.jpg',
    'featured': True
}
```

## Deployment

### Production Considerations

1. **Change the SECRET_KEY**: Generate a secure random key
   ```python
   import secrets
   secrets.token_hex(32)
   ```

2. **Set FLASK_ENV to production**:
   ```env
   FLASK_ENV=production
   ```

3. **Use a production WSGI server** (e.g., Gunicorn):
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```

4. **Set up a reverse proxy** (e.g., Nginx)

5. **Use environment variables** for sensitive data

6. **Enable HTTPS** with SSL certificates

### Deployment Platforms

This application can be deployed to:
- Heroku
- DigitalOcean
- AWS (EC2, Elastic Beanstalk)
- Google Cloud Platform
- PythonAnywhere
- Render

## API Endpoints

### Contact Form
- **POST** `/api/contact`
  - Sends contact form email
  - Body: `{ name, email, subject, message, projectType }`

### Projects
- **GET** `/api/projects?category=<category>&technology=<tech>`
  - Returns filtered projects

### Blog
- **GET** `/api/blog?category=<category>&tag=<tag>`
  - Returns filtered blog posts

## Contributing

Feel free to fork this project and customize it for your own portfolio!

## License

This project is open source and available under the MIT License.

## Support

For questions or issues, please open an issue on GitHub or contact through the website's contact form.

## Acknowledgments

- Flask framework and community
- Python-Markdown for markdown processing
- Font Awesome for icons
- All open-source contributors

---

Built with ❤️ using Python and Flask
