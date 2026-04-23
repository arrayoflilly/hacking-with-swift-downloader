from pathlib import Path

# -------------------------
# Settings
# -------------------------

BASE = "https://www.hackingwithswift.com"
START = "/quick-start/swiftdata"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

IMG_PATH = Path(__file__).parent / "img" / "cover 3.png"

FONT_ROBOTO = Path("font/Roboto-VariableFont_wdth,wght.ttf").absolute().as_uri()
FONT_ROBOTO_ITALIC = Path("font/Roboto-Italic-VariableFont_wdth,wght.ttf").absolute().as_uri()
FONT_SLAB = Path("font/RobotoSlab-VariableFont_wght.ttf").absolute().as_uri()
FONT_MONTSERRAT = Path("font/Montserrat-VariableFont_wght.ttf").absolute().as_uri()

AUTHOR = "Paul Hudson (Hacking with Swift)"
TITLE = "SwiftData by Example"
DATE_STR = "Updated for Xcode 16.4"

PDF_DIR = Path(__file__).parent / "output"
PDF_PATH = PDF_DIR / "swiftdata-by-example.pdf"

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_PATH = CACHE_DIR / f"{START.strip('/').replace('/', '_')}.json"
CACHE_TTL = 60 * 60 * 24  