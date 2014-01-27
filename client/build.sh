#!/bin/sh
rm -rf NVUploader.app
python macsetup.py py2app
mv dist/NVUploader.app .
rm -rf build dist
