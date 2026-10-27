"""Verify generated local links and assets, without making network requests."""
from pathlib import Path
from urllib.parse import unquote, urlsplit
from bs4 import BeautifulSoup

project = Path(__file__).resolve().parents[1]
base = project / "site/_site"
failures = []
assert not (base / "dist").exists(), "Generated dist directory must not be copied into the site"
pages = sorted(base.rglob("*.html"))
assert len(pages) == 6, f"Expected six published pages, found {len(pages)}"
for path in pages:
    soup = BeautifulSoup(path.read_text(), "html.parser")
    for tag, attribute in [("a", "href"), ("img", "src"), ("script", "src"), ("link", "href")]:
        for node in soup.find_all(tag):
            value = node.get(attribute, "")
            parsed = urlsplit(value)
            if not value or parsed.scheme or parsed.netloc:
                continue
            if not parsed.path:
                target = path
            elif parsed.path.startswith("/"):
                target = base / unquote(parsed.path.lstrip("/"))
            else:
                target = path.parent / unquote(parsed.path)
            if target.is_dir(): target = target / "index.html"
            if not target.exists(): failures.append((str(path.relative_to(base)), value))
            elif parsed.fragment and target.suffix == ".html":
                target_soup = soup if target == path else BeautifulSoup(target.read_text(), "html.parser")
                # Quarto's copy buttons and navigation sometimes use a bare '#'.
                if not target_soup.find(id=unquote(parsed.fragment)):
                    failures.append((str(path.relative_to(base)), value))
    assert all(image.has_attr("alt") for image in soup.find_all("img")), f"Missing image alt text: {path}"
assert not failures, f"Broken local references: {failures}"
assert len(list((base / "site/assets/notebooks").glob("*.zip"))) == 4
print("Six published pages: local links, chart assets, script modules, downloads, anchors, and image alt text verified.")
