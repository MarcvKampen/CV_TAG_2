# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['cv_processing_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('logo_domein_wit_abrikoos_01_rgb.jpg', '.'),
        ('cv_processing_settings.json', '.') # Include generic settings if present
    ],
    hiddenimports=[
        'mistralai',
        'pandas',
        'PyQt6',
        'requests',
        'openpyxl',
        'xlsxwriter'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='RecruiteeTagger',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='app_icon.ico', # Uncomment if an .ico file is available
)
