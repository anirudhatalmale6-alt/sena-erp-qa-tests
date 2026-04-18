#!/usr/bin/env python3
"""
Sena ERP - CRUD Masters Test Script
Tests Add/Create operations on all master pages.
Uses Playwright (Python) in headless mode.
"""

import json
import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

BASE_URL = "http://13.210.47.18:8088"
SCREENSHOT_DIR = "/var/lib/freelancer/projects/40298427/erp-test/screenshots/crud"
RESULTS_FILE = "/var/lib/freelancer/projects/40298427/erp-test/results_crud.json"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Master pages to test
MASTER_PAGES = [
    # Simple Masters
    {"name": "State", "path": "/9ed39e2ea931586b6a985a6942ef573e", "category": "Simple"},
    {"name": "City", "path": "/4ed5d2eaed1a1fadcc41ad1d58ed603e", "category": "Simple"},
    {"name": "Company Type", "path": "/4cbb903cfae35c7d1844aac2363280b4", "category": "Simple"},
    {"name": "Customer Type", "path": "/4fe8a4cd07dfac7245a1e6cacb76ea5e", "category": "Simple"},
    {"name": "Vendor Type", "path": "/01f9a24e9744ed8edf5beb17513aafb4", "category": "Simple"},
    {"name": "Ledger Group", "path": "/2b0f7f32c7f7af6b51bf090558391d67", "category": "Simple"},
    {"name": "Commodity Master", "path": "/b515f30a4688bf67cd17f0cd09512ecf", "category": "Simple"},
    # Complex Masters
    {"name": "Charge Master", "path": "/af33c0fa2a013f51745b910eb3f70046", "category": "Complex"},
    {"name": "Company Master", "path": "/005480c8a6a0357d17cff2e8eb7e060d", "category": "Complex"},
    {"name": "Customer Master", "path": "/423b21e5932f11b123a1ddb35654b51b", "category": "Complex"},
    {"name": "Shipping Line Code", "path": "/9cdaacf035c457148bc2134dfe09fc50", "category": "Complex"},
    {"name": "Address", "path": "/de7c54d99428fb909bef013577070f0d", "category": "Complex"},
    # Ocean Masters
    {"name": "Job Type", "path": "/3f80ea99d7b24220db44943ed1838285", "category": "Ocean"},
    {"name": "Vessel", "path": "/ed6c460e3ce8e91132123ff09428a37d", "category": "Ocean"},
    {"name": "Ocean Port Sector", "path": "/51b6df155998f6c6b3ccc2701b59693d", "category": "Ocean"},
    {"name": "Ocean Port", "path": "/eac46b9f08f604c039b439ef2dd5663f", "category": "Ocean"},
    # Air Masters
    {"name": "Airport", "path": "/d1ed858f6d8126a814e31f18a7de5f8e", "category": "Air"},
    {"name": "Carrier Airlines", "path": "/1abf8c1a21e96e8d369b40b322331782", "category": "Air"},
    # Quote Setup
    {"name": "Carriers", "path": "/8ee4a920e024b1d3beadaadd006a0a31", "category": "Quote"},
    {"name": "Exchange Rates", "path": "/b63cf46906108334186c3ecf25f4ddb8", "category": "Quote"},
]

# JavaScript to discover all visible form fields
DISCOVER_FIELDS_JS = """
() => {
    const fields = [];
    document.querySelectorAll('input:not([type="hidden"]), select, textarea').forEach(el => {
        // Check if element is visible: either has offsetParent (not display:none)
        // or is inside an open modal
        const isVisible = el.offsetParent !== null ||
                          el.closest('.modal.show') !== null ||
                          el.closest('.modal.in') !== null ||
                          el.closest('.modal[style*="display: block"]') !== null;
        if (isVisible) {
            let label = '';
            if (el.id) {
                const lbl = document.querySelector(`label[for="${el.id}"]`);
                if (lbl) label = lbl.textContent.trim();
            }
            if (!label && el.closest('.form-group')) {
                const lbl = el.closest('.form-group').querySelector('label');
                if (lbl) label = lbl.textContent.trim();
            }
            if (!label && el.closest('.mb-3')) {
                const lbl = el.closest('.mb-3').querySelector('label');
                if (lbl) label = lbl.textContent.trim();
            }
            fields.push({
                'tag': el.tagName,
                'type': el.type || '',
                'name': el.name || '',
                'id': el.id || '',
                'placeholder': el.placeholder || '',
                'required': el.required,
                'readonly': el.readOnly || false,
                'disabled': el.disabled || false,
                'options': el.tagName === 'SELECT' ? Array.from(el.options).map(o => ({
                    'value': o.value,
                    'text': o.text.trim()
                })) : [],
                'label': label,
                'className': el.className || '',
                'value': el.value || ''
            });
        }
    });
    return fields;
}
"""

# JavaScript to check for success/error messages after submission
CHECK_RESULT_JS = """
() => {
    const result = { success: false, error: false, messages: [] };

    // Check for success indicators
    const successSelectors = [
        '.alert-success', '.toast-success', '.swal2-success',
        '.notification-success', '.text-success',
        '[class*="success"]', '.alert.alert-success'
    ];
    for (const sel of successSelectors) {
        const els = document.querySelectorAll(sel);
        els.forEach(el => {
            if (el.offsetParent !== null || el.textContent.trim()) {
                result.success = true;
                result.messages.push('SUCCESS: ' + el.textContent.trim().substring(0, 200));
            }
        });
    }

    // Check for SweetAlert success
    const swal = document.querySelector('.swal2-popup');
    if (swal) {
        const swalTitle = swal.querySelector('.swal2-title');
        const swalContent = swal.querySelector('.swal2-html-container, .swal2-content');
        const text = (swalTitle?.textContent || '') + ' ' + (swalContent?.textContent || '');
        if (text.toLowerCase().includes('success') || text.toLowerCase().includes('created') || text.toLowerCase().includes('saved') || text.toLowerCase().includes('added')) {
            result.success = true;
            result.messages.push('SWAL_SUCCESS: ' + text.trim().substring(0, 200));
        } else if (text.toLowerCase().includes('error') || text.toLowerCase().includes('fail') || text.toLowerCase().includes('invalid')) {
            result.error = true;
            result.messages.push('SWAL_ERROR: ' + text.trim().substring(0, 200));
        } else {
            result.messages.push('SWAL: ' + text.trim().substring(0, 200));
        }
    }

    // Check for toastr
    const toasts = document.querySelectorAll('.toast-message, .toastr, .Toastify__toast, #toast-container .toast');
    toasts.forEach(el => {
        const text = el.textContent.trim();
        if (text) {
            if (el.closest('.toast-success') || text.toLowerCase().includes('success')) {
                result.success = true;
                result.messages.push('TOAST_SUCCESS: ' + text.substring(0, 200));
            } else if (el.closest('.toast-error') || text.toLowerCase().includes('error')) {
                result.error = true;
                result.messages.push('TOAST_ERROR: ' + text.substring(0, 200));
            } else {
                result.messages.push('TOAST: ' + text.substring(0, 200));
            }
        }
    });

    // Check for error indicators
    const errorSelectors = [
        '.alert-danger', '.alert-error', '.toast-error',
        '.invalid-feedback:not(:empty)', '.field-error',
        '.text-danger', '.has-error', '.is-invalid',
        '.validation-error', '.error-message'
    ];
    for (const sel of errorSelectors) {
        const els = document.querySelectorAll(sel);
        els.forEach(el => {
            const text = el.textContent.trim();
            if (text && el.offsetParent !== null) {
                result.error = true;
                result.messages.push('ERROR: ' + text.substring(0, 200));
            }
        });
    }

    // Check for modal still open (might mean validation failed)
    const modal = document.querySelector('.modal.show, .modal.in, .modal[style*="display: block"]');
    if (modal) {
        result.messages.push('MODAL_STILL_OPEN');
    }

    return result;
}
"""


def generate_test_value(field, page_name):
    """Generate appropriate test data based on field type and attributes."""
    tag = field.get("tag", "")
    ftype = field.get("type", "").lower()
    name = field.get("name", "").lower()
    field_id = field.get("id", "").lower()
    placeholder = field.get("placeholder", "").lower()
    label = field.get("label", "").lower()
    identifier = name or field_id or label or placeholder

    # Skip readonly/disabled fields
    if field.get("readonly") or field.get("disabled"):
        return None

    # Skip search/filter fields
    if any(x in identifier for x in ["search", "filter", "datatable", "_length"]):
        return None

    # Skip file inputs
    if ftype == "file":
        return None

    # Skip checkbox/radio (handle separately)
    if ftype in ("checkbox", "radio"):
        return "CHECK"

    # Select fields
    if tag == "SELECT":
        options = field.get("options", [])
        # Pick second option if available (first is often blank/placeholder)
        non_empty = [o for o in options if o.get("value")]
        if len(non_empty) > 0:
            return {"type": "select", "value": non_empty[0]["value"]}
        elif len(options) > 1:
            return {"type": "select", "value": options[1]["value"]}
        return None

    # Build a clean identifier for the test value
    clean_name = (name or field_id or page_name).replace(" ", "_").replace("-", "_")
    clean_name = clean_name[:20]  # Keep it short

    # Date inputs
    if ftype == "date" or "date" in identifier:
        return "2026-04-18"

    # Email
    if ftype == "email" or "email" in identifier or "e-mail" in identifier:
        return "autotest@example.com"

    # Phone/mobile/tel
    if ftype == "tel" or any(x in identifier for x in ["phone", "mobile", "tel", "fax", "contact"]):
        return "1234567890"

    # Number inputs
    if ftype == "number" or any(x in identifier for x in ["amount", "rate", "qty", "quantity", "price", "cost", "weight", "volume"]):
        return "100"

    # URL
    if ftype == "url" or "url" in identifier or "website" in identifier:
        return "https://autotest.example.com"

    # PIN/ZIP/Postal code
    if any(x in identifier for x in ["pin", "zip", "postal"]):
        return "400001"

    # PAN
    if "pan" in identifier and "company" not in identifier:
        return "AAAPA1234A"

    # GST
    if "gst" in identifier or "gstin" in identifier:
        return "22AAAAA0000A1Z5"

    # Default text
    return f"AUTOTEST_{clean_name}"


def fill_field(page, field, value):
    """Fill a single form field with the given value."""
    if value is None:
        return False

    selector = None
    if field.get("id"):
        selector = f"#{field['id']}"
    elif field.get("name"):
        selector = f"[name=\"{field['name']}\"]"
    else:
        return False

    try:
        el = page.locator(selector).first
        if not el.is_visible(timeout=1000):
            return False

        if value == "CHECK":
            # Checkbox/radio - check it
            if not el.is_checked():
                el.check(timeout=2000)
            return True

        if isinstance(value, dict) and value.get("type") == "select":
            el.select_option(value=value["value"], timeout=3000)
            return True

        # Text-like input
        el.click(timeout=2000)
        el.fill("", timeout=1000)  # Clear first
        el.fill(str(value), timeout=3000)
        return True

    except Exception as e:
        # Try JavaScript fallback
        try:
            if isinstance(value, dict) and value.get("type") == "select":
                page.evaluate(f"""
                    () => {{
                        const el = document.querySelector('{selector}');
                        if (el) {{ el.value = '{value["value"]}'; el.dispatchEvent(new Event('change', {{bubbles: true}})); }}
                    }}
                """)
            elif value != "CHECK":
                page.evaluate(f"""
                    () => {{
                        const el = document.querySelector('{selector}');
                        if (el) {{
                            el.value = '{str(value).replace("'", "\\'")}';
                            el.dispatchEvent(new Event('input', {{bubbles: true}}));
                            el.dispatchEvent(new Event('change', {{bubbles: true}}));
                        }}
                    }}
                """)
            return True
        except Exception:
            return False


def find_and_click_add_button(page):
    """Find and click the Add New button. Returns True if found and clicked."""
    add_selectors = [
        "button:has-text('Add New')",
        "a:has-text('Add New')",
        "button:has-text('Add')",
        "a:has-text('Add')",
        ".btn:has-text('Add New')",
        ".btn:has-text('Add')",
        "button:has-text('Create')",
        "a:has-text('Create')",
        "button:has-text('New')",
        ".btn-primary:has-text('Add')",
        "[data-toggle='modal']:has-text('Add')",
        "[data-bs-toggle='modal']:has-text('Add')",
    ]
    for sel in add_selectors:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=2000):
                btn.click(timeout=5000)
                return True
        except Exception:
            continue

    # Try finding button via JS
    try:
        found = page.evaluate("""
            () => {
                const btns = document.querySelectorAll('button, a.btn, a[class*="btn"]');
                for (const btn of btns) {
                    const text = btn.textContent.trim().toLowerCase();
                    if (text.includes('add') || text.includes('new') || text.includes('create')) {
                        btn.click();
                        return true;
                    }
                }
                return false;
            }
        """)
        return found
    except Exception:
        return False


def find_and_click_submit(page):
    """Find and click the submit/save button. Returns True if found and clicked."""
    submit_selectors = [
        "button[type='submit']",
        "input[type='submit']",
        "button:has-text('Save')",
        "button:has-text('Submit')",
        "button:has-text('Create')",
        "button:has-text('Add')",
        ".btn-primary:has-text('Save')",
        ".btn-success:has-text('Save')",
        ".modal.show button[type='submit']",
        ".modal.show button:has-text('Save')",
        ".modal.show button:has-text('Submit')",
        ".modal.in button[type='submit']",
        ".modal.in button:has-text('Save')",
    ]
    for sel in submit_selectors:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=2000):
                btn.click(timeout=5000)
                return True
        except Exception:
            continue

    # JS fallback
    try:
        found = page.evaluate("""
            () => {
                // Try inside open modal first
                let container = document.querySelector('.modal.show, .modal.in, .modal[style*="display: block"]');
                if (!container) container = document;

                const btns = container.querySelectorAll('button, input[type="submit"]');
                for (const btn of btns) {
                    const text = btn.textContent.trim().toLowerCase();
                    if (btn.type === 'submit' || text.includes('save') || text.includes('submit') || text.includes('create')) {
                        btn.click();
                        return true;
                    }
                }
                return false;
            }
        """)
        return found
    except Exception:
        return False


def check_record_in_table(page, test_prefix="AUTOTEST_"):
    """Check if a record with AUTOTEST_ prefix appears in the page table."""
    try:
        content = page.evaluate("""
            (prefix) => {
                const tables = document.querySelectorAll('table');
                for (const table of tables) {
                    if (table.textContent.includes(prefix)) {
                        return true;
                    }
                }
                return false;
            }
        """, test_prefix)
        return content
    except Exception:
        return False


def test_master_page(page, master, results):
    """Test CRUD (Create) operation on a single master page."""
    page_name = master["name"]
    page_path = master["path"]
    page_url = BASE_URL + page_path
    safe_name = page_name.replace(" ", "_").replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    result = {
        "name": page_name,
        "category": master["category"],
        "url": page_url,
        "status": "UNKNOWN",
        "fields_found": 0,
        "fields_filled": 0,
        "fields_detail": [],
        "add_button_found": False,
        "submit_clicked": False,
        "success_detected": False,
        "error_detected": False,
        "record_in_table": False,
        "messages": [],
        "screenshots": {},
        "timestamp": timestamp,
        "error_info": None,
    }

    try:
        print(f"\n{'='*60}")
        print(f"Testing: {page_name} ({master['category']})")
        print(f"URL: {page_url}")
        print(f"{'='*60}")

        # Step 1: Navigate to the page
        print(f"  [1] Navigating to page...")
        try:
            page.goto(page_url, wait_until="networkidle", timeout=30000)
        except PlaywrightTimeout:
            page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        # Screenshot the list page
        list_screenshot = os.path.join(SCREENSHOT_DIR, f"{safe_name}_01_list.png")
        page.screenshot(path=list_screenshot, full_page=False)
        result["screenshots"]["list"] = list_screenshot
        print(f"  [2] List page screenshot saved")

        # Step 2: Find and click Add New button
        print(f"  [3] Looking for Add New button...")
        add_clicked = find_and_click_add_button(page)
        result["add_button_found"] = add_clicked

        if not add_clicked:
            result["status"] = "NO_ADD_BUTTON"
            result["messages"].append("Could not find Add New button on this page")
            print(f"  [!] No Add New button found - SKIPPING")
            return result

        print(f"  [4] Add New button clicked, waiting for form...")
        page.wait_for_timeout(2000)

        # Screenshot the form
        form_screenshot = os.path.join(SCREENSHOT_DIR, f"{safe_name}_02_form.png")
        page.screenshot(path=form_screenshot, full_page=False)
        result["screenshots"]["form"] = form_screenshot
        print(f"  [5] Form screenshot saved")

        # Step 3: Discover form fields
        print(f"  [6] Discovering form fields...")
        fields = page.evaluate(DISCOVER_FIELDS_JS)

        # Filter out likely non-form fields (search boxes, datatables length selectors, etc.)
        form_fields = []
        for f in fields:
            fid = (f.get("id", "") + f.get("name", "") + f.get("className", "")).lower()
            # Skip DataTables search, page length selectors, and login fields
            if any(skip in fid for skip in ["search", "datatables", "_length", "username", "password", "signupform"]):
                continue
            # Skip if it looks like a filter field
            if "filter" in fid:
                continue
            form_fields.append(f)

        result["fields_found"] = len(form_fields)
        print(f"  [7] Found {len(form_fields)} form fields")

        if len(form_fields) == 0:
            result["status"] = "NO_FIELDS"
            result["messages"].append("No form fields found after clicking Add New")
            print(f"  [!] No form fields found - SKIPPING")
            return result

        # Step 4: Fill each field
        print(f"  [8] Filling form fields...")
        filled_count = 0
        for field in form_fields:
            value = generate_test_value(field, page_name)
            field_info = {
                "name": field.get("name", ""),
                "id": field.get("id", ""),
                "type": field.get("type", ""),
                "tag": field.get("tag", ""),
                "label": field.get("label", ""),
                "value_attempted": str(value) if value else None,
                "filled": False,
            }

            if value is not None:
                success = fill_field(page, field, value)
                field_info["filled"] = success
                if success:
                    filled_count += 1
                    identifier = field.get("label") or field.get("name") or field.get("id") or "unknown"
                    print(f"       Filled: {identifier} = {value}")

            result["fields_detail"].append(field_info)

        result["fields_filled"] = filled_count
        print(f"  [9] Filled {filled_count}/{len(form_fields)} fields")

        # Screenshot after filling
        filled_screenshot = os.path.join(SCREENSHOT_DIR, f"{safe_name}_03_filled.png")
        page.screenshot(path=filled_screenshot, full_page=False)
        result["screenshots"]["filled"] = filled_screenshot

        # Step 5: Submit the form
        print(f"  [10] Submitting form...")
        submit_clicked = find_and_click_submit(page)
        result["submit_clicked"] = submit_clicked

        if not submit_clicked:
            result["status"] = "NO_SUBMIT_BUTTON"
            result["messages"].append("Could not find submit/save button")
            print(f"  [!] No submit button found")
            return result

        print(f"  [11] Form submitted, waiting for response...")
        page.wait_for_timeout(3000)

        # Screenshot after submission
        after_screenshot = os.path.join(SCREENSHOT_DIR, f"{safe_name}_04_after_submit.png")
        page.screenshot(path=after_screenshot, full_page=False)
        result["screenshots"]["after_submit"] = after_screenshot
        print(f"  [12] After-submit screenshot saved")

        # Step 6: Check result
        print(f"  [13] Checking for success/error messages...")
        check_result = page.evaluate(CHECK_RESULT_JS)
        result["success_detected"] = check_result.get("success", False)
        result["error_detected"] = check_result.get("error", False)
        result["messages"].extend(check_result.get("messages", []))

        # If a SweetAlert is open, dismiss it
        try:
            swal_btn = page.locator(".swal2-confirm, .swal2-actions button")
            if swal_btn.first.is_visible(timeout=1000):
                swal_btn.first.click(timeout=2000)
                page.wait_for_timeout(1000)
        except Exception:
            pass

        # If modal is still open, check if form was rejected
        try:
            modal_open = page.evaluate("""
                () => {
                    const m = document.querySelector('.modal.show, .modal.in, .modal[style*="display: block"]');
                    return m !== null;
                }
            """)
            if modal_open and not result["success_detected"]:
                result["messages"].append("Modal still open after submit - likely validation error")
        except Exception:
            pass

        # Step 7: Check if record appears in table
        # First close any modal if still open
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
        except Exception:
            pass

        # Navigate back to list to check
        try:
            page.goto(page_url, wait_until="networkidle", timeout=15000)
            page.wait_for_timeout(2000)
            result["record_in_table"] = check_record_in_table(page)
            if result["record_in_table"]:
                result["messages"].append("AUTOTEST record found in table")
                print(f"  [14] AUTOTEST record found in table!")
            else:
                print(f"  [14] AUTOTEST record NOT found in table")
        except Exception:
            pass

        # Determine final status
        if result["success_detected"]:
            result["status"] = "SUCCESS"
        elif result["record_in_table"]:
            result["status"] = "SUCCESS"
        elif result["error_detected"]:
            result["status"] = "ERROR"
        elif result["submit_clicked"] and not result["error_detected"]:
            result["status"] = "SUBMITTED_UNKNOWN"
        else:
            result["status"] = "UNKNOWN"

        print(f"  [RESULT] Status: {result['status']}")
        for msg in result["messages"]:
            print(f"           {msg}")

    except Exception as e:
        result["status"] = "EXCEPTION"
        result["error_info"] = str(e)
        result["messages"].append(f"Exception: {str(e)}")
        print(f"  [EXCEPTION] {str(e)}")

        # Try to take an error screenshot
        try:
            err_screenshot = os.path.join(SCREENSHOT_DIR, f"{safe_name}_error.png")
            page.screenshot(path=err_screenshot, full_page=False)
            result["screenshots"]["error"] = err_screenshot
        except Exception:
            pass

    return result


def main():
    print("=" * 70)
    print("Sena ERP - CRUD Masters Test Script")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    print(f"Pages to test: {len(MASTER_PAGES)}")
    print("=" * 70)

    all_results = {
        "run_timestamp": datetime.now().isoformat(),
        "base_url": BASE_URL,
        "total_pages": len(MASTER_PAGES),
        "summary": {},
        "pages": [],
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            ignore_https_errors=True,
        )
        context.set_default_timeout(30000)
        page = context.new_page()

        # Step 1: Login
        print("\n[LOGIN] Logging in to Sena ERP...")
        try:
            page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        except PlaywrightTimeout:
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        # Take login page screenshot
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "00_login_page.png"))

        # Login via JS
        page.evaluate("""
            () => {
                document.getElementById("username").value = "superadmin";
                document.getElementById("password").value = "Nick@#24";
                document.getElementById("signupForm").submit();
            }
        """)

        print("[LOGIN] Credentials submitted, waiting 8 seconds...")
        page.wait_for_timeout(8000)

        # Verify login
        current_url = page.url
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "00_after_login.png"))
        print(f"[LOGIN] Current URL after login: {current_url}")

        if "login" in current_url.lower() or "signin" in current_url.lower():
            print("[LOGIN] WARNING: May still be on login page!")
        else:
            print("[LOGIN] Login appears successful!")

        # Step 2: Test each master page
        for i, master in enumerate(MASTER_PAGES, 1):
            print(f"\n--- Page {i}/{len(MASTER_PAGES)} ---")
            result = test_master_page(page, master, all_results)
            all_results["pages"].append(result)

            # Save intermediate results after each page
            with open(RESULTS_FILE, "w") as f:
                json.dump(all_results, f, indent=2, default=str)

        browser.close()

    # Generate summary
    statuses = {}
    for r in all_results["pages"]:
        status = r["status"]
        statuses[status] = statuses.get(status, 0) + 1

    all_results["summary"] = {
        "total_tested": len(all_results["pages"]),
        "by_status": statuses,
        "success_count": statuses.get("SUCCESS", 0),
        "error_count": statuses.get("ERROR", 0),
        "exception_count": statuses.get("EXCEPTION", 0),
    }

    # Final save
    with open(RESULTS_FILE, "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total pages tested: {all_results['summary']['total_tested']}")
    for status, count in sorted(statuses.items()):
        print(f"  {status}: {count}")
    print(f"\nDetailed results saved to: {RESULTS_FILE}")
    print(f"Screenshots saved to: {SCREENSHOT_DIR}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
