from PIL import Image, ImageDraw, ImageFont

# Create placeholder image
img = Image.new('RGB', (800, 600), color=(13, 17, 23))
draw = ImageDraw.Draw(img)

# Try to use a font, fallback to default
try:
    font = ImageFont.truetype("arial.ttf", 60)
except:
    font = ImageFont.load_default()

# Draw text
draw.text((400, 300), 'PLACEHOLDER', fill=(88, 214, 141), anchor='mm', font=font)

# Save
img.save('static/images/placeholder.jpg')
print("✓ Created placeholder.jpg")