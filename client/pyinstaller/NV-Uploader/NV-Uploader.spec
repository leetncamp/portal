# -*- mode: python -*-
a = Analysis(['../NV-Uploader.py'],
             pathex=['/Users/lee/Desktop/portal/client/pyinstaller/NV-Uploader'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='NV-Uploader',
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
               name='NV-Uploader')
app = BUNDLE(coll,
             name='NV-Uploader.app',
             icon=None)
