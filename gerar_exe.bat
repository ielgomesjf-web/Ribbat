@echo off
REM Gera o Ribbat.exe (fica na pasta "dist").
REM Precisa ter: pip install pygame pyinstaller
cd /d "%~dp0"
python -m PyInstaller --onefile --windowed --name Ribbat --icon "%~dp0ribbat.ico" ^
  --workpath build --specpath build --noconfirm ^
  ribbat.py
echo.
echo Pronto! O jogo esta em: %~dp0dist\Ribbat.exe
pause
