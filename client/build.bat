# run this in the git bash shell
rm -rf NVUploader
cd pyinstaller
rm -rf build dist NVUploader
python pyinstaller.py --windowed "..\NVUploader.py"
move NVUploader\dist\NVUploader ..