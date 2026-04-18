"""
Sena ERP - Job Creation, Reports, and Account Pages Test Script
Tests job creation workflows, financial reports, booking reports, closed jobs,
quotes, account pages, HR employee, and DSR reports.
"""

import asyncio
import json
import os
import time
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "http://13.210.47.18:8088"
SCREENSHOT_DIR = "/var/lib/freelancer/projects/40298427/erp-test/screenshots/jobs_reports"
RESULTS_FILE = "/var/lib/freelancer/projects/40298427/erp-test/results_jobs_reports.json"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

results = {
    "test_run": datetime.now().isoformat(),
    "base_url": BASE_URL,
    "parts": {}
}

def save_results():
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2, default=str)

async def login(page):
    print("[LOGIN] Navigating to login page...")
    await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)
    await page.screenshot(path=f"{SCREENSHOT_DIR}/00_login_page.png", full_page=False)

    await page.evaluate('''() => {
        document.getElementById("username").value = "superadmin";
        document.getElementById("password").value = "Nick@#24";
        document.getElementById("signupForm").submit();
    }''')
    print("[LOGIN] Submitted credentials, waiting 8 seconds...")
    await page.wait_for_timeout(8000)
    await page.screenshot(path=f"{SCREENSHOT_DIR}/00_after_login.png", full_page=False)
    print("[LOGIN] Login complete.")

async def check_page_status(page, url, name):
    """Navigate to page and check if it loads or returns 404/error."""
    try:
        resp = await page.goto(f"{BASE_URL}{url}", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)
        status = resp.status if resp else "unknown"

        body_text = await page.evaluate("() => document.body ? document.body.innerText.substring(0, 500) : ''")
        is_404 = status == 404 or "404" in body_text or "not found" in body_text.lower() or "Cannot GET" in body_text
        is_error = status >= 400 or "error" in body_text.lower()[:100]

        return {
            "status": status,
            "is_404": is_404,
            "is_error": is_error and not is_404,
            "body_preview": body_text[:200]
        }
    except Exception as e:
        return {"status": "error", "is_404": False, "is_error": True, "body_preview": str(e)}

async def discover_form_fields(page):
    """Discover all visible form fields on the page."""
    fields = await page.evaluate('''() => {
        const results = [];
        // Inputs
        document.querySelectorAll('input:not([type="hidden"])').forEach(el => {
            if (el.offsetParent !== null || el.offsetHeight > 0) {
                results.push({
                    tag: 'input',
                    type: el.type || 'text',
                    name: el.name || '',
                    id: el.id || '',
                    placeholder: el.placeholder || '',
                    required: el.required,
                    value: el.value || ''
                });
            }
        });
        // Selects
        document.querySelectorAll('select').forEach(el => {
            if (el.offsetParent !== null || el.offsetHeight > 0) {
                const options = Array.from(el.options).map(o => ({value: o.value, text: o.text}));
                results.push({
                    tag: 'select',
                    name: el.name || '',
                    id: el.id || '',
                    required: el.required,
                    options: options.slice(0, 10),
                    optionCount: options.length
                });
            }
        });
        // Textareas
        document.querySelectorAll('textarea').forEach(el => {
            if (el.offsetParent !== null || el.offsetHeight > 0) {
                results.push({
                    tag: 'textarea',
                    name: el.name || '',
                    id: el.id || '',
                    required: el.required
                });
            }
        });
        return results;
    }''')
    return fields

async def fill_form_fields(page, fields):
    """Fill form fields with test data using fast JS-based approach."""
    result = await page.evaluate('''(fields) => {
        const filled = [];
        function setNativeValue(el, value) {
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set
                || Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')?.set;
            if (nativeInputValueSetter) nativeInputValueSetter.call(el, value);
            else el.value = value;
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
        }
        for (const field of fields) {
            try {
                let el = null;
                if (field.id) el = document.getElementById(field.id);
                if (!el && field.name) el = document.querySelector("[name='" + field.name + "']");
                if (!el) continue;
                if (el.offsetParent === null && el.offsetHeight === 0) continue;

                const key = field.name || field.id || 'unknown';
                if (field.tag === 'input') {
                    const t = field.type || 'text';
                    if (['text','search','tel','url'].includes(t)) {
                        setNativeValue(el, 'AUTOTEST_' + key);
                        filled.push('input[' + key + ']=AUTOTEST_...');
                    } else if (t === 'email') {
                        setNativeValue(el, 'autotest@test.com');
                        filled.push('input[' + key + ']=autotest@test.com');
                    } else if (t === 'number') {
                        setNativeValue(el, '100');
                        filled.push('input[' + key + ']=100');
                    } else if (t === 'date') {
                        setNativeValue(el, '2026-04-18');
                        filled.push('input[' + key + ']=2026-04-18');
                    } else if (t === 'password') {
                        setNativeValue(el, 'AUTOTEST_pass123');
                        filled.push('input[' + key + ']=AUTOTEST_pass123');
                    }
                } else if (field.tag === 'select') {
                    const opts = el.options;
                    for (let i = 0; i < opts.length; i++) {
                        if (opts[i].value && opts[i].value !== '') {
                            el.value = opts[i].value;
                            el.dispatchEvent(new Event('change', {bubbles: true}));
                            filled.push('select[' + key + ']=' + opts[i].value);
                            break;
                        }
                    }
                } else if (field.tag === 'textarea') {
                    setNativeValue(el, 'AUTOTEST_textarea_' + key);
                    filled.push('textarea[' + key + ']=AUTOTEST_...');
                }
            } catch(e) {}
        }
        return filled;
    }''', fields)
    return result

async def try_click_add_new(page):
    """Try to find and click an Add New button."""
    selectors = [
        "a:has-text('Add New')",
        "button:has-text('Add New')",
        "a:has-text('Add Job')",
        "button:has-text('Add Job')",
        "a:has-text('New Job')",
        "button:has-text('New Job')",
        ".btn:has-text('Add New')",
        ".btn:has-text('Add')",
        "a:has-text('Add')",
        "button:has-text('Add')",
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.is_visible(timeout=500):
                await loc.click()
                return True, sel
        except:
            continue
    return False, None

async def try_submit_form(page):
    """Try to submit a form."""
    selectors = [
        "button[type='submit']",
        "input[type='submit']",
        "button:has-text('Save')",
        "button:has-text('Submit')",
        "button:has-text('Create')",
        "button:has-text('Add')",
        ".btn:has-text('Save')",
        ".btn:has-text('Submit')",
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.is_visible(timeout=500):
                await loc.click()
                return True, sel
        except:
            continue
    return False, None

async def get_table_row_count(page):
    """Count rows in main data tables."""
    count = await page.evaluate('''() => {
        const tables = document.querySelectorAll('table');
        let maxRows = 0;
        tables.forEach(t => {
            const rows = t.querySelectorAll('tbody tr');
            if (rows.length > maxRows) maxRows = rows.length;
        });
        return maxRows;
    }''')
    return count

async def check_success_error(page):
    """Check for success or error messages."""
    result = await page.evaluate('''() => {
        const body = document.body ? document.body.innerText : '';
        const success_patterns = ['success', 'created', 'saved', 'added', 'updated'];
        const error_patterns = ['error', 'failed', 'invalid', 'required', 'cannot'];

        // Check alerts, toasts, modals
        const alerts = document.querySelectorAll('.alert, .toast, .notification, .swal2-popup, .modal.show');
        let alertText = '';
        alerts.forEach(a => alertText += a.innerText + ' ');

        const combined = (alertText + ' ' + body.substring(0, 1000)).toLowerCase();

        let hasSuccess = success_patterns.some(p => combined.includes(p));
        let hasError = error_patterns.some(p => combined.includes(p));

        return {
            hasSuccess,
            hasError,
            alertText: alertText.substring(0, 300),
            bodyPreview: body.substring(0, 300)
        };
    }''')
    return result

async def try_date_filter(page, screenshot_prefix):
    """Try to find and use date filters on report pages."""
    try:
        # Look for date inputs
        date_inputs = await page.evaluate('''() => {
            const inputs = document.querySelectorAll('input[type="date"], input.datepicker, input[name*="date"], input[name*="from"], input[name*="to"], input[placeholder*="date" i], input[placeholder*="Date" i]');
            return Array.from(inputs).map(i => ({id: i.id, name: i.name, type: i.type, placeholder: i.placeholder}));
        }''')

        if len(date_inputs) >= 2:
            # Try filling from/to dates
            for inp in date_inputs[:2]:
                sel = f"#{inp['id']}" if inp['id'] else f"[name='{inp['name']}']"
                try:
                    el = page.locator(sel).first
                    if await el.is_visible(timeout=1000):
                        await el.fill("2026-01-01")
                except:
                    pass

            # Try clicking filter/search button
            for btn_sel in ["button:has-text('Filter')", "button:has-text('Search')", "button:has-text('Go')", "button:has-text('Apply')", "button[type='submit']"]:
                try:
                    btn = page.locator(btn_sel).first
                    if await btn.is_visible(timeout=1000):
                        await btn.click()
                        await page.wait_for_timeout(2000)
                        break
                except:
                    continue

            await page.screenshot(path=f"{SCREENSHOT_DIR}/{screenshot_prefix}_filtered.png", full_page=False)
            return {"filtered": True, "date_inputs_found": len(date_inputs)}

        return {"filtered": False, "date_inputs_found": len(date_inputs)}
    except Exception as e:
        return {"filtered": False, "error": str(e)}


# ========== PART 1: Job Creation Tests ==========
async def test_job_creation(page):
    print("\n" + "="*60)
    print("PART 1: JOB CREATION TESTS")
    print("="*60)

    jobs = [
        ("Ocean Import", "/9dddd5ce1b1375bc497feeb871842d4b"),
        ("Ocean Export", "/ddc5bbfa18cf713c1478e511ea7455a7"),
        ("Air Import", "/951733b073f499bd67fa764d38df48a8"),
        ("Air Export", "/8b574ca0cd37f8b76897ecc0f9d9ad34"),
        ("Land Import", "/8013f48199799dce7a1fde812910a496"),
        ("Land Export", "/2ca1dbee9121459dedd8cf2e88823068"),
    ]

    part_results = {}

    for name, url in jobs:
        safe_name = name.lower().replace(" ", "_")
        print(f"\n--- Testing {name} Open Jobs ---")
        test_result = {"name": name, "url": url}

        try:
            # Step 1: Navigate and screenshot
            status_info = await check_page_status(page, url, name)
            test_result["page_status"] = status_info
            await page.screenshot(path=f"{SCREENSHOT_DIR}/p1_{safe_name}_list.png", full_page=False)

            if status_info["is_404"]:
                print(f"  [404] Page not found for {name}")
                test_result["result"] = "404 - Page not found"
                part_results[safe_name] = test_result
                continue

            print(f"  Page loaded (status: {status_info['status']})")

            # Get row count
            row_count = await get_table_row_count(page)
            test_result["existing_rows"] = row_count
            print(f"  Existing rows: {row_count}")

            # Step 2: Click Add New
            clicked, btn_sel = await try_click_add_new(page)
            test_result["add_new_clicked"] = clicked
            test_result["add_new_selector"] = btn_sel

            if not clicked:
                print(f"  [WARN] Could not find Add New button for {name}")
                test_result["result"] = "No Add New button found"
                part_results[safe_name] = test_result
                continue

            print(f"  Clicked Add New via: {btn_sel}")
            await page.wait_for_timeout(3000)
            await page.screenshot(path=f"{SCREENSHOT_DIR}/p1_{safe_name}_form.png", full_page=False)

            # Step 3: Discover fields
            fields = await discover_form_fields(page)
            test_result["form_fields"] = fields
            print(f"  Found {len(fields)} form fields")
            for f in fields[:10]:
                print(f"    - {f['tag']}[{f.get('type','')}] name={f.get('name','')} id={f.get('id','')}")

            # Step 4: Fill fields
            filled = await fill_form_fields(page, fields)
            test_result["fields_filled"] = filled
            print(f"  Filled {len(filled)} fields")

            await page.screenshot(path=f"{SCREENSHOT_DIR}/p1_{safe_name}_filled.png", full_page=False)

            # Step 5: Submit
            submitted, sub_sel = await try_submit_form(page)
            test_result["submitted"] = submitted
            test_result["submit_selector"] = sub_sel

            if submitted:
                print(f"  Submitted via: {sub_sel}")
                await page.wait_for_timeout(3000)
                await page.screenshot(path=f"{SCREENSHOT_DIR}/p1_{safe_name}_result.png", full_page=False)

                # Check result
                msg = await check_success_error(page)
                test_result["post_submit"] = msg
                print(f"  Success: {msg['hasSuccess']}, Error: {msg['hasError']}")
                if msg['alertText']:
                    print(f"  Alert: {msg['alertText'][:100]}")
            else:
                print(f"  [WARN] Could not find submit button")
                test_result["result"] = "No submit button found"

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            test_result["error"] = str(e)

        part_results[safe_name] = test_result

    results["parts"]["part1_job_creation"] = part_results
    save_results()
    print("\nPart 1 complete. Results saved.")


# ========== PART 2: Booking Reports ==========
async def test_booking_reports(page):
    print("\n" + "="*60)
    print("PART 2: BOOKING REPORTS")
    print("="*60)

    reports = [
        ("Ocean Import Booking", "/e14e00f9b8b4f2a0fbce2a5f843a543d"),
        ("Ocean Export Booking", "/a77dd96ff658388a662b311c5bbd1a75"),
        ("Air Import Booking", "/6e2cac0a97967fe9b38243a12ec09be0"),
        ("Air Export Booking", "/7d27d418fe920b6bc9230e81ef3a9bae"),
    ]

    part_results = {}

    for name, url in reports:
        safe_name = name.lower().replace(" ", "_")
        print(f"\n--- Testing {name} Report ---")
        test_result = {"name": name, "url": url}

        try:
            status_info = await check_page_status(page, url, name)
            test_result["page_status"] = status_info
            await page.screenshot(path=f"{SCREENSHOT_DIR}/p2_{safe_name}.png", full_page=False)

            if status_info["is_404"]:
                print(f"  [404] Page not found")
                test_result["result"] = "404"
                part_results[safe_name] = test_result
                continue

            print(f"  Page loaded (status: {status_info['status']})")
            row_count = await get_table_row_count(page)
            test_result["row_count"] = row_count
            print(f"  Table rows: {row_count}")

            # Try date filter
            filter_result = await try_date_filter(page, f"p2_{safe_name}")
            test_result["filter"] = filter_result
            print(f"  Filter attempted: {filter_result}")

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            test_result["error"] = str(e)

        part_results[safe_name] = test_result

    results["parts"]["part2_booking_reports"] = part_results
    save_results()
    print("\nPart 2 complete. Results saved.")


# ========== PART 3: Financial Reports ==========
async def test_financial_reports(page):
    print("\n" + "="*60)
    print("PART 3: FINANCIAL REPORTS")
    print("="*60)

    reports = [
        ("Purchase Invoice", "/purchase-invoice"),
        ("Sales Invoice", "/sales-invoice"),
        ("Purchase Invoice VAT", "/purchase-invoice-with-vat"),
        ("Sales Invoice VAT", "/sales-invoice/with-vat"),
        ("Ledger Report", "/ledger"),
        ("Customer Ageing", "/reports/customer-aging"),
        ("Supplier Ageing", "/reports/supplier-ageing"),
        ("Jobs w/o Purchase Inv", "/purchase-invoice-missing"),
        ("Jobs w/o Sales Inv", "/sales-charges-without-invoice"),
    ]

    part_results = {}

    for name, url in reports:
        safe_name = name.lower().replace(" ", "_").replace("/", "_")
        print(f"\n--- Testing {name} ---")
        test_result = {"name": name, "url": url}

        try:
            status_info = await check_page_status(page, url, name)
            test_result["page_status"] = status_info
            await page.screenshot(path=f"{SCREENSHOT_DIR}/p3_{safe_name}.png", full_page=False)

            if status_info["is_404"]:
                print(f"  [404] Page not found")
                test_result["result"] = "404"
                part_results[safe_name] = test_result
                continue

            print(f"  Page loaded (status: {status_info['status']})")
            row_count = await get_table_row_count(page)
            test_result["row_count"] = row_count
            print(f"  Table rows: {row_count}")

            # Check for filter forms
            filter_result = await try_date_filter(page, f"p3_{safe_name}")
            test_result["filter"] = filter_result
            print(f"  Filter: {filter_result}")

            # Check data display
            has_table = await page.evaluate("() => document.querySelectorAll('table').length")
            test_result["tables_found"] = has_table
            print(f"  Tables on page: {has_table}")

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            test_result["error"] = str(e)

        part_results[safe_name] = test_result

    results["parts"]["part3_financial_reports"] = part_results
    save_results()
    print("\nPart 3 complete. Results saved.")


# ========== PART 4: Closed Jobs and Quotes ==========
async def test_closed_jobs_quotes(page):
    print("\n" + "="*60)
    print("PART 4: CLOSED JOBS AND QUOTES")
    print("="*60)

    pages_list = [
        ("Ocean Import Closed", "/670effb783ab68c5759f4523c9ad5185"),
        ("Ocean Export Closed", "/12d57e567d9ab44399006309b5d542a4"),
        ("Air Import Closed", "/3092560bb3f11343b8ceb0e02a739a01"),
        ("Air Export Closed", "/8ec1c8a3d9ad635d8fd2adb2c583b7c0"),
        ("Quotes", "/68915d3ba92a6ff8c96734362d61b15e"),
        ("Rate Database", "/95ea21eb539e083e42f57313509a93ed"),
        ("Client Rates", "/db6f53167f5911e700a4b3aae0352572"),
    ]

    part_results = {}

    for name, url in pages_list:
        safe_name = name.lower().replace(" ", "_")
        print(f"\n--- Testing {name} ---")
        test_result = {"name": name, "url": url}

        try:
            status_info = await check_page_status(page, url, name)
            test_result["page_status"] = status_info
            await page.screenshot(path=f"{SCREENSHOT_DIR}/p4_{safe_name}.png", full_page=False)

            if status_info["is_404"]:
                print(f"  [404] Page not found")
                test_result["result"] = "404"
                part_results[safe_name] = test_result
                continue

            print(f"  Page loaded (status: {status_info['status']})")
            row_count = await get_table_row_count(page)
            test_result["row_count"] = row_count
            print(f"  Table rows: {row_count}")

            # For Quotes, try Add New
            if name == "Quotes":
                clicked, btn_sel = await try_click_add_new(page)
                test_result["add_new_clicked"] = clicked
                if clicked:
                    print(f"  Clicked Add New for Quotes via: {btn_sel}")
                    await page.wait_for_timeout(3000)
                    await page.screenshot(path=f"{SCREENSHOT_DIR}/p4_quotes_form.png", full_page=False)

                    fields = await discover_form_fields(page)
                    test_result["quote_form_fields"] = fields
                    print(f"  Quote form fields: {len(fields)}")
                    for f in fields[:10]:
                        print(f"    - {f['tag']}[{f.get('type','')}] name={f.get('name','')} id={f.get('id','')}")
                else:
                    print(f"  [WARN] No Add New button for Quotes")

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            test_result["error"] = str(e)

        part_results[safe_name] = test_result

    results["parts"]["part4_closed_jobs_quotes"] = part_results
    save_results()
    print("\nPart 4 complete. Results saved.")


# ========== PART 5: Account Pages ==========
async def test_account_pages(page):
    print("\n" + "="*60)
    print("PART 5: ACCOUNT PAGES (DEBTORS & CREDITORS)")
    print("="*60)

    pages_list = [
        # Debtors
        ("Consignee Due", "/1abe8a244329f592bb3bbb96e22e0344"),
        ("Consignee Paid", "/8c8bcb5e96e6c22e001efff53fcadf28"),
        ("Agent Due (Debtor)", "/28f3b7864cdf11d6b30b148bec8d6307"),
        ("Agent Paid (Debtor)", "/b621a0964636bcee73d691db7d3572fd"),
        ("Shipper Due", "/8211377a76b5f20c607e278620d4abe3"),
        ("Shipper Paid", "/76264365e7c5a943b7629804aeab136b"),
        # Creditors
        ("Shipping Line Due", "/8e1b7fdf1fd87dcc9e0546d03ae62556"),
        ("Shipping Line Paid", "/d18ec27a83b522669c9efc55a880f917"),
        ("Co-Loader Due", "/285ee3bf7d21a421fb354e824a0ba678"),
        ("Co-Loader Paid", "/49ab2c7ef13c1de745c5e511ea7d306f"),
        ("Supplier Due", "/57e215a5d82f9e54a6e6b2ddfd0372c1"),
        ("Supplier Paid", "/832128c1bea0bf94b30c16a8417125ae"),
        ("Agent Due (Creditor)", "/455492c7888db5aafecf4facc1aa7639"),
        ("Agent Paid (Creditor)", "/bfd9d957f28679c09593198e7cefb085"),
    ]

    part_results = {}

    for name, url in pages_list:
        safe_name = name.lower().replace(" ", "_").replace("(", "").replace(")", "")
        print(f"\n--- Testing {name} ---")
        test_result = {"name": name, "url": url}

        try:
            status_info = await check_page_status(page, url, name)
            test_result["page_status"] = status_info
            await page.screenshot(path=f"{SCREENSHOT_DIR}/p5_{safe_name}.png", full_page=False)

            if status_info["is_404"]:
                print(f"  [404] Page not found")
                test_result["result"] = "404"
                part_results[safe_name] = test_result
                continue

            print(f"  Page loaded (status: {status_info['status']})")
            row_count = await get_table_row_count(page)
            test_result["row_count"] = row_count
            print(f"  Table rows: {row_count}")

            # Try date filter
            filter_result = await try_date_filter(page, f"p5_{safe_name}")
            test_result["filter"] = filter_result
            print(f"  Filter: {filter_result}")

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            test_result["error"] = str(e)

        part_results[safe_name] = test_result

    results["parts"]["part5_account_pages"] = part_results
    save_results()
    print("\nPart 5 complete. Results saved.")


# ========== PART 6: HR Employee ==========
async def test_hr_employee(page):
    print("\n" + "="*60)
    print("PART 6: HR EMPLOYEE")
    print("="*60)

    test_result = {"name": "Employee", "url": "/51564f2eb2d3a1bca494e86b1c67635e"}

    try:
        status_info = await check_page_status(page, "/51564f2eb2d3a1bca494e86b1c67635e", "Employee")
        test_result["page_status"] = status_info
        await page.screenshot(path=f"{SCREENSHOT_DIR}/p6_employee_list.png", full_page=False)

        if status_info["is_404"]:
            print("  [404] Page not found")
            test_result["result"] = "404"
        else:
            print(f"  Page loaded (status: {status_info['status']})")
            row_count = await get_table_row_count(page)
            test_result["row_count"] = row_count
            print(f"  Table rows: {row_count}")

            # Click Add New
            clicked, btn_sel = await try_click_add_new(page)
            test_result["add_new_clicked"] = clicked

            if clicked:
                print(f"  Clicked Add New via: {btn_sel}")
                await page.wait_for_timeout(3000)
                await page.screenshot(path=f"{SCREENSHOT_DIR}/p6_employee_form.png", full_page=False)

                # Discover fields
                fields = await discover_form_fields(page)
                test_result["form_fields"] = fields
                print(f"  Found {len(fields)} form fields")
                for f in fields[:15]:
                    print(f"    - {f['tag']}[{f.get('type','')}] name={f.get('name','')} id={f.get('id','')}")

                # Fill fields
                filled = await fill_form_fields(page, fields)
                test_result["fields_filled"] = filled
                print(f"  Filled {len(filled)} fields")

                await page.screenshot(path=f"{SCREENSHOT_DIR}/p6_employee_filled.png", full_page=False)

                # Submit
                submitted, sub_sel = await try_submit_form(page)
                test_result["submitted"] = submitted

                if submitted:
                    print(f"  Submitted via: {sub_sel}")
                    await page.wait_for_timeout(3000)
                    await page.screenshot(path=f"{SCREENSHOT_DIR}/p6_employee_result.png", full_page=False)

                    msg = await check_success_error(page)
                    test_result["post_submit"] = msg
                    print(f"  Success: {msg['hasSuccess']}, Error: {msg['hasError']}")
                else:
                    print("  [WARN] No submit button found")
            else:
                print("  [WARN] No Add New button found")

    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        test_result["error"] = str(e)

    results["parts"]["part6_hr_employee"] = test_result
    save_results()
    print("\nPart 6 complete. Results saved.")


# ========== PART 7: DSR Reports ==========
async def test_dsr_reports(page):
    print("\n" + "="*60)
    print("PART 7: DSR REPORTS (known issues)")
    print("="*60)

    dsr_pages = [
        ("Basic Graph", "/fe83dce7816670353cfa807c5722d816"),
        ("Ocean Import DSR", "/1387f1ae3dc1d840789d15c546e89125"),
        ("Ocean Export DSR", "/c745c437840b2e21636a2cbdab4b33a6"),
        ("Air Import DSR", "/abf5db603d4276889077e81de984cf6d"),
        ("Air Export DSR", "/627db3ba79d7139f8dfd6f462e1b0514"),
    ]

    part_results = {}

    for name, url in dsr_pages:
        safe_name = name.lower().replace(" ", "_")
        print(f"\n--- Testing {name} ---")
        test_result = {"name": name, "url": url}

        try:
            status_info = await check_page_status(page, url, name)
            test_result["page_status"] = status_info
            await page.screenshot(path=f"{SCREENSHOT_DIR}/p7_{safe_name}.png", full_page=False)

            if status_info["is_404"]:
                print(f"  [404] Page not found (expected)")
                test_result["result"] = "404 - Expected"
            elif status_info["is_error"]:
                print(f"  [ERROR] Page error: {status_info['status']}")
                test_result["result"] = f"Error - {status_info['status']}"
            else:
                print(f"  Page loaded (status: {status_info['status']})")
                row_count = await get_table_row_count(page)
                test_result["row_count"] = row_count
                print(f"  Table rows: {row_count}")

        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            test_result["error"] = str(e)

        part_results[safe_name] = test_result

    results["parts"]["part7_dsr_reports"] = part_results
    save_results()
    print("\nPart 7 complete. Results saved.")


# ========== MAIN ==========
async def main():
    print("="*60)
    print("SENA ERP - Jobs, Reports & Accounts Test Suite")
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Base URL: {BASE_URL}")
    print("="*60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()

        try:
            await login(page)

            await test_job_creation(page)
            await test_booking_reports(page)
            await test_financial_reports(page)
            await test_closed_jobs_quotes(page)
            await test_account_pages(page)
            await test_hr_employee(page)
            await test_dsr_reports(page)

        except Exception as e:
            print(f"\n[FATAL ERROR] {str(e)}")
            results["fatal_error"] = str(e)
        finally:
            await browser.close()

    results["completed"] = datetime.now().isoformat()
    save_results()

    # Print summary
    print("\n" + "="*60)
    print("TEST SUITE COMPLETE")
    print("="*60)
    print(f"Results saved to: {RESULTS_FILE}")
    print(f"Screenshots saved to: {SCREENSHOT_DIR}")

    # Summary counts
    for part_name, part_data in results.get("parts", {}).items():
        if isinstance(part_data, dict) and "name" in part_data:
            # Single test (part 6)
            status = part_data.get("page_status", {})
            print(f"  {part_name}: status={status.get('status', '?')}, 404={status.get('is_404', '?')}")
        elif isinstance(part_data, dict):
            total = len(part_data)
            not_found = sum(1 for v in part_data.values() if isinstance(v, dict) and v.get("page_status", {}).get("is_404"))
            loaded = total - not_found
            print(f"  {part_name}: {loaded}/{total} pages loaded, {not_found} 404s")

if __name__ == "__main__":
    asyncio.run(main())
