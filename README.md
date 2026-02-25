# IP Enrichment Pipeline

IP enrichment pipeline using external blocklists and OpenCTI.

This project:

- Downloads and processes blocklists
- Uploads IPs as observables to OpenCTI
- Retrieves enrichment data
- Updates a local processed CSV file

---

## Requirements

- Python **3.13.9**
- OpenCTI instance
- OpenCTI API token

---

## Project Structure

```_
ip-enrichment/
│
├── pyproject.toml
├── README.md
├── .gitignore
│
├── src/
    └── ip_enrichment/
        ├── cli.py
        ├── config.py
        ├── blocklist/
        │   └── manager.py
        └── opencti/
            └── manager.py
```
---

## Environment Configuration

Create your environment file:

```bash
cp .env.example .env
```

Edit `.env` and configure:

### Blocklists
```bash
BLOCKLIST_URL=
RAW_FILE_PATH=
FORMATTED_FILE_PATH=
PROCESSED_IP_FILE_PATH=
```

### OpenCTI credentials
```bash
OPENCTI_URL=
OPENCTI_TOKEN=
```

# Option 1 — Using venv (Recommended)
## 1. Create Virtual Environment

```bash
python -m venv .venv
```

## 2. Activate

### Linux / macOS

```bash
source .venv/bin/activate
```
### Windows

```bash
.venv\Scripts\activate
```

## 3. Upgrade pip

```bash
pip install --upgrade pip
```

## 4. Install Project (Editable Mode)

```bash
pip install -e .
```

## 5. Run

```bash
ip-enrichment --number_ips 10 --wait_time 1 --threshold 30
```

Or directly:

```bash
python -m ip_enrichment.main --number_ips 10
```

# Option 2 — Using Conda
## 1. Create Environment

```bash
conda create -n ip-enrichment python=3.13
```

## 2. Activate

```bash
conda activate ip-enrichment
```

## 3. Install Project

```bash
pip install -e .
```

## 4. Run

```bash
ip-enrichment --number_ips 10
```

# CLI Arguments (TBD)

| Argument     | Description                                   | Default |
| ------------ | --------------------------------------------- | ------- |
| --number_ips | Max number of IPs processed per run           | 10      |
| --wait_time  | Minutes to wait before retrieving API results | 1       |
| --threshold  | Days before an IP is considered outdated      | 30      |


# Development Installation
Install with development tools:

```bash
pip install -e .[dev]
```

# Notes

- `.env` must not be committed.
- Use `.env.example` as a template.
- Ensure your OpenCTI API token has permission to create observables.
- Python 3.13 is recent — verify library compatibility if issues arise.