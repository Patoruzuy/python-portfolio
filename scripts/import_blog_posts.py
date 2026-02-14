"""
Import blog posts from markdown files to database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import BlogPost
from datetime import datetime, timezone
import re
from slugify import slugify

def parse_frontmatter(content):
    """Extract frontmatter from markdown"""
    frontmatter = {}
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            lines = parts[1].strip().split('\n')
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip()
            content = parts[2].strip()
    return frontmatter, content

def import_blog_posts():
    """Import blog posts from markdown files"""
    print("📝 Importing blog posts from markdown files...")
    
    blog_posts_dir = 'blog_posts'
    
    if not os.path.exists(blog_posts_dir):
        print(f"❌ Directory {blog_posts_dir} not found")
        return
    
    with app.app_context():
        # Clear existing sample posts first
        print("🗑️  Clearing sample blog posts...")
        BlogPost.query.delete()
        db.session.commit()
        
        imported = 0
        for filename in sorted(os.listdir(blog_posts_dir)):
            if not filename.endswith('.md'):
                continue
            
            filepath = os.path.join(blog_posts_dir, filename)
            
            if os.path.isfile(filepath):
                print(f"  Reading {filename}...")
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse frontmatter
                frontmatter, markdown_content = parse_frontmatter(content)
                
                if not markdown_content.strip():
                    print(f"  ⚠️  Skipping empty file: {filename}")
                    continue
                
                # Extract title from frontmatter or first heading
                title = frontmatter.get('title', '')
                if not title:
                    # Try to find first heading
                    match = re.search(r'^#\s+(.+)$', markdown_content, re.MULTILINE)
                    if match:
                        title = match.group(1)
                    else:
                        title = filename.replace('.md', '').replace('-', ' ').title()
                
                # Generate slug
                slug = frontmatter.get('slug', slugify(title))
                
                # Extract excerpt
                excerpt = frontmatter.get('excerpt', '')
                if not excerpt:
                    # Get first paragraph after headings
                    lines = [l for l in markdown_content.split('\n') if l.strip() and not l.startswith('#')]
                    if lines:
                        excerpt = lines[0][:300]
                
                # Get other fields
                author = frontmatter.get('author', 'Sebastian Gomez')
                category = frontmatter.get('category', 'Tutorial')
                tags = frontmatter.get('tags', '')
                image_url = frontmatter.get('image', '/static/images/blog-placeholder.jpg')
                read_time = frontmatter.get('read_time', 0)
                
                # Parse read_time if it's a string like "12 min"
                if isinstance(read_time, str):
                    match = re.search(r'(\d+)', read_time)
                    read_time = int(match.group(1)) if match else 0
                
                # Parse date
                date_str = frontmatter.get('date', '')
                if date_str:
                    try:
                        created_at = datetime.strptime(date_str, '%Y-%m-%d')
                        created_at = created_at.replace(tzinfo=timezone.utc)
                    except:
                        created_at = datetime.now(timezone.utc)
                else:
                    created_at = datetime.now(timezone.utc)
                
                # Check if post already exists
                existing = BlogPost.query.filter_by(slug=slug).first()
                if existing:
                    print(f"  ⚠️  Post '{title}' already exists, skipping...")
                    continue
                
                # Create blog post
                post = BlogPost(
                    title=title,
                    slug=slug,
                    content=markdown_content,
                    excerpt=excerpt,
                    author=author,
                    category=category,
                    tags=tags,
                    image_url=image_url,
                    read_time=read_time,
                    published=True,
                    created_at=created_at,
                    updated_at=datetime.now(timezone.utc)
                )
                
                db.session.add(post)
                imported += 1
                print(f"  ✅ Imported: {title}")
        
        if imported > 0:
            db.session.commit()
            print(f"\n✅ Successfully imported {imported} blog posts!")
        else:
            print("\n⚠️  No new blog posts to import")

if __name__ == '__main__':
    import_blog_posts()
