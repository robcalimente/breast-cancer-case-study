"""Execute every chapter in a fresh kernel; reject errors and retain inspectable outputs."""
import os
from pathlib import Path
import shutil
import zipfile
import nbformat
from nbclient import NotebookClient

project = Path(__file__).resolve().parents[1]
os.environ["JUPYTER_PATH"] = str(project / ".venv/share/jupyter")
os.environ["MPLCONFIGDIR"] = str(project / ".venv/matplotlib")
os.environ["PATH"] = str(project / ".venv/bin") + os.pathsep + os.environ.get("PATH", "")
for path in sorted((project / "notebooks").glob("*.ipynb")):
    notebook = nbformat.read(path, as_version=4)
    for cell in notebook.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
    NotebookClient(notebook, timeout=180, kernel_name="python3", resources={"metadata": {"path": str(project)}}).execute()
    nbformat.write(notebook, path)
    downloads = project / "site/assets/notebooks"
    downloads.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(downloads / (path.stem + ".zip"), "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(path, arcname=path.name)
    print(f"Executed {path.name} in a fresh kernel", flush=True)
