# Job Application Automation Assistant

Version 1 processes job listings exported from LoopCV. It currently accepts CSV files, cleans their columns, removes duplicate listings, and classifies jobs using the job title only.

## Version 1 scope

- Input: CSV
- Duplicate key: company, job title, and location (case-insensitive)
- Priorities: High Priority, Medium Priority, Low Priority, and Not Applying
- Relevance score: 1 to 10, based only on the job title
- Relevant jobs default to `Saved`.
- Senior or clearly irrelevant jobs default to `Not Applying`.
- No browser automation, LinkedIn automation, email sending, or paid APIs

The classifier does not infer requirements, experience, or skills that are not present in the CSV.

## Project structure

```text
job-application-automation/
├── main.py
├── requirements.txt
├── README.md
├── data/
│   ├── input/
│   │   └── sample_jobs.csv
│   └── output/
├── src/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── cleaner.py
│   ├── deduplicator.py
│   └── classifier.py
└── tests/
    └── test_classifier.py
```

## Windows PowerShell setup

Open PowerShell in the project folder, then run these commands:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use this once for the current PowerShell session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Run the sample

After setup, the first processing command is:

```powershell
python main.py
```

This reads `data/input/sample_jobs.csv` and writes:

```text
data/output/processed_jobs.csv
```

To process another LoopCV export:

```powershell
python main.py .\data\input\my_loopcv_export.csv
```

To choose a different output file:

```powershell
python main.py .\data\input\my_loopcv_export.csv --output .\data\output\my_results.csv
```

## Run locally from the saved LoopCV CSV

Google Cloud credentials are not needed for the local workflow. Preview the
Application Queue using your saved export:

```powershell
python main.py sync --input "D:\data\input\jobs.csv"
```

After reviewing the preview, create or update the local queue CSV:

```powershell
python main.py sync --input "D:\data\input\jobs.csv" --apply
```

The queue is saved to `data/output/application_queue.csv`. Historical queue rows
are retained when a later CSV no longer contains the job.

Run local reports without Google credentials:

```powershell
python main.py dashboard
python main.py followups
python main.py analyze
```

## Process the original Google Sheet

The supplied sheet is private, so it must be shared with a Google service-account
email and accessed with that account's JSON key file. Then run:

```powershell
python main.py "https://docs.google.com/spreadsheets/d/1AKxetFFGWOwYhPdbg672x-sh7P0qU-uyiF2V4MFX3t4/edit?gid=0#gid=0" --google-credentials .\credentials\google-service-account.json
```

The first worksheet tab is used by default. Select another tab with
`--worksheet "Tab name"`. Keep the JSON key file outside source control.

## Run tests

```powershell
python -m pytest
```

## Milestone 3 and later commands

Set `GOOGLE_CREDENTIALS` or pass `--google-credentials`. Sync is read-only by
default and prints a JSON preview. The raw `Jobs` worksheet is never written.

```powershell
python main.py sync --google-credentials .\credentials\google-service-account.json
python main.py sync --google-credentials .\credentials\google-service-account.json --apply
python main.py dashboard --google-credentials .\credentials\google-service-account.json
python main.py followups --google-credentials .\credentials\google-service-account.json
python main.py analyze --google-credentials .\credentials\google-service-account.json
```

`apply` prepares a review summary for a queue job using its stable ID and stops
before submission. Cold-email generation is an unsent draft only. No browser
submission or email sending is implemented.
