@echo off
SET PATH=C:\Compilers\Python36\Scripts\;C:\Compilers\Python36\;%PATH%
python -m venv venv
call .\venv\Scripts\activate.bat
pip install -r requirements.txt