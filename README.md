# Stitch Workspace Hub

Stitch Workspace Hub is a Windows desktop workspace assistant built with Python and PySide6. It combines an app launcher, desktop activity view, recommendations, an optional AI companion, and a small desktop pet.

## Download for Windows

Open the repository's **Releases** page and download the latest `StitchWorkspaceHub-windows.zip`. Extract the ZIP and run `StitchWorkspaceHub.exe`.

## Run from source

Windows 10 or newer and Python 3.10+ are recommended.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

The Windows build can be created locally with:

```powershell
pyinstaller --noconfirm --clean --windowed --name StitchWorkspaceHub main.py
Compress-Archive -Path dist\StitchWorkspaceHub\* -DestinationPath StitchWorkspaceHub-windows.zip -Force
```

## Optional AI companion

AI features use Groq and are disabled unless a key is configured. Copy `.env.example` to `.env`, then add your own key:

```text
GROQ_API_KEY=your_key_here
```

Never commit `.env` or share an API key. The application remains usable without AI features.

## Platform note

The app is designed for Windows because it reads installed applications and desktop windows using Windows APIs. Some discovery features are reduced when `pywin32` is unavailable.
