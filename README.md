# Freshworks Aadhaar Upload Automation

This script:
- Reads names from `aadhar.txt`
- Converts pages of `Aadhar.pdf` into per-person PNG files
- Searches matching accounts in Freshworks CRM
- Uploads the image document to eligible accounts
- Sets `cf_file_uploaded = true` after successful upload

## Requirements

- Windows/macOS/Linux
- Python `3.10+`
- Access to Freshworks CRM in browser

## Install Python

### Windows

1. Download Python from `https://www.python.org/downloads/windows/`
2. Run installer and enable `Add python.exe to PATH`
3. Click `Install Now`
4. Verify:

```bash
python --version
pip --version
```

If `python` is not recognized, restart terminal and try:

```bash
py --version
```

### macOS

Install with Homebrew:

```bash
brew install python
python3 --version
pip3 --version
```

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y python3 python3-pip
python3 --version
pip3 --version
```

## Project Files

Keep these files in the project root (same folder as `main.py`):

- `main.py`
- `api_client.py`
- `processor.py`
- `pdf_converter.py`
- `logger.py`
- `Aadhar.pdf` (exact filename)
- `aadhar.txt` (one name per line)

`image/` and `log/` folders are created automatically if missing.

## Install

From project root:

```bash
python -m pip install -r requirements.txt
```

If your system uses `python3`, use:

```bash
python3 -m pip install -r requirements.txt
```

## Input Rules

- Each line in `aadhar.txt` is a person name.
- Page order in `Aadhar.pdf` should match name order in `aadhar.txt`.
- If counts differ, script continues but logs a warning.

## Get Freshworks Auth Headers

While logged in to Freshworks in browser:

1. Open Developer Tools (`F12`)
2. Go to Network tab
3. Trigger a CRM request
4. Copy:
   - `Cookie` header value
   - `X-CSRF-Token` header value

Use fresh values if session expires.

## Run

```bash
python main.py --cookie "PASTE_COOKIE_HERE" --csrf "PASTE_CSRF_TOKEN_HERE"
```

## Output

- Converted images: `image/*.png`
- Run logs: `log/run_YYYYMMDD_HHMMSS.log`
- Console summary at end with uploaded/skipped/failed counts

## Important Project-Specific Settings

In `api_client.py`, these are hardcoded:

- `BASE_URL = "https://sundirect-606378453475310199.myfreshworks.com"`
- `OWNER_ID = 403000001694`

If your friend uses a different Freshworks account or owner filter, update these values before running.

## Common Issues

- `Auth failed` / `Session expired`: copy fresh `Cookie` and `X-CSRF-Token`.
- `aadhar.txt not found` or `Aadhar.pdf not found`: place files in project root with exact names.
- Upload/update API errors: check account eligibility and permissions in Freshworks.
