#!/usr/bin/env python3
from __future__ import annotations

import os
import argparse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from app.pdf.pdf_factory import render_pdf, example_data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", default="planning", help="planning | scheduling | post")
    ap.add_argument("--out", default="storage/pdf/TEST.pdf", help="ruta salida")
    args = ap.parse_args()

    base_dir = os.path.abspath(os.path.dirname(__file__))
    out_path = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    data = example_data(args.type)

    c = canvas.Canvas(out_path, pagesize=A4)
    render_pdf(args.type, c, data, base_dir=base_dir)
    c.save()

    print("OK PDF generado:", out_path)


if __name__ == "__main__":
    main()

