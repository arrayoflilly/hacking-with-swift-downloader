from pathlib import Path
# -------------------------
# Settings
# -------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BASE = "https://www.hackingwithswift.com"
START = "/quick-start/swiftui"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

IMG_PATH = PROJECT_ROOT / "assets" / "img" / "swiftui.png"
CSS_PATH = PROJECT_ROOT / "assets" / "css" / "styles.css"

FONT_ROBOTO = (PROJECT_ROOT / "assets" / "fonts" / "Roboto-VariableFont_wdth,wght.ttf").as_uri()
FONT_ROBOTO_ITALIC = (PROJECT_ROOT / "assets" / "fonts" / "Roboto-Italic-VariableFont_wdth,wght.ttf").as_uri()
FONT_SLAB = (PROJECT_ROOT / "assets" / "fonts" / "RobotoSlab-VariableFont_wght.ttf").as_uri()
FONT_MONTSERRAT = (PROJECT_ROOT / "assets" / "fonts" / "Montserrat-VariableFont_wght.ttf").as_uri()

AUTHOR = "Paul Hudson (Hacking with Swift)"
TITLE = "SwiftUI by Examples"
DATE_STR = "Updated for Xcode 16.4"

PDF_DIR = PROJECT_ROOT / "output"
PDF_PATH = PDF_DIR / "swiftui-by-examples.pdf"

CACHE_DIR = PROJECT_ROOT / "cache"
CACHE_PATH = CACHE_DIR / f"{START.strip('/').replace('/', '_')}.json"
CACHE_TTL = 60 * 60 * 24  
