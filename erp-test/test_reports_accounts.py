#!/usr/bin/env python3
"""
Sena ERP - Comprehensive test for Financial Reports, Account Pages (Debtors/Creditors), and DSR Reports.
"""

import json
import os
import sys
import time
import traceback
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# Unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

BASE_URL = "http://13.210.47.18:8088"
SCREENSHOT_DIR = "/var/lib/freelancer/projects/40298427/erp-test/screenshots/reports_accounts"
RESULTS_FILE = "/var/lib/freelancer/projects/40298427/erp-test/results_reports_accounts.json"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

ALL_RESULTS = []


def save_results():
    """Save results to JSON and print summary."""
    summary = {
        "test_run": datetime.now().isoformat(),
        "total_pages_tested": len(ALL_RESULTS),
        "pages_loaded_ok": sum(1 for r in ALL_RESULTS if r.get("load_status") == 200),
        "pages_with_errors": sum(1 for r in ALL_RESULTS if r.get("errors")),
        "pages_with_data": sum(1 for r in ALL_RESULTS if r.get("table", {}).get("has_data")),
        "results": ALL_RESULTS
    }

    with open(RESULTS_FILE, "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total pages tested: {summary['total_pages_tested']}")
    print(f"Pages loaded OK (200): {summary['pages_loaded_ok']}")
    print(f"Pages with errors: {summary['pages_with_errors']}")
    print(f"Pages with data: {summary['pages_with_data']}")

    print(f"\n{'Name':<40} {'Status':<8} {'Rows':<8} {'Cols':<5} {'Filters':<8} {'Actions':<8}")
    print("-" * 80)
    for r in ALL_RESULTS:
        name = r["name"][:39]
        status = str(r.get("load_status", "?"))
        rows = str(r.get("table", {}).get("row_count", "?"))
        cols = str(len(r.get("table", {}).get("columns", [])))
        filters = str(len(r.get("filter_controls", [])))
        actions = str(len(r.get("action_buttons", [])))
        print(f"{name:<40} {status:<8} {rows:<8} {cols:<5} {filters:<8} {actions:<8}")

    print(f"\nResults saved to: {RESULTS_FILE}")
    print(f"Screenshots in: {SCREENSHOT_DIR}")


def ss(page, name):
    """Take a screenshot and return the path."""
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    try:
        page.screenshot(path=path, full_page=True, timeout=15000)
    except Exception:
        try:
            page.screenshot(path=path, full_page=False, timeout=10000)
        except Exception:
            pass
    return path


def login(page):
    """Login to the ERP system."""
    page.goto(f"{BASE_URL}/", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2000)
    page.evaluate('''() => {
        document.getElementById("username").value = "superadmin";
        document.getElementById("password").value = "Nick@#24";
        document.getElementById("signupForm").submit();
    }''')
    page.wait_for_timeout(8000)
    ss(page, "00_after_login")
    print("Login complete.")


def get_table_info(page):
    """Extract table info: row count, columns, and sample data."""
    info = {"row_count": 0, "columns": [], "has_data": False}
    try:
        # Try common table selectors
        for sel in ["table", ".table", "#dataTable", ".dataTables_wrapper table",
                     "table.dataTable", ".table-responsive table"]:
            tables = page.query_selector_all(sel)
            if tables:
                table = tables[0]
                # Get headers
                headers = table.query_selector_all("thead th, thead td")
                if not headers:
                    headers = table.query_selector_all("tr:first-child th, tr:first-child td")
                info["columns"] = [h.inner_text().strip() for h in headers if h.inner_text().strip()]

                # Get data rows
                rows = table.query_selector_all("tbody tr")
                if not rows:
                    all_rows = table.query_selector_all("tr")
                    rows = all_rows[1:] if len(all_rows) > 1 else []
                info["row_count"] = len(rows)
                info["has_data"] = len(rows) > 0

                # Check for "no data" messages
                if len(rows) == 1:
                    txt = rows[0].inner_text().strip().lower()
                    if "no data" in txt or "no record" in txt or "no matching" in txt:
                        info["row_count"] = 0
                        info["has_data"] = False
                break
    except Exception as e:
        info["error"] = str(e)
    return info


def get_filter_controls(page):
    """Find filter controls on the page."""
    controls = []
    try:
        # Date inputs
        for inp in page.query_selector_all("input[type='date'], input.datepicker, input.flatpickr, input[name*='date'], input[id*='date'], input[name*='from'], input[name*='to']"):
            name = inp.get_attribute("name") or inp.get_attribute("id") or inp.get_attribute("placeholder") or "date_input"
            controls.append({"type": "date_input", "name": name})

        # Text search
        for inp in page.query_selector_all("input[type='search'], input[type='text'][name*='search'], input.form-control[placeholder*='earch'], .dataTables_filter input"):
            name = inp.get_attribute("name") or inp.get_attribute("placeholder") or "search"
            controls.append({"type": "search_input", "name": name})

        # Dropdowns/selects
        for sel in page.query_selector_all("select"):
            name = sel.get_attribute("name") or sel.get_attribute("id") or "select"
            options = sel.query_selector_all("option")
            opt_texts = [o.inner_text().strip() for o in options[:10]]
            controls.append({"type": "select", "name": name, "options_sample": opt_texts})

        # Buttons
        for btn in page.query_selector_all("button, input[type='submit'], a.btn"):
            txt = btn.inner_text().strip() if btn.inner_text() else ""
            if any(k in txt.lower() for k in ["search", "filter", "apply", "submit", "go", "find", "show"]):
                controls.append({"type": "button", "text": txt})
    except Exception as e:
        controls.append({"type": "error", "message": str(e)})
    return controls


def get_action_buttons(page):
    """Find action buttons on table rows."""
    actions = []
    try:
        for btn in page.query_selector_all("tbody a, tbody button, tbody .btn, tbody i.fa, tbody .action-btn"):
            txt = btn.inner_text().strip() if btn.inner_text() else ""
            title = btn.get_attribute("title") or ""
            cls = btn.get_attribute("class") or ""
            href = btn.get_attribute("href") or ""
            label = txt or title or ""
            if not label:
                # Check for icon classes
                for icon_key in ["view", "edit", "delete", "print", "pdf", "download", "eye", "pencil", "trash"]:
                    if icon_key in cls.lower():
                        label = icon_key
                        break
            if label:
                actions.append({"text": label[:50], "href": href[:100] if href else ""})
        # Deduplicate
        seen = set()
        unique = []
        for a in actions:
            key = a["text"]
            if key not in seen:
                seen.add(key)
                unique.append(a)
        actions = unique[:15]
    except Exception:
        pass
    return actions


def get_payment_controls(page):
    """Find payment-related controls (checkboxes, payment fields)."""
    pcontrols = {"checkboxes": 0, "payment_fields": [], "submit_button": None}
    try:
        cbs = page.query_selector_all("input[type='checkbox']")
        pcontrols["checkboxes"] = len(cbs)

        for inp in page.query_selector_all("input[name*='payment'], input[name*='amount'], input[id*='payment'], input[id*='amount'], input[name*='paid'], input[placeholder*='mount']"):
            name = inp.get_attribute("name") or inp.get_attribute("id") or inp.get_attribute("placeholder") or "payment_field"
            pcontrols["payment_fields"].append(name)

        for btn in page.query_selector_all("button, input[type='submit']"):
            txt = (btn.inner_text() or "").strip().lower()
            if any(k in txt for k in ["submit", "record", "save", "pay"]):
                pcontrols["submit_button"] = (btn.inner_text() or "").strip()
                break
    except Exception:
        pass
    return pcontrols


def try_date_filter(page, result):
    """Try to apply a date filter."""
    try:
        date_inputs = page.query_selector_all("input[type='date'], input[name*='from_date'], input[name*='to_date'], input[name*='start_date'], input[name*='end_date'], input[id*='from'], input[id*='to'], input[name*='from'], input[name*='to']")
        if len(date_inputs) >= 2:
            date_inputs[0].fill("2024-01-01")
            date_inputs[1].fill("2026-04-19")
            result["date_filter_applied"] = True
        elif len(date_inputs) == 1:
            date_inputs[0].fill("2024-01-01")
            result["date_filter_applied"] = True
        else:
            result["date_filter_applied"] = False
            return

        # Click filter/search button
        for btn in page.query_selector_all("button, input[type='submit'], a.btn"):
            txt = (btn.inner_text() or "").strip().lower()
            if any(k in txt for k in ["search", "filter", "apply", "go", "show", "find", "submit"]):
                btn.click()
                page.wait_for_timeout(3000)
                result["filter_button_clicked"] = True
                break
    except Exception as e:
        result["date_filter_error"] = str(e)


def try_view_first_row(page, page_key, result):
    """Try to click the first view/print action on first row."""
    try:
        row_actions = page.query_selector_all("tbody tr:first-child a, tbody tr:first-child button")
        for btn in row_actions:
            txt = (btn.inner_text() or "").strip().lower()
            title = (btn.get_attribute("title") or "").lower()
            cls = (btn.get_attribute("class") or "").lower()
            href = btn.get_attribute("href") or ""
            if any(k in (txt + title + cls) for k in ["view", "eye", "print", "detail", "show", "open"]):
                btn.click()
                page.wait_for_timeout(3000)
                ss(page, f"{page_key}_detail_view")
                result["detail_view_opened"] = True
                # Check if modal or new page
                modal = page.query_selector(".modal.show, .modal.in, .modal[style*='display: block']")
                if modal:
                    result["detail_type"] = "modal"
                    result["detail_content"] = modal.inner_text()[:500]
                    # Close modal
                    close = modal.query_selector(".close, .btn-close, [data-dismiss='modal'], [data-bs-dismiss='modal']")
                    if close:
                        close.click()
                        page.wait_for_timeout(1000)
                else:
                    result["detail_type"] = "page"
                    result["detail_url"] = page.url
                    result["detail_content"] = page.inner_text("body")[:500]
                return
        result["detail_view_opened"] = False
    except Exception as e:
        result["detail_view_error"] = str(e)


def check_chart(page):
    """Check if a chart/graph is rendered on the page."""
    info = {"has_chart": False, "chart_type": None}
    try:
        canvas = page.query_selector_all("canvas")
        if canvas:
            info["has_chart"] = True
            info["chart_type"] = "canvas (likely Chart.js)"
            info["canvas_count"] = len(canvas)

        svg = page.query_selector_all("svg")
        if svg:
            # Filter out icon SVGs
            for s in svg:
                w = s.get_attribute("width") or "0"
                h = s.get_attribute("height") or "0"
                cls = s.get_attribute("class") or ""
                if any(k in cls.lower() for k in ["chart", "graph", "plot", "highcharts"]):
                    info["has_chart"] = True
                    info["chart_type"] = "SVG chart"
                    break
                try:
                    wi = int(w.replace("px", ""))
                    hi = int(h.replace("px", ""))
                    if wi > 200 and hi > 100:
                        info["has_chart"] = True
                        info["chart_type"] = "SVG (large)"
                        break
                except:
                    pass

        # Check for Highcharts or other chart containers
        for sel in [".highcharts-container", ".chart-container", "#chart", ".apexcharts-canvas", ".plotly"]:
            el = page.query_selector(sel)
            if el:
                info["has_chart"] = True
                info["chart_type"] = sel
                break
    except Exception:
        pass
    return info


def test_page(page, name, path, page_key, page_type="report"):
    """Test a single page thoroughly."""
    result = {
        "name": name,
        "url": f"{BASE_URL}{path}",
        "path": path,
        "page_type": page_type,
        "load_status": None,
        "screenshots": [],
        "errors": []
    }

    try:
        print(f"\n--- Testing: {name} ({path}) ---")
        resp = page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded", timeout=30000)
        result["load_status"] = resp.status if resp else "unknown"
        page.wait_for_timeout(3000)

        # Check for error pages
        body_text = page.inner_text("body")[:2000]
        if "404" in body_text[:200] and "not found" in body_text[:200].lower():
            result["load_status"] = 404
        if "500" in body_text[:200] and ("error" in body_text[:200].lower() or "exception" in body_text[:200].lower()):
            result["load_status"] = 500

        # Screenshot
        sp = ss(page, f"{page_key}_01_initial")
        result["screenshots"].append(sp)

        # Page title
        result["page_title"] = page.title()

        # Get table info
        tinfo = get_table_info(page)
        result["table"] = tinfo

        # Get filter controls
        fcontrols = get_filter_controls(page)
        result["filter_controls"] = fcontrols

        # Get action buttons
        actions = get_action_buttons(page)
        result["action_buttons"] = actions

        # Page-type specific tests
        if page_type in ["invoice_report", "report"]:
            # Try date filter
            try_date_filter(page, result)
            if result.get("date_filter_applied"):
                page.wait_for_timeout(2000)
                sp2 = ss(page, f"{page_key}_02_filtered")
                result["screenshots"].append(sp2)
                tinfo2 = get_table_info(page)
                result["table_after_filter"] = tinfo2

            # Try viewing first row detail
            if tinfo["has_data"]:
                try_view_first_row(page, page_key, result)
                # Go back if we navigated away
                if page.url != f"{BASE_URL}{path}":
                    page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded", timeout=20000)
                    page.wait_for_timeout(2000)

        elif page_type == "ledger":
            # Look for account selection
            selects = page.query_selector_all("select")
            if selects:
                options = selects[0].query_selector_all("option")
                if len(options) > 1:
                    # Select second option (first is usually placeholder)
                    selects[0].select_option(index=1)
                    result["ledger_account_selected"] = True
                    page.wait_for_timeout(2000)

            try_date_filter(page, result)
            page.wait_for_timeout(2000)
            sp2 = ss(page, f"{page_key}_02_filtered")
            result["screenshots"].append(sp2)
            tinfo2 = get_table_info(page)
            result["table_after_filter"] = tinfo2

            # Check for balance info
            for keyword in ["opening", "closing", "balance", "debit", "credit"]:
                if keyword in body_text.lower():
                    result.setdefault("balance_keywords_found", []).append(keyword)

        elif page_type == "ageing":
            # Check for ageing columns
            cols = tinfo.get("columns", [])
            result["ageing_columns"] = cols
            ageing_buckets = [c for c in cols if any(d in c.lower() for d in ["30", "60", "90", "120", "current", "overdue"])]
            result["ageing_buckets_found"] = ageing_buckets

        elif page_type == "debtor" or page_type == "creditor":
            # Check for payment controls
            pcontrols = get_payment_controls(page)
            result["payment_controls"] = pcontrols

            # Try date filter
            try_date_filter(page, result)
            if result.get("date_filter_applied"):
                page.wait_for_timeout(2000)
                sp2 = ss(page, f"{page_key}_02_filtered")
                result["screenshots"].append(sp2)

            # Document payment flow without submitting
            if pcontrols["checkboxes"] > 0:
                result["payment_flow"] = "Checkboxes available for selecting invoices"
                # Try selecting first checkbox
                try:
                    cb = page.query_selector("tbody input[type='checkbox']")
                    if cb:
                        cb.check()
                        page.wait_for_timeout(1000)
                        sp3 = ss(page, f"{page_key}_03_checkbox_selected")
                        result["screenshots"].append(sp3)
                        result["payment_flow"] += " - Successfully selected first checkbox"
                        # Uncheck it
                        cb.uncheck()
                except Exception:
                    pass

        elif page_type == "dsr":
            chart_info = check_chart(page)
            result["chart"] = chart_info
            try_date_filter(page, result)
            if result.get("date_filter_applied"):
                page.wait_for_timeout(2000)
                sp2 = ss(page, f"{page_key}_02_filtered")
                result["screenshots"].append(sp2)

        elif page_type == "dsr_graph":
            chart_info = check_chart(page)
            result["chart"] = chart_info
            fcontrols = get_filter_controls(page)
            result["filter_controls"] = fcontrols

        print(f"  Status: {result['load_status']}, Rows: {tinfo['row_count']}, Columns: {len(tinfo.get('columns', []))}")

    except Exception as e:
        result["errors"].append(str(e))
        result["traceback"] = traceback.format_exc()
        print(f"  ERROR: {e}")
        try:
            sp = ss(page, f"{page_key}_error")
            result["screenshots"].append(sp)
        except:
            pass

    ALL_RESULTS.append(result)
    return result


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        context.set_default_timeout(60000)
        page = context.new_page()

        # Login
        login(page)

        # =============================================
        # PART 1: Financial Reports (9 pages)
        # =============================================
        print("\n" + "=" * 60)
        print("PART 1: FINANCIAL REPORTS")
        print("=" * 60)

        financial_reports = [
            ("Purchase Invoice", "/purchase-invoice", "fin_01_purchase_inv", "invoice_report"),
            ("Sales Invoice", "/sales-invoice", "fin_02_sales_inv", "invoice_report"),
            ("Purchase Invoice with VAT", "/purchase-invoice-with-vat", "fin_03_purchase_inv_vat", "invoice_report"),
            ("Sales Invoice with VAT", "/sales-invoice/with-vat", "fin_04_sales_inv_vat", "invoice_report"),
            ("Ledger Report", "/ledger", "fin_05_ledger", "ledger"),
            ("Customer Ageing", "/reports/customer-aging", "fin_06_customer_ageing", "ageing"),
            ("Supplier Ageing", "/reports/supplier-ageing", "fin_07_supplier_ageing", "ageing"),
            ("Jobs without Purchase Invoice", "/purchase-invoice-missing", "fin_08_jobs_no_purchase", "report"),
            ("Jobs without Sales Invoice", "/sales-charges-without-invoice", "fin_09_jobs_no_sales", "report"),
        ]

        for name, path, key, ptype in financial_reports:
            test_page(page, name, path, key, ptype)

        # =============================================
        # PART 2: Account Pages - Debtors (6 pages)
        # =============================================
        print("\n" + "=" * 60)
        print("PART 2: ACCOUNT PAGES - DEBTORS")
        print("=" * 60)

        debtor_pages = [
            ("Consignee Due", "/1abe8a244329f592bb3bbb96e22e0344", "dbt_01_consignee_due", "debtor"),
            ("Consignee Paid", "/8c8bcb5e96e6c22e001efff53fcadf28", "dbt_02_consignee_paid", "debtor"),
            ("Agent Due (Debtor)", "/28f3b7864cdf11d6b30b148bec8d6307", "dbt_03_agent_due", "debtor"),
            ("Agent Paid (Debtor)", "/b621a0964636bcee73d691db7d3572fd", "dbt_04_agent_paid", "debtor"),
            ("Shipper Due", "/8211377a76b5f20c607e278620d4abe3", "dbt_05_shipper_due", "debtor"),
            ("Shipper Paid", "/76264365e7c5a943b7629804aeab136b", "dbt_06_shipper_paid", "debtor"),
        ]

        for name, path, key, ptype in debtor_pages:
            test_page(page, name, path, key, ptype)

        # =============================================
        # PART 3: Account Pages - Creditors (8 pages)
        # =============================================
        print("\n" + "=" * 60)
        print("PART 3: ACCOUNT PAGES - CREDITORS")
        print("=" * 60)

        creditor_pages = [
            ("Shipping Line Due", "/8e1b7fdf1fd87dcc9e0546d03ae62556", "crd_01_shipping_due", "creditor"),
            ("Shipping Line Paid", "/d18ec27a83b522669c9efc55a880f917", "crd_02_shipping_paid", "creditor"),
            ("Co-Loader Due", "/285ee3bf7d21a421fb354e824a0ba678", "crd_03_coloader_due", "creditor"),
            ("Co-Loader Paid", "/49ab2c7ef13c1de745c5e511ea7d306f", "crd_04_coloader_paid", "creditor"),
            ("Supplier Due", "/57e215a5d82f9e54a6e6b2ddfd0372c1", "crd_05_supplier_due", "creditor"),
            ("Supplier Paid", "/832128c1bea0bf94b30c16a8417125ae", "crd_06_supplier_paid", "creditor"),
            ("Agent Due (Creditor)", "/455492c7888db5aafecf4facc1aa7639", "crd_07_agent_due", "creditor"),
            ("Agent Paid (Creditor)", "/bfd9d957f28679c09593198e7cefb085", "crd_08_agent_paid", "creditor"),
        ]

        for name, path, key, ptype in creditor_pages:
            test_page(page, name, path, key, ptype)

        # =============================================
        # PART 4: DSR Reports (5 pages)
        # =============================================
        print("\n" + "=" * 60)
        print("PART 4: DSR REPORTS")
        print("=" * 60)

        dsr_pages = [
            ("Basic Graph", "/fe83dce7816670353cfa807c5722d816", "dsr_01_basic_graph", "dsr_graph"),
            ("Ocean Import DSR", "/1387f1ae3dc1d840789d15c546e89125", "dsr_02_ocean_import", "dsr"),
            ("Ocean Export DSR", "/c745c437840b2e21636a2cbdab4b33a6", "dsr_03_ocean_export", "dsr"),
            ("Air Import DSR", "/abf5db603d4276889077e81de984cf6d", "dsr_04_air_import", "dsr"),
            ("Air Export DSR", "/627db3ba79d7139f8dfd6f462e1b0514", "dsr_05_air_export", "dsr"),
        ]

        for name, path, key, ptype in dsr_pages:
            test_page(page, name, path, key, ptype)

        # Save results BEFORE closing browser
        save_results()

        try:
            browser.close()
        except Exception:
            pass
        print("Browser closed. Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        traceback.print_exc()
        save_results()
    finally:
        os._exit(0)
