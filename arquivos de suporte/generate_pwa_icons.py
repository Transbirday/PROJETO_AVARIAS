from PIL import Image, ImageDraw

def create_icon(size, filename):
    # Colors
    bg_color = (13, 110, 253)  # Bootstrap Blue #0d6efd
    fg_color = (255, 255, 255)  # White
    
    # Create image
    img = Image.new('RGB', (size, size), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw a stylized "T" (Transbirday) or a box
    # Let's draw a simple stylized "box" with a checkmark
    padding = size // 5
    box_top_left = (padding, padding)
    box_bottom_right = (size - padding, size - padding)
    
    # Draw box outline
    draw.rectangle([box_top_left, box_bottom_right], outline=fg_color, width=size//20)
    
    # Draw checkmark inside
    check_coords = [
        (size * 0.35, size * 0.5),
        (size * 0.45, size * 0.65),
        (size * 0.7, size * 0.35)
    ]
    draw.line(check_coords, fill=fg_color, width=size//15, joint='curve')
    
    # Save
    img.save(filename)
    print(f"Generated: {filename} ({size}x{size})")

if __name__ == "__main__":
    import os
    os.makedirs('static/images', exist_ok=True)
    create_icon(160, 'static/images/pwa_icon.png')
    create_icon(512, 'static/images/pwa_icon_512.png')
