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

## Run tests

```powershell
python -m pytest
```
