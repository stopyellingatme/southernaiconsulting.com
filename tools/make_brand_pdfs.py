#!/usr/bin/env python3
"""Turn the outlined brand SVGs into true vector PDFs for print vendors.

    python3 tools/make_brand_pdfs.py

Uses headless Chrome's print-to-PDF. Two quirks are handled here:
  * An <img src="file://...svg"> often has not loaded when printing starts and
    you get a blank page, so the SVG markup is inlined instead.
  * Chrome writes the PDF and then hangs on exit in this environment, so each
    run is given a timeout and killed once the file exists.
"""

import os
import re
import subprocess

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BRAND = "brand"
TMP = "/tmp/sac_pdfwrap.html"

# Widest sensible print size per lockup; aspect is preserved from the viewBox.
TARGETS = [
    ("logo-horizontal-colour", 4.0),
    ("logo-horizontal-navy", 4.0),
    ("logo-horizontal-black", 4.0),
    ("logo-horizontal-white", 4.0),
    ("logo-stacked-colour", 2.5),
    ("logo-mark-colour", 1.5),
]


def build_wrapper(svg_path, width_in):
    svg = open(svg_path).read()
    m = re.search(r'viewBox="([-\d.]+) ([-\d.]+) ([\d.]+) ([\d.]+)"', svg)
    w, h = float(m.group(3)), float(m.group(4))
    height_in = width_in * h / w
    # drop the literal width/height so CSS controls the physical size
    svg = re.sub(r'\swidth="[\d.]+"\s+height="[\d.]+"', "", svg, count=1)
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><style>"
        f"@page {{ size: {width_in}in {height_in:.4f}in; margin: 0 }}"
        f"html,body{{margin:0;padding:0;width:{width_in}in;height:{height_in:.4f}in}}"
        f"svg{{display:block;width:{width_in}in;height:{height_in:.4f}in}}"
        f"</style></head><body>{svg}</body></html>"
    )
    open(TMP, "w").write(html)
    return width_in, height_in


def main():
    ok, failed = [], []
    for name, width_in in TARGETS:
        svg_path = f"{BRAND}/{name}.svg"
        if not os.path.exists(svg_path):
            failed.append(f"{name} (no source SVG)")
            continue
        w_in, h_in = build_wrapper(svg_path, width_in)
        out = f"{BRAND}/{name}.pdf"
        if os.path.exists(out):
            os.remove(out)
        cmd = [
            CHROME, "--headless", "--disable-gpu", "--no-sandbox",
            "--no-first-run", "--no-default-browser-check", "--disable-extensions",
            "--no-pdf-header-footer", "--virtual-time-budget=3000",
            "--user-data-dir=/tmp/sac_pdf_profile",
            f"--print-to-pdf={out}", f"file://{TMP}",
        ]
        try:
            subprocess.run(cmd, timeout=30, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            pass          # Chrome hangs after writing; the file is already there
        if os.path.exists(out) and os.path.getsize(out) > 2000:
            size = os.path.getsize(out)
            ok.append(f"{out}  {w_in}x{h_in:.2f}in  {size}b")
        else:
            failed.append(f"{name} (blank or missing output)")

    for line in ok:
        print("  ok  ", line)
    for line in failed:
        print("  FAIL", line)
    print(f"\n{len(ok)} PDFs written, {len(failed)} failed")


if __name__ == "__main__":
    main()
