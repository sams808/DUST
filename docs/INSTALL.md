# Installing and updating DUST

## Requirements

- Windows with the **py launcher** (installs alongside Python from
  [python.org](https://www.python.org/downloads/) - tick "py launcher"
  during setup if asked).
- **Python 3.11** available as `py -3.11`. Plain `python` on your PATH
  may resolve to a different install without the app's dependencies -
  the app and its scripts always call `py -3.11` explicitly to avoid that.

## First-time install

1. Get the code: `git clone https://github.com/sams808/DUST.git`
   (or download/extract the ZIP from GitHub).
2. Open the `DUST` folder, right-click **install.ps1** -> *Run with
   PowerShell*. If Windows blocks it, run instead from a PowerShell
   prompt opened in that folder:

   ```powershell
   powershell -ExecutionPolicy Bypass -File install.ps1
   ```

3. `install.ps1` will:
   - confirm `py -3.11` is available (and tell you where to get it if not),
   - install everything in `requirements.txt` (PySide6, matplotlib,
     pandas, numpy, pytest),
   - generate the brand assets in `assets/` (logo, splash, icon),
   - write/refresh **`DUST.bat`**, the double-click launcher.
4. Double-click `DUST.bat` to start the app.

## Updating

Whenever you pull new code (or just want dependencies/launcher
refreshed), right-click **update.ps1** -> *Run with PowerShell*
(or `powershell -ExecutionPolicy Bypass -File update.ps1`). It will:

- `git pull` if this folder is a git checkout,
- upgrade dependencies from `requirements.txt`,
- regenerate brand assets,
- rewrite `DUST.bat` so the launcher always matches the current app.

## Running without the installer

You never *need* the PowerShell scripts - they only automate setup.
Once dependencies are installed, any of these work:

```
DUST.bat                  <- double-click, or from a terminal
py -3.11 app.py
```

## Running the test suite

```
py -3.11 -m pytest tests/
```

18 tests pin the model calculations against exact values pulled from
the reference spreadsheets - see
[MODELS_REFERENCE.md](MODELS_REFERENCE.md) for what they check and why.

## Troubleshooting

- **"Python 3.11 was not found via the 'py' launcher"** - install
  Python 3.11 from python.org, making sure the "py launcher for all
  users" option is checked during setup, then re-run `install.ps1`.
- **`DUST.bat` flashes and closes** - that means it failed *before*
  falling back to the visible console mode, which normally only
  happens if `py`/`pyw` aren't on PATH at all. Open a terminal in the
  DUST folder and run `py -3.11 app.py` directly to see the real error.
- **pip install fails behind a proxy/firewall** - run
  `py -3.11 -m pip install -r requirements.txt` yourself with whatever
  proxy flags your network needs, then re-run `install.ps1` (it will
  skip straight past since packages are already present).
