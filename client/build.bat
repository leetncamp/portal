del NVUploader.exe
copy NVUploader.py pyinstaller
cd pyinstaller
c:\Python27\python.exe pyinstaller.py --onefile --windowed NVUploader.py
move NVUploader\dist\NVUploader.exe ..