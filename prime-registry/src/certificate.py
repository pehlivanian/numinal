"""
Prime Registry - Certificate Generator
Renders HTML certificate template to PDF using Jinja2 + WeasyPrint.
"""

from pathlib import Path
from datetime import datetime

TEMPLATE_PATH = Path(__file__).parent / "certificate.html"


def render_certificate(record: dict) -> bytes:
    """
    Render a certificate PDF from a registration record.
    Returns raw PDF bytes.

    Requires: pip install jinja2 weasyprint
    """
    try:
        from jinja2 import Template
        from weasyprint import HTML
    except ImportError:
        raise ImportError("Install with: pip install jinja2 weasyprint")

    template_src = TEMPLATE_PATH.read_text()
    template = Template(template_src)

    # Format the issued_at nicely
    issued_at = record["issued_at"]
    try:
        dt = datetime.fromisoformat(issued_at)
        issued_at_display = dt.strftime("%B %d, %Y at %H:%M UTC")
    except Exception:
        issued_at_display = issued_at

    html_content = template.render(
        bot_name=record["bot_name"],
        tier=record["tier"],
        prime_1=record["prime_1"],
        prime_2=record.get("prime_2"),
        cert_id=record["id"],
        issued_at=issued_at_display,
        cert_hash=record["cert_hash"],
        verify_url=record["verify_url"],
    )

    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes


def save_certificate(record: dict, output_path: Path) -> Path:
    """Render certificate and save to file."""
    pdf = render_certificate(record)
    output_path.write_bytes(pdf)
    return output_path


# ─── CLI test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from generator import claim

    bot = sys.argv[1] if len(sys.argv) > 1 else "Quincy-Prime-1"
    tier = sys.argv[2] if len(sys.argv) > 2 else "twin"

    print(f"Generating {tier} certificate for {bot}...")
    record = claim(bot, tier)

    out = Path(f"certificate_{bot.replace(' ', '_')}.pdf")
    save_certificate(record, out)
    print(f"✅ Certificate saved to: {out}")
    print(f"   Verify at: {record['verify_url']}")
