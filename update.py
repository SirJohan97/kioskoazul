import os
import re

files = ['site/public/index.html', 'site/public/menu.html', 'site/public/reservas.html', 'site/public/galeria.html']

logo_url = 'https://storage.googleapis.com/aida-data-store-prod/21f00b953a992e59e13cf6c8d35ecab4d2eb7b8b42af91de2bc88bfd7fb8f507'
favicon_tag = f'<link rel="icon" href="{logo_url}" />'

replacements = [
    # General texts
    (r'El\s+Capit[aá]n\s+de\s+la\s+Playa', 'Restaurante Kiosco Azul'),
    (r'¡Buenos\s+Días,\s+Capitán!', '¡Buenos Días!'),
    (r'Pisco\s+Sour\s+del\s+Capitán', 'Pisco Sour Kiosco Azul'),
    
    # Colors
    (r'--gold:\s*#F5A623', '--gold: #C0392B; --navy: #1D3C5C'),
    (r'--gold-glow:\s*rgba\(245,\s*166,\s*35,\s*0\.4\)', '--gold-glow: rgba(192, 57, 43, 0.4)'),
    (r'--glass-border:\s*rgba\(245,\s*166,\s*35,\s*0\.25\)', '--glass-border: rgba(24, 106, 122, 0.3)'),
    (r'--glass-border:\s*rgba\(245,166,35,0\.22\)', '--glass-border: rgba(24, 106, 122, 0.3)'),
    (r'--glass-bg:\s*rgba\(10,\s*10,\s*20,\s*0\.35\)', '--glass-bg: rgba(24, 106, 122, 0.15)'),
    (r'--glass-bg:\s*rgba\(10,10,30,0\.45\)', '--glass-bg: rgba(24, 106, 122, 0.25)'),
    (r'--glass-bg:\s*rgba\(10,10,30,0\.5\)', '--glass-bg: rgba(24, 106, 122, 0.3)'),
    (r'245, 166, 35', '192, 57, 43'),
    (r'245,166,35', '192,57,43'),
    (r'#F5A623', '#C0392B'),
    
    # Specific elements
    (r'<i\s+class="fas\s+fa-anchor"></i>', f'<img src="{logo_url}" alt="Logo" style="height:45px;width:45px;border-radius:50%;object-fit:cover;">'),
]

for filepath in files:
    if not os.path.exists(filepath):
        continue
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Apply text replacements
    for pattern, repl in replacements:
        content = re.sub(pattern, repl, content, flags=re.IGNORECASE)

    # Insert favicon if not exists
    if 'rel="icon"' not in content:
        content = content.replace('</head>', f'  {favicon_tag}\n</head>')

    # Update nav-logo specifically for index.html
    content = re.sub(
        r'<a\s+href="#hero"\s+class="nav-logo">\s*<img[^>]+>\s*<div>\s*El\s+Capitán\s*<span>de\s+la\s+Playa</span>\s*</div>\s*</a>',
        f'<a href="#hero" class="nav-logo" style="display:flex;align-items:center;gap:10px;">\n        <img src="{logo_url}" alt="Logo Kiosco Azul" style="height: 45px; width: 45px; border-radius: 50%; object-fit: cover;">\n        <div>\n          Kiosco Azul\n          <span>Delicias del Mar</span>\n        </div>\n      </a>',
        content,
        flags=re.IGNORECASE
    )

    # Update nav-logo for other pages if they didn't have the anchor icon block
    content = re.sub(
        r'<a\s+href="index\.html"\s+class="nav-logo">El\s+Capitán\s*<span>de\s+la\s+Playa</span></a>',
        f'<a href="index.html" class="nav-logo" style="display:flex;align-items:center;gap:10px;"><img src="{logo_url}" alt="Logo" style="height:40px;width:40px;border-radius:50%;object-fit:cover;"><div>Kiosco Azul <span>Delicias del Mar</span></div></a>',
        content,
        flags=re.IGNORECASE
    )

    # Update title tagline in index hero
    content = re.sub(
        r'<h1\s+class="hero-title">\s*<em>El\s+Capitán</em><br\s*/>de\s+la\s+Playa\s*</h1>',
        r'<h1 class="hero-title">\n        <em>Kiosco</em><br />Azul\n      </h1>',
        content,
        flags=re.IGNORECASE
    )
    
    # Catch any remaining "El Capitán"
    content = re.sub(r'El\s+Capitán', 'Kiosco Azul', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print(f"Successfully updated 4 HTML files with new Kiosco Azul branding.")
