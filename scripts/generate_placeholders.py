import os

def create_svg_placeholder(filename, text, width=800, height=600, bg_color="#2d3748", text_color="#a0aec0"):
    svg_content = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <rect width="100%" height="100%" fill="{bg_color}"/>
    <text x="50%" y="50%" font-family="monospace" font-size="24" fill="{text_color}" text-anchor="middle" dominant-baseline="middle">
        {text}
    </text>
    <rect x="5%" y="5%" width="90%" height="90%" fill="none" stroke="{text_color}" stroke-width="2" stroke-dasharray="10,5"/>
</svg>'''
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print(f"Created {filename}")

def main():
    images_dir = os.path.join('static', 'images')
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    # Placeholders map: list of (filename, text)
    placeholders = [
        ('course-python.jpg', 'Python Course'), 
        ('flask-templates.jpg', 'Flask Templates'),
        ('rpi-kit.jpg', 'RPi Kit'),
        ('code-review.jpg', 'Code Review'),
        ('smart-home.jpg', 'Smart Home'),
        ('weather-station.jpg', 'Weather Station'),
        ('pi-cluster.jpg', 'Pi Cluster'),
        ('ml-pipeline.jpg', 'ML Pipeline'),
        ('django-api.jpg', 'Django API'),
        ('dashboard.jpg', 'Data Dashboard'),
        ('testing.jpg', 'Testing Framework'),
        ('about-me.png', 'Profile Image'),
        ('placeholder.jpg', 'Blog Placeholder')
    ]

    for filename, text in placeholders:
        # Note: We are saving as .svg even if filename ends in .jpg/png for browser compatibility if referenced directly
        # But wait, <img> tag expects the type declared in src extension? 
        # Actually browsers handle SVG content even with wrong extension often, OR we should rename references.
        # But user asked to replace placeholders. 
        # Safest way: Create .svg files and update the code references? 
        # OR: Just create files with the requested names but writing SVG content. 
        # Most modern browsers render SVG content regardless of extension if header is missing (intro local file),
        # but locally served it might rely on extension for MIME type.
        # Let's create proper .svg files and I'll update the references in app.py/json later if needed.
        # Wait, the user asked "generate images to remplace".
        # If I save SVG content into a .jpg file, it won't render in an <img> tag as image/jpeg.
        # So I will create .svg files and replacing the extensions in json/app.py is too much work right now.
        
        # ACTUALLY: I can use a simple trick. I can't generate binary JPG/PNG without PIL.
        # But I can generate ONE generic 'placeholder.svg' and update all references to it?
        # The user wants specific images for projects.
        
        # Let's create SVG files with the EXACT names but append .svg? No, that breaks links.
        # Let's create them as .svg and update app.py references? That's safe.
        # Or better: I will create `generate_placeholders.py` that needs `Pillow` and tell the user to run `pip install Pillow`.
        # That's the most robust solution for "generating images".
        pass

if __name__ == '__main__':
    # Checking for Pillow
    try:
        from PIL import Image, ImageDraw, ImageFont
        print("Pillow found. Generating images...")
        
        images_dir = os.path.join('static', 'images')
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
            
        placeholders = [
            ('course-python.jpg', 'Python Course', '#2c3e50'), 
            ('flask-templates.jpg', 'Flask Templates', '#e67e22'),
            ('rpi-kit.jpg', 'RPi Kit', '#c0392b'),
            ('code-review.jpg', 'Code Review', '#8e44ad'),
            ('smart-home.jpg', 'Smart Home', '#27ae60'),
            ('weather-station.jpg', 'Weather Station', '#2980b9'),
            ('pi-cluster.jpg', 'Pi Cluster', '#d35400'),
            ('ml-pipeline.jpg', 'ML Pipeline', '#16a085'),
            ('django-api.jpg', 'Django API', '#2c3e50'),
            ('dashboard.jpg', 'Data Dashboard', '#f39c12'),
            ('testing.jpg', 'Testing Framework', '#7f8c8d'),
            ('about-me.png', 'ME', '#34495e'),
            ('placeholder.jpg', 'Blog Post', '#95a5a6'),
            ('favicon.ico', '>_', '#0d1117', (64, 64))
        ]
        
        for item in placeholders:
            if len(item) == 3:
                filename, text, color = item
                size = (800, 600)
            else:
                filename, text, color, size = item

            filepath = os.path.join(images_dir, filename)
            
            # Skip if file already exists to avoid overwriting user's real images
            if os.path.exists(filepath):
                print(f"Skipping {filename} - file already exists")
                continue
                
            img = Image.new('RGB', size, color=color)
            d = ImageDraw.Draw(img)
            # Use default font or try to load one
            try:
                # Try simple monospace
                font = ImageFont.truetype("arial.ttf", 60)
            except:
                font = ImageFont.load_default()
                
            # Center text (approximate if default font)
            # For default font, we can't easily center large text, but let's try
            d.text((400, 300), text, fill="white", anchor="mm", font=font)
            
            filepath = os.path.join(images_dir, filename)
            img.save(filepath)
            print(f"Generated {filepath}")
            
    except ImportError:
        print("Pillow library not found.")
        print("Please run: pip install Pillow")
        print("Then run this script again: python scripts/generate_placeholders.py")