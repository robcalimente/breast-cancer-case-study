"""Copy verified Quarto output to the static host's supported dist directory."""
from pathlib import Path
import shutil
import subprocess
import sys

project = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(project / "scripts/check_site.py")], cwd=project, check=True)
destination = project / "dist"
if destination.exists():
    if destination.is_symlink():
        raise RuntimeError("Refuse to replace a symlink at dist.")
    shutil.rmtree(destination)
shutil.copytree(project / "site/_site", destination)
print("Verified Quarto output staged in dist/ for static hosting.")
