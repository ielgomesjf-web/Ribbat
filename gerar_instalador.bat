@echo off
REM Gera o "Instalar Ribbat.exe" (fica na pasta "dist"). Rode o gerar_exe.bat ANTES.
REM Precisa ter: pip install pyinstaller
cd /d "%~dp0"
if not exist dist\Ribbat.exe (
  echo Falta o dist\Ribbat.exe: rode o gerar_exe.bat primeiro.
  pause
  exit /b 1
)
python -m PyInstaller --onefile --windowed --name "Instalar Ribbat" --icon "%~dp0ribbat.ico" ^
  --add-data "%~dp0dist\Ribbat.exe;." --add-data "%~dp0ribbat.ico;." --add-data "%~dp0icone.png;." ^
  --workpath build --specpath build --noconfirm ^
  instalador.py
echo.
echo Pronto! O instalador esta em: %~dp0dist\Instalar Ribbat.exe
pause
