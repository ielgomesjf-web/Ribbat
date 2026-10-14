"""
Instalador do Ribbat (igual jogo de verdade): copia o jogo pra pasta de programas do usuário,
cria atalho no menu Iniciar (e na Área de Trabalho, se quiser) e aparece em "Aplicativos instalados"
do Windows pra desinstalar. Não precisa de administrador.

Rodando com --desinstalar (é o que o Windows chama), ele tira tudo de volta.
O progresso do jogador (save) fica guardado em %APPDATA%\\Ribbat e NÃO é apagado.

Pra gerar: gerar_instalador.bat (precisa do dist\\Ribbat.exe pronto antes).
"""
import os
import shutil
import subprocess
import sys
import tkinter as tk
import winreg
from tkinter import messagebox

NOME = "Ribbat e o Pergaminho Perdido"
VERSAO = "1.0"
PASTA = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Programs", "Ribbat")
JOGO = os.path.join(PASTA, "Ribbat.exe")
DESINSTALADOR = os.path.join(PASTA, "Desinstalar Ribbat.exe")
CHAVE = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Ribbat"
SEM_JANELA = 0x08000000                  # CREATE_NO_WINDOW (o PowerShell roda escondido)
VERDE, VERDE_ESC, CREME = "#4f8f4a", "#2e5e32", "#f6f0dc"


def recurso(nome):
    """Arquivo que vem dentro do instalador (o Ribbat.exe e o ícone)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, nome)


def pasta_especial(nome):
    """Desktop / menu Iniciar de verdade (funciona mesmo se o Windows mudou de lugar, tipo OneDrive)."""
    saida = subprocess.run(["powershell", "-NoProfile", "-Command", f"[Environment]::GetFolderPath('{nome}')"],
                           capture_output=True, text=True, creationflags=SEM_JANELA)
    return saida.stdout.strip()


def atalhos():
    """(menu Iniciar, Área de Trabalho). Se o Windows não disser onde fica, aquele vira None."""
    return tuple(os.path.join(p, "Ribbat.lnk") if p else None
                 for p in (pasta_especial("Programs"), pasta_especial("Desktop")))


def criar_atalho(lnk, alvo):
    script = (f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}'); "
              f"$s.TargetPath = '{alvo}'; $s.WorkingDirectory = '{os.path.dirname(alvo)}'; "
              f"$s.IconLocation = '{alvo},0'; $s.Description = '{NOME}'; $s.Save()")
    subprocess.run(["powershell", "-NoProfile", "-Command", script], creationflags=SEM_JANELA, check=True)


def registrar():
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, CHAVE) as k:
        winreg.SetValueEx(k, "DisplayName", 0, winreg.REG_SZ, NOME)
        winreg.SetValueEx(k, "DisplayVersion", 0, winreg.REG_SZ, VERSAO)
        winreg.SetValueEx(k, "Publisher", 0, winreg.REG_SZ, "Gomes")
        winreg.SetValueEx(k, "DisplayIcon", 0, winreg.REG_SZ, JOGO)
        winreg.SetValueEx(k, "InstallLocation", 0, winreg.REG_SZ, PASTA)
        winreg.SetValueEx(k, "UninstallString", 0, winreg.REG_SZ, f'"{DESINSTALADOR}" --desinstalar')
        winreg.SetValueEx(k, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(k, "NoRepair", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(k, "EstimatedSize", 0, winreg.REG_DWORD, os.path.getsize(JOGO) // 1024)


def instalar(area_de_trabalho):
    os.makedirs(PASTA, exist_ok=True)
    try:
        shutil.copy2(recurso("Ribbat.exe"), JOGO)
    except PermissionError:
        raise RuntimeError("O Ribbat está aberto. Feche o jogo e tente de novo.")
    if getattr(sys, "frozen", False):
        shutil.copy2(sys.executable, DESINSTALADOR)     # o próprio instalador vira o desinstalador
    menu, desktop = atalhos()
    if menu:
        criar_atalho(menu, JOGO)
    if area_de_trabalho and desktop:
        criar_atalho(desktop, JOGO)
    registrar()


def desinstalar():
    for lnk in atalhos():
        if lnk and os.path.exists(lnk):
            os.remove(lnk)
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, CHAVE)
    except OSError:
        pass
    if os.path.exists(JOGO):
        os.remove(JOGO)
    # o desinstalador não consegue apagar a si mesmo enquanto está aberto: apaga a pasta depois que fechar
    subprocess.Popen(f'cmd /c ping 127.0.0.1 -n 3 > nul & rmdir /s /q "{PASTA}"', creationflags=SEM_JANELA, shell=True)


# ---------------------------------------------------------------- a janelinha
class Janela:
    def __init__(self, modo):
        self.raiz = tk.Tk()
        self.raiz.title("Desinstalar Ribbat" if modo == "desinstalar" else "Instalar Ribbat")
        self.raiz.configure(bg=CREME)
        self.raiz.resizable(False, False)
        try:
            self.raiz.iconbitmap(recurso("ribbat.ico"))
        except tk.TclError:
            pass
        largura, altura = 460, 330
        x = (self.raiz.winfo_screenwidth() - largura) // 2
        y = (self.raiz.winfo_screenheight() - altura) // 2
        self.raiz.geometry(f"{largura}x{altura}+{x}+{y}")
        try:
            self.foto = tk.PhotoImage(file=recurso("icone.png")).subsample(2, 2)
            tk.Label(self.raiz, image=self.foto, bg=CREME).pack(pady=(18, 4))
        except tk.TclError:
            pass
        tk.Label(self.raiz, text="RIBBAT", font=("Segoe UI", 26, "bold"), fg=VERDE, bg=CREME).pack()
        tk.Label(self.raiz, text="e o Pergaminho Perdido", font=("Segoe UI", 11), fg=VERDE_ESC, bg=CREME).pack()
        self.caixa = tk.Frame(self.raiz, bg=CREME)
        self.caixa.pack(pady=16)
        self.modo = modo
        if modo == "desinstalar":
            self.mensagem("Quer tirar o Ribbat do computador?\n(teu progresso continua guardado)")
            self.botao("Desinstalar", self.fazer_desinstalar)
        else:
            self.desktop = tk.BooleanVar(value=True)
            tk.Checkbutton(self.caixa, text="Criar atalho na Área de Trabalho", variable=self.desktop,
                           bg=CREME, activebackground=CREME, font=("Segoe UI", 10)).pack(pady=(0, 10))
            self.botao("Instalar", self.fazer_instalar)

    def limpar(self):
        for w in self.caixa.winfo_children():
            w.destroy()

    def mensagem(self, texto):
        tk.Label(self.caixa, text=texto, font=("Segoe UI", 10), bg=CREME, justify="center").pack(pady=(0, 10))

    def botao(self, texto, acao, cor=VERDE):
        tk.Button(self.caixa, text=texto, command=acao, font=("Segoe UI", 12, "bold"), bg=cor, fg="white",
                  activebackground=VERDE_ESC, activeforeground="white", relief="flat", padx=22, pady=6,
                  cursor="hand2").pack(side="left", padx=6)

    def fazer_instalar(self):
        self.limpar()
        self.mensagem("Instalando...")
        self.raiz.update()
        try:
            instalar(self.desktop.get())
        except Exception as erro:                       # noqa: BLE001 (mostra qualquer problema pro jogador)
            self.limpar()
            self.mensagem(f"Não deu pra instalar:\n{erro}")
            self.botao("Tentar de novo", lambda: (self.limpar(), self.fazer_instalar()))
            return
        self.limpar()
        self.mensagem("Pronto! O Ribbat está instalado.")
        self.botao("Jogar agora!", self.jogar)
        self.botao("Fechar", self.raiz.destroy, cor="#8a8a80")

    def jogar(self):
        subprocess.Popen([JOGO], cwd=PASTA)
        self.raiz.destroy()

    def fazer_desinstalar(self):
        desinstalar()
        self.limpar()
        self.mensagem("Pronto! O Ribbat foi desinstalado.\nTchau, sapinho!")
        self.botao("Fechar", self.raiz.destroy)


def main():
    if "--desinstalar" in sys.argv or "desinstalar" in os.path.basename(sys.executable).lower():
        Janela("desinstalar").raiz.mainloop()
    else:
        Janela("instalar").raiz.mainloop()


if __name__ == "__main__":
    main()
