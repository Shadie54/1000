# -*- mode: python ; coding: utf-8 -*-
#
# Build hry Tisíc (PyInstaller, onedir):
#   build.bat                       (alebo: pyinstaller Tisic.spec --noconfirm --clean)
# Výsledok: dist\Tisic\Tisic.exe + dist\Tisic\_internal\ (hra, assets, Python).
# Na rozdanie zbaliť celý priečinok dist\Tisic do zipu.
#
# Testy (tester\) a nástroje (tools\) sa do exe nedostanú — main.py ich
# neimportuje.


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'pydoc', 'numpy'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Tisic',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX býva príčinou falošných poplachov antivírusov
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/graphics/1000.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Tisic',
)
