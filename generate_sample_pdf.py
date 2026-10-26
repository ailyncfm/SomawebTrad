#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from reportlab.pdfgen import canvas

# Para poder importar "app"
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app.pdf.pdf_factory import example_data, render_pdf  # noqa: E402


def main():
    doc_type = (sys.argv[1] if len(sys.argv) > 1 else "planning").strip().lower()
    out_dir = BASE_DIR / "storage" / "samples"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"sample_{doc_type}.pdf"
    c = canvas.Canvas(str(out_path))

    data = example_data(doc_type)
    render_pdf(doc_type, c, data, base_dir=str(BASE_DIR))
    c.save()

    print(f"OK -> {out_path}")


if __name__ == "__main__":
    main()

