# PyInstaller spec for the portable Windows build.
# Build from the repository root: pyinstaller packaging/pdf-fusion.spec --noconfirm
# The result is a single file, dist/PDF-Fusion.exe.
import os

from PyInstaller.utils.hooks import collect_all

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))  # noqa: F821  SPECPATH is set by PyInstaller

datas = [
    (
        os.path.join(ROOT, "pdf_fusion", "i18n", "locales"),
        os.path.join("pdf_fusion", "i18n", "locales"),
    ),
]
binaries = []
hiddenimports = []
for package in ("customtkinter", "tkinterdnd2"):
    package_datas, package_binaries, package_imports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_imports

a = Analysis(  # noqa: F821  provided by PyInstaller
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
)
pyz = PYZ(a.pure)  # noqa: F821
exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="PDF-Fusion",
    console=False,
    upx=False,
)
