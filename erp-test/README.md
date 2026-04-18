# Sena ERP - QA Test Suite

Comprehensive Playwright-based test suite for the Sena ERP freight/logistics system.

## Prerequisites

- Python 3.8+
- Playwright for Python

```bash
pip install playwright
playwright install chromium
```

## Test Scripts

### 1. test_all_pages.py - Page Load Testing
Tests all 72 pages in the ERP system for basic load functionality.
- Navigates to each page via direct URL
- Checks HTTP status, page title, presence of tables/forms/buttons
- Detects server errors (500, 404, exceptions)
- Saves results to `results_all_pages.json`

```bash
python test_all_pages.py
```

### 2. test_crud_masters.py - CRUD Operations
Tests Create operations on 20 master data pages.
- Clicks "Add New" on each master page
- Discovers and fills all form fields with AUTOTEST_ prefixed data
- Submits forms and verifies record creation
- Saves results to `results_crud.json`

```bash
python test_crud_masters.py
```

### 3. test_jobs_and_reports.py - Job Workflows & Reports
Comprehensive testing of job creation, reports, and account pages.
- Tests job creation for all 6 transport modes (Ocean/Air/Land Import/Export)
- Tests all 9 financial report pages with date filtering
- Tests all 14 account pages (Debtors + Creditors)
- Tests booking reports, closed jobs, quotes, DSR reports
- Saves results to `results_jobs_reports.json`

```bash
python test_jobs_and_reports.py
```

### 4. discover_all_menus.py - Menu Discovery
Discovers the complete sidebar menu structure.
- Maps all modules and sub-pages
- Saves menu tree to `menu_structure.json`

```bash
python discover_all_menus.py
```

## Configuration

All scripts use these default settings (modify at top of each file):
```python
BASE_URL = "http://13.210.47.18:8088"
USERNAME = "superadmin"
PASSWORD = "Nick@#24"
```

## Output

- Screenshots: `screenshots/` subdirectories
- Results: JSON files in the root directory
- Report: `Sena_ERP_Full_Test_Report.pdf`

## Running for Future Upgrades

After each ERP upgrade:
1. Run `test_all_pages.py` first to check all pages load
2. Run `test_crud_masters.py` to verify data entry works
3. Run `test_jobs_and_reports.py` to verify job workflows and reports
4. Compare results JSON files with previous runs to identify regressions
