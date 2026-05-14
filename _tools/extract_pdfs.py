"""Extract text from base papers to .txt files for analysis."""
import os, sys
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(r"D:\framework")
OUT = ROOT / "_extracted"
OUT.mkdir(exist_ok=True)

pdfs = sorted([p for p in ROOT.iterdir() if p.suffix.lower() == ".pdf"])
for p in pdfs:
    try:
        r = PdfReader(str(p))
        pages = []
        for i, page in enumerate(r.pages):
            try:
                pages.append(f"\n\n===== PAGE {i+1} =====\n" + (page.extract_text() or ""))
            except Exception as e:
                pages.append(f"\n\n===== PAGE {i+1} (ERROR: {e}) =====\n")
        text = "".join(pages)
        out_path = OUT / (p.stem + ".txt")
        out_path.write_text(text, encoding="utf-8", errors="replace")
        print(f"OK  {p.name}  ->  {out_path.name}  ({len(text):,} chars, {len(r.pages)} pages)")
    except Exception as e:
        print(f"ERR {p.name}: {e}")
