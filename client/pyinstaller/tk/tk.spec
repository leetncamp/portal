# -*- mode: python -*-
a = Analysis(['../../Desktop/tk.py'],
             pathex=['/Users/lee/Downloads/pyinstaller/tk'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='tk',
          debug=False,
          strip=None,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='tk')
app = BUNDLE(coll,
             name='tk.app',
             icon=None)
