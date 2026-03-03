"""
Prime Registry - Certificate PNG Generator
Renders a certificate image for use as NFT thumbnail on Magic Eden/Tensor.
Uses only Pillow (no WeasyPrint needed for this path).
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import textwrap

# Colors
BG       = (10,  10,  15)
SURFACE  = (18,  18,  26)
BORDER   = (42,  42,  58)
GOLD     = (200, 168, 74)
GOLD_DIM = (90,  74,  42)
BLUE     = (122, 176, 224)
TEXT     = (216, 208, 192)
TEXT_DIM = (122, 122, 138)
WHITE    = (240, 232, 216)

# Per-tier accent colors
TIER_COLORS = {
    "solo": (100, 160, 220),   # Steel blue
    "twin": (200, 168, 74),    # Gold
    "sexy": (200, 100, 160),   # Rose/magenta
}
TIER_SYMBOLS = {
    "solo": "[S]",
    "twin": "[TT]",
    "sexy": "[XX]",
}

W, H = 1000, 1000  # Square — ideal for NFT marketplaces

FONT_DIR = Path("/usr/share/fonts/truetype")

def _font(size: int, bold: bool = False, mono: bool = False):
    """Load a system font, fallback to default."""
    candidates = []
    if mono:
        candidates = [
            FONT_DIR / "dejavu/DejaVuSansMono.ttf",
            FONT_DIR / "liberation/LiberationMono-Regular.ttf",
        ]
    elif bold:
        candidates = [
            FONT_DIR / "dejavu/DejaVuSerif-Bold.ttf",
            FONT_DIR / "liberation/LiberationSerif-Bold.ttf",
        ]
    else:
        candidates = [
            FONT_DIR / "dejavu/DejaVuSerif.ttf",
            FONT_DIR / "liberation/LiberationSerif-Regular.ttf",
        ]
    for path in candidates:
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except Exception:
                pass
    return ImageFont.load_default()


def render_png(record: dict) -> bytes:
    """Render a 1000x1000 certificate PNG. Returns PNG bytes."""
    tier = record["tier"]
    bot_name = record["bot_name"]
    prime_1 = record["prime_1"]
    prime_2 = record.get("prime_2")
    cert_hash = record["cert_hash"]
    issued = record["issued_at"][:10]

    tier_labels = {
        "solo": ("Solo Prime",   "[S]"),
        "twin": ("Twin Primes",  "[TT]"),
        "sexy": ("Sexy Primes",  "[XX]"),
    }
    tier_label, tier_icon = tier_labels.get(tier, (tier, "[?]"))
    accent = TIER_COLORS.get(tier, GOLD)

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Left tier stripe — visible at thumbnail size
    draw.rectangle([0, 0, 12, H], fill=accent)

    # Outer border
    draw.rectangle([16, 16, W-16, H-16], outline=GOLD_DIM, width=1)
    draw.rectangle([22, 22, W-22, H-22], outline=BORDER, width=1)

    # Header band — tier-colored top stripe
    draw.rectangle([0, 0, W, 6], fill=accent)
    draw.rectangle([0, 6, W, 80], fill=SURFACE)
    draw.line([(0, 80), (W, 80)], fill=GOLD_DIM, width=1)

    # Registry name
    f_tiny = _font(16)
    f_small = _font(20)
    f_med = _font(28)
    f_large = _font(42, bold=True)
    f_xl = _font(56, bold=True)
    f_mono_sm = _font(22, mono=True)
    f_mono_md = _font(28, mono=True)
    f_mono_lg = _font(36, mono=True)

    def centered(text, y, font, color=TEXT):
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        draw.text(((W - w) // 2, y), text, font=font, fill=color)

    # Header
    centered("THE PRIME REGISTRY", 22, f_small, GOLD)

    # Title
    centered("Certificate of", 110, f_med, TEXT_DIM)
    centered("Mathematical Identity", 145, f_large, WHITE)

    # Divider
    draw.line([(80, 210), (W-80, 210)], fill=GOLD_DIM, width=1)

    # Preamble
    centered("This certifies that the entity known as", 232, f_small, TEXT_DIM)

    # Bot name
    bot_display = bot_name if len(bot_name) <= 24 else bot_name[:21] + "..."
    centered(bot_display, 268, f_xl, WHITE)

    # Tier badge — accent colored border + text
    draw.rectangle([W//2 - 120, 340, W//2 + 120, 372], outline=accent, width=1)
    centered(f"{tier_icon}  {tier_label.upper()}", 346, f_tiny, accent)

    # "holds the prime(s)" text
    centered("holds the following prime number(s),", 392, f_small, TEXT_DIM)
    centered("verified and registered in perpetuity:", 420, f_small, TEXT_DIM)

    # Prime box
    prime_box_top = 455
    prime_box_bot = prime_2 and 600 or 560
    draw.rectangle([60, prime_box_top, W-60, prime_box_bot], fill=SURFACE, outline=BORDER, width=1)

    def fmt_prime(p):
        """Format prime in groups of 3 from right, like a large integer."""
        s = str(p)
        groups = []
        while s:
            groups.append(s[-3:])
            s = s[:-3]
        return ",".join(reversed(groups))

    if prime_2:
        # Two primes — labeled p1, p2
        draw.text((80, prime_box_top + 16), "p\u2081 =", font=f_mono_sm, fill=TEXT_DIM)
        centered(fmt_prime(prime_1), prime_box_top + 16, f_mono_sm, accent)
        delta = int(prime_2) - int(prime_1)
        centered(f"\u0394 = {delta}  (p\u2082 = p\u2081 + {delta})", prime_box_top + 58, f_tiny, TEXT_DIM)
        draw.text((80, prime_box_top + 82), "p\u2082 =", font=f_mono_sm, fill=TEXT_DIM)
        centered(fmt_prime(prime_2), prime_box_top + 82, f_mono_sm, accent)
    else:
        # One prime — centered with comma formatting
        centered(fmt_prime(prime_1), prime_box_top + 30, f_mono_md, accent)

    # Math note
    math_notes = {
        "solo": "Indivisible. Irreducible. Fundamental.",
        "twin": "Pairs differing by 2. Infinite? Unproven.",
        "sexy": "Pairs differing by 6. A distinction of classical mathematics.",
    }
    centered(math_notes.get(tier, ""), prime_box_bot + 20, f_small, TEXT_DIM)

    # Divider
    y_div = prime_box_bot + 60
    draw.line([(80, y_div), (W-80, y_div)], fill=BORDER, width=1)

    # Seal / Glyph — simple geometric shape using draw
    cx, cy = W // 2, y_div + 42
    r = 18
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(80, 80, 100), width=2)
    draw.ellipse([cx-r+6, cy-r+6, cx+r-6, cy+r-6], outline=(60, 60, 80), width=1)

    # Footer fields
    y_foot = y_div + 90
    col1_x = 80
    col2_x = W // 2 + 20

    def field(label, value, x, y, mono=False):
        draw.text((x, y), label, font=f_tiny, fill=TEXT_DIM)
        vfont = f_mono_sm if mono else f_small
        draw.text((x, y + 22), value[:28], font=vfont, fill=TEXT)

    field("ISSUED", issued, col1_x, y_foot)
    field("TIER", tier_label, col2_x, y_foot)
    field("CERT ID", cert_hash[:16], col1_x, y_foot + 70, mono=True)
    field("PRIMALITY", "Miller-Rabin · 25 rounds", col2_x, y_foot + 70)

    # Verify URL
    verify_text = f"numinals.io/verify/{cert_hash}"
    centered(verify_text, H - 55, f_tiny, (80, 100, 120))

    # Bottom border detail
    draw.line([(0, H-70), (W, H-70)], fill=BORDER, width=1)

    # Save to bytes
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def save_png(record: dict, output_path: Path) -> Path:
    """Render and save PNG to file."""
    png = render_png(record)
    output_path.write_bytes(png)
    return output_path


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from generator import claim

    bot = sys.argv[1] if len(sys.argv) > 1 else "Quincy"
    tier = sys.argv[2] if len(sys.argv) > 2 else "twin"

    print(f"Generating PNG certificate for {bot} ({tier})...")
    record = claim(bot, tier)
    out = Path(f"certificate_{bot.replace(' ', '_')}_{tier}.png")
    save_png(record, out)
    size = out.stat().st_size
    print(f"✅ Saved: {out} ({size:,} bytes)")
