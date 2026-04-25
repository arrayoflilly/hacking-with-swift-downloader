from pathlib import Path
# -------------------------
# Settings
# -------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BASE = "https://www.hackingwithswift.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

PDF_DIR = PROJECT_ROOT / "output"

BOOKS = [
    {
        "id": 0,
        "title": "Hacking with iOS: SwiftUI Edition",
        "author": "Paul Hudson and the Hacking with Swift team",
        "url": "/quick-start/ios-swiftui",
        "cover": PROJECT_ROOT / "assets" / "img" / "ios.png",
        "date_str": "Updated for Xcode 16.4",
        "pdf_name": "hacking-with-ios-swiftui.pdf",
    },
    {
        "id": 1,
        "title": "Swift for Complete Beginners",
        "author": "Paul Hudson and the Hacking with Swift team",
        "url": "/quick-start/beginners",
        "cover": PROJECT_ROOT / "assets" / "img" / "beginners.png",
        "date_str": "Updated for Xcode 16.4",
        "pdf_name": "swift-for-complete-beginners.pdf",
    },
    {
        "id": 2,
        "title": "Swift in Sixty Seconds",
        "author": "Paul Hudson and the Hacking with Swift team",
        "url": "/sixty",
        "cover": PROJECT_ROOT / "assets" / "img" / "sixty.png",
        "date_str": "Updated for Xcode 16.4",
        "pdf_name": "swift-in-sixty-seconds.pdf",
    },
    {
        "id": 3,
        "title": "Understanding Swift",
        "author": "Paul Hudson and the Hacking with Swift team",
        "url": "/quick-start/understanding-swift",
        "cover": PROJECT_ROOT / "assets" / "img" / "swift.png",
        "date_str": "Updated for Xcode 16.4",
        "pdf_name": "understanding-swift.pdf",
    },
    {
        "id": 4,
        "title": "SwiftUI by Example",
        "author": "Paul Hudson and the Hacking with Swift team",
        "url": "/quick-start/swiftui",
        "cover": PROJECT_ROOT / "assets" / "img" / "swiftui.png",
        "date_str": "Updated for Xcode 16.4",
        "pdf_name": "swiftui-by-example.pdf",
    },
    {
        "id": 5,
        "title": "SwiftData by Example",
        "author": "Paul Hudson and the Hacking with Swift team",
        "url": "/quick-start/swiftdata",
        "cover": PROJECT_ROOT / "assets" / "img" / "swiftdata.png",
        "date_str": "Updated for Xcode 16.4",
        "pdf_name": "swiftdata-by-example.pdf",
    },
    {
        "id": 6,
        "title": "Swift Concurrency by Example",
        "author": "Paul Hudson and the Hacking with Swift team",
        "url": "/quick-start/concurrency",
        "cover": PROJECT_ROOT / "assets" / "img" / "concurrency.png",
        "date_str": "Updated for Xcode 16.4",
        "pdf_name": "swift-concurrency-by-example.pdf",
    },
    {
        "id": 7,
        "title": "100 Days of Swift",
        "author": "Paul Hudson and the Hacking with Swift team",
        "url": "/100",
        "cover": PROJECT_ROOT / "assets" / "img" / "swift.png",
        "date_str": "Updated for Xcode 16.4",
        "pdf_name": "100-days-of-swift.pdf",
    },
    {
        "id": 8,
        "title": "100 Days of SwiftUI",
        "author": "Paul Hudson and the Hacking with Swift team",
        "url": "/100/swiftui",
        "cover": PROJECT_ROOT / "assets" / "img" / "3d.png",
        "date_str": "Updated for Xcode 16.4",
        "pdf_name": "100-days-of-swiftui.pdf",
    },
]

BOOK_ID = 0
TITLE = BOOKS[BOOK_ID]["title"]
AUTHOR = BOOKS[BOOK_ID]["author"]
START = BOOKS[BOOK_ID]["url"]
IMG_PATH = BOOKS[BOOK_ID]["cover"]
DATE_STR = BOOKS[BOOK_ID]["date_str"]
PDF_PATH = PDF_DIR / BOOKS[BOOK_ID]["pdf_name"]

CSS_PATH = PROJECT_ROOT / "assets" / "css" / "styles.css"

FONT_ROBOTO = (PROJECT_ROOT / "assets" / "fonts" / "Roboto-VariableFont_wdth,wght.ttf").as_uri()
FONT_ROBOTO_ITALIC = (PROJECT_ROOT / "assets" / "fonts" / "Roboto-Italic-VariableFont_wdth,wght.ttf").as_uri()
FONT_SLAB = (PROJECT_ROOT / "assets" / "fonts" / "RobotoSlab-VariableFont_wght.ttf").as_uri()
FONT_MONTSERRAT = (PROJECT_ROOT / "assets" / "fonts" / "Montserrat-VariableFont_wght.ttf").as_uri()

CACHE_DIR = PROJECT_ROOT / "cache"
CACHE_PATH = CACHE_DIR / f"{START.strip('/').replace('/', '_')}.json"
CACHE_TTL = 60 * 60 * 24  

