import os
import sys
import urllib.request
import json
import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Add project root to sys.path to import core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../core")))

try:
    from functions.platonus import UNIVERSITIES
except ImportError:
    # Fallback in case import fails
    UNIVERSITIES = {
        "kstu": {"name": "Әбілқас Сағынов атындағы КарТУ", "website": "https://kstu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=kstu.kz"},
        "buketov": {"name": "Е.А. Бөкетов атындағы Қарағанды университеті", "website": "https://buketov.edu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=buketov.edu.kz"},
        "kiu": {"name": "Қарағанды индустриялық университеті", "website": "https://tttu.edu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=tttu.edu.kz"},
        "keu": {"name": "Қарағанды Қазтұтынуодағы университеті", "website": "https://keu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=keu.kz"},
        "enu": {"name": "Л.Н. Гумилев атындағы Еуразия ұлттық университеті", "website": "https://enu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=enu.kz"},
        "kazatu": {"name": "С. Сейфуллин атындағы ҚазАТЗУ", "website": "https://kazatu.edu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=kazatu.edu.kz"},
        "mnu": {"name": "Maqsut Narikbayev University", "website": "https://mnu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=mnu.kz"},
        "kaznaru": {"name": "Қазақ ұлттық аграрлық зерттеу университеті (KazNARU)", "website": "https://kaznaru.edu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=kaznaru.edu.kz"},
        "almau": {"name": "Almaty Management University (AlmaU)", "website": "https://almau.edu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=almau.edu.kz"},
        "narxoz": {"name": "Narxoz University", "website": "https://narxoz.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=narxoz.kz"},
        "alt": {"name": "ALT University", "website": "https://alt.edu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=alt.edu.kz"},
        "aues": {"name": "Алматы энергетика және байланыс университеті (AUES)", "website": "https://aues.edu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=aues.edu.kz"},
        "qyzpu": {"name": "Қазақ ұлттық қыздар педагогикалық университеті (QyzPU)", "website": "https://qyzpu.edu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=qyzpu.edu.kz"},
        "kafu": {"name": "Қазақстан-Американдық еркін университеті (KAFU)", "website": "https://kafu.edu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=kafu.edu.kz"},
        "krmu": {"name": "Қазақстан-Ресей медицина университеті (KRMU)", "website": "https://medkrmu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=medkrmu.kz"},
        "kaztbu": {"name": "Қазақ технология және бизнес университеті (KazUTB)", "website": "https://kaztbu.edu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=kaztbu.edu.kz"},
        "ayu": {"name": "Қ.А. Ясауи атындағы Халықаралық қазақ-түрік университеті (AYU)", "website": "https://ayu.edu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=ayu.edu.kz"},
        "skma": {"name": "Оңтүстік Қазақстан медицина академиясы (SKMA)", "website": "https://skma.edu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=skma.edu.kz"},
        "caiu": {"name": "Орталық Азия инновациялық университеті (CAIU)", "website": "https://caiu.edu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=caiu.edu.kz"},
        "tau": {"name": "Тұран-Астана университеті (TAU)", "website": "https://tau-edu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=tau-edu.kz"},
        "wku": {"name": "М. Өтемісов атындағы Батыс Қазақстан университеті (WKU)", "website": "https://wku.edu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=wku.edu.kz"},
        "kaznuvhi": {"name": "Қазақ ұлттық су шаруашылығы және ирригация университеті", "website": "https://kaznuvhi.edu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=kaznuvhi.edu.kz"},
        "knus": {"name": "Қазақ спорт және туризм академиясы", "website": "https://knus.edu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=knus.edu.kz"},
        "mtgu": {"name": "Халықаралық көлік-гуманитарлық университеті", "website": "https://mtgu.edu.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=mtgu.edu.kz"},
        "quniversity": {"name": "Q University", "website": "https://q-university.kz", "logo": "https://www.google.com/s2/favicons?sz=256&domain=q-university.kz"},
    }

# Ensure directories exist
SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))
LOGOS_DIR = os.path.join(SCRATCH_DIR, "logos")
os.makedirs(LOGOS_DIR, exist_ok=True)

# Colors for placeholder logos
PLACEHOLDER_COLORS = [
    (14, 165, 233),   # sky-500
    (59, 130, 246),   # blue-500
    (139, 92, 246),   # violet-500
    (236, 72, 153),   # pink-500
    (244, 63, 94),    # rose-500
    (234, 179, 8),    # yellow-500
    (34, 197, 94),    # green-500
    (20, 184, 166),   # teal-500
]

def get_logo_path(code, domain, logo_url):
    filename = f"{code}.png"
    filepath = os.path.join(LOGOS_DIR, filename)
    
    # If already downloaded, return path
    if os.path.exists(filepath):
        return filepath
        
    print(f"Downloading logo for {code} from {logo_url}...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # Try downloading with user agent
    try:
        req = urllib.request.Request(logo_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            with open(filepath, 'wb') as f:
                f.write(response.read())
        return filepath
    except Exception as e:
        print(f"Failed to download logo for {code}: {e}")
        # Let's try downloading from a fallback URL (e.g. buketov.edu.kz direct favicon)
        fallback_url = f"https://{domain}/favicon.ico"
        try:
            print(f"Trying fallback: {fallback_url}...")
            req = urllib.request.Request(fallback_url, headers=headers)
            with urllib.request.urlopen(req, timeout=3) as response:
                with open(filepath, 'wb') as f:
                    f.write(response.read())
            return filepath
        except Exception as e2:
            print(f"Fallback failed too: {e2}")
            
    return None

def create_placeholder_logo(code, name, index):
    # Generates a beautiful 256x256 image with letters
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Get color
    bg_color = PLACEHOLDER_COLORS[index % len(PLACEHOLDER_COLORS)]
    
    # Draw circle
    draw.ellipse([8, 8, 248, 248], fill=bg_color)
    
    # Get letters
    letters = ""
    words = name.split()
    if len(words) >= 2:
        letters = (words[0][0] + words[1][0]).upper()
    else:
        letters = code[:2].upper()
        
    # Draw text
    # Try to load a font, otherwise use default
    font = None
    for font_path in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"
    ]:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, 110)
                break
            except:
                pass
                
    # Center text
    if font:
        # Get text size
        bbox = draw.textbbox((0, 0), letters, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((256-w)/2 - bbox[0], (256-h)/2 - bbox[1] - 10), letters, fill=(255, 255, 255, 245), font=font)
    else:
        # Basic text drawing if no font found
        draw.text((80, 100), letters, fill=(255, 255, 255, 255))
        
    return img

def draw_glow(image, center, radius, color):
    # Draw a soft glowing blob in the background
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.ellipse([center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius], fill=color)
    blurred = overlay.filter(ImageFilter.GaussianBlur(radius * 0.6))
    return Image.alpha_composite(image, blurred)

def generate_collage():
    # 1. Output dimensions
    canvas_w = 1200
    canvas_h = 1200
    
    # 2. Create base canvas with dark gradient
    base = Image.new("RGBA", (canvas_w, canvas_h), (7, 7, 10, 255)) # Deep dark #07070a
    draw = ImageDraw.Draw(base)
    
    # Draw gradient
    for y in range(canvas_h):
        # Interpolate between #0d0d18 and #060609
        r = int(13 - (13 - 6) * (y / canvas_h))
        g = int(13 - (13 - 6) * (y / canvas_h))
        b = int(24 - (24 - 9) * (y / canvas_h))
        draw.line([(0, y), (canvas_w, y)], fill=(r, g, b, 255))
        
    # Draw subtle background grid lines
    grid_size = 80
    for x in range(0, canvas_w, grid_size):
        draw.line([(x, 0), (x, canvas_h)], fill=(255, 255, 255, 6))
    for y in range(0, canvas_h, grid_size):
        draw.line([(0, y), (canvas_w, y)], fill=(255, 255, 255, 6))
        
    # Add beautiful background glows (cyan and violet)
    base = draw_glow(base, (200, 200), 300, (14, 165, 233, 30))  # Sky blue glow top-left
    base = draw_glow(base, (1000, 1000), 400, (139, 92, 246, 25)) # Violet glow bottom-right
    base = draw_glow(base, (600, 600), 200, (236, 72, 153, 15))   # Pink glow center

    # 3. Create grid of university logo cards on a transparent grid layer
    # We want a 5x5 grid
    cols = 5
    rows = 5
    card_size = 150
    spacing = 50
    
    grid_w = cols * card_size + (cols - 1) * spacing
    grid_h = rows * card_size + (rows - 1) * spacing
    
    # Create a large transparent layer to hold the grid so it doesn't get clipped when rotated
    # Bounding box of rotated rect with size WxH at 45 degrees is (W+H)/sqrt(2) ~ 1.414 * size.
    # To be safe, we create a 2000x2000 canvas.
    grid_layer_size = 2200
    grid_layer = Image.new("RGBA", (grid_layer_size, grid_layer_size), (0, 0, 0, 0))
    grid_draw = ImageDraw.Draw(grid_layer)
    
    # Calculate start positions to center the grid on the grid_layer
    start_x = (grid_layer_size - grid_w) / 2
    start_y = (grid_layer_size - grid_h) / 2
    
    univ_items = list(UNIVERSITIES.items())
    
    for idx, (code, info) in enumerate(univ_items):
        if idx >= cols * rows:
            break
            
        r = idx // cols
        c = idx % cols
        
        # Position of card
        cx = start_x + c * (card_size + spacing)
        cy = start_y + r * (card_size + spacing)
        
        # Draw card background: dark semi-transparent card with subtle border
        # We draw a rounded rect
        card_r = 28 # Corner radius
        # Draw shadow first (very soft)
        shadow_offset = 6
        grid_draw.rounded_rectangle(
            [cx + 2, cy + shadow_offset, cx + card_size + 2, cy + card_size + shadow_offset],
            radius=card_r,
            fill=(0, 0, 0, 80)
        )
        # Draw main card
        grid_draw.rounded_rectangle(
            [cx, cy, cx + card_size, cy + card_size],
            radius=card_r,
            fill=(18, 18, 29, 210),      # Dark glassmorphism card
            outline=(255, 255, 255, 24), # Subtle white border
            width=2
        )
        
        # Get or generate logo
        logo_img = None
        domain = info.get("website", "").replace("https://", "").replace("http://", "").split("/")[0]
        logo_path = get_logo_path(code, domain, info.get("logo", ""))
        
        if logo_path and os.path.exists(logo_path):
            try:
                logo_img = Image.open(logo_path).convert("RGBA")
            except Exception as e:
                print(f"Could not load downloaded logo image: {e}")
                
        if logo_img is None:
            logo_img = create_placeholder_logo(code, info.get("name", code), idx)
            
        # Resize logo to fit inside the card (leaving padding)
        logo_padding = 34
        logo_target_size = card_size - 2 * logo_padding # e.g. 150 - 68 = 82px
        
        # Keep aspect ratio
        logo_w, logo_h = logo_img.size
        ratio = min(logo_target_size / logo_w, logo_target_size / logo_h)
        new_w = int(logo_w * ratio)
        new_h = int(logo_h * ratio)
        logo_img = logo_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Paste logo into card (centered)
        paste_x = int(cx + (card_size - new_w) / 2)
        paste_y = int(cy + (card_size - new_h) / 2)
        
        # If the logo has transparency, use it as mask
        grid_layer.paste(logo_img, (paste_x, paste_y), logo_img)

    # 4. Rotate the entire grid layer by 45 degrees
    rotated_grid = grid_layer.rotate(45, resample=Image.Resampling.BICUBIC, expand=False)
    
    # 5. Composite the rotated grid onto the base canvas, centered
    # The grid_layer was centered around (1100, 1100).
    # We want to paste its center (1100, 1100) onto the base canvas center (600, 600)
    paste_offset_x = 600 - 1100
    paste_offset_y = 600 - 1100
    
    base.paste(rotated_grid, (paste_offset_x, paste_offset_y), rotated_grid)
    
    # 6. Add "Univer" title in the center/foreground or as an overlay?
    # Let's add a premium glassmorphic title tag at the center-bottom or top
    title_box_w = 400
    title_box_h = 70
    title_x = (canvas_w - title_box_w) / 2
    title_y = canvas_h - 130
    
    # Soft shadow for title
    draw.rounded_rectangle(
        [title_x, title_y + 4, title_x + title_box_w, title_y + title_box_h + 4],
        radius=18,
        fill=(0, 0, 0, 120)
    )
    # Glassmorphic container
    draw.rounded_rectangle(
        [title_x, title_y, title_x + title_box_w, title_y + title_box_h],
        radius=18,
        fill=(10, 10, 16, 230),
        outline=(255, 255, 255, 30),
        width=2
    )
    
    # Draw logo/text in container
    font = None
    for font_path in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc"
    ]:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, 28)
                break
            except:
                pass
                
    text = "Univer • Студент көмекшісі"
    if font:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(
            (title_x + (title_box_w - tw)/2 - bbox[0], title_y + (title_box_h - th)/2 - bbox[1] - 2),
            text,
            fill=(255, 255, 255, 240),
            font=font
        )
    else:
        draw.text((title_x + 80, title_y + 25), text, fill=(255, 255, 255, 255))
        
    # Save the collage
    output_path = os.path.join(SCRATCH_DIR, "collage_output.png")
    # Convert RGBA to RGB for JPEG-like or save as PNG
    base.save(output_path, "PNG")
    print(f"Collage successfully generated and saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    generate_collage()
