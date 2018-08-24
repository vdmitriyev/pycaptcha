@echo off
SET PATH=C:\Compilers\Python36\Scripts\;C:\Compilers\Python36\;%PATH%
call .\venv\Scripts\activate.bat
python pycaptcha_api.py -m SERVER