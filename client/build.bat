#!/bin/sh
rm -rf NV-Uploader.app
cd pyinstaller
python pyinstaller.py --noconfirm --upx-dir=/usr/local/bin --windowed ../NV-Uploader.py; mv NV-Uploader/dist/NV-Uploader.app ~/Desktop
