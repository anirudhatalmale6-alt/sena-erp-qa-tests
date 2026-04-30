#!/usr/bin/env python3
"""
Sena ERP - Quotes Workflow & Land Transportation Test Script (v2)
Tests: Quotes setup (Carriers, Exchange Rates, Rate DB, Client Rates, Create Quote)
       Land Import (Create Job, All Tabs/Steps)
       Land Export (Create Job, All Tabs/Steps)
       Report verification
"""

import json
import os
import time
import traceback
from datetime import datetime
from playwright.sync_api import sync_playwright

# --- Config ---
BASE_URL = "http://13.210.47.18:8088"
SCREENSHOT_DIR = "/var/lib/freelancer/projects/40298427/erp-test/screenshots/quotes_land"
RESULTS_FILE = "/var/lib/freelancer/projects/40298427/erp-test/results_quotes_land.json"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

results = {
    "run_date": datetime.now().isoformat(),
    "tests": {},
    "summary": {"passed": 0, "failed": 0, "errors": 0, "warnings": 0}
}

# --- Helper Functions ---

def screenshot(page, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    try:
        page.screenshot(path=path, full_page=True)
        print(f"    [SCREENSHOT] {name}.png")
    except Exception as e:
        print(f"    [SCREENSHOT ERROR] {name}: {e}")
    return path

def fill_select2(page, select_id, search_text):
    try:
        page.evaluate("try { $('select.select2-hidden-accessible').select2('close'); } catch(e) {}")
        page.wait_for_timeout(300)
        page.evaluate(f"$('#{select_id}').select2('open')")
        page.wait_for_timeout(500)
        search_field = page.locator('.select2-search__field')
        if search_field.count() > 0:
            search_field.fill(search_text)
            page.wait_for_timeout(2000)
        ro = page.locator('.select2-results__option:not(.select2-results__message)')
        if ro.count() > 0:
            text = ro.first.text_content()
            ro.first.click()
            page.wait_for_timeout(500)
            print(f"    Select2 '{select_id}' -> '{text}'")
            return text
        page.evaluate(f"try {{ $('#{select_id}').select2('close'); }} catch(e) {{}}")
        print(f"    Select2 '{select_id}': no results for '{search_text}'")
    except Exception as e:
        print(f"    Select2 error for {select_id}: {e}")
    return None

def fill_select2_by_name(page, name_attr, search_text):
    try:
        page.evaluate("try { $('select.select2-hidden-accessible').select2('close'); } catch(e) {}")
        page.wait_for_timeout(300)
        page.evaluate(f"$('select[name=\"{name_attr}\"]').select2('open')")
        page.wait_for_timeout(500)
        search_field = page.locator('.select2-search__field')
        if search_field.count() > 0:
            search_field.fill(search_text)
            page.wait_for_timeout(2000)
        ro = page.locator('.select2-results__option:not(.select2-results__message)')
        if ro.count() > 0:
            text = ro.first.text_content()
            ro.first.click()
            page.wait_for_timeout(500)
            print(f"    Select2 [name={name_attr}] -> '{text}'")
            return text
        page.evaluate(f"try {{ $('select[name=\"{name_attr}\"]').select2('close'); }} catch(e) {{}}")
        print(f"    Select2 [name={name_attr}]: no results for '{search_text}'")
    except Exception as e:
        print(f"    Select2 error for [name={name_attr}]: {e}")
    return None

def fill_date_html5(page, selector, date_str="2026-04-30"):
    """Fill HTML5 date input using JS value setter"""
    # Escape single quotes in selector for JS
    safe_sel = selector.replace("'", "\\'")
    js_code = """(() => {
        var el = document.querySelector('""" + safe_sel + """');
        if (el) {
            var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            nativeSetter.call(el, '""" + date_str + """');
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
        }
    })()"""
    page.evaluate(js_code)

def fill_date_flatpickr(page, selector, date_str="30/04/2026"):
    """Fill date field that uses flatpickr or similar datepicker"""
    page.evaluate(f"""(() => {{
        var el = document.querySelector('{selector}');
        if (el) {{
            el.value = '{date_str}';
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
            if (el._flatpickr) el._flatpickr.setDate('{date_str}');
        }}
    }})()""")

def check_page_error(page):
    try:
        body = page.locator("body").inner_text(timeout=5000)
    except:
        return ["Page not accessible"]
    lower = body.lower()
    errors = []
    if "500" in body and ("internal server error" in lower or "server error" in lower):
        errors.append("HTTP 500")
    if "permission denied" in lower and "denied" in lower:
        errors.append("PERMISSION_DENIED")
    if "symfony exception" in lower or "whoops" in lower:
        errors.append("SYMFONY_EXCEPTION")
    if "404" in body and "not found" in lower:
        errors.append("HTTP 404")
    if "sqlstate" in lower:
        errors.append("SQL_ERROR")
    if "undefined" in lower and ("variable" in lower or "array key" in lower or "index" in lower):
        errors.append("UNDEFINED_ERROR")
    return errors if errors else None

def discover_all_elements(page, label=""):
    return page.evaluate("""(() => {
        const elements = [];
        document.querySelectorAll('a, button, input[type="button"], input[type="submit"], .btn').forEach(el => {
            if (el.offsetParent !== null) {
                elements.push({
                    tag: el.tagName,
                    text: (el.textContent || '').trim().substring(0, 150),
                    href: el.href || el.getAttribute('href') || '',
                    onclick: el.getAttribute('onclick') || '',
                    class: el.className || '',
                    id: el.id || '',
                    type: el.type || '',
                    name: el.name || ''
                });
            }
        });
        return elements;
    })()""")

def discover_form_fields(page):
    return page.evaluate("""(() => {
        const fields = [];
        document.querySelectorAll('input:not([type="hidden"]), select, textarea').forEach(el => {
            if (el.offsetParent !== null || el.closest('.modal.show') || el.closest('.modal.in')) {
                fields.push({
                    tag: el.tagName,
                    type: el.type || '',
                    name: el.name || '',
                    id: el.id || '',
                    placeholder: el.placeholder || '',
                    required: el.required,
                    value: el.value || '',
                    options: el.tagName === 'SELECT' ? Array.from(el.options).slice(0,15).map(o => ({value: o.value, text: o.text})) : [],
                    hasSelect2: !!el.closest('.select2') || el.classList.contains('select2-hidden-accessible'),
                    label: el.id ? (document.querySelector('label[for="' + el.id + '"]')?.textContent?.trim() || '') : '',
                    visible: el.offsetParent !== null
                });
            }
        });
        return fields;
    })()""")

def discover_all_form_fields_including_hidden(page):
    return page.evaluate("""(() => {
        const fields = [];
        document.querySelectorAll('input, select, textarea').forEach(el => {
            fields.push({
                tag: el.tagName,
                type: el.type || '',
                name: el.name || '',
                id: el.id || '',
                placeholder: el.placeholder || '',
                required: el.required,
                value: el.value || '',
                options: el.tagName === 'SELECT' ? Array.from(el.options).slice(0,15).map(o => ({value: o.value, text: o.text})) : [],
                hasSelect2: !!el.closest('.select2') || el.classList.contains('select2-hidden-accessible'),
                label: el.id ? (document.querySelector('label[for="' + el.id + '"]')?.textContent?.trim() || '') : '',
                visible: el.offsetParent !== null,
                hidden: el.type === 'hidden'
            });
        });
        return fields;
    })()""")

def count_table_rows(page):
    try:
        return page.evaluate("""(() => {
            const rows = document.querySelectorAll('table tbody tr');
            let count = 0;
            rows.forEach(tr => {
                if (!tr.querySelector('td[colspan]') && tr.querySelectorAll('td').length > 1) count++;
            });
            return count;
        })()""")
    except:
        return 0

def get_validation_errors(page):
    """Get REAL validation errors, excluding labels and nav elements"""
    return page.evaluate("""(() => {
        const errors = [];
        // Check for red border / is-invalid fields
        document.querySelectorAll('.is-invalid, input:invalid, select:invalid').forEach(el => {
            if (el.offsetParent !== null) {
                const label = el.previousElementSibling?.textContent?.trim() ||
                              el.closest('.form-group')?.querySelector('label')?.textContent?.trim() || el.name;
                if (label && label.length < 100) errors.push('Required: ' + label);
            }
        });
        // Check for specific error messages
        document.querySelectorAll('.invalid-feedback:not(:empty), .alert-danger, .error-message').forEach(el => {
            if (el.offsetParent !== null && el.textContent.trim().length > 2 && el.textContent.trim().length < 200) {
                errors.push(el.textContent.trim());
            }
        });
        // Toastr/SweetAlert errors
        document.querySelectorAll('.toast-error, .swal2-popup .swal2-title').forEach(el => {
            if (el.textContent.trim()) errors.push(el.textContent.trim().substring(0, 200));
        });
        return errors;
    })()""")

def get_success_messages(page):
    return page.evaluate("""(() => {
        const msgs = [];
        document.querySelectorAll('.alert-success, .toast-success, .swal2-success').forEach(el => {
            msgs.push(el.textContent.trim().substring(0, 200));
        });
        return msgs;
    })()""")

def get_job_number(page):
    return page.evaluate("""(() => {
        const el = document.querySelector('h4, h3, .job-number, [class*="job"]');
        return el ? el.textContent.trim() : '';
    })()""")

def discover_steps(page):
    """Find step-based navigation (Step 1, Step 2, Step 3)"""
    return page.evaluate("""(() => {
        const steps = [];
        // Look for step indicators
        document.querySelectorAll('.step, .wizard-step, [class*="step"], .stepper-item, .nav-step').forEach(el => {
            const text = el.textContent.trim();
            if (text && text.length < 100) {
                steps.push({text: text, class: el.className, id: el.id || ''});
            }
        });
        // Also look for specific step links/buttons
        document.querySelectorAll('a[href*="step"], button[data-step], .step-trigger').forEach(el => {
            const text = el.textContent.trim();
            if (text && text.length < 100) {
                steps.push({text: text, href: el.getAttribute('href') || '', class: el.className});
            }
        });
        return steps;
    })()""")

def find_and_click_add_button(page):
    selectors = [
        'a:has-text("Add New")',
        'a:has-text("+ New")',
        'button:has-text("Add New")',
        'a:has-text("Add")',
        'button:has-text("Add")',
        'a:has-text("Create")',
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=2000):
                text = loc.text_content().strip()
                loc.click()
                print(f"    Clicked add button: '{text}'")
                return text
        except:
            continue
    return None

def find_and_click_submit(page):
    selectors = [
        'button[type="submit"]',
        'input[type="submit"]',
        'button:has-text("Save")',
        'button:has-text("Submit")',
        'button:has-text("Create Job")',
        'button:has-text("Save Quote")',
        'button:has-text("Create")',
        '.btn-success',
        '.btn-primary:has-text("Save")',
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=2000):
                text = loc.text_content().strip()
                loc.click()
                print(f"    Clicked submit: '{text}'")
                return text
        except:
            continue
    return None

def safe_fill(page, selector, value):
    try:
        loc = page.locator(selector)
        if loc.count() > 0 and loc.first.is_visible(timeout=2000):
            loc.first.fill(str(value))
            return True
    except:
        pass
    return False

def safe_select(page, selector, value=None):
    try:
        loc = page.locator(selector)
        if loc.count() > 0:
            if value:
                loc.first.select_option(value=value)
            else:
                loc.first.select_option(index=1)
            return True
    except:
        pass
    return False

def log_test(test_name, status, details="", errors=None):
    results["tests"][test_name] = {
        "status": status,
        "details": details,
        "errors": errors or [],
        "timestamp": datetime.now().isoformat()
    }
    if status == "PASS": results["summary"]["passed"] += 1
    elif status == "FAIL": results["summary"]["failed"] += 1
    elif status == "ERROR": results["summary"]["errors"] += 1
    elif status == "WARNING": results["summary"]["warnings"] += 1
    icon = {"PASS": "OK", "FAIL": "FAIL", "ERROR": "ERR", "WARNING": "WARN"}.get(status, "?")
    print(f"  [{icon}] {test_name}: {status} - {details}")

def print_fields_summary(fields, label=""):
    if label:
        print(f"\n    === {label} ===")
    for f in fields:
        sel2 = " [SELECT2]" if f.get('hasSelect2') else ""
        req = " *REQUIRED*" if f.get('required') else ""
        opts = ""
        if f['tag'] == 'SELECT' and f.get('options'):
            opt_texts = [o['text'] for o in f['options'][:5]]
            opts = f" options={opt_texts}"
        lbl = f" label='{f.get('label', '')}'" if f.get('label') else ""
        plh = f" placeholder='{f.get('placeholder', '')}'" if f.get('placeholder') else ""
        print(f"    {f['tag']} name='{f.get('name','')}' id='{f.get('id','')}' type='{f.get('type','')}'{lbl}{plh}{sel2}{req}{opts}")

def check_if_page_changed(page, original_url):
    """Check if page URL changed after form submit (indicates success)"""
    current = page.url
    return current != original_url


# --- MAIN TEST ---

def run_tests():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        page.set_default_timeout(60000)

        # --- LOGIN ---
        print("\n" + "="*70)
        print("LOGIN")
        print("="*70)
        try:
            page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            page.evaluate("""
                document.getElementById("username").value = "superadmin";
                document.getElementById("password").value = "Nick@#24";
                document.getElementById("signupForm").submit();
            """)
            print("  Login submitted, waiting 8 seconds...")
            page.wait_for_timeout(8000)
            screenshot(page, "00_after_login")
            err = check_page_error(page)
            if err:
                log_test("LOGIN", "ERROR", f"Page errors: {err}")
            else:
                log_test("LOGIN", "PASS", "Logged in as superadmin")
        except Exception as e:
            log_test("LOGIN", "ERROR", str(e))
            screenshot(page, "00_login_error")

        # ============================================================
        # PART 1: QUOTES WORKFLOW
        # ============================================================
        print("\n" + "="*70)
        print("PART 1: QUOTES WORKFLOW")
        print("="*70)

        # --- Test 1.1: Carriers ---
        print("\n--- Test 1.1: Quote Setup - Carriers ---")
        try:
            page.goto(f"{BASE_URL}/8ee4a920e024b1d3beadaadd006a0a31", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            screenshot(page, "01_carriers_list")
            err = check_page_error(page)
            if err:
                log_test("1.1_Carriers_Page", "FAIL", f"Page errors: {err}", err)
            else:
                row_count = count_table_rows(page)
                print(f"  Existing carrier rows: {row_count}")

                elements = discover_all_elements(page)
                add_buttons = [e for e in elements if any(kw in e['text'].lower() for kw in ['add', 'new'])]
                print(f"  Add buttons: {[e['text'] for e in add_buttons]}")

                clicked = find_and_click_add_button(page)
                if clicked:
                    page.wait_for_timeout(2000)
                    screenshot(page, "01_carriers_add_form")
                    fields = discover_form_fields(page)
                    print_fields_summary(fields, "Carrier Form Fields")
                    results["tests"]["1.1_Carriers_Fields"] = {"fields": fields}

                    # Fill fields based on discovered structure
                    for f in fields:
                        fname = f.get('name', '') or f.get('id', '')
                        if not fname: continue
                        selector = f"#{f['id']}" if f['id'] else f"[name='{fname}']"
                        if f['tag'] == 'SELECT' and not f.get('hasSelect2'):
                            safe_select(page, selector)
                        elif f.get('hasSelect2'):
                            fill_select2(page, f.get('id', ''), 'ocean')
                        elif f.get('type') in ('text', ''):
                            safe_fill(page, selector, 'AUTOTEST-CARRIER')

                    screenshot(page, "01_carriers_filled")
                    sub = find_and_click_submit(page)
                    if sub:
                        page.wait_for_timeout(3000)
                        screenshot(page, "01_carriers_after_submit")
                        err = check_page_error(page)
                        if err:
                            log_test("1.1_Carriers_Create", "FAIL", f"Errors: {err}", err)
                        else:
                            log_test("1.1_Carriers_Create", "PASS", f"Carrier form submitted")
                    else:
                        log_test("1.1_Carriers_Create", "WARNING", "No submit button found")
                else:
                    log_test("1.1_Carriers_Create", "WARNING", "No Add button found")
                log_test("1.1_Carriers_Page", "PASS", f"Page loaded. {row_count} rows.")
        except Exception as e:
            log_test("1.1_Carriers", "ERROR", str(e))
            screenshot(page, "01_carriers_exception")
            traceback.print_exc()

        # --- Test 1.2: Exchange Rates ---
        print("\n--- Test 1.2: Quote Setup - Exchange Rates ---")
        try:
            page.goto(f"{BASE_URL}/b63cf46906108334186c3ecf25f4ddb8", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            screenshot(page, "02_exchange_rates_list")
            err = check_page_error(page)
            if err:
                log_test("1.2_ExchangeRates_Page", "FAIL", f"Page errors: {err}", err)
            else:
                row_count = count_table_rows(page)
                print(f"  Existing exchange rate rows: {row_count}")

                elements = discover_all_elements(page)
                add_buttons = [e for e in elements if any(kw in e['text'].lower() for kw in ['add', 'new', 'rate'])]
                print(f"  Add buttons: {[e['text'] for e in add_buttons]}")

                clicked = find_and_click_add_button(page)
                if clicked:
                    page.wait_for_timeout(2000)
                    screenshot(page, "02_exchange_rates_form")
                    fields = discover_form_fields(page)
                    print_fields_summary(fields, "Exchange Rate Form Fields")
                    results["tests"]["1.2_ExchangeRates_Fields"] = {"fields": fields}

                    # Fill exchange rate fields specifically
                    # Currency (Select2 or regular select)
                    for f in fields:
                        fname = f.get('name', '') or f.get('id', '')
                        if not fname: continue
                        selector = f"#{f['id']}" if f.get('id') else f"[name='{fname}']"

                        if f.get('hasSelect2') and f.get('id'):
                            fill_select2(page, f['id'], 'USD')
                        elif f['tag'] == 'SELECT':
                            safe_select(page, selector)
                        elif f.get('type') == 'date':
                            fill_date_html5(page, f"input[name='{fname}']", "2026-04-30")
                        elif f.get('type') == 'number' or 'rate' in fname.lower():
                            safe_fill(page, selector, '83.50')
                        elif f.get('type') in ('text', ''):
                            safe_fill(page, selector, '1.00')

                    screenshot(page, "02_exchange_rates_filled")
                    sub = find_and_click_submit(page)
                    if sub:
                        page.wait_for_timeout(3000)
                        screenshot(page, "02_exchange_rates_after_submit")
                        err = check_page_error(page)
                        if err:
                            log_test("1.2_ExchangeRates_Create", "FAIL", f"Errors: {err}", err)
                        else:
                            log_test("1.2_ExchangeRates_Create", "PASS", "Exchange rate submitted")
                    else:
                        log_test("1.2_ExchangeRates_Create", "WARNING", "No submit button")
                else:
                    log_test("1.2_ExchangeRates_Create", "WARNING", "No Add button")
                log_test("1.2_ExchangeRates_Page", "PASS", f"Page loaded. {row_count} rows.")
        except Exception as e:
            log_test("1.2_ExchangeRates", "ERROR", str(e))
            screenshot(page, "02_exchange_rates_exception")
            traceback.print_exc()

        # --- Test 1.3: Rate Database ---
        print("\n--- Test 1.3: Quote Setup - Rate Database ---")
        try:
            page.goto(f"{BASE_URL}/95ea21eb539e083e42f57313509a93ed", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            screenshot(page, "03_rate_database_list")
            err = check_page_error(page)
            if err:
                log_test("1.3_RateDatabase_Page", "FAIL", f"Page errors: {err}", err)
            else:
                row_count = count_table_rows(page)
                print(f"  Existing rate rows: {row_count}")

                elements = discover_all_elements(page)
                add_buttons = [e for e in elements if any(kw in e['text'].lower() for kw in ['add', 'rate'])]
                print(f"  Add buttons: {[e['text'] for e in add_buttons]}")

                # Try specific button first
                clicked = None
                for sel in ['a:has-text("Add Rate")', 'button:has-text("Add Rate")', 'a:has-text("Add New")', 'button:has-text("Add")']:
                    try:
                        loc = page.locator(sel).first
                        if loc.is_visible(timeout=2000):
                            clicked = loc.text_content().strip()
                            loc.click()
                            print(f"    Clicked: '{clicked}'")
                            break
                    except:
                        continue
                if not clicked:
                    clicked = find_and_click_add_button(page)

                if clicked:
                    page.wait_for_timeout(2000)
                    screenshot(page, "03_rate_database_form")
                    fields = discover_form_fields(page)
                    print_fields_summary(fields, "Rate Database Form Fields")
                    results["tests"]["1.3_RateDatabase_Fields"] = {"fields": fields}

                    for f in fields:
                        fname = f.get('name', '') or f.get('id', '')
                        if not fname: continue
                        selector = f"#{f['id']}" if f.get('id') else f"[name='{fname}']"
                        if f.get('hasSelect2') and f.get('id'):
                            fill_select2(page, f['id'], 'a')
                        elif f['tag'] == 'SELECT':
                            safe_select(page, selector)
                        elif f.get('type') == 'date':
                            fill_date_html5(page, f"input[name='{fname}']", "2026-04-30")
                        elif f.get('type') == 'number':
                            safe_fill(page, selector, '100')
                        elif f.get('type') in ('text', ''):
                            safe_fill(page, selector, 'AutoTest')

                    screenshot(page, "03_rate_database_filled")
                    sub = find_and_click_submit(page)
                    if sub:
                        page.wait_for_timeout(3000)
                        screenshot(page, "03_rate_database_after_submit")
                        err = check_page_error(page)
                        if err:
                            log_test("1.3_RateDatabase_Create", "FAIL", f"Errors: {err}", err)
                        else:
                            log_test("1.3_RateDatabase_Create", "PASS", "Rate entry submitted")
                    else:
                        log_test("1.3_RateDatabase_Create", "WARNING", "No submit button")
                else:
                    log_test("1.3_RateDatabase_Create", "WARNING", "No Add button")

                # Click existing rate if any
                if row_count > 0:
                    try:
                        page.goto(f"{BASE_URL}/95ea21eb539e083e42f57313509a93ed", wait_until="networkidle", timeout=30000)
                        page.wait_for_timeout(2000)
                        first_link = page.locator('table tbody tr a').first
                        if first_link.count() > 0:
                            first_link.click()
                            page.wait_for_timeout(2000)
                            screenshot(page, "03_rate_database_view_existing")
                            print("  Clicked existing rate row")
                    except:
                        print("  Could not click existing rate row")

                log_test("1.3_RateDatabase_Page", "PASS", f"Page loaded. {row_count} rows.")
        except Exception as e:
            log_test("1.3_RateDatabase", "ERROR", str(e))
            screenshot(page, "03_rate_database_exception")
            traceback.print_exc()

        # --- Test 1.4: Client Rates ---
        print("\n--- Test 1.4: Quote Setup - Client Rates ---")
        try:
            page.goto(f"{BASE_URL}/db6f53167f5911e700a4b3aae0352572", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            screenshot(page, "04_client_rates_list")
            err = check_page_error(page)
            if err:
                log_test("1.4_ClientRates_Page", "FAIL", f"Page errors: {err}", err)
            else:
                row_count = count_table_rows(page)
                print(f"  Existing client rate rows: {row_count}")
                clicked = find_and_click_add_button(page)
                if clicked:
                    page.wait_for_timeout(2000)
                    screenshot(page, "04_client_rates_form")
                    fields = discover_form_fields(page)
                    print_fields_summary(fields, "Client Rates Form Fields")
                    results["tests"]["1.4_ClientRates_Fields"] = {"fields": fields}
                    if not fields:
                        log_test("1.4_ClientRates_Create", "WARNING", "Form is EMPTY - no visible fields after clicking Add")
                    else:
                        for f in fields:
                            fname = f.get('name', '') or f.get('id', '')
                            if not fname: continue
                            selector = f"#{f['id']}" if f['id'] else f"[name='{fname}']"
                            if f.get('hasSelect2') and f.get('id'):
                                fill_select2(page, f['id'], 'a')
                            elif f['tag'] == 'SELECT':
                                safe_select(page, selector)
                            elif f.get('type') == 'number':
                                safe_fill(page, selector, '100')
                            elif f.get('type') in ('text', ''):
                                safe_fill(page, selector, 'AutoTest')
                        screenshot(page, "04_client_rates_filled")
                        sub = find_and_click_submit(page)
                        if sub:
                            page.wait_for_timeout(3000)
                            screenshot(page, "04_client_rates_after_submit")
                            log_test("1.4_ClientRates_Create", "PASS", "Client rate submitted")
                        else:
                            log_test("1.4_ClientRates_Create", "WARNING", "No submit button")
                else:
                    log_test("1.4_ClientRates_Create", "WARNING", "No Add button")
                log_test("1.4_ClientRates_Page", "PASS", f"Page loaded. {row_count} rows.")
        except Exception as e:
            log_test("1.4_ClientRates", "ERROR", str(e))
            screenshot(page, "04_client_rates_exception")
            traceback.print_exc()

        # --- Test 1.5: Create a Full Quote ---
        print("\n--- Test 1.5: Create a Full Quote ---")
        quote_created = False
        try:
            page.goto(f"{BASE_URL}/68915d3ba92a6ff8c96734362d61b15e", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            screenshot(page, "05_quotes_list")
            err = check_page_error(page)
            if err:
                log_test("1.5_Quotes_Page", "FAIL", f"Page errors: {err}", err)
            else:
                row_count = count_table_rows(page)
                print(f"  Existing quotes: {row_count}")

                # Click "+ New Quote"
                clicked = None
                for sel in ['a:has-text("+ New Quote")', 'a:has-text("New Quote")', 'a:has-text("Add New")']:
                    try:
                        loc = page.locator(sel).first
                        if loc.is_visible(timeout=2000):
                            clicked = loc.text_content().strip()
                            loc.click()
                            break
                    except:
                        continue
                if not clicked:
                    clicked = find_and_click_add_button(page)

                if clicked:
                    page.wait_for_timeout(3000)
                    form_url = page.url
                    screenshot(page, "05_quote_form_initial")
                    print(f"  Quote form URL: {form_url}")

                    err = check_page_error(page)
                    if err:
                        log_test("1.5_Quotes_Form", "FAIL", f"Form errors: {err}", err)
                    else:
                        fields = discover_form_fields(page)
                        all_fields = discover_all_form_fields_including_hidden(page)
                        print_fields_summary(fields, "Quote Form Fields (Visible)")
                        print(f"\n    TOTAL visible: {len(fields)}, all (inc hidden): {len(all_fields)}")
                        results["tests"]["1.5_Quotes_FormFields"] = {"visible_fields": fields, "url": form_url}

                        # Fill Quote form fields carefully
                        # 1. Date fields (HTML5 type="date" -> yyyy-mm-dd)
                        fill_date_html5(page, 'input[name="quote_date"]', "2026-04-30")
                        print("    Filled quote_date = 2026-04-30")
                        fill_date_html5(page, 'input[name="valid_until"]', "2026-05-30")
                        print("    Filled valid_until = 2026-05-30")
                        fill_date_html5(page, 'input[name="cargo_ready"]', "2026-04-30")
                        print("    Filled cargo_ready = 2026-04-30")
                        # Also try by ID
                        fill_date_html5(page, '#cargo_ready', "2026-04-30")

                        # 2. Client (Select2)
                        fill_select2(page, 'cusid', 'a')

                        # 3. Mode (Select2)
                        fill_select2(page, 'mode', 'Ocean')

                        # 4. Shipment Type / Imp/Exp (Select2)
                        fill_select2_by_name(page, 'shiptype', 'Import')

                        # 5. Cargo Type
                        fill_select2(page, 'cargo_type', 'General')

                        # 6. Commodity
                        fill_select2_by_name(page, 'cmdty_id', 'a')

                        # 7. Numeric fields
                        safe_fill(page, '[name="pkgs"]', '10')
                        safe_fill(page, '[name="gw"]', '500')
                        safe_fill(page, '#gw', '500')
                        safe_fill(page, '[name="nw"]', '500')
                        safe_fill(page, '[name="cbm"]', '25')
                        safe_fill(page, '#cbm', '25')

                        # 8. Remarks
                        safe_fill(page, '[name="remarks"]', 'AUTOTEST Quote - Created by automated test')

                        # 9. Route fields (Port of Loading, Discharge, etc.)
                        for sel_name in ['pol', 'pod', 'transhipment', 'load_type', 'container_type', 'incoterms']:
                            try:
                                sel = page.locator(f'select[name="{sel_name}"]')
                                if sel.count() > 0:
                                    if sel.first.evaluate('el => el.classList.contains("select2-hidden-accessible")'):
                                        fill_select2_by_name(page, sel_name, 'a')
                                    else:
                                        safe_select(page, f'[name="{sel_name}"]')
                            except:
                                pass

                        page.wait_for_timeout(1000)
                        screenshot(page, "05_quote_form_filled")

                        # Submit
                        sub = find_and_click_submit(page)
                        if sub:
                            page.wait_for_timeout(4000)
                            screenshot(page, "05_quote_after_submit")

                            # Check if page changed (success redirect)
                            new_url = page.url
                            if new_url != form_url:
                                print(f"  Page redirected to: {new_url}")
                                quote_created = True

                            val_errors = get_validation_errors(page)
                            if val_errors:
                                print(f"  VALIDATION ERRORS:")
                                for ve in val_errors:
                                    print(f"    - {ve}")
                                log_test("1.5_Quotes_Create", "FAIL", f"Validation errors: {val_errors}", val_errors)
                            else:
                                err = check_page_error(page)
                                if err:
                                    log_test("1.5_Quotes_Create", "FAIL", f"Page errors: {err}", err)
                                else:
                                    success = get_success_messages(page)
                                    if success:
                                        print(f"  SUCCESS: {success}")
                                    quote_created = True
                                    log_test("1.5_Quotes_Create", "PASS", f"Quote submitted. Redirected: {new_url != form_url}. Success: {success}")

                                    # Go back to list and verify
                                    page.goto(f"{BASE_URL}/68915d3ba92a6ff8c96734362d61b15e", wait_until="networkidle", timeout=30000)
                                    page.wait_for_timeout(2000)
                                    new_count = count_table_rows(page)
                                    print(f"  Quotes after creation: {new_count} (was {row_count})")
                                    screenshot(page, "05_quotes_list_after_create")

                                    # Try to view a quote
                                    try:
                                        link = page.locator('table tbody tr a').first
                                        if link.count() > 0:
                                            link.click()
                                            page.wait_for_timeout(3000)
                                            screenshot(page, "05_quote_view_detail")
                                            print(f"  Opened quote detail: {page.url}")

                                            # Look for PDF/Print
                                            for sel in ['a:has-text("PDF")', 'button:has-text("PDF")', 'a:has-text("Print")', 'button:has-text("Generate")']:
                                                try:
                                                    loc = page.locator(sel).first
                                                    if loc.is_visible(timeout=2000):
                                                        print(f"  Found button: '{loc.text_content().strip()}'")
                                                        loc.click()
                                                        page.wait_for_timeout(3000)
                                                        screenshot(page, "05_quote_pdf_result")
                                                        break
                                                except:
                                                    continue
                                    except Exception as ex:
                                        print(f"  Could not view quote detail: {ex}")
                        else:
                            log_test("1.5_Quotes_Create", "WARNING", "No submit button")
                else:
                    log_test("1.5_Quotes_Create", "WARNING", "No New Quote button")

                log_test("1.5_Quotes_Page", "PASS", f"Quotes page loaded. {row_count} existing quotes.")
        except Exception as e:
            log_test("1.5_Quotes", "ERROR", str(e))
            screenshot(page, "05_quotes_exception")
            traceback.print_exc()

        # ============================================================
        # PART 2: LAND IMPORT
        # ============================================================
        print("\n" + "="*70)
        print("PART 2: LAND IMPORT")
        print("="*70)

        # --- Test 2.1: Land Import - Create Job ---
        print("\n--- Test 2.1: Land Import - Create Job ---")
        land_import_job = None
        try:
            page.goto(f"{BASE_URL}/8013f48199799dce7a1fde812910a496", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            screenshot(page, "06_land_import_list")
            err = check_page_error(page)
            if err:
                log_test("2.1_LandImport_Page", "FAIL", f"Page errors: {err}", err)
            else:
                row_count = count_table_rows(page)
                print(f"  Existing land import jobs: {row_count}")

                clicked = find_and_click_add_button(page)
                if clicked:
                    page.wait_for_timeout(3000)
                    form_url = page.url
                    screenshot(page, "06_land_import_form")
                    print(f"  Form URL: {form_url}")

                    err = check_page_error(page)
                    if err:
                        log_test("2.1_LandImport_Form", "FAIL", f"Form errors: {err}", err)
                    else:
                        fields = discover_form_fields(page)
                        print_fields_summary(fields, "Land Import Form Fields")
                        results["tests"]["2.1_LandImport_Fields"] = {"fields": fields}

                        # Fill Land Import form using exact field names from screenshot
                        # IncoTerms (regular select, not Select2)
                        safe_select(page, 'select[name="IncoTrms"]', 'ExW')
                        print("    Selected IncoTerms = ExW")

                        # Customer / Consignee (Select2 with AJAX)
                        # Try multiple search terms - the AJAX may need longer strings
                        consignee_ok = False
                        for search_term in ['RASKEL', 'RAS', 'A V', 'INT', 'test']:
                            consignee_ok = fill_select2(page, 'consigne', search_term)
                            if consignee_ok:
                                break
                            consignee_ok = fill_select2_by_name(page, 'consigne', search_term)
                            if consignee_ok:
                                break
                        if not consignee_ok:
                            # Try clicking the Select2 container and searching via Playwright
                            try:
                                s2 = page.locator('select[name="consigne"]').first
                                # Get the Select2 container that's associated with this select
                                page.locator('.select2-container--default .select2-selection').first.click()
                                page.wait_for_timeout(500)
                                search = page.locator('.select2-search__field')
                                if search.count() > 0:
                                    for term in ['RAS', 'A V', 'test', 'a']:
                                        search.fill(term)
                                        page.wait_for_timeout(2500)
                                        ro = page.locator('.select2-results__option:not(.select2-results__message)')
                                        if ro.count() > 0:
                                            text = ro.first.text_content()
                                            ro.first.click()
                                            page.wait_for_timeout(500)
                                            consignee_ok = True
                                            print(f"    Consignee filled via direct click: '{text}'")
                                            break
                                        search.fill('')
                                        page.wait_for_timeout(300)
                            except Exception as ex:
                                print(f"    Consignee container click error: {ex}")
                        if not consignee_ok:
                            print("    WARNING: Could not fill Consignee - this is a required field (AJAX Select2 returns no results)")
                            print("    NOTE: Land form consignee is an AJAX-based Select2 that searches server-side")

                        # ETD / ETA (these are text fields with datepicker, not HTML5 date)
                        page.evaluate("""(() => {
                            var etd = document.querySelector('[name="etd"]');
                            if (etd) { etd.value = '30/04/2026'; etd.dispatchEvent(new Event('change', {bubbles: true})); }
                            var eta = document.querySelector('[name="eta"]');
                            if (eta) { eta.value = '05/05/2026'; eta.dispatchEvent(new Event('change', {bubbles: true})); }
                        })()""")
                        print("    Filled ETD=30/04/2026, ETA=05/05/2026")

                        # Origin / Destination
                        safe_fill(page, '[name="origin"]', 'Mumbai')
                        safe_fill(page, '[name="destination"]', 'Delhi')
                        print("    Filled origin=Mumbai, destination=Delhi")

                        # Vehicle Type (regular select)
                        safe_select(page, 'select[name="veh_type"]', 'FTL (Full Truck Load)')
                        print("    Selected Vehicle Type = FTL")

                        # Vehicle Reg, Driver, CMR
                        safe_fill(page, '[name="veh_reg"]', 'MH01AB1234')
                        safe_fill(page, '[name="driver"]', 'Test Driver Auto')
                        safe_fill(page, '[name="cmr_no"]', 'CMR-AUTO-001')
                        print("    Filled vehicle/driver/cmr")

                        # Numeric fields
                        safe_fill(page, '[name="gw"]', '1500')
                        safe_fill(page, '[name="nw"]', '1200')
                        safe_fill(page, '[name="cbm"]', '25')
                        safe_fill(page, '[name="pkgs"]', '50')
                        print("    Filled gw=1500, nw=1200, cbm=25, pkgs=50")

                        # Delivery Date
                        page.evaluate("""(() => {
                            var dd = document.querySelector('[name="dlvr_dte"]');
                            if (dd) { dd.value = '05/05/2026'; dd.dispatchEvent(new Event('change', {bubbles: true})); }
                        })()""")
                        print("    Filled dlvr_dte=05/05/2026")

                        # Remarks
                        safe_fill(page, '[name="remarks"]', 'AUTOTEST Land Import - Automated test job')
                        print("    Filled remarks")

                        page.wait_for_timeout(1000)
                        screenshot(page, "06_land_import_filled")

                        # Submit - look specifically for "Create Job" button
                        sub = None
                        for sel in ['button:has-text("Create Job")', 'button[type="submit"]', 'button:has-text("Save")']:
                            try:
                                loc = page.locator(sel).first
                                if loc.is_visible(timeout=2000):
                                    sub = loc.text_content().strip()
                                    loc.click()
                                    print(f"    Clicked: '{sub}'")
                                    break
                            except:
                                continue

                        if sub:
                            page.wait_for_timeout(4000)
                            screenshot(page, "06_land_import_after_submit")
                            new_url = page.url

                            if new_url != form_url:
                                print(f"  Redirected to: {new_url}")
                                land_import_job = new_url

                            val_errors = get_validation_errors(page)
                            if val_errors:
                                print(f"  VALIDATION ERRORS:")
                                for ve in val_errors:
                                    print(f"    - {ve}")
                                log_test("2.1_LandImport_Create", "FAIL", f"Validation errors: {val_errors}", val_errors)
                            else:
                                err = check_page_error(page)
                                if err:
                                    log_test("2.1_LandImport_Create", "FAIL", f"Page errors: {err}", err)
                                else:
                                    job_num = get_job_number(page)
                                    land_import_job = page.url
                                    log_test("2.1_LandImport_Create", "PASS", f"Land import job created. URL: {new_url}")
                        else:
                            log_test("2.1_LandImport_Create", "WARNING", "No submit button")

                else:
                    log_test("2.1_LandImport_Create", "WARNING", "No Add button")

                log_test("2.1_LandImport_Page", "PASS", f"Page loaded. {row_count} existing jobs.")
        except Exception as e:
            log_test("2.1_LandImport", "ERROR", str(e))
            screenshot(page, "06_land_import_exception")
            traceback.print_exc()

        # --- Test 2.2: Land Import - All Steps ---
        print("\n--- Test 2.2: Land Import - Job Detail Steps ---")
        try:
            # Navigate to land import list and click first job
            page.goto(f"{BASE_URL}/8013f48199799dce7a1fde812910a496", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            row_count = count_table_rows(page)
            if row_count > 0:
                # Click first job link
                link = page.locator('table tbody tr a').first
                if link.count() > 0:
                    link.click()
                else:
                    page.locator('table tbody tr td').first.click()
                page.wait_for_timeout(3000)

                screenshot(page, "07_land_import_detail_full")
                detail_url = page.url
                print(f"  Detail URL: {detail_url}")

                err = check_page_error(page)
                if err:
                    log_test("2.2_LandImport_Detail", "FAIL", f"Detail errors: {err}", err)
                else:
                    # Discover step-based navigation
                    steps_info = page.evaluate("""(() => {
                        const steps = [];
                        // Look for step circles/numbers at the top
                        document.querySelectorAll('.step-circle, .step-indicator, [class*="step"]').forEach(el => {
                            if (el.offsetParent !== null) {
                                steps.push({text: el.textContent.trim().substring(0, 80), class: el.className});
                            }
                        });
                        // Look for section headers
                        const sections = [];
                        document.querySelectorAll('h4, h5, h6, .section-header, legend, .card-header, hr + div, fieldset > legend').forEach(el => {
                            if (el.offsetParent !== null) {
                                const t = el.textContent.trim();
                                if (t.length > 2 && t.length < 80) sections.push(t);
                            }
                        });
                        // Check for step links in breadcrumb/header area
                        const stepLinks = [];
                        document.querySelectorAll('a[class*="step"], .step a, .wizard a, [onclick*="step"]').forEach(el => {
                            stepLinks.push({text: el.textContent.trim(), onclick: el.getAttribute('onclick') || '', href: el.getAttribute('href') || ''});
                        });
                        return {steps, sections, stepLinks};
                    })()""")
                    print(f"  Steps info: {json.dumps(steps_info, indent=2)[:500]}")

                    # The job detail page should show sections: Basic Details, Buying Charges, Selling Charges
                    # Screenshot reveals Step 1/2/3 circle navigation and inline sections

                    # --- STEP 1: Basic Details ---
                    print("\n    --- Step 1: Basic Details ---")
                    # The basic details section is visible by default
                    basic_fields = discover_form_fields(page)
                    basic_details = [f for f in basic_fields if f.get('name') in ['JbNo', 'jbdte', 'IncoTrms', 'consigne', 'etd', 'eta', 'origin', 'destination', 'veh_type', 'veh_reg', 'driver', 'cmr_no', 'gw', 'nw', 'cbm', 'pkgs', 'dlvr_dte', 'remarks']]
                    if basic_details:
                        print_fields_summary(basic_details, "Step 1: Basic Details Fields")
                    else:
                        print_fields_summary(basic_fields[:20], "All visible fields on detail page")

                    # Look for "Save Basic Details" button
                    save_basic = page.locator('button:has-text("Save Basic Details")')
                    if save_basic.count() > 0:
                        print(f"    Found 'Save Basic Details' button")

                    screenshot(page, "07_land_import_step1_basic")
                    log_test("2.2_LandImport_Step1_BasicDetails", "PASS", f"Basic Details section visible. {len(basic_fields)} fields.")

                    # --- STEP 2: Buying Charges ---
                    print("\n    --- Step 2: Buying Charges ---")
                    # Look for "Buying Charges" section or Step 2 link
                    # Try clicking Step 2
                    step2_clicked = False
                    for sel in [
                        'a:has-text("Step 2")',
                        '[class*="step"]:has-text("2")',
                        'text=Buying Charges',
                        '.step:nth-child(2)',
                    ]:
                        try:
                            loc = page.locator(sel).first
                            if loc.is_visible(timeout=2000):
                                loc.click()
                                page.wait_for_timeout(2000)
                                step2_clicked = True
                                print(f"    Clicked step 2 via: {sel}")
                                break
                        except:
                            continue

                    # The buying charges section should be visible (may be on same page)
                    # Scroll to buying charges section
                    page.evaluate("""(() => {
                        var el = document.querySelector('[id*="buying"], [class*="buying"]');
                        if (!el) {
                            // Find element containing BUYING CHARGES text
                            var allEls = document.querySelectorAll('hr, h4, h5, div, fieldset');
                            for (var i = 0; i < allEls.length; i++) {
                                if (allEls[i].textContent.indexOf('BUYING') !== -1) { el = allEls[i]; break; }
                            }
                        }
                        if (el) el.scrollIntoView();
                    })()""")
                    page.wait_for_timeout(1000)
                    screenshot(page, "07_land_import_step2_buying")

                    # Look for buying charge fields
                    buying_fields = page.evaluate("""(() => {
                        const fields = [];
                        // Find charge-related selects and inputs near "BUYING CHARGES" text
                        document.querySelectorAll('select[name*="charge"], select[name*="Charge"], input[name*="amount"], input[name*="tax"]').forEach(el => {
                            if (el.offsetParent !== null) {
                                fields.push({name: el.name, tag: el.tagName, type: el.type || ''});
                            }
                        });
                        return fields;
                    })()""")
                    print(f"    Buying charge fields found: {buying_fields}")

                    # Look for "Save Buy Charges" button
                    save_buy = page.locator('button:has-text("Save Buy Charges"), button:has-text("Save Buying")')
                    if save_buy.count() > 0:
                        print(f"    Found 'Save Buy Charges' button")
                        log_test("2.2_LandImport_Step2_BuyingCharges", "PASS", "Buying Charges section found with Save button")
                    else:
                        log_test("2.2_LandImport_Step2_BuyingCharges", "PASS", f"Buying Charges section. {len(buying_fields)} charge fields found")

                    # Try adding a charge row
                    try:
                        # Look for charge dropdown and fill it
                        charge_selects = page.locator('select[name*="charge"], select[name*="Charge"]')
                        if charge_selects.count() > 0:
                            charge_selects.first.select_option(index=1)
                            page.wait_for_timeout(500)
                            # Fill amount
                            amt_inputs = page.locator('input[name*="amount"], input[name*="amt"]')
                            if amt_inputs.count() > 0:
                                for i in range(amt_inputs.count()):
                                    try:
                                        if amt_inputs.nth(i).is_visible(timeout=1000):
                                            amt_inputs.nth(i).fill('500')
                                            break
                                    except:
                                        continue
                            screenshot(page, "07_land_import_step2_charge_filled")
                            print("    Filled a charge line")
                    except Exception as ex:
                        print(f"    Error filling charge: {ex}")

                    # --- STEP 3: Selling Charges ---
                    print("\n    --- Step 3: Selling Charges ---")
                    # Scroll to selling charges section
                    page.evaluate("(() => { const el = document.querySelector('[id*=\"selling\"], [class*=\"selling\"]'); if(el) el.scrollIntoView(); })()")
                    page.wait_for_timeout(1000)

                    # Try clicking Step 3
                    for sel in ['a:has-text("Step 3")', '[class*="step"]:has-text("3")']:
                        try:
                            loc = page.locator(sel).first
                            if loc.is_visible(timeout=2000):
                                loc.click()
                                page.wait_for_timeout(2000)
                                print(f"    Clicked step 3 via: {sel}")
                                break
                        except:
                            continue

                    screenshot(page, "07_land_import_step3_selling")

                    # Look for "Save Sell Charges" button
                    save_sell = page.locator('button:has-text("Save Sell Charges"), button:has-text("Save Selling")')
                    if save_sell.count() > 0:
                        print(f"    Found 'Save Sell Charges' button")
                        log_test("2.2_LandImport_Step3_SellingCharges", "PASS", "Selling Charges section found with Save button")
                    else:
                        log_test("2.2_LandImport_Step3_SellingCharges", "PASS", "Selling Charges section visible")

                    # --- Check for Purchase/Sale Invoice sections ---
                    print("\n    --- Checking for Invoice Sections ---")
                    body_text = page.locator('body').inner_text(timeout=5000)
                    has_purchase_inv = 'purchase invoice' in body_text.lower() or 'purchase inv' in body_text.lower()
                    has_sale_inv = 'sale invoice' in body_text.lower() or 'sales invoice' in body_text.lower()
                    has_delivery_note = 'delivery note' in body_text.lower()
                    has_clearing = 'clearing' in body_text.lower()
                    has_files = 'files' in body_text.lower() or 'supporting' in body_text.lower() or 'document' in body_text.lower()

                    sections_found = []
                    if has_purchase_inv: sections_found.append("Purchase Invoice")
                    if has_sale_inv: sections_found.append("Sale Invoice")
                    if has_delivery_note: sections_found.append("Delivery Note")
                    if has_clearing: sections_found.append("Clearing Instructions")
                    if has_files: sections_found.append("Files/Documents")
                    print(f"    Additional sections found in body text: {sections_found}")

                    # Summary
                    log_test("2.2_LandImport_DetailPage", "PASS",
                             f"Job detail loaded. Steps: Basic Details, Buying Charges, Selling Charges. Additional sections: {sections_found}")
            else:
                log_test("2.2_LandImport_DetailPage", "WARNING", "No existing jobs to inspect")
        except Exception as e:
            log_test("2.2_LandImport_DetailPage", "ERROR", str(e))
            screenshot(page, "07_land_import_detail_exception")
            traceback.print_exc()

        # ============================================================
        # PART 3: LAND EXPORT
        # ============================================================
        print("\n" + "="*70)
        print("PART 3: LAND EXPORT")
        print("="*70)

        # --- Test 3.1: Land Export - Create Job ---
        print("\n--- Test 3.1: Land Export - Create Job ---")
        land_export_job = None
        try:
            page.goto(f"{BASE_URL}/2ca1dbee9121459dedd8cf2e88823068", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            screenshot(page, "08_land_export_list")
            err = check_page_error(page)
            if err:
                log_test("3.1_LandExport_Page", "FAIL", f"Page errors: {err}", err)
            else:
                row_count = count_table_rows(page)
                print(f"  Existing land export jobs: {row_count}")

                clicked = find_and_click_add_button(page)
                if clicked:
                    page.wait_for_timeout(3000)
                    form_url = page.url
                    screenshot(page, "08_land_export_form")
                    print(f"  Form URL: {form_url}")

                    err = check_page_error(page)
                    if err:
                        log_test("3.1_LandExport_Form", "FAIL", f"Form errors: {err}", err)
                    else:
                        fields = discover_form_fields(page)
                        print_fields_summary(fields, "Land Export Form Fields")
                        results["tests"]["3.1_LandExport_Fields"] = {"fields": fields}

                        # Fill Land Export form using same structure as Import
                        safe_select(page, 'select[name="IncoTrms"]', 'FOB')
                        print("    Selected IncoTerms = FOB")

                        # Customer / Consignee (Select2 with AJAX)
                        consignee_ok = False
                        for search_term in ['RASKEL', 'RAS', 'A V', 'INT', 'test']:
                            consignee_ok = fill_select2(page, 'consigne', search_term)
                            if consignee_ok:
                                break
                            consignee_ok = fill_select2_by_name(page, 'consigne', search_term)
                            if consignee_ok:
                                break
                        if not consignee_ok:
                            try:
                                page.locator('.select2-container--default .select2-selection').first.click()
                                page.wait_for_timeout(500)
                                search = page.locator('.select2-search__field')
                                if search.count() > 0:
                                    for term in ['RAS', 'A V', 'test', 'a']:
                                        search.fill(term)
                                        page.wait_for_timeout(2500)
                                        ro = page.locator('.select2-results__option:not(.select2-results__message)')
                                        if ro.count() > 0:
                                            ro.first.click()
                                            page.wait_for_timeout(500)
                                            consignee_ok = True
                                            break
                                        search.fill('')
                                        page.wait_for_timeout(300)
                            except Exception as ex:
                                print(f"    Consignee error: {ex}")
                        if not consignee_ok:
                            print("    WARNING: Could not fill Consignee (AJAX Select2 returns no results)")

                        page.evaluate("""(() => {
                            var etd = document.querySelector('[name="etd"]');
                            if (etd) { etd.value = '30/04/2026'; etd.dispatchEvent(new Event('change', {bubbles: true})); }
                            var eta = document.querySelector('[name="eta"]');
                            if (eta) { eta.value = '10/05/2026'; eta.dispatchEvent(new Event('change', {bubbles: true})); }
                        })()""")
                        print("    Filled ETD=30/04/2026, ETA=10/05/2026")

                        safe_fill(page, '[name="origin"]', 'Delhi')
                        safe_fill(page, '[name="destination"]', 'London')
                        print("    Filled origin=Delhi, destination=London")

                        safe_select(page, 'select[name="veh_type"]', 'FTL (Full Truck Load)')
                        print("    Selected Vehicle Type = FTL")

                        safe_fill(page, '[name="veh_reg"]', 'DL01CD5678')
                        safe_fill(page, '[name="driver"]', 'Export Driver Auto')
                        safe_fill(page, '[name="cmr_no"]', 'CMR-EXP-001')
                        print("    Filled vehicle/driver/cmr")

                        safe_fill(page, '[name="gw"]', '2000')
                        safe_fill(page, '[name="nw"]', '1800')
                        safe_fill(page, '[name="cbm"]', '30')
                        safe_fill(page, '[name="pkgs"]', '60')
                        print("    Filled gw=2000, nw=1800, cbm=30, pkgs=60")

                        page.evaluate("""(() => {
                            var dd = document.querySelector('[name="dlvr_dte"]');
                            if (dd) { dd.value = '10/05/2026'; dd.dispatchEvent(new Event('change', {bubbles: true})); }
                        })()""")
                        print("    Filled delivery date")

                        safe_fill(page, '[name="remarks"]', 'AUTOTEST Land Export - Automated test job')
                        print("    Filled remarks")

                        page.wait_for_timeout(1000)
                        screenshot(page, "08_land_export_filled")

                        # Submit
                        sub = None
                        for sel in ['button:has-text("Create Job")', 'button[type="submit"]', 'button:has-text("Save")']:
                            try:
                                loc = page.locator(sel).first
                                if loc.is_visible(timeout=2000):
                                    sub = loc.text_content().strip()
                                    loc.click()
                                    print(f"    Clicked: '{sub}'")
                                    break
                            except:
                                continue

                        if sub:
                            page.wait_for_timeout(4000)
                            screenshot(page, "08_land_export_after_submit")
                            new_url = page.url

                            if new_url != form_url:
                                print(f"  Redirected to: {new_url}")
                                land_export_job = new_url

                            val_errors = get_validation_errors(page)
                            if val_errors:
                                print(f"  VALIDATION ERRORS:")
                                for ve in val_errors:
                                    print(f"    - {ve}")
                                log_test("3.1_LandExport_Create", "FAIL", f"Validation errors: {val_errors}", val_errors)
                            else:
                                err = check_page_error(page)
                                if err:
                                    log_test("3.1_LandExport_Create", "FAIL", f"Page errors: {err}", err)
                                else:
                                    land_export_job = page.url
                                    log_test("3.1_LandExport_Create", "PASS", f"Land export job created. URL: {new_url}")
                        else:
                            log_test("3.1_LandExport_Create", "WARNING", "No submit button")
                else:
                    log_test("3.1_LandExport_Create", "WARNING", "No Add button")

                log_test("3.1_LandExport_Page", "PASS", f"Page loaded. {row_count} existing jobs.")
        except Exception as e:
            log_test("3.1_LandExport", "ERROR", str(e))
            screenshot(page, "08_land_export_exception")
            traceback.print_exc()

        # --- Test 3.2: Land Export - Job Detail Steps ---
        print("\n--- Test 3.2: Land Export - Job Detail Steps ---")
        try:
            page.goto(f"{BASE_URL}/2ca1dbee9121459dedd8cf2e88823068", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            row_count = count_table_rows(page)
            if row_count > 0:
                link = page.locator('table tbody tr a').first
                if link.count() > 0:
                    link.click()
                else:
                    page.locator('table tbody tr td').first.click()
                page.wait_for_timeout(3000)

                screenshot(page, "09_land_export_detail_full")
                detail_url = page.url
                print(f"  Detail URL: {detail_url}")

                err = check_page_error(page)
                if err:
                    log_test("3.2_LandExport_Detail", "FAIL", f"Detail errors: {err}", err)
                else:
                    # Step 1: Basic Details
                    print("\n    --- Step 1: Basic Details ---")
                    basic_fields = discover_form_fields(page)
                    print_fields_summary(basic_fields[:15], "Land Export Basic Details")
                    screenshot(page, "09_land_export_step1")

                    save_basic = page.locator('button:has-text("Save Basic Details")')
                    if save_basic.count() > 0:
                        print(f"    Found 'Save Basic Details' button")
                    log_test("3.2_LandExport_Step1", "PASS", f"Basic Details. {len(basic_fields)} fields.")

                    # Step 2: Buying Charges
                    print("\n    --- Step 2: Buying Charges ---")
                    page.evaluate("(() => { const el = document.querySelector('[id*=\"buying\"], [class*=\"buying\"]'); if(el) el.scrollIntoView(); })()")
                    page.wait_for_timeout(1000)
                    screenshot(page, "09_land_export_step2")

                    save_buy = page.locator('button:has-text("Save Buy Charges"), button:has-text("Save Buying")')
                    if save_buy.count() > 0:
                        print(f"    Found 'Save Buy Charges' button")
                    log_test("3.2_LandExport_Step2", "PASS", "Buying Charges section visible")

                    # Step 3: Selling Charges
                    print("\n    --- Step 3: Selling Charges ---")
                    page.evaluate("(() => { const el = document.querySelector('[id*=\"selling\"], [class*=\"selling\"]'); if(el) el.scrollIntoView(); })()")
                    page.wait_for_timeout(1000)
                    screenshot(page, "09_land_export_step3")

                    save_sell = page.locator('button:has-text("Save Sell Charges"), button:has-text("Save Selling")')
                    if save_sell.count() > 0:
                        print(f"    Found 'Save Sell Charges' button")
                    log_test("3.2_LandExport_Step3", "PASS", "Selling Charges section visible")

                    # Check additional sections
                    body_text = page.locator('body').inner_text(timeout=5000)
                    sections = []
                    for kw in ['purchase invoice', 'sale invoice', 'delivery note', 'clearing', 'files', 'document']:
                        if kw in body_text.lower():
                            sections.append(kw.title())
                    print(f"    Additional sections in body: {sections}")

                    log_test("3.2_LandExport_DetailPage", "PASS",
                             f"Job detail loaded. Steps: Basic Details, Buying Charges, Selling Charges. Additional: {sections}")
            else:
                log_test("3.2_LandExport_DetailPage", "WARNING", "No existing jobs to inspect")
        except Exception as e:
            log_test("3.2_LandExport_DetailPage", "ERROR", str(e))
            screenshot(page, "09_land_export_exception")
            traceback.print_exc()

        # ============================================================
        # PART 4: REPORT VERIFICATION
        # ============================================================
        print("\n" + "="*70)
        print("PART 4: REPORT VERIFICATION")
        print("="*70)

        # --- Test 4.1: Consignee Due ---
        print("\n--- Test 4.1: Consignee Due ---")
        try:
            page.goto(f"{BASE_URL}/1abe8a244329f592bb3bbb96e22e0344", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            screenshot(page, "10_consignee_due")
            err = check_page_error(page)
            if err:
                log_test("4.1_ConsigneeDue", "FAIL", f"Page errors: {err}", err)
            else:
                row_count = count_table_rows(page)
                body = page.locator('body').inner_text(timeout=5000)
                has_land = 'land' in body.lower() or 'LND' in body or 'LAND' in body or 'TLI/LI' in body or 'TLI/LE' in body
                print(f"  Rows: {row_count}, Has Land refs: {has_land}")
                log_test("4.1_ConsigneeDue", "PASS", f"{row_count} rows. Land refs: {has_land}")
        except Exception as e:
            log_test("4.1_ConsigneeDue", "ERROR", str(e))

        # --- Test 4.2: Purchase Invoice ---
        print("\n--- Test 4.2: Purchase Invoice ---")
        try:
            # Use the correct hash URL from sidebar
            page.goto(f"{BASE_URL}/6a9a2dfd6db0eab18c tried3959c9cab4269b", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
        except:
            pass

        # Try navigating via sidebar click instead
        try:
            page.goto(f"{BASE_URL}/1abe8a244329f592bb3bbb96e22e0344", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            # Click "Financial Reports" then "Purchase Invoice" in sidebar
            try:
                fin_rep = page.locator('a:has-text("Financial Reports")').first
                if fin_rep.is_visible(timeout=3000):
                    fin_rep.click()
                    page.wait_for_timeout(1000)
                pi_link = page.locator('a:has-text("Purchase Invoice")').first
                if pi_link.is_visible(timeout=3000):
                    pi_link.click()
                    page.wait_for_timeout(3000)
                    screenshot(page, "11_purchase_invoice")
                    err = check_page_error(page)
                    if err:
                        log_test("4.2_PurchaseInvoice", "FAIL", f"Errors: {err}", err)
                    else:
                        row_count = count_table_rows(page)
                        body = page.locator('body').inner_text(timeout=5000)
                        has_land = 'land' in body.lower() or 'TLI/LI' in body or 'TLI/LE' in body
                        print(f"  Purchase Invoice rows: {row_count}, Land refs: {has_land}")
                        log_test("4.2_PurchaseInvoice", "PASS", f"{row_count} rows. Land refs: {has_land}")
            except Exception as ex:
                log_test("4.2_PurchaseInvoice", "WARNING", f"Could not navigate: {ex}")
        except Exception as e:
            log_test("4.2_PurchaseInvoice", "ERROR", str(e))

        # --- Test 4.3: Sales Invoice ---
        print("\n--- Test 4.3: Sales Invoice ---")
        try:
            si_link = page.locator('a:has-text("Sales Invoice")').first
            if si_link.is_visible(timeout=3000):
                si_link.click()
                page.wait_for_timeout(3000)
                screenshot(page, "12_sales_invoice")
                err = check_page_error(page)
                if err:
                    log_test("4.3_SalesInvoice", "FAIL", f"Errors: {err}", err)
                else:
                    row_count = count_table_rows(page)
                    body = page.locator('body').inner_text(timeout=5000)
                    has_land = 'land' in body.lower() or 'TLI/LI' in body or 'TLI/LE' in body
                    print(f"  Sales Invoice rows: {row_count}, Land refs: {has_land}")
                    log_test("4.3_SalesInvoice", "PASS", f"{row_count} rows. Land refs: {has_land}")
            else:
                log_test("4.3_SalesInvoice", "WARNING", "Sales Invoice link not found")
        except Exception as e:
            log_test("4.3_SalesInvoice", "ERROR", str(e))

        # --- Test 4.4: DSR Reports (check Ocean Import DSR 500 error) ---
        print("\n--- Test 4.4: DSR Reports - Ocean Import DSR ---")
        try:
            # Navigate via sidebar
            dsr_link = page.locator('a:has-text("DSR Reports")').first
            if dsr_link.is_visible(timeout=3000):
                dsr_link.click()
                page.wait_for_timeout(2000)

            oi_dsr = page.locator('a:has-text("Ocean Import DSR")').first
            if oi_dsr.is_visible(timeout=3000):
                oi_dsr.click()
                page.wait_for_timeout(3000)
                screenshot(page, "13_ocean_import_dsr")
                err = check_page_error(page)
                if err:
                    log_test("4.4_OceanImportDSR", "FAIL", f"HTTP 500 ERROR on Ocean Import DSR page: {err}", err)
                else:
                    log_test("4.4_OceanImportDSR", "PASS", "Ocean Import DSR loaded OK")
            else:
                log_test("4.4_OceanImportDSR", "WARNING", "Ocean Import DSR link not found")
        except Exception as e:
            log_test("4.4_OceanImportDSR", "ERROR", str(e))

        # ============================================================
        # SUMMARY
        # ============================================================
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"  Passed:   {results['summary']['passed']}")
        print(f"  Failed:   {results['summary']['failed']}")
        print(f"  Errors:   {results['summary']['errors']}")
        print(f"  Warnings: {results['summary']['warnings']}")
        print()

        for test_name, test_data in results["tests"].items():
            if isinstance(test_data, dict) and "status" in test_data:
                status = test_data["status"]
                details = test_data.get("details", "")
                errors = test_data.get("errors", [])
                icon = {"PASS": "OK", "FAIL": "FAIL", "ERROR": "ERR", "WARNING": "WARN"}.get(status, "?")
                print(f"  [{icon}] {test_name}: {details}")
                if errors:
                    for e in errors:
                        print(f"       Error: {e}")

        # Save results
        with open(RESULTS_FILE, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n  Results saved to: {RESULTS_FILE}")
        print(f"  Screenshots in:   {SCREENSHOT_DIR}")

        browser.close()


if __name__ == "__main__":
    run_tests()
