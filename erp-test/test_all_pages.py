"""
Sena ERP - Comprehensive Playwright Test Script
Tests all pages by direct URL navigation, captures screenshots,
checks for tables/forms, and attempts record creation on master pages.
"""

import asyncio
import json
import os
import time
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "http://13.210.47.18:8088"
SCREENSHOT_DIR = "/var/lib/freelancer/projects/40298427/erp-test/screenshots/all_pages"
RESULTS_FILE = "/var/lib/freelancer/projects/40298427/erp-test/results_all_pages.json"

USERNAME = "superadmin"
PASSWORD = "Nick@#24"

# Complete URL map
PAGES = {
    # Dashboard
    "Dashboard": "/4d5c7c941df8262af83d7b494f9d120e",

    # HR
    "HR - Employee": "/51564f2eb2d3a1bca494e86b1c67635e",

    # Account - Debtors
    "Debtors - Consignee Due": "/1abe8a244329f592bb3bbb96e22e0344",
    "Debtors - Consignee Paid": "/8c8bcb5e96e6c22e001efff53fcadf28",
    "Debtors - Agent Due": "/28f3b7864cdf11d6b30b148bec8d6307",
    "Debtors - Agent Paid": "/b621a0964636bcee73d691db7d3572fd",
    "Debtors - Shipper Due": "/8211377a76b5f20c607e278620d4abe3",
    "Debtors - Shipper Paid": "/76264365e7c5a943b7629804aeab136b",

    # Account - Creditors
    "Creditors - Shipping Line Due": "/8e1b7fdf1fd87dcc9e0546d03ae62556",
    "Creditors - Shipping Line Paid": "/d18ec27a83b522669c9efc55a880f917",
    "Creditors - Co-Loader Due": "/285ee3bf7d21a421fb354e824a0ba678",
    "Creditors - Co-Loader Paid": "/49ab2c7ef13c1de745c5e511ea7d306f",
    "Creditors - Supplier Due": "/57e215a5d82f9e54a6e6b2ddfd0372c1",
    "Creditors - Supplier Paid": "/832128c1bea0bf94b30c16a8417125ae",
    "Creditors - Agent Due": "/455492c7888db5aafecf4facc1aa7639",
    "Creditors - Agent Paid": "/bfd9d957f28679c09593198e7cefb085",

    # Financial Reports
    "Financial - Purchase Invoice": "/purchase-invoice",
    "Financial - Sales Invoice": "/sales-invoice",
    "Financial - Purchase Invoice VAT": "/purchase-invoice-with-vat",
    "Financial - Sales Invoice VAT": "/sales-invoice/with-vat",
    "Financial - Ledger Report": "/ledger",
    "Financial - Customer Ageing": "/reports/customer-aging",
    "Financial - Supplier Ageing": "/reports/supplier-ageing",
    "Financial - Jobs w/o Purchase Inv": "/purchase-invoice-missing",
    "Financial - Jobs w/o Sales Inv": "/sales-charges-without-invoice",
    "Financial - Activity Log": "/activity-log",
    "Financial - Credit Note Register": "/credit-note-register",

    # Common Masters
    "Master - State": "/9ed39e2ea931586b6a985a6942ef573e",
    "Master - City": "/4ed5d2eaed1a1fadcc41ad1d58ed603e",
    "Master - Company Type": "/4cbb903cfae35c7d1844aac2363280b4",
    "Master - Charge Master": "/af33c0fa2a013f51745b910eb3f70046",
    "Master - Company Master": "/005480c8a6a0357d17cff2e8eb7e060d",
    "Master - Customer Type": "/4fe8a4cd07dfac7245a1e6cacb76ea5e",
    "Master - Ledger Group": "/2b0f7f32c7f7af6b51bf090558391d67",
    "Master - Customer Master": "/423b21e5932f11b123a1ddb35654b51b",
    "Master - Vendor Master": "/237cddc13035afd40df532c9c471b4ea",
    "Master - Vendor Type": "/01f9a24e9744ed8edf5beb17513aafb4",
    "Master - Shipping Line Code": "/9cdaacf035c457148bc2134dfe09fc50",
    "Master - Commodity Master": "/b515f30a4688bf67cd17f0cd09512ecf",
    "Master - Address": "/de7c54d99428fb909bef013577070f0d",

    # Ocean Masters
    "Ocean Master - Job Type": "/3f80ea99d7b24220db44943ed1838285",
    "Ocean Master - Vessel": "/ed6c460e3ce8e91132123ff09428a37d",
    "Ocean Master - Port Sector": "/51b6df155998f6c6b3ccc2701b59693d",
    "Ocean Master - Port": "/eac46b9f08f604c039b439ef2dd5663f",

    # Air Masters
    "Air Master - Airport": "/d1ed858f6d8126a814e31f18a7de5f8e",
    "Air Master - Carrier Airlines": "/1abf8c1a21e96e8d369b40b322331782",

    # Quote Setup
    "Quote Setup - Carriers": "/8ee4a920e024b1d3beadaadd006a0a31",
    "Quote Setup - Exchange Rates": "/b63cf46906108334186c3ecf25f4ddb8",
    "Quote Setup - Rate Database": "/95ea21eb539e083e42f57313509a93ed",
    "Quote Setup - Client Rates": "/db6f53167f5911e700a4b3aae0352572",

    # Quotes
    "Quotes": "/68915d3ba92a6ff8c96734362d61b15e",

    # Ocean Import
    "Ocean Import - Open Jobs": "/9dddd5ce1b1375bc497feeb871842d4b",
    "Ocean Import - Closed Jobs": "/670effb783ab68c5759f4523c9ad5185",
    "Ocean Import - Booking Report": "/e14e00f9b8b4f2a0fbce2a5f843a543d",

    # Ocean Export
    "Ocean Export - Open Jobs": "/ddc5bbfa18cf713c1478e511ea7455a7",
    "Ocean Export - Closed Jobs": "/12d57e567d9ab44399006309b5d542a4",
    "Ocean Export - Booking Report": "/a77dd96ff658388a662b311c5bbd1a75",

    # Air Import
    "Air Import - Open Jobs": "/951733b073f499bd67fa764d38df48a8",
    "Air Import - Closed Jobs": "/3092560bb3f11343b8ceb0e02a739a01",
    "Air Import - Booking Report": "/6e2cac0a97967fe9b38243a12ec09be0",

    # Air Export
    "Air Export - Open Jobs": "/8b574ca0cd37f8b76897ecc0f9d9ad34",
    "Air Export - Closed Jobs": "/8ec1c8a3d9ad635d8fd2adb2c583b7c0",
    "Air Export - Booking Report": "/7d27d418fe920b6bc9230e81e58bc28b",

    # Land Import
    "Land Import - Open Jobs": "/8013f48199799dce7a1fde812ebda23b",
    "Land Import - Closed Jobs": "/ad661c9739fbf14ddd1802a6c4bb9f0c",

    # Land Export
    "Land Export - Open Jobs": "/2ca1dbee9121459dedd8cf2e8c3b8e69",
    "Land Export - Closed Jobs": "/2785ba86aa37c0a8ff38e247ad1c5e55",

    # DSR Reports
    "DSR - Basic Graph": "/fe83dce7816670353cfa807c5e45db0e",
    "DSR - Ocean Import": "/1387f1ae3dc1d840789d15c545b8a7e5",
    "DSR - Ocean Export": "/c745c437840b2e21636a2cbdab3c0e59",
    "DSR - Air Import": "/abf5db603d4276889077e81dee45d0ca",
    "DSR - Air Export": "/627db3ba79d7139f8dfd6f462fdce3ab",
}

# Master pages where we attempt to click "Add" button
ADD_BUTTON_MASTERS = [
    "Master - State",
    "Master - City",
    "Master - Company Type",
    "Master - Charge Master",
    "Master - Customer Type",
    "Master - Vendor Type",
    "Ocean Master - Job Type",
    "Ocean Master - Vessel",
    "Air Master - Airport",
]


async def login(page):
    """Login via JS form submission with CSRF token."""
    print("[LOGIN] Navigating to login page...")
    await page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
    await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "00_login_page.png"))

    # Get CSRF token
    csrf_token = await page.evaluate("""() => {
        const meta = document.querySelector('meta[name="csrf-token"]');
        if (meta) return meta.getAttribute('content');
        const input = document.querySelector('input[name="_token"]');
        if (input) return input.value;
        return null;
    }""")
    print(f"[LOGIN] CSRF token: {csrf_token[:20] if csrf_token else 'NOT FOUND'}...")

    # Fill the form and submit via JS
    logged_in = await page.evaluate("""(args) => {
        const form = document.getElementById('signupForm');
        if (!form) return 'FORM_NOT_FOUND';

        // Set field values
        const usernameField = form.querySelector('input[name="username"], input[name="email"], input[type="text"], input[type="email"]');
        const passwordField = form.querySelector('input[name="password"], input[type="password"]');

        if (!usernameField || !passwordField) return 'FIELDS_NOT_FOUND';

        usernameField.value = args.username;
        passwordField.value = args.password;

        // Trigger change events
        usernameField.dispatchEvent(new Event('input', {bubbles: true}));
        usernameField.dispatchEvent(new Event('change', {bubbles: true}));
        passwordField.dispatchEvent(new Event('input', {bubbles: true}));
        passwordField.dispatchEvent(new Event('change', {bubbles: true}));

        // Submit
        form.submit();
        return 'SUBMITTED';
    }""", {"username": USERNAME, "password": PASSWORD})

    print(f"[LOGIN] Form submission result: {logged_in}")

    if logged_in == "FORM_NOT_FOUND":
        # Fallback: try direct POST
        print("[LOGIN] Form not found, trying direct input fill...")
        await page.fill('input[type="text"], input[type="email"], input[name="username"], input[name="email"]', USERNAME)
        await page.fill('input[type="password"]', PASSWORD)
        await page.click('button[type="submit"], input[type="submit"], .btn-primary')

    # Wait for navigation after login
    try:
        await page.wait_for_url(f"{BASE_URL}/**", timeout=30000)
    except Exception:
        pass

    await page.wait_for_timeout(3000)
    await page.screenshot(path=os.path.join(SCREENSHOT_DIR, "01_after_login.png"))

    current_url = page.url
    print(f"[LOGIN] Current URL after login: {current_url}")

    # Check if we landed on dashboard or are still on login
    if "/login" in current_url or current_url.rstrip("/") == BASE_URL.rstrip("/"):
        # Maybe login page is the root, check page content
        title = await page.title()
        print(f"[LOGIN] Page title: {title}")
        body_text = await page.evaluate("() => document.body ? document.body.innerText.substring(0, 200) : ''")
        print(f"[LOGIN] Body preview: {body_text[:100]}")

    return True


async def analyze_page(page, page_name, page_path):
    """Navigate to a page, take screenshot, and analyze its content."""
    result = {
        "name": page_name,
        "url": f"{BASE_URL}{page_path}",
        "path": page_path,
        "status": "unknown",
        "http_status": None,
        "title": None,
        "has_table": False,
        "table_row_count": 0,
        "has_form": False,
        "form_fields": [],
        "has_error": False,
        "error_text": None,
        "has_add_button": False,
        "screenshot": None,
        "load_time_ms": 0,
    }

    safe_name = page_name.replace(" ", "_").replace("-", "_").replace("/", "_")
    screenshot_path = os.path.join(SCREENSHOT_DIR, f"{safe_name}.png")

    start = time.time()
    try:
        response = await page.goto(
            f"{BASE_URL}{page_path}",
            wait_until="networkidle",
            timeout=60000
        )
        # Extra wait for JS rendering
        await page.wait_for_timeout(2000)

        elapsed = int((time.time() - start) * 1000)
        result["load_time_ms"] = elapsed
        result["http_status"] = response.status if response else None
        result["title"] = await page.title()

        # Take screenshot
        await page.screenshot(path=screenshot_path, full_page=False)
        result["screenshot"] = screenshot_path

        # Check for errors (common error indicators)
        error_info = await page.evaluate("""() => {
            const body = document.body ? document.body.innerText : '';
            const errorPatterns = [
                '500', 'Internal Server Error', 'Page not found', '404',
                'Whoops', 'Exception', 'Error', 'Forbidden', '403',
                'Unauthorized', '401', 'Something went wrong'
            ];
            // Check for prominent error messages (not just any mention of 'error')
            const h1 = document.querySelector('h1');
            const h1Text = h1 ? h1.innerText : '';
            const alertDanger = document.querySelector('.alert-danger, .error-page, .error-content');
            const alertText = alertDanger ? alertDanger.innerText : '';

            let foundError = null;
            if (alertText) foundError = alertText.substring(0, 200);
            for (const pattern of ['500', '404', '403', '401', 'Whoops', 'Exception', 'Internal Server Error', 'Page not found']) {
                if (h1Text.includes(pattern)) {
                    foundError = h1Text.substring(0, 200);
                    break;
                }
            }
            return foundError;
        }""")

        if error_info:
            result["has_error"] = True
            result["error_text"] = error_info
            result["status"] = "error"
        elif response and response.status >= 400:
            result["has_error"] = True
            result["error_text"] = f"HTTP {response.status}"
            result["status"] = "error"
        else:
            result["status"] = "ok"

        # Check for tables
        table_info = await page.evaluate("""() => {
            const tables = document.querySelectorAll('table');
            if (tables.length === 0) {
                // Check for DataTables or dynamic tables
                const dt = document.querySelectorAll('.dataTables_wrapper, .dataTable, [id*="DataTables"]');
                if (dt.length > 0) {
                    const rows = document.querySelectorAll('.dataTables_wrapper tbody tr, .dataTable tbody tr');
                    return { found: true, rowCount: rows.length, type: 'datatable' };
                }
                return { found: false, rowCount: 0, type: null };
            }
            // Find the main data table (largest one)
            let maxRows = 0;
            for (const t of tables) {
                const rows = t.querySelectorAll('tbody tr');
                if (rows.length > maxRows) maxRows = rows.length;
            }
            return { found: true, rowCount: maxRows, type: 'table' };
        }""")

        result["has_table"] = table_info["found"]
        result["table_row_count"] = table_info["rowCount"]

        # Check for forms
        form_info = await page.evaluate("""() => {
            const forms = document.querySelectorAll('form');
            const fields = [];
            const allInputs = document.querySelectorAll('input:not([type="hidden"]), select, textarea');
            for (const inp of allInputs) {
                const name = inp.getAttribute('name') || inp.getAttribute('id') || '';
                const type = inp.tagName.toLowerCase() === 'select' ? 'select' :
                             inp.tagName.toLowerCase() === 'textarea' ? 'textarea' :
                             (inp.getAttribute('type') || 'text');
                const placeholder = inp.getAttribute('placeholder') || '';
                if (name && !name.startsWith('_')) {
                    fields.push({ name: name, type: type, placeholder: placeholder });
                }
            }
            return { found: forms.length > 0 || fields.length > 0, fields: fields.slice(0, 30) };
        }""")

        result["has_form"] = form_info["found"]
        result["form_fields"] = form_info["fields"]

        # Check for Add button
        add_btn = await page.evaluate("""() => {
            const buttons = document.querySelectorAll('button, a.btn, .btn');
            for (const btn of buttons) {
                const text = btn.innerText.trim().toLowerCase();
                if (text.includes('add') || text.includes('create') || text.includes('new')) {
                    return { found: true, text: btn.innerText.trim(), tag: btn.tagName };
                }
            }
            // Also check for plus icons used as add buttons
            const plusBtns = document.querySelectorAll('[data-toggle="modal"], [data-bs-toggle="modal"]');
            for (const btn of plusBtns) {
                const text = btn.innerText.trim().toLowerCase();
                const title = (btn.getAttribute('title') || '').toLowerCase();
                if (text.includes('add') || title.includes('add') || btn.querySelector('.fa-plus, .fa-plus-circle')) {
                    return { found: true, text: btn.innerText.trim() || btn.getAttribute('title') || 'plus-icon', tag: btn.tagName };
                }
            }
            return { found: false, text: null, tag: null };
        }""")

        result["has_add_button"] = add_btn["found"]

    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        result["load_time_ms"] = elapsed
        result["status"] = "exception"
        result["has_error"] = True
        result["error_text"] = str(e)[:300]
        # Try to take screenshot even on error
        try:
            await page.screenshot(path=screenshot_path, full_page=False)
            result["screenshot"] = screenshot_path
        except Exception:
            pass

    return result


async def try_add_record(page, page_name, page_path):
    """Try to click the Add button on a master page and capture the form."""
    add_result = {
        "page": page_name,
        "add_clicked": False,
        "modal_appeared": False,
        "form_fields_in_modal": [],
        "screenshot": None,
        "error": None,
    }

    safe_name = page_name.replace(" ", "_").replace("-", "_").replace("/", "_")

    try:
        # Navigate to the page first
        await page.goto(f"{BASE_URL}{page_path}", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(2000)

        # Try to find and click the Add button
        add_clicked = await page.evaluate("""() => {
            const buttons = document.querySelectorAll('button, a.btn, .btn, a');
            for (const btn of buttons) {
                const text = btn.innerText.trim().toLowerCase();
                const title = (btn.getAttribute('title') || '').toLowerCase();
                const hasPlus = btn.querySelector('.fa-plus, .fa-plus-circle, .ti-plus');
                if (text.includes('add') || text === '+' || title.includes('add') || hasPlus) {
                    btn.click();
                    return true;
                }
            }
            // Try data-toggle modal triggers
            const modalBtns = document.querySelectorAll('[data-toggle="modal"], [data-bs-toggle="modal"]');
            for (const btn of modalBtns) {
                btn.click();
                return true;
            }
            return false;
        }""")

        add_result["add_clicked"] = add_clicked

        if add_clicked:
            # Wait for modal/form to appear
            await page.wait_for_timeout(2000)

            # Check if a modal appeared
            modal_info = await page.evaluate("""() => {
                const modal = document.querySelector('.modal.show, .modal.in, .modal[style*="display: block"]');
                if (!modal) {
                    // Check if page navigated to an add form
                    const forms = document.querySelectorAll('form');
                    if (forms.length > 0) {
                        const fields = [];
                        const inputs = document.querySelectorAll('input:not([type="hidden"]), select, textarea');
                        for (const inp of inputs) {
                            const name = inp.getAttribute('name') || inp.getAttribute('id') || '';
                            const type = inp.tagName.toLowerCase() === 'select' ? 'select' :
                                         inp.tagName.toLowerCase() === 'textarea' ? 'textarea' :
                                         (inp.getAttribute('type') || 'text');
                            const label_el = inp.closest('.form-group, .mb-3');
                            const label = label_el ? (label_el.querySelector('label') ? label_el.querySelector('label').innerText.trim() : '') : '';
                            if (name && !name.startsWith('_')) {
                                fields.push({ name, type, label });
                            }
                        }
                        return { found: true, type: 'page_form', fields: fields.slice(0, 30) };
                    }
                    return { found: false, type: null, fields: [] };
                }

                const fields = [];
                const inputs = modal.querySelectorAll('input:not([type="hidden"]), select, textarea');
                for (const inp of inputs) {
                    const name = inp.getAttribute('name') || inp.getAttribute('id') || '';
                    const type = inp.tagName.toLowerCase() === 'select' ? 'select' :
                                 inp.tagName.toLowerCase() === 'textarea' ? 'textarea' :
                                 (inp.getAttribute('type') || 'text');
                    const label_el = inp.closest('.form-group, .mb-3');
                    const label = label_el ? (label_el.querySelector('label') ? label_el.querySelector('label').innerText.trim() : '') : '';
                    if (name && !name.startsWith('_')) {
                        fields.push({ name, type, label });
                    }
                }
                return { found: true, type: 'modal', fields: fields.slice(0, 30) };
            }""")

            add_result["modal_appeared"] = modal_info["found"]
            add_result["form_fields_in_modal"] = modal_info["fields"]

            # Take screenshot of the add form/modal
            add_screenshot = os.path.join(SCREENSHOT_DIR, f"{safe_name}_ADD_FORM.png")
            await page.screenshot(path=add_screenshot, full_page=False)
            add_result["screenshot"] = add_screenshot

            # Close the modal if open
            try:
                close_btn = page.locator('.modal.show .close, .modal.show .btn-close, .modal.in .close, button[data-dismiss="modal"], button[data-bs-dismiss="modal"]')
                if await close_btn.count() > 0:
                    await close_btn.first.click()
                    await page.wait_for_timeout(500)
            except Exception:
                pass

    except Exception as e:
        add_result["error"] = str(e)[:300]

    return add_result


async def main():
    print("=" * 70)
    print("SENA ERP - Comprehensive Page Test")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    print(f"Total pages to test: {len(PAGES)}")
    print("=" * 70)

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    results = {
        "test_run": {
            "started_at": datetime.now().isoformat(),
            "base_url": BASE_URL,
            "total_pages": len(PAGES),
        },
        "login": {},
        "pages": [],
        "add_attempts": [],
        "summary": {},
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            ignore_https_errors=True,
        )
        context.set_default_timeout(30000)
        page = await context.new_page()

        # Step 1: Login
        print("\n[STEP 1] Logging in...")
        try:
            await login(page)
            results["login"] = {"status": "success", "url_after_login": page.url}
            print(f"[LOGIN] Success - URL: {page.url}")
        except Exception as e:
            results["login"] = {"status": "failed", "error": str(e)}
            print(f"[LOGIN] Failed: {e}")
            # Try to continue anyway

        # Step 2: Test all pages
        print(f"\n[STEP 2] Testing {len(PAGES)} pages...")
        ok_count = 0
        error_count = 0
        exception_count = 0

        for i, (page_name, page_path) in enumerate(PAGES.items(), 1):
            print(f"  [{i:02d}/{len(PAGES)}] {page_name} ... ", end="", flush=True)
            result = await analyze_page(page, page_name, page_path)
            results["pages"].append(result)

            status_icon = "OK" if result["status"] == "ok" else "ERR" if result["status"] == "error" else "EXC"
            extra = ""
            if result["has_table"]:
                extra += f" | table({result['table_row_count']} rows)"
            if result["has_form"]:
                extra += f" | form({len(result['form_fields'])} fields)"
            if result["has_add_button"]:
                extra += " | [ADD]"
            if result["has_error"]:
                extra += f" | err: {(result['error_text'] or '')[:50]}"

            print(f"{status_icon} ({result['load_time_ms']}ms){extra}")

            if result["status"] == "ok":
                ok_count += 1
            elif result["status"] == "error":
                error_count += 1
            else:
                exception_count += 1

        # Step 3: Try Add button on master pages
        print(f"\n[STEP 3] Testing Add button on {len(ADD_BUTTON_MASTERS)} master pages...")
        for page_name in ADD_BUTTON_MASTERS:
            if page_name not in PAGES:
                continue
            page_path = PAGES[page_name]
            print(f"  [ADD] {page_name} ... ", end="", flush=True)
            add_result = await try_add_record(page, page_name, page_path)
            results["add_attempts"].append(add_result)

            if add_result["add_clicked"] and add_result["modal_appeared"]:
                fields = [f.get("label") or f.get("name") for f in add_result["form_fields_in_modal"]]
                print(f"OK - Modal with {len(add_result['form_fields_in_modal'])} fields: {', '.join(fields[:5])}")
            elif add_result["add_clicked"]:
                print("CLICKED but no modal/form detected")
            else:
                print("NO ADD BUTTON FOUND")

        await browser.close()

    # Build summary
    results["summary"] = {
        "total_pages": len(PAGES),
        "ok": ok_count,
        "errors": error_count,
        "exceptions": exception_count,
        "pages_with_tables": sum(1 for p in results["pages"] if p["has_table"]),
        "pages_with_forms": sum(1 for p in results["pages"] if p["has_form"]),
        "pages_with_add_button": sum(1 for p in results["pages"] if p["has_add_button"]),
        "add_attempts_total": len(results["add_attempts"]),
        "add_modals_found": sum(1 for a in results["add_attempts"] if a["modal_appeared"]),
    }
    results["test_run"]["finished_at"] = datetime.now().isoformat()

    # Save results JSON
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n[SAVED] Results: {RESULTS_FILE}")

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total pages tested:    {results['summary']['total_pages']}")
    print(f"  OK (loaded fine):      {results['summary']['ok']}")
    print(f"  Errors (HTTP/content): {results['summary']['errors']}")
    print(f"  Exceptions (timeout):  {results['summary']['exceptions']}")
    print(f"  Pages with tables:     {results['summary']['pages_with_tables']}")
    print(f"  Pages with forms:      {results['summary']['pages_with_forms']}")
    print(f"  Pages with Add button: {results['summary']['pages_with_add_button']}")
    print(f"  Add modals found:      {results['summary']['add_modals_found']} / {results['summary']['add_attempts_total']}")
    print()

    # Detailed pass/fail table
    print(f"{'Page':<45} {'Status':<8} {'HTTP':<5} {'Table':<7} {'Rows':<6} {'Form':<6} {'Add':<5}")
    print("-" * 85)
    for p in results["pages"]:
        status = "PASS" if p["status"] == "ok" else "FAIL"
        http = str(p["http_status"] or "---")
        table = "YES" if p["has_table"] else "-"
        rows = str(p["table_row_count"]) if p["has_table"] else "-"
        form = "YES" if p["has_form"] else "-"
        add = "YES" if p["has_add_button"] else "-"
        print(f"{p['name']:<45} {status:<8} {http:<5} {table:<7} {rows:<6} {form:<6} {add:<5}")

    # List errors
    error_pages = [p for p in results["pages"] if p["status"] != "ok"]
    if error_pages:
        print(f"\n{'='*70}")
        print("FAILED PAGES:")
        print("=" * 70)
        for p in error_pages:
            print(f"  {p['name']}: {p['error_text'][:80] if p['error_text'] else 'Unknown error'}")

    print(f"\nScreenshots saved to: {SCREENSHOT_DIR}")
    print(f"Results JSON saved to: {RESULTS_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
