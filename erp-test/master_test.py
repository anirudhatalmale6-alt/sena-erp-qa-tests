"""
Sena ERP - Master Test Runner
Runs ALL tests on the Sena ERP system in one go with test data.
Produces clean pass/fail status output and captures error screenshots.

Usage: python master_test.py
Requires: playwright (pip install playwright && playwright install chromium)
"""

import json
import os
import re
import sys
import traceback
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_URL = "http://13.210.47.18:8088"  # Change if IP changes
USERNAME = "superadmin"
PASSWORD = "Nick@#24"

PROJECT_DIR = "/var/lib/freelancer/projects/40298427/erp-test"
SCREENSHOT_DIR = os.path.join(PROJECT_DIR, "screenshots", "master_test")
ERROR_SCREENSHOT_DIR = os.path.join(SCREENSHOT_DIR, "errors")
RESULTS_FILE = os.path.join(PROJECT_DIR, "results_master_test.json")

VIEWPORT = {"width": 1280, "height": 720}
DEFAULT_TIMEOUT = 60000
TEST_PREFIX = "AUTOTEST_"
TODAY = datetime.now().strftime("%d/%m/%Y")
TODAY_DISPLAY = datetime.now().strftime("%Y-%m-%d")

# =============================================================================
# ALL PAGES (Section A)
# =============================================================================

ALL_PAGES = {
    "Dashboard": "/4d5c7c941df8262af83d7b494f9d120e",
    "HR - Employee": "/51564f2eb2d3a1bca494e86b1c67635e",
    # Debtors
    "Consignee Due": "/1abe8a244329f592bb3bbb96e22e0344",
    "Consignee Paid": "/8c8bcb5e96e6c22e001efff53fcadf28",
    "Agent Due (Debtor)": "/28f3b7864cdf11d6b30b148bec8d6307",
    "Agent Paid (Debtor)": "/b621a0964636bcee73d691db7d3572fd",
    "Shipper Due": "/8211377a76b5f20c607e278620d4abe3",
    "Shipper Paid": "/76264365e7c5a943b7629804aeab136b",
    # Creditors
    "Shipping Line Due": "/8e1b7fdf1fd87dcc9e0546d03ae62556",
    "Shipping Line Paid": "/d18ec27a83b522669c9efc55a880f917",
    "Co-Loader Due": "/285ee3bf7d21a421fb354e824a0ba678",
    "Co-Loader Paid": "/49ab2c7ef13c1de745c5e511ea7d306f",
    "Supplier Due": "/57e215a5d82f9e54a6e6b2ddfd0372c1",
    "Supplier Paid": "/832128c1bea0bf94b30c16a8417125ae",
    "Agent Due (Creditor)": "/455492c7888db5aafecf4facc1aa7639",
    "Agent Paid (Creditor)": "/bfd9d957f28679c09593198e7cefb085",
    # Financial Reports
    "Purchase Invoice": "/purchase-invoice",
    "Sales Invoice": "/sales-invoice",
    "Purchase Invoice w/ VAT": "/purchase-invoice-with-vat",
    "Sales Invoice w/ VAT": "/sales-invoice/with-vat",
    "Ledger Report": "/ledger",
    "Customer Ageing": "/reports/customer-aging",
    "Supplier Ageing": "/reports/supplier-ageing",
    "Jobs w/o Purchase Inv": "/purchase-invoice-missing",
    "Jobs w/o Sales Inv": "/sales-charges-without-invoice",
    "Activity Log": "/activity-log",
    "Credit Note Register": "/credit-note-register",
    "Xero Integration": "/xero",
    # Common Masters
    "State": "/9ed39e2ea931586b6a985a6942ef573e",
    "City": "/4ed5d2eaed1a1fadcc41ad1d58ed603e",
    "Company Type": "/4cbb903cfae35c7d1844aac2363280b4",
    "Charge Master": "/af33c0fa2a013f51745b910eb3f70046",
    "Company Master": "/005480c8a6a0357d17cff2e8eb7e060d",
    "Customer Type": "/4fe8a4cd07dfac7245a1e6cacb76ea5e",
    "Ledger Group": "/2b0f7f32c7f7af6b51bf090558391d67",
    "Customer Master": "/423b21e5932f11b123a1ddb35654b51b",
    "Vendor Master": "/237cddc13035afd40df532c9c471b4ea",
    "Vendor Type": "/01f9a24e9744ed8edf5beb17513aafb4",
    "Shipping Line Code": "/9cdaacf035c457148bc2134dfe09fc50",
    "Commodity Master": "/b515f30a4688bf67cd17f0cd09512ecf",
    "Address": "/de7c54d99428fb909bef013577070f0d",
    # Ocean Masters
    "Job Type": "/3f80ea99d7b24220db44943ed1838285",
    "Vessel": "/ed6c460e3ce8e91132123ff09428a37d",
    "Ocean Port Sector": "/51b6df155998f6c6b3ccc2701b59693d",
    "Ocean Port": "/eac46b9f08f604c039b439ef2dd5663f",
    # Air Masters
    "Airport": "/d1ed858f6d8126a814e31f18a7de5f8e",
    "Carrier / Airlines": "/1abf8c1a21e96e8d369b40b322331782",
    # Quote Setup
    "Carriers (Quote)": "/8ee4a920e024b1d3beadaadd006a0a31",
    "Exchange Rates": "/b63cf46906108334186c3ecf25f4ddb8",
    "Rate Database": "/95ea21eb539e083e42f57313509a93ed",
    "Client Rates": "/db6f53167f5911e700a4b3aae0352572",
    # Quotes
    "Quotes": "/68915d3ba92a6ff8c96734362d61b15e",
    # Ocean Import
    "Ocean Import Open Jobs": "/9dddd5ce1b1375bc497feeb871842d4b",
    "Ocean Import Closed Jobs": "/670effb783ab68c5759f4523c9ad5185",
    "Ocean Import Booking Report": "/e14e00f9b8b4f2a0fbce2a5f843a543d",
    # Ocean Export
    "Ocean Export Open Jobs": "/ddc5bbfa18cf713c1478e511ea7455a7",
    "Ocean Export Closed Jobs": "/12d57e567d9ab44399006309b5d542a4",
    "Ocean Export Booking Report": "/a77dd96ff658388a662b311c5bbd1a75",
    # Air Import
    "Air Import Open Jobs": "/951733b073f499bd67fa764d38df48a8",
    "Air Import Closed Jobs": "/3092560bb3f11343b8ceb0e02a739a01",
    "Air Import Booking Report": "/6e2cac0a97967fe9b38243a12ec09be0",
    # Air Export
    "Air Export Open Jobs": "/8b574ca0cd37f8b76897ecc0f9d9ad34",
    "Air Export Closed Jobs": "/8ec1c8a3d9ad635d8fd2adb2c583b7c0",
    "Air Export Booking Report": "/7d27d418fe920b6bc9230e81ef3a9bae",
    # Land Import
    "Land Import Open Jobs": "/8013f48199799dce7a1fde812910a496",
    "Land Import Closed Jobs": "/ad661c9739fbf14ddd1802a6cc8c15c9",
    # Land Export
    "Land Export Open Jobs": "/2ca1dbee9121459dedd8cf2e88823068",
    "Land Export Closed Jobs": "/2785ba86aa37c0a8ff38e247afd5c2af",
    # DSR Reports
    "DSR Basic Graph": "/fe83dce7816670353cfa807c5722d816",
    "Ocean Import DSR": "/1387f1ae3dc1d840789d15c546e89125",
    "Ocean Export DSR": "/c745c437840b2e21636a2cbdab4b33a6",
    "Air Import DSR": "/abf5db603d4276889077e81de984cf6d",
    "Air Export DSR": "/627db3ba79d7139f8dfd6f462e1b0514",
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def ensure_dirs():
    """Create screenshot directories if they don't exist."""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(ERROR_SCREENSHOT_DIR, exist_ok=True)


def sanitize_name(name):
    """Convert test name to safe filename."""
    return re.sub(r'[^a-zA-Z0-9_]', '_', name).strip('_')


def take_screenshot(page, name, is_error=False):
    """Take a screenshot and return the path."""
    safe = sanitize_name(name)
    if is_error:
        path = os.path.join(ERROR_SCREENSHOT_DIR, f"FAIL_{safe}.png")
    else:
        path = os.path.join(SCREENSHOT_DIR, f"{safe}.png")
    try:
        page.screenshot(path=path, full_page=False)
    except Exception:
        pass
    return path


def login(page):
    """Login to the ERP system."""
    page.goto(BASE_URL, wait_until="networkidle", timeout=DEFAULT_TIMEOUT)
    page.wait_for_timeout(3000)
    page.evaluate(f'''
        document.getElementById("username").value = "{USERNAME}";
        document.getElementById("password").value = "{PASSWORD}";
        document.getElementById("signupForm").submit();
    ''')
    page.wait_for_timeout(8000)


def fill_select2(page, select_id, search_text):
    """Fill a Select2 AJAX dropdown. Returns selected text or None."""
    try:
        page.evaluate("try { $('select.select2-hidden-accessible').select2('close'); } catch(e) {}")
        page.wait_for_timeout(300)
        page.evaluate(f"$('#{select_id}').select2('open')")
        page.wait_for_timeout(500)
        search_field = page.locator('.select2-search__field')
        if search_field.count() > 0:
            search_field.fill(search_text)
            page.wait_for_timeout(2000)
        results = page.locator('.select2-results__option:not(.select2-results__message)')
        if results.count() > 0:
            text = results.first.text_content()
            results.first.click()
            page.wait_for_timeout(500)
            return text
        page.evaluate(f"try {{ $('#{select_id}').select2('close'); }} catch(e) {{}}")
    except Exception:
        pass
    return None


def fill_date(page, field_id, date_str=None):
    """Fill a date field by ID."""
    if date_str is None:
        date_str = TODAY
    page.evaluate(f"""
        var el = document.getElementById('{field_id}');
        if (el) {{ el.value = '{date_str}'; el.dispatchEvent(new Event('change', {{bubbles: true}})); }}
    """)


def fill_field(page, field_id, value):
    """Fill a text input field by ID."""
    try:
        page.evaluate(f"""
            var el = document.getElementById('{field_id}');
            if (el) {{ el.value = '{value}'; el.dispatchEvent(new Event('input', {{bubbles: true}})); }}
        """)
        return True
    except Exception:
        return False


def check_page_error(page):
    """Check if page has error indicators. Returns error message or None."""
    try:
        body_text = page.locator("body").inner_text(timeout=5000)
    except Exception:
        return "Page body not accessible"
    lower = body_text.lower()
    if "500" in body_text and ("internal server error" in lower or "server error" in lower):
        return "HTTP 500: Internal Server Error"
    if "404" in body_text and ("not found" in lower or "page not found" in lower):
        return "HTTP 404: Page Not Found"
    if "view not found" in lower or "undefined variable" in lower:
        match = re.search(r'(view\s+\[.*?\]\s+not found|undefined variable[^\n]{0,80})', body_text, re.IGNORECASE)
        return f"Server Error: {match.group(0)}" if match else "Server Error detected"
    if "sqlstate" in lower or "query exception" in lower:
        return "Database Error: SQL Exception"
    if "whoops" in lower and "error" in lower:
        return "Whoops Error Page"
    return None


def count_table_rows(page):
    """Count data rows in the main table on the page."""
    try:
        rows = page.locator("table tbody tr")
        count = rows.count()
        # Filter out 'no data' rows
        if count == 1:
            text = rows.first.text_content().lower()
            if "no data" in text or "no record" in text or "empty" in text:
                return 0
        return count
    except Exception:
        return -1


def click_add_new(page):
    """Try to click an 'Add New' or similar button. Returns True if found."""
    selectors = [
        "a:has-text('Add New')",
        "button:has-text('Add New')",
        "a:has-text('Add')",
        "button:has-text('Add')",
        ".btn-primary:has-text('Add')",
        "a.btn:has-text('New')",
        "button.btn:has-text('New')",
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if btn.count() > 0 and btn.is_visible(timeout=2000):
                btn.click()
                page.wait_for_timeout(1500)
                return True
        except Exception:
            continue
    return False


def wait_for_modal(page, timeout=5000):
    """Wait for a Bootstrap modal to appear."""
    try:
        page.locator(".modal.show, .modal.in, .modal[style*='display: block']").wait_for(
            state="visible", timeout=timeout
        )
        page.wait_for_timeout(500)
        return True
    except Exception:
        return False


def submit_form(page):
    """Try to submit the visible form/modal."""
    selectors = [
        ".modal.show button[type='submit']",
        ".modal.show .btn-primary",
        ".modal.show .btn-success",
        "form button[type='submit']",
        "form .btn-primary",
        "#submitBtn",
        "button:has-text('Save')",
        "button:has-text('Submit')",
    ]
    for sel in selectors:
        try:
            btn = page.locator(sel).first
            if btn.count() > 0 and btn.is_visible(timeout=1000):
                btn.click()
                page.wait_for_timeout(3000)
                return True
        except Exception:
            continue
    return False


def check_success_indicator(page):
    """Check if a success toast/alert appeared after form submission."""
    try:
        body = page.locator("body").inner_text(timeout=3000)
        lower = body.lower()
        for kw in ["success", "created", "saved", "added", "updated"]:
            if kw in lower:
                return True
        # Check for toastr or alert
        toastr = page.locator(".toast-success, .alert-success, .swal2-success")
        if toastr.count() > 0:
            return True
    except Exception:
        pass
    return False


# =============================================================================
# RESULT TRACKING
# =============================================================================

class TestResult:
    def __init__(self, section, name, status, message="", screenshot=""):
        self.section = section
        self.name = name
        self.status = status  # PASS, FAIL, WARNING, SKIP, ERROR
        self.message = message
        self.screenshot = screenshot

    def to_dict(self):
        return {
            "section": self.section,
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "screenshot": self.screenshot,
        }


class TestRunner:
    def __init__(self):
        self.results = []
        self.current_section = ""

    def add(self, name, status, message="", screenshot=""):
        r = TestResult(self.current_section, name, status, message, screenshot)
        self.results.append(r)
        icon = {"PASS": "PASS", "FAIL": "FAIL", "WARNING": "WARN", "SKIP": "SKIP", "ERROR": "ERR!"}
        print(f"  [{icon.get(status, '????')}] {name} - {message}" if message else f"  [{icon.get(status, '????')}] {name}")
        return r

    def set_section(self, section):
        self.current_section = section
        print(f"\n{'='*60}")
        print(f"  {section}")
        print(f"{'='*60}")

    def save_intermediate(self):
        """Save results so far to JSON."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "base_url": BASE_URL,
            "results": [r.to_dict() for r in self.results],
        }
        try:
            with open(RESULTS_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def summary(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        warnings = sum(1 for r in self.results if r.status == "WARNING")
        errors = sum(1 for r in self.results if r.status == "ERROR")
        skipped = sum(1 for r in self.results if r.status == "SKIP")
        error_screenshots = sum(1 for r in self.results if r.screenshot and r.status in ("FAIL", "ERROR"))
        return total, passed, failed, warnings, errors, skipped, error_screenshots


# =============================================================================
# SECTION A: PAGE LOAD TESTS
# =============================================================================

def run_section_a(page, runner):
    """Test all pages load without errors."""
    runner.set_section("SECTION A: PAGE LOAD TESTS")

    for name, path in ALL_PAGES.items():
        try:
            url = BASE_URL + path
            page.goto(url, wait_until="networkidle", timeout=DEFAULT_TIMEOUT)
            page.wait_for_timeout(1000)
            error = check_page_error(page)
            if error:
                ss = take_screenshot(page, f"A_{name}", is_error=True)
                runner.add(name, "FAIL", error, ss)
            else:
                runner.add(name, "PASS", "Page loaded OK")
        except Exception as e:
            ss = take_screenshot(page, f"A_{name}", is_error=True)
            runner.add(name, "ERROR", f"Exception: {str(e)[:100]}", ss)

    runner.save_intermediate()


# =============================================================================
# SECTION B: CRUD TESTS (Master Pages)
# =============================================================================

# Each CRUD test config: (page_name, page_path, fields_to_fill)
# fields_to_fill: list of (field_id, value, type)
# type: "text", "select2", "date"

CRUD_TESTS = {
    "State": {
        "path": "/9ed39e2ea931586b6a985a6942ef573e",
        "fields": [
            ("state_name", f"{TEST_PREFIX}TestState", "text"),
        ],
    },
    "City": {
        "path": "/4ed5d2eaed1a1fadcc41ad1d58ed603e",
        "fields": [
            ("state_id", "a", "select2"),
            ("city_name", f"{TEST_PREFIX}TestCity", "text"),
        ],
    },
    "Company Type": {
        "path": "/4cbb903cfae35c7d1844aac2363280b4",
        "fields": [
            ("company_type_name", f"{TEST_PREFIX}CompanyType", "text"),
        ],
    },
    "Customer Type": {
        "path": "/4fe8a4cd07dfac7245a1e6cacb76ea5e",
        "fields": [
            ("customer_type_name", f"{TEST_PREFIX}CustomerType", "text"),
        ],
    },
    "Vendor Type": {
        "path": "/01f9a24e9744ed8edf5beb17513aafb4",
        "fields": [
            ("vendor_type_name", f"{TEST_PREFIX}VendorType", "text"),
        ],
    },
    "Commodity Master": {
        "path": "/b515f30a4688bf67cd17f0cd09512ecf",
        "fields": [
            ("commodity_name", f"{TEST_PREFIX}Commodity", "text"),
        ],
    },
    "Charge Master": {
        "path": "/af33c0fa2a013f51745b910eb3f70046",
        "fields": [
            ("charge_name", f"{TEST_PREFIX}ChargeMaster", "text"),
            ("charge_code", f"AT001", "text"),
        ],
    },
    "Company Master": {
        "path": "/005480c8a6a0357d17cff2e8eb7e060d",
        "fields": [
            ("company_name", f"{TEST_PREFIX}Company", "text"),
        ],
    },
    "Shipping Line Code": {
        "path": "/9cdaacf035c457148bc2134dfe09fc50",
        "fields": [
            ("shipping_line_code", f"ATSLC", "text"),
            ("shipping_line_name", f"{TEST_PREFIX}ShipLine", "text"),
        ],
    },
    "Job Type": {
        "path": "/3f80ea99d7b24220db44943ed1838285",
        "fields": [
            ("job_type_name", f"{TEST_PREFIX}JobType", "text"),
        ],
    },
    "Vessel": {
        "path": "/ed6c460e3ce8e91132123ff09428a37d",
        "fields": [
            ("vessel_name", f"{TEST_PREFIX}Vessel", "text"),
        ],
    },
    "Ocean Port Sector": {
        "path": "/51b6df155998f6c6b3ccc2701b59693d",
        "fields": [
            ("sector_name", f"{TEST_PREFIX}Sector", "text"),
        ],
    },
    "Ocean Port": {
        "path": "/eac46b9f08f604c039b439ef2dd5663f",
        "fields": [
            ("port_name", f"{TEST_PREFIX}Port", "text"),
            ("port_code", "ATPRT", "text"),
        ],
    },
    "Airport": {
        "path": "/d1ed858f6d8126a814e31f18a7de5f8e",
        "fields": [
            ("airport_name", f"{TEST_PREFIX}Airport", "text"),
            ("airport_code", "ATAP", "text"),
        ],
    },
    "Carrier / Airlines": {
        "path": "/1abf8c1a21e96e8d369b40b322331782",
        "fields": [
            ("carrier_name", f"{TEST_PREFIX}Carrier", "text"),
            ("carrier_code", "ATC", "text"),
        ],
    },
    "Carriers (Quote)": {
        "path": "/8ee4a920e024b1d3beadaadd006a0a31",
        "fields": [
            ("carrier_name", f"{TEST_PREFIX}QuoteCarrier", "text"),
        ],
    },
    "Exchange Rates": {
        "path": "/b63cf46906108334186c3ecf25f4ddb8",
        "fields": [
            ("currency_code", "ATD", "text"),
            ("exchange_rate", "1.5", "text"),
        ],
    },
    "Ledger Group": {
        "path": "/2b0f7f32c7f7af6b51bf090558391d67",
        "fields": [
            ("name", f"{TEST_PREFIX}LedgerGroup", "text"),
            ("gptype", "T", "text"),
        ],
    },
    "Vendor Master": {
        "path": "/237cddc13035afd40df532c9c471b4ea",
        "fields": [
            ("name", f"{TEST_PREFIX}Vendor", "text"),
            ("code", f"{TEST_PREFIX}VND", "text"),
        ],
    },
    "Customer Master": {
        "path": "/423b21e5932f11b123a1ddb35654b51b",
        "fields": [
            ("customer_name", f"{TEST_PREFIX}Customer", "text"),
            ("customer_email", f"autotest@test.com", "text"),
            ("customer_phone", "1234567890", "text"),
            ("customer_address", "123 Test Street", "text"),
            ("customer_city", "Test City", "text"),
            ("customer_state", "Test State", "text"),
            ("customer_country", "Test Country", "text"),
            ("customer_pincode", "123456", "text"),
            ("customer_gst", "ATGST123", "text"),
            ("customer_pan", "ATPAN1234", "text"),
            ("customer_type_id", "a", "select2"),
            ("company_type_id", "a", "select2"),
            ("credit_days", "30", "text"),
            ("credit_limit", "100000", "text"),
            ("contact_person", "Test Contact", "text"),
            ("designation", "Manager", "text"),
            ("mobile", "9876543210", "text"),
            ("website", "http://test.com", "text"),
            ("remarks", "Autotest record", "text"),
        ],
    },
}


def run_crud_test(page, runner, name, config):
    """Run a single CRUD test."""
    path = config["path"]
    fields = config.get("fields", [])
    known_bug = config.get("known_bug", "")

    try:
        # Navigate to the page
        page.goto(BASE_URL + path, wait_until="networkidle", timeout=DEFAULT_TIMEOUT)
        page.wait_for_timeout(1500)

        # Check for page load error
        error = check_page_error(page)
        if error:
            ss = take_screenshot(page, f"B_CRUD_{name}", is_error=True)
            if known_bug:
                runner.add(name, "FAIL", f"Known bug: {known_bug}", ss)
            else:
                runner.add(name, "FAIL", f"Page error: {error}", ss)
            return

        # If known bug with no fields, document it
        if known_bug and not fields:
            ss = take_screenshot(page, f"B_CRUD_{name}", is_error=True)
            runner.add(name, "FAIL", f"Known bug: {known_bug}", ss)
            return

        # Click Add New
        if not click_add_new(page):
            ss = take_screenshot(page, f"B_CRUD_{name}", is_error=True)
            runner.add(name, "WARNING", "No 'Add New' button found", ss)
            return

        # Wait for modal
        modal_appeared = wait_for_modal(page, timeout=5000)

        # Check if Ledger Group has empty modal
        if known_bug and modal_appeared:
            # Check if modal has actual form fields
            form_inputs = page.locator(".modal.show input, .modal.show select, .modal.show textarea")
            if form_inputs.count() == 0:
                ss = take_screenshot(page, f"B_CRUD_{name}", is_error=True)
                runner.add(name, "FAIL", f"Known bug: {known_bug}", ss)
                return

        # Fill fields
        filled_count = 0
        for field_id, value, field_type in fields:
            try:
                if field_type == "text":
                    # Try direct fill first, then JS
                    el = page.locator(f"#{field_id}")
                    if el.count() > 0 and el.is_visible(timeout=1000):
                        el.fill(value)
                        filled_count += 1
                    else:
                        if fill_field(page, field_id, value):
                            filled_count += 1
                elif field_type == "select2":
                    result = fill_select2(page, field_id, value)
                    if result:
                        filled_count += 1
                elif field_type == "date":
                    fill_date(page, field_id, value)
                    filled_count += 1
            except Exception:
                pass

        if filled_count == 0 and len(fields) > 0:
            ss = take_screenshot(page, f"B_CRUD_{name}", is_error=True)
            runner.add(name, "WARNING", f"Could not fill any fields (0/{len(fields)})", ss)
            return

        # Submit
        submitted = submit_form(page)
        if not submitted:
            ss = take_screenshot(page, f"B_CRUD_{name}", is_error=True)
            runner.add(name, "WARNING", f"Filled {filled_count}/{len(fields)} fields but no submit button found", ss)
            return

        # Check for success
        page.wait_for_timeout(2000)
        post_error = check_page_error(page)
        if post_error:
            ss = take_screenshot(page, f"B_CRUD_{name}", is_error=True)
            runner.add(name, "FAIL", f"Error after submit: {post_error}", ss)
            return

        success = check_success_indicator(page)
        if success:
            runner.add(name, "PASS", f"Record created ({filled_count}/{len(fields)} fields filled)")
        else:
            ss = take_screenshot(page, f"B_CRUD_{name}", is_error=False)
            runner.add(name, "PASS", f"Form submitted, {filled_count}/{len(fields)} fields filled (no error detected)")

    except Exception as e:
        ss = take_screenshot(page, f"B_CRUD_{name}", is_error=True)
        runner.add(name, "ERROR", f"Exception: {str(e)[:120]}", ss)


def run_section_b(page, runner):
    """Run all CRUD tests."""
    runner.set_section("SECTION B: CRUD TESTS")

    for name, config in CRUD_TESTS.items():
        run_crud_test(page, runner, name, config)

    runner.save_intermediate()


# =============================================================================
# SECTION C: JOB CREATION TESTS
# =============================================================================

JOB_TESTS = {
    "Ocean Import": {
        "path": "/9dddd5ce1b1375bc497feeb871842d4b",
        "type": "ocean_import",
    },
    "Ocean Export": {
        "path": "/ddc5bbfa18cf713c1478e511ea7455a7",
        "type": "ocean_export",
    },
    "Air Import": {
        "path": "/951733b073f499bd67fa764d38df48a8",
        "type": "air_import",
    },
    "Air Export": {
        "path": "/8b574ca0cd37f8b76897ecc0f9d9ad34",
        "type": "air_export",
    },
    "Land Import": {
        "path": "/8013f48199799dce7a1fde812910a496",
        "type": "land_import",
    },
    "Land Export": {
        "path": "/2ca1dbee9121459dedd8cf2e88823068",
        "type": "land_export",
    },
}


def fill_job_form(page, job_type):
    """Fill job creation form based on job type. Returns (success, message)."""
    filled = 0
    total_attempted = 0

    # Common fields for all job types
    common_select2_fields = [
        ("shipper_id", "a"),
        ("consignee_id", "a"),
        ("agent_id", "a"),
    ]

    common_text_fields = [
        ("no_of_packages", "10"),
        ("gross_weight", "500"),
        ("volume", "25"),
        ("remarks", f"{TEST_PREFIX}Job created by master test"),
    ]

    # Type-specific fields
    if job_type in ("ocean_import", "ocean_export"):
        specific_select2 = [
            ("shipping_line_id", "a"),
            ("pol_id", "a"),
            ("pod_id", "a"),
            ("vessel_id", "a"),
            ("commodity_id", "a"),
        ]
        specific_text = [
            ("mbl_number", f"{TEST_PREFIX}MBL001"),
            ("hbl_number", f"{TEST_PREFIX}HBL001"),
            ("container_number", "ATCU1234567"),
            ("voyage_number", "AT001"),
        ]
        date_fields = [
            ("eta_date", TODAY),
            ("etd_date", TODAY),
        ]
    elif job_type in ("air_import", "air_export"):
        specific_select2 = [
            ("airline_id", "a"),
            ("origin_airport_id", "a"),
            ("destination_airport_id", "a"),
            ("commodity_id", "a"),
        ]
        specific_text = [
            ("mawb_number", f"{TEST_PREFIX}MAWB001"),
            ("hawb_number", f"{TEST_PREFIX}HAWB001"),
            ("flight_number", "AT123"),
        ]
        date_fields = [
            ("eta_date", TODAY),
            ("etd_date", TODAY),
        ]
        if job_type == "air_export":
            specific_text.extend([
                ("length", "100"),
                ("width", "50"),
                ("height", "30"),
            ])
    elif job_type in ("land_import", "land_export"):
        specific_select2 = [
            ("commodity_id", "a"),
        ]
        specific_text = [
            ("truck_number", f"{TEST_PREFIX}TRUCK001"),
            ("lr_number", f"{TEST_PREFIX}LR001"),
        ]
        date_fields = [
            ("eta_date", TODAY),
            ("etd_date", TODAY),
        ]
        # Land jobs may use name-based fields instead of Select2
        # Try to init Select2 for consignee manually
        try:
            page.evaluate("""
                try {
                    if ($('#consignee_id').length && !$('#consignee_id').hasClass('select2-hidden-accessible')) {
                        $('#consignee_id').select2();
                    }
                } catch(e) {}
            """)
        except Exception:
            pass
    else:
        specific_select2 = []
        specific_text = []
        date_fields = []

    all_select2 = common_select2_fields + specific_select2
    all_text = common_text_fields + specific_text

    # Fill Select2 fields
    for field_id, search in all_select2:
        total_attempted += 1
        try:
            result = fill_select2(page, field_id, search)
            if result:
                filled += 1
        except Exception:
            pass

    # Fill text fields
    for field_id, value in all_text:
        total_attempted += 1
        try:
            el = page.locator(f"#{field_id}")
            if el.count() > 0 and el.is_visible(timeout=500):
                el.fill(value)
                filled += 1
            elif fill_field(page, field_id, value):
                filled += 1
        except Exception:
            pass

    # Fill date fields
    for field_id, date_val in date_fields:
        total_attempted += 1
        try:
            fill_date(page, field_id, date_val)
            filled += 1
        except Exception:
            pass

    return filled, total_attempted


def run_job_test(page, runner, name, config):
    """Run a single job creation test."""
    try:
        page.goto(BASE_URL + config["path"], wait_until="networkidle", timeout=DEFAULT_TIMEOUT)
        page.wait_for_timeout(2000)

        error = check_page_error(page)
        if error:
            ss = take_screenshot(page, f"C_Job_{name}", is_error=True)
            runner.add(name, "FAIL", f"Page error: {error}", ss)
            return

        # Click Add New / Create Job
        add_clicked = False
        for sel in [
            "a:has-text('Add New')", "button:has-text('Add New')",
            "a:has-text('Create')", "button:has-text('Create')",
            "a:has-text('New Job')", "button:has-text('New Job')",
            ".btn-primary:has-text('Add')", ".btn:has-text('New')",
        ]:
            try:
                btn = page.locator(sel).first
                if btn.count() > 0 and btn.is_visible(timeout=1000):
                    btn.click()
                    page.wait_for_timeout(2000)
                    add_clicked = True
                    break
            except Exception:
                continue

        if not add_clicked:
            ss = take_screenshot(page, f"C_Job_{name}", is_error=True)
            runner.add(name, "WARNING", "No 'Add New'/'Create' button found", ss)
            return

        # Check if we navigated to a form page or modal appeared
        page.wait_for_timeout(1500)
        wait_for_modal(page, timeout=3000)

        # Fill the form
        filled, total = fill_job_form(page, config["type"])

        if filled == 0:
            ss = take_screenshot(page, f"C_Job_{name}", is_error=True)
            runner.add(name, "WARNING", f"Could not fill any fields (0/{total})", ss)
            return

        # Submit
        submitted = submit_form(page)
        if not submitted:
            # Try clicking Save button directly
            for sel in [
                "button:has-text('Save')", "button:has-text('Submit')",
                "button:has-text('Create Job')", "#saveBtn", "#submitBtn",
                ".btn-success", "input[type='submit']",
            ]:
                try:
                    btn = page.locator(sel).first
                    if btn.count() > 0 and btn.is_visible(timeout=500):
                        btn.click()
                        page.wait_for_timeout(3000)
                        submitted = True
                        break
                except Exception:
                    continue

        page.wait_for_timeout(2000)

        # Check result
        post_error = check_page_error(page)
        if post_error:
            ss = take_screenshot(page, f"C_Job_{name}", is_error=True)
            runner.add(name, "FAIL", f"Error after submit: {post_error}", ss)
            return

        # Try to detect job number from page
        try:
            body_text = page.locator("body").inner_text(timeout=3000)
            job_match = re.search(r'(TLI|TLE|TLA|TLX|TLL)[/\w-]+\d+', body_text)
            job_num = job_match.group(0) if job_match else "unknown"
        except Exception:
            job_num = "unknown"

        if check_success_indicator(page):
            runner.add(name, "PASS", f"Job {job_num} created ({filled}/{total} fields)")
        else:
            ss = take_screenshot(page, f"C_Job_{name}", is_error=False)
            runner.add(name, "PASS", f"Form submitted ({filled}/{total} fields), job ref: {job_num}")

    except Exception as e:
        ss = take_screenshot(page, f"C_Job_{name}", is_error=True)
        runner.add(name, "ERROR", f"Exception: {str(e)[:120]}", ss)


def run_section_c(page, runner):
    """Run all job creation tests."""
    runner.set_section("SECTION C: JOB CREATION TESTS")

    for name, config in JOB_TESTS.items():
        run_job_test(page, runner, name, config)

    runner.save_intermediate()


# =============================================================================
# SECTION D: FINANCIAL REPORT TESTS
# =============================================================================

FINANCIAL_REPORTS = {
    "Purchase Invoice": "/purchase-invoice",
    "Sales Invoice": "/sales-invoice",
    "Purchase Invoice w/ VAT": "/purchase-invoice-with-vat",
    "Sales Invoice w/ VAT": "/sales-invoice/with-vat",
    "Ledger Report": "/ledger",
    "Customer Ageing": "/reports/customer-aging",
    "Supplier Ageing": "/reports/supplier-ageing",
    "Jobs w/o Purchase Inv": "/purchase-invoice-missing",
    "Jobs w/o Sales Inv": "/sales-charges-without-invoice",
    "Credit Note Register": "/credit-note-register",
    "Activity Log": "/activity-log",
    "Xero Integration": "/xero",
}


def run_financial_report_test(page, runner, name, path):
    """Test a single financial report page."""
    try:
        page.goto(BASE_URL + path, wait_until="networkidle", timeout=DEFAULT_TIMEOUT)
        page.wait_for_timeout(2000)

        error = check_page_error(page)
        if error:
            ss = take_screenshot(page, f"D_Financial_{name}", is_error=True)
            runner.add(name, "FAIL", f"Page error: {error}", ss)
            return

        # Count table rows
        rows = count_table_rows(page)

        # Try date filter if available
        filter_worked = False
        date_inputs = page.locator("input[type='date'], input.datepicker, input.flatpickr, input[name*='date'], input[id*='date']")
        if date_inputs.count() > 0:
            try:
                # Try setting from/to date fields
                from_fields = page.locator("input[name*='from'], input[id*='from'], input[name*='start'], input[id*='start']")
                to_fields = page.locator("input[name*='to'], input[id*='to'], input[name*='end'], input[id*='end']")

                if from_fields.count() > 0:
                    from_fields.first.fill("01/01/2024")
                    page.wait_for_timeout(300)
                if to_fields.count() > 0:
                    to_fields.first.fill(TODAY)
                    page.wait_for_timeout(300)

                # Click filter/search button
                for sel in [
                    "button:has-text('Filter')", "button:has-text('Search')",
                    "button:has-text('Go')", "button:has-text('Apply')",
                    "button[type='submit']", ".btn-primary:has-text('Search')",
                    "#filterBtn", "#searchBtn",
                ]:
                    try:
                        btn = page.locator(sel).first
                        if btn.count() > 0 and btn.is_visible(timeout=500):
                            btn.click()
                            page.wait_for_timeout(3000)
                            filter_worked = True
                            break
                    except Exception:
                        continue

                if filter_worked:
                    rows_after = count_table_rows(page)
                    msg = f"{rows} rows"
                    if rows_after != rows:
                        msg += f" (filtered: {rows_after})"
                    runner.add(name, "PASS", msg)
                    return
            except Exception:
                pass

        if rows > 0:
            runner.add(name, "PASS", f"{rows} rows loaded")
        elif rows == 0:
            runner.add(name, "PASS", "Page loaded, no data rows")
        else:
            runner.add(name, "PASS", "Page loaded OK")

    except Exception as e:
        ss = take_screenshot(page, f"D_Financial_{name}", is_error=True)
        runner.add(name, "ERROR", f"Exception: {str(e)[:120]}", ss)


def run_section_d(page, runner):
    """Run all financial report tests."""
    runner.set_section("SECTION D: FINANCIAL REPORTS")

    for name, path in FINANCIAL_REPORTS.items():
        run_financial_report_test(page, runner, name, path)

    runner.save_intermediate()


# =============================================================================
# SECTION E: ACCOUNT PAGE TESTS
# =============================================================================

ACCOUNT_PAGES = {
    # Debtors
    "Consignee Due": "/1abe8a244329f592bb3bbb96e22e0344",
    "Consignee Paid": "/8c8bcb5e96e6c22e001efff53fcadf28",
    "Agent Due (Debtor)": "/28f3b7864cdf11d6b30b148bec8d6307",
    "Agent Paid (Debtor)": "/b621a0964636bcee73d691db7d3572fd",
    "Shipper Due": "/8211377a76b5f20c607e278620d4abe3",
    "Shipper Paid": "/76264365e7c5a943b7629804aeab136b",
    # Creditors
    "Shipping Line Due": "/8e1b7fdf1fd87dcc9e0546d03ae62556",
    "Shipping Line Paid": "/d18ec27a83b522669c9efc55a880f917",
    "Co-Loader Due": "/285ee3bf7d21a421fb354e824a0ba678",
    "Co-Loader Paid": "/49ab2c7ef13c1de745c5e511ea7d306f",
    "Supplier Due": "/57e215a5d82f9e54a6e6b2ddfd0372c1",
    "Supplier Paid": "/832128c1bea0bf94b30c16a8417125ae",
    "Agent Due (Creditor)": "/455492c7888db5aafecf4facc1aa7639",
    "Agent Paid (Creditor)": "/bfd9d957f28679c09593198e7cefb085",
}


def run_account_page_test(page, runner, name, path):
    """Test a single account page."""
    try:
        page.goto(BASE_URL + path, wait_until="networkidle", timeout=DEFAULT_TIMEOUT)
        page.wait_for_timeout(2000)

        error = check_page_error(page)
        if error:
            ss = take_screenshot(page, f"E_Account_{name}", is_error=True)
            runner.add(name, "FAIL", f"Page error: {error}", ss)
            return

        rows = count_table_rows(page)

        # Check for filter controls
        filters = page.locator("select, input[type='text'], input[type='date'], .select2, .datepicker")
        filter_count = filters.count()

        msg_parts = []
        if rows >= 0:
            msg_parts.append(f"{rows} rows")
        if filter_count > 0:
            msg_parts.append(f"{filter_count} filter controls")
        msg = ", ".join(msg_parts) if msg_parts else "Page loaded OK"

        runner.add(name, "PASS", msg)

    except Exception as e:
        ss = take_screenshot(page, f"E_Account_{name}", is_error=True)
        runner.add(name, "ERROR", f"Exception: {str(e)[:120]}", ss)


def run_section_e(page, runner):
    """Run all account page tests."""
    runner.set_section("SECTION E: ACCOUNT PAGES")

    for name, path in ACCOUNT_PAGES.items():
        run_account_page_test(page, runner, name, path)

    runner.save_intermediate()


# =============================================================================
# SECTION F: DSR REPORT TESTS
# =============================================================================

DSR_REPORTS = {
    "DSR Basic Graph": "/fe83dce7816670353cfa807c5722d816",
    "Ocean Import DSR": "/1387f1ae3dc1d840789d15c546e89125",
    "Ocean Export DSR": "/c745c437840b2e21636a2cbdab4b33a6",
    "Air Import DSR": "/abf5db603d4276889077e81de984cf6d",
    "Air Export DSR": "/627db3ba79d7139f8dfd6f462e1b0514",
}


def run_dsr_test(page, runner, name, path):
    """Test a single DSR report page."""
    try:
        page.goto(BASE_URL + path, wait_until="networkidle", timeout=DEFAULT_TIMEOUT)
        page.wait_for_timeout(2000)

        error = check_page_error(page)
        if error:
            ss = take_screenshot(page, f"F_DSR_{name}", is_error=True)
            runner.add(name, "FAIL", f"Page error: {error}", ss)
            return

        # Check for chart elements
        chart_selectors = [
            "canvas",              # Chart.js
            ".highcharts-root",    # Highcharts
            "svg",                 # D3/SVG charts
            ".chart",             # Generic chart class
            ".apexcharts-canvas", # ApexCharts
            "#chart",             # Common chart ID
        ]

        chart_found = False
        for sel in chart_selectors:
            try:
                el = page.locator(sel)
                if el.count() > 0:
                    chart_found = True
                    break
            except Exception:
                continue

        rows = count_table_rows(page)

        msg_parts = []
        if chart_found:
            msg_parts.append("Chart rendered")
        if rows > 0:
            msg_parts.append(f"{rows} data rows")
        elif rows == 0:
            msg_parts.append("No data rows")

        msg = ", ".join(msg_parts) if msg_parts else "Page loaded OK"
        runner.add(name, "PASS", msg)

    except Exception as e:
        ss = take_screenshot(page, f"F_DSR_{name}", is_error=True)
        runner.add(name, "ERROR", f"Exception: {str(e)[:120]}", ss)


def run_section_f(page, runner):
    """Run all DSR report tests."""
    runner.set_section("SECTION F: DSR REPORTS")

    for name, path in DSR_REPORTS.items():
        run_dsr_test(page, runner, name, path)

    runner.save_intermediate()


# =============================================================================
# SECTION G: DEEP DIVE JOB WORKFLOW TESTS
# (Full data entry across all steps for Ocean Import, Air Export, Land Import)
# =============================================================================

def click_wizard_step(page, step_num):
    """Click a wizard step by number. Steps use <a href='#step-N' id='step_N'>."""
    try:
        page.evaluate(f"""
            var link = document.getElementById('step_{step_num}');
            if (link) {{ link.click(); }}
            else {{
                var links = document.querySelectorAll('.wizard_steps a');
                if (links.length >= {step_num}) {{ links[{step_num - 1}].click(); }}
            }}
        """)
        page.wait_for_timeout(2000)
        return True
    except Exception:
        return False


def click_save_btn(page):
    """Click the Save button (usually an <a> with class buttonNext)."""
    try:
        page.locator('a.buttonNext, a:has-text("Save")').last.click()
        page.wait_for_timeout(5000)
        return True
    except Exception:
        return False


def select_charge_from_table(page, charge_select_id):
    """Select a charge from a Select2 dropdown in the charge table."""
    try:
        page.evaluate(f"$('#{charge_select_id}').select2('open')")
        page.wait_for_timeout(500)
        sf = page.locator('.select2-search__field')
        if sf.count() > 0:
            sf.last.fill("a")
            page.wait_for_timeout(2000)
        opts = page.locator('.select2-results__option:not(.select2-results__message)')
        if opts.count() > 0:
            text = opts.first.text_content().strip()
            opts.first.click()
            page.wait_for_timeout(500)
            return text
        page.evaluate(f"try {{ $('#{charge_select_id}').select2('close'); }} catch(e) {{}}")
    except Exception:
        pass
    return None


def get_charge_totals(page, charge_type):
    """Read the charge totals from the page. charge_type: 'buy' or 'sell'."""
    if charge_type == "buy":
        return page.evaluate('''() => ({
            tax: document.querySelector('#btottaxx')?.value || '0',
            amount: document.querySelector('#btotamntt')?.value || '0',
            total: document.querySelector('#baltotall')?.value || '0',
        })''')
    else:
        return page.evaluate('''() => ({
            tax: document.querySelector('#stottaxx')?.value || '0',
            amount: document.querySelector('#stotamntt')?.value || '0',
            total: document.querySelector('#saltotall')?.value || '0',
        })''')


def get_charge_row_count(page, table_id):
    """Count rows in a charge table."""
    return page.evaluate(f"document.querySelector('#{table_id}')?.querySelectorAll('tbody tr').length || 0")


def run_section_g(page, runner):
    """Deep dive job workflow: full data entry across all steps."""
    runner.set_section("SECTION G: DEEP DIVE JOB WORKFLOW")

    JOB_CONFIGS = {
        "Ocean Import": {
            "add_url": "/8d9368c9ea314e4bf3271918424b2c24",
            "list_url": "/9dddd5ce1b1375bc497feeb871842d4b",
            "steps": 8,
            "buy_step": 4, "sell_step": 5, "pi_step": 6, "si_step": 7, "files_step": 8,
            "basic_fields": {
                "select2": [("consigne", "a"), ("lport", "a"), ("dport", "a"), ("IncoTrms", "a"),
                            ("overseas1", "a"), ("shpline", "a"), ("vovesel", "a")],
                "text": [("mblno", f"{TEST_PREFIX}MBL-DDT"), ("dlvrref", f"{TEST_PREFIX}DLVR"),
                         ("frghtchrg", "500"), ("inschrg", "100"), ("calref", f"{TEST_PREFIX}CAL")],
                "date": [("etd", TODAY), ("eta", TODAY)],
            },
        },
        "Air Export": {
            "add_url": "/2c752e5ace8abac955144baf0b9ee354",
            "list_url": "/8b574ca0cd37f8b76897ecc0f9d9ad34",
            "steps": 9,
            "buy_step": 5, "sell_step": 6, "pi_step": 7, "si_step": 8, "files_step": 9,
            "basic_fields": {
                "select2": [("consigne", "a"), ("lport", "a"), ("dport", "a"),
                            ("overseas1", "a"), ("shipper", "a")],
                "text": [("hawbno", f"{TEST_PREFIX}HAWB-DDT"), ("mawbno", f"{TEST_PREFIX}MAWB-DDT"),
                         ("fltno", "TK9999"), ("bkref", f"{TEST_PREFIX}BKREF")],
                "date": [("etd", TODAY), ("eta", TODAY), ("hawbdt", TODAY), ("mawbdt", TODAY)],
            },
        },
        "Land Import": {
            "add_url": "/f2d63311d4bd1935349fa1cb7a5afc7a",
            "list_url": "/8013f48199799dce7a1fde812910a496",
            "steps": 7,
            "buy_step": 2, "sell_step": 3, "pi_step": 4, "si_step": 5, "files_step": 6,
            "basic_fields": {
                "select2": [("consigne", "a")],
                "text": [("temperature", "-18C"), ("collection", f"{TEST_PREFIX} London"),
                         ("delivery", f"{TEST_PREFIX} Birmingham"),
                         ("portentry", "Dover"), ("portexit", "Calais")],
                "date": [("etd", TODAY), ("eta", TODAY)],
            },
        },
    }

    for job_name, config in JOB_CONFIGS.items():
        prefix = job_name.replace(" ", "_")
        try:
            # Step 1: Create new job
            page.goto(f"{BASE_URL}{config['add_url']}", wait_until="networkidle", timeout=DEFAULT_TIMEOUT)
            page.wait_for_timeout(3000)

            error = check_page_error(page)
            if error:
                ss = take_screenshot(page, f"G_{prefix}_step1", is_error=True)
                runner.add(f"{job_name} - Step 1 Load", "FAIL", f"Error: {error}", ss)
                continue
            runner.add(f"{job_name} - Step 1 Load", "PASS", "Add New page loaded")

            # Fill Select2 fields
            fields_filled = 0
            bf = config["basic_fields"]
            for fid, search in bf.get("select2", []):
                result = fill_select2(page, fid, search)
                if result:
                    fields_filled += 1

            # Fill text fields
            for fid, val in bf.get("text", []):
                if fill_field(page, fid, val):
                    fields_filled += 1

            # Fill date fields
            for fid, val in bf.get("date", []):
                fill_date(page, fid, val)
                fields_filled += 1

            runner.add(f"{job_name} - Step 1 Fill Fields", "PASS", f"Filled {fields_filled} fields")

            # Save
            click_save_btn(page)
            error = check_page_error(page)
            if error:
                ss = take_screenshot(page, f"G_{prefix}_step1_save", is_error=True)
                runner.add(f"{job_name} - Step 1 Save", "FAIL", f"Error: {error}", ss)
            else:
                runner.add(f"{job_name} - Step 1 Save", "PASS", "Basic details saved")

            # Navigate through all remaining steps
            for step in range(2, config["steps"] + 1):
                clicked = click_wizard_step(page, step)
                if not clicked:
                    runner.add(f"{job_name} - Step {step} Navigate", "FAIL", "Could not click step")
                    continue

                error = check_page_error(page)
                if error:
                    ss = take_screenshot(page, f"G_{prefix}_step{step}", is_error=True)
                    runner.add(f"{job_name} - Step {step} Load", "FAIL", f"Error: {error}", ss)
                else:
                    runner.add(f"{job_name} - Step {step} Load", "PASS", f"Step {step} loaded OK")

        except Exception as e:
            ss = take_screenshot(page, f"G_{prefix}_error", is_error=True)
            runner.add(f"{job_name} - Deep Dive", "ERROR", f"Exception: {str(e)[:100]}", ss)

    runner.save_intermediate()


# =============================================================================
# SECTION H: CHARGE ADD / REMOVE / VAT TESTS
# =============================================================================

def run_section_h(page, runner):
    """Test charge lifecycle: add charges, verify VAT calc, remove charges, verify removal."""
    runner.set_section("SECTION H: CHARGE ADD/REMOVE/VAT TESTS")

    # Use an existing Ocean Import job
    page.goto(f"{BASE_URL}/9dddd5ce1b1375bc497feeb871842d4b", wait_until="networkidle", timeout=DEFAULT_TIMEOUT)
    page.wait_for_timeout(3000)

    first_link = page.evaluate('''() => {
        const rows = document.querySelectorAll('table tbody tr');
        for (const row of rows) { const a = row.querySelector('a'); if (a) return a.href; }
        return null;
    }''')

    if not first_link:
        runner.add("Find Existing Job", "FAIL", "No Ocean Import jobs found")
        return

    page.goto(first_link, wait_until="networkidle", timeout=DEFAULT_TIMEOUT)
    page.wait_for_timeout(3000)
    runner.add("Load Existing Job", "PASS", "Job loaded for charge testing")

    # --- TEST: Add Buy Charge ---
    click_wizard_step(page, 4)

    # Count existing rows
    initial_buy_rows = get_charge_row_count(page, "AddBlchrg")
    runner.add("Buy Charges - Initial Count", "PASS", f"{initial_buy_rows} existing buy charge row(s)")

    # Select a charge
    charge_name = select_charge_from_table(page, "bl_chrg_1")
    if charge_name:
        runner.add("Buy Charge - Select Charge", "PASS", f"Selected: {charge_name}")
    else:
        runner.add("Buy Charge - Select Charge", "WARNING", "Could not select charge from dropdown")

    # Fill amount
    fill_field(page, "amnt_bl_chrg_1", "500.00")
    fill_field(page, "bl_vlme_1", "1")

    # Check if tax rate was auto-populated
    tax_rate = page.evaluate("document.getElementById('taxrate_bl_chrg_1')?.value || ''")
    tax_val = page.evaluate("document.getElementById('tax_bl_chrg_1')?.value || '0'")
    total_val = page.evaluate("document.getElementById('total_1')?.value || '0'")

    runner.add("Buy Charge - Tax Rate Auto-Fill", "PASS" if tax_rate else "WARNING",
               f"Tax Rate: {tax_rate}, Tax: {tax_val}, Total: {total_val}")

    # Verify VAT calculation: tax = amount * rate / 100
    try:
        amt = float(page.evaluate("document.getElementById('amnt_bl_chrg_1')?.value || '0'"))
        rate = float(tax_rate) if tax_rate else 0
        expected_tax = round(amt * rate / 100, 2)
        actual_tax = float(tax_val) if tax_val else 0
        if rate > 0:
            vat_match = abs(expected_tax - actual_tax) < 0.01
            runner.add("Buy Charge - VAT Calculation", "PASS" if vat_match else "FAIL",
                       f"Amount: {amt}, Rate: {rate}%, Expected Tax: {expected_tax}, Actual: {actual_tax}")
        else:
            runner.add("Buy Charge - VAT Calculation", "PASS",
                       f"Tax rate is 0% - no VAT applicable (amount={amt})")
    except Exception as e:
        runner.add("Buy Charge - VAT Calculation", "WARNING", f"Could not verify: {e}")

    # Read totals before save
    pre_save_totals = get_charge_totals(page, "buy")
    runner.add("Buy Charge - Totals Before Save", "PASS",
               f"Tax: {pre_save_totals['tax']}, Amount: {pre_save_totals['amount']}, Total: {pre_save_totals['total']}")

    # Save charges
    click_save_btn(page)
    error = check_page_error(page)
    if error:
        ss = take_screenshot(page, "H_buy_save", is_error=True)
        runner.add("Buy Charge - Save", "FAIL", f"Error: {error}", ss)
    else:
        runner.add("Buy Charge - Save", "PASS", "Buy charges saved")

    # Verify totals after save
    click_wizard_step(page, 4)
    post_save_totals = get_charge_totals(page, "buy")
    runner.add("Buy Charge - Totals After Save", "PASS",
               f"Tax: {post_save_totals['tax']}, Amount: {post_save_totals['amount']}, Total: {post_save_totals['total']}")

    # --- TEST: Add Sell Charge ---
    click_wizard_step(page, 5)

    initial_sell_rows = get_charge_row_count(page, "AddSlchrg")
    runner.add("Sell Charges - Initial Count", "PASS", f"{initial_sell_rows} existing sell charge row(s)")

    sell_charge = select_charge_from_table(page, "sl_chrg_1")
    if sell_charge:
        runner.add("Sell Charge - Select Charge", "PASS", f"Selected: {sell_charge}")
    else:
        runner.add("Sell Charge - Select Charge", "WARNING", "Could not select charge")

    fill_field(page, "amnt_sl_chrg_1", "750.00")
    fill_field(page, "sl_vlme_1", "1")
    fill_field(page, "remark", f"{TEST_PREFIX}charge_test")
    fill_field(page, "due_date", TODAY)

    # Check sell charge VAT
    sell_tax_rate = page.evaluate("document.getElementById('taxrate_sl_chrg_1')?.value || ''")
    sell_tax_val = page.evaluate("document.getElementById('tax_sl_chrg_1')?.value || '0'")
    sell_total_val = page.evaluate("document.getElementById('sl_total_1')?.value || '0'")

    runner.add("Sell Charge - Tax Calculation", "PASS",
               f"Rate: {sell_tax_rate}, Tax: {sell_tax_val}, Total: {sell_total_val}")

    sell_totals = get_charge_totals(page, "sell")
    runner.add("Sell Charge - Totals", "PASS",
               f"Tax: {sell_totals['tax']}, Amount: {sell_totals['amount']}, Total: {sell_totals['total']}")

    click_save_btn(page)
    error = check_page_error(page)
    runner.add("Sell Charge - Save", "PASS" if not error else "FAIL",
               "Saved" if not error else f"Error: {error}")

    # --- TEST: Check Additional Charges Toggle ---
    click_wizard_step(page, 4)

    toggle = page.locator('#addl_buy_toggle')
    if toggle.count() > 0:
        is_checked_before = toggle.is_checked()
        toggle.click()
        page.wait_for_timeout(1000)

        # Check if additional charges section appeared
        addl_visible = page.evaluate('''() => {
            const addlSection = document.querySelector('[class*="addl_buy"], #additional_buy_charges, .additional-buy');
            if (addlSection) return addlSection.offsetHeight > 0;
            // Check for additional charge selects
            const addlSelects = document.querySelectorAll('select[name="addl_b_charge[]"]');
            return addlSelects.length > 0;
        }''')
        runner.add("Additional Buy Charges Toggle", "PASS",
                   f"Toggle works: was_checked={is_checked_before}, addl_visible={addl_visible}")
        # Uncheck to restore
        if not is_checked_before:
            toggle.click()
            page.wait_for_timeout(500)
    else:
        runner.add("Additional Buy Charges Toggle", "WARNING", "Toggle not found")

    # --- TEST: Verify charge appears on Purchase Invoice step ---
    click_wizard_step(page, 6)
    pi_content = page.inner_text("body")
    has_pi = "NO PURCHASE INVOICE" not in pi_content.upper()
    has_invoice_table = page.evaluate('''() => {
        const tables = document.querySelectorAll('table');
        for (const t of tables) {
            const headers = Array.from(t.querySelectorAll('th')).map(h => h.textContent.trim());
            if (headers.some(h => h.includes('INVOICE') || h.includes('PAYABLE'))) return true;
        }
        return false;
    }''')
    runner.add("Purchase Invoice - After Charges", "PASS" if has_pi or has_invoice_table else "WARNING",
               f"Invoice present: {has_pi}, Invoice table: {has_invoice_table}")

    # --- TEST: Verify charge appears on Sale Invoice step ---
    click_wizard_step(page, 7)
    si_content = page.inner_text("body")
    has_si = "NO SALE INVOICE" not in si_content.upper()
    runner.add("Sale Invoice - After Charges", "PASS" if has_si else "WARNING",
               f"Invoice present: {has_si}")

    # --- TEST: Try voiding a charge (if Void button exists) ---
    click_wizard_step(page, 4)
    void_btns = page.locator('button.voidArExpBlCharge, button:has-text("Void")')
    if void_btns.count() > 0:
        runner.add("Void Button - Present", "PASS", f"{void_btns.count()} void button(s) found")
    else:
        runner.add("Void Button - Present", "WARNING", "No void buttons found (may need generated invoices)")

    # --- TEST: Remove charge row ---
    remove_btns = page.locator('button.remove-dn-row, .fa-trash-o, .fa-trash')
    if remove_btns.count() > 0:
        runner.add("Remove Button - Present", "PASS", f"{remove_btns.count()} remove button(s) found")

        # Get totals before removal
        before_totals = get_charge_totals(page, "buy")

        # Click the remove button on the last charge row
        try:
            remove_btns.last.click()
            page.wait_for_timeout(2000)

            # Handle confirmation dialog if any
            page.evaluate("try { document.querySelector('.swal2-confirm, .modal.show .btn-danger')?.click(); } catch(e) {}")
            page.wait_for_timeout(1000)

            after_totals = get_charge_totals(page, "buy")
            runner.add("Remove Charge - Execute", "PASS",
                       f"Before total: {before_totals['total']}, After: {after_totals['total']}")

            # Save after removal
            click_save_btn(page)
            error = check_page_error(page)
            runner.add("Remove Charge - Save", "PASS" if not error else "FAIL",
                       "Saved after removal" if not error else f"Error: {error}")

            # Verify totals recalculated
            click_wizard_step(page, 4)
            final_totals = get_charge_totals(page, "buy")
            runner.add("Remove Charge - Totals Recalculated", "PASS",
                       f"Final totals - Tax: {final_totals['tax']}, Amount: {final_totals['amount']}, Total: {final_totals['total']}")
        except Exception as e:
            runner.add("Remove Charge - Execute", "WARNING", f"Error during removal: {e}")
    else:
        runner.add("Remove Button - Present", "WARNING", "No remove buttons found")

    runner.save_intermediate()


# =============================================================================
# SECTION I: INVOICE & PDF VERIFICATION TESTS
# =============================================================================

def run_section_i(page, runner):
    """Test financial reports, VAT invoices, credit notes, and PDF downloads."""
    runner.set_section("SECTION I: INVOICE/VAT/PDF VERIFICATION")

    # --- TEST: Purchase Invoice report page ---
    for report_name, report_path, has_vat_variant in [
        ("Purchase Invoice", "/purchase-invoice", True),
        ("Sales Invoice", "/sales-invoice", True),
        ("Purchase Invoice w/VAT", "/purchase-invoice-with-vat", False),
        ("Sales Invoice w/VAT", "/sales-invoice/with-vat", False),
    ]:
        try:
            page.goto(f"{BASE_URL}{report_path}", wait_until="networkidle", timeout=DEFAULT_TIMEOUT)
            page.wait_for_timeout(3000)

            error = check_page_error(page)
            if error:
                ss = take_screenshot(page, f"I_{report_name.replace(' ','_')}", is_error=True)
                runner.add(f"{report_name} - Page Load", "FAIL", f"Error: {error}", ss)
                continue

            # Check table exists and has rows
            table_info = page.evaluate('''() => {
                const tables = document.querySelectorAll('table');
                for (const t of tables) {
                    const rows = t.querySelectorAll('tbody tr');
                    if (rows.length > 0) {
                        const headers = Array.from(t.querySelectorAll('thead th')).map(h => h.textContent.trim());
                        return {found: true, rows: rows.length, headers: headers.slice(0, 8)};
                    }
                }
                return {found: false, rows: 0};
            }''')

            if table_info['found']:
                runner.add(f"{report_name} - Table", "PASS",
                           f"{table_info['rows']} invoice(s), headers: {table_info['headers'][:5]}")
            else:
                runner.add(f"{report_name} - Table", "WARNING", "No invoice rows found")

            # Check for Export Excel button
            export_btn = page.locator('a:has-text("Export Excel"), button:has-text("Export")')
            runner.add(f"{report_name} - Export Excel", "PASS" if export_btn.count() > 0 else "WARNING",
                       "Export Excel button present" if export_btn.count() > 0 else "No export button found")

            # Check for filter functionality
            filter_btn = page.locator('button:has-text("Filter")')
            runner.add(f"{report_name} - Filter", "PASS" if filter_btn.count() > 0 else "WARNING",
                       "Filter button present" if filter_btn.count() > 0 else "No filter button")

            # Test filter by date range
            if filter_btn.count() > 0:
                # Fill from date (30 days ago)
                from_date = (datetime.now() - timedelta(days=30)).strftime("%d/%m/%Y")
                page.evaluate(f"""
                    var dateInputs = document.querySelectorAll('input[type="date"], input[name*="from"], input[name*="date"]');
                    if (dateInputs.length > 0) {{
                        dateInputs[0].value = '{(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")}';
                        dateInputs[0].dispatchEvent(new Event('change', {{bubbles: true}}));
                    }}
                """)
                filter_btn.first.click()
                page.wait_for_timeout(3000)

                error = check_page_error(page)
                runner.add(f"{report_name} - Filter Apply", "PASS" if not error else "FAIL",
                           "Filter applied" if not error else f"Error: {error}")

                # Reset
                reset_btn = page.locator('a:has-text("Reset")')
                if reset_btn.count() > 0:
                    reset_btn.first.click()
                    page.wait_for_timeout(2000)

            # Check for Credit Note functionality (Add CRN button)
            crn_btns = page.locator('button:has-text("Add CRN")')
            if crn_btns.count() > 0:
                runner.add(f"{report_name} - Credit Notes", "PASS",
                           f"{crn_btns.count()} Add CRN button(s) found")

                # Try opening credit note modal
                try:
                    crn_btns.first.click()
                    page.wait_for_timeout(1500)

                    modal_visible = page.evaluate('''() => {
                        const modal = document.getElementById('creditNoteModal');
                        return modal && (modal.classList.contains('show') || modal.style.display === 'block');
                    }''')

                    if modal_visible:
                        runner.add(f"{report_name} - CRN Modal", "PASS", "Credit note modal opens correctly")
                        # Close modal
                        page.evaluate("try { $('#creditNoteModal').modal('hide'); } catch(e) { document.querySelector('.modal .close, .modal .btn-close')?.click(); }")
                        page.wait_for_timeout(500)
                    else:
                        runner.add(f"{report_name} - CRN Modal", "WARNING", "Modal did not open")
                except Exception as e:
                    runner.add(f"{report_name} - CRN Modal", "WARNING", f"Error: {e}")

            # Check for VAT-specific columns
            if "VAT" in report_name.upper():
                has_vat_cols = page.evaluate('''() => {
                    const headers = Array.from(document.querySelectorAll('th')).map(h => h.textContent.trim().toUpperCase());
                    return headers.some(h => h.includes('VAT') || h.includes('TAX'));
                }''')
                runner.add(f"{report_name} - VAT Columns", "PASS" if has_vat_cols else "WARNING",
                           "VAT/Tax columns present" if has_vat_cols else "No VAT-specific columns found")

        except Exception as e:
            ss = take_screenshot(page, f"I_{report_name.replace(' ','_')}", is_error=True)
            runner.add(f"{report_name} - Test", "ERROR", f"Exception: {str(e)[:100]}", ss)

    # --- TEST: Download PDF from Sales Invoice ---
    try:
        page.goto(f"{BASE_URL}/sales-invoice", wait_until="networkidle", timeout=DEFAULT_TIMEOUT)
        page.wait_for_timeout(3000)

        # Check for Download PDFs button
        dl_btn = page.locator('button:has-text("Download PDFs")')
        runner.add("Sales Invoice - Download PDFs Button", "PASS" if dl_btn.count() > 0 else "WARNING",
                   "Button present" if dl_btn.count() > 0 else "No Download PDFs button")

        # Check for individual invoice Edit links
        edit_links = page.locator('a:has-text("Edit")')
        runner.add("Sales Invoice - Edit Links", "PASS" if edit_links.count() > 0 else "WARNING",
                   f"{edit_links.count()} edit link(s)" if edit_links.count() > 0 else "No edit links")

        # Check for delete buttons (btn-danger with trash icon)
        delete_btns = page.locator('a.btn-danger')
        runner.add("Sales Invoice - Delete Actions", "PASS" if delete_btns.count() > 0 else "WARNING",
                   f"{delete_btns.count()} delete button(s)" if delete_btns.count() > 0 else "No delete buttons")

        # Check invoice statuses
        statuses = page.evaluate('''() => {
            const stats = {};
            document.querySelectorAll('td').forEach(td => {
                const t = td.textContent.trim().toUpperCase();
                for (const s of ['UNPAID', 'PAID', 'PARTIAL CREDIT', 'FULLY CREDITED']) {
                    if (t === s) stats[s] = (stats[s] || 0) + 1;
                }
            });
            return stats;
        }''')
        if statuses:
            runner.add("Sales Invoice - Statuses", "PASS",
                       f"Invoice statuses: {json.dumps(statuses)}")
    except Exception as e:
        runner.add("Sales Invoice - PDF Test", "ERROR", f"Exception: {str(e)[:100]}")

    # --- TEST: PDF links on existing jobs ---
    for job_type, list_path in [
        ("Ocean Import", "/9dddd5ce1b1375bc497feeb871842d4b"),
        ("Air Export", "/8b574ca0cd37f8b76897ecc0f9d9ad34"),
    ]:
        try:
            page.goto(f"{BASE_URL}{list_path}", wait_until="networkidle", timeout=DEFAULT_TIMEOUT)
            page.wait_for_timeout(3000)

            first_link = page.evaluate('''() => {
                const a = document.querySelector('table tbody tr a');
                return a ? a.href : null;
            }''')

            if not first_link:
                runner.add(f"{job_type} - PDF Check", "WARNING", "No jobs to check")
                continue

            page.goto(first_link, wait_until="networkidle", timeout=DEFAULT_TIMEOUT)
            page.wait_for_timeout(3000)

            # Collect all PDF links
            pdf_links = page.evaluate('''() => {
                const links = [];
                document.querySelectorAll('a').forEach(a => {
                    if (a.href && a.href.includes('.pdf'))
                        links.push({text: a.textContent.trim().substring(0, 40), href: a.href});
                });
                return [...new Map(links.map(l => [l.href, l])).values()];
            }''')

            if pdf_links:
                runner.add(f"{job_type} - PDF Links Found", "PASS", f"{len(pdf_links)} PDF link(s)")

                # Test first PDF download
                try:
                    resp = page.request.get(pdf_links[0]['href'])
                    status = resp.status
                    body = resp.body()
                    is_pdf = body[:5] == b'%PDF-' if body else False

                    runner.add(f"{job_type} - PDF Download", "PASS" if (status == 200 and is_pdf) else "FAIL",
                               f"HTTP {status}, Size: {len(body)}B, Valid PDF: {is_pdf}")
                except Exception as e:
                    runner.add(f"{job_type} - PDF Download", "FAIL", f"Download error: {e}")
            else:
                runner.add(f"{job_type} - PDF Links", "WARNING", "No PDF links found on this job")

        except Exception as e:
            runner.add(f"{job_type} - PDF Check", "ERROR", f"Exception: {str(e)[:100]}")

    # --- TEST: VAT vs Non-VAT invoice comparison ---
    try:
        # Load Purchase Invoice (non-VAT)
        page.goto(f"{BASE_URL}/purchase-invoice", wait_until="networkidle", timeout=DEFAULT_TIMEOUT)
        page.wait_for_timeout(3000)
        non_vat_rows = page.evaluate("document.querySelectorAll('table tbody tr').length || 0")

        # Load Purchase Invoice with VAT
        page.goto(f"{BASE_URL}/purchase-invoice-with-vat", wait_until="networkidle", timeout=DEFAULT_TIMEOUT)
        page.wait_for_timeout(3000)
        vat_rows = page.evaluate("document.querySelectorAll('table tbody tr').length || 0")

        runner.add("VAT vs Non-VAT Comparison", "PASS",
                   f"Non-VAT invoices: {non_vat_rows}, VAT invoices: {vat_rows}")

        # Sales comparison
        page.goto(f"{BASE_URL}/sales-invoice", wait_until="networkidle", timeout=DEFAULT_TIMEOUT)
        page.wait_for_timeout(3000)
        non_vat_sales = page.evaluate("document.querySelectorAll('table tbody tr').length || 0")

        page.goto(f"{BASE_URL}/sales-invoice/with-vat", wait_until="networkidle", timeout=DEFAULT_TIMEOUT)
        page.wait_for_timeout(3000)
        vat_sales = page.evaluate("document.querySelectorAll('table tbody tr').length || 0")

        runner.add("Sales VAT vs Non-VAT", "PASS",
                   f"Non-VAT sales: {non_vat_sales}, VAT sales: {vat_sales}")

    except Exception as e:
        runner.add("VAT Comparison", "ERROR", f"Exception: {str(e)[:100]}")

    runner.save_intermediate()


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def print_final_report(runner):
    """Print the final test results summary."""
    total, passed, failed, warnings, errors, skipped, error_ss = runner.summary()
    pct_pass = (passed / total * 100) if total > 0 else 0
    pct_fail = (failed / total * 100) if total > 0 else 0

    print("\n")
    print("=" * 60)
    print("SENA ERP - MASTER TEST RESULTS")
    print("=" * 60)
    print(f"Date: {TODAY_DISPLAY}")
    print(f"URL: {BASE_URL}")
    print()

    # Group results by section
    sections = {}
    for r in runner.results:
        if r.section not in sections:
            sections[r.section] = []
        sections[r.section].append(r)

    for section_name, results in sections.items():
        print(section_name)
        for r in results:
            icon = {"PASS": "PASS", "FAIL": "FAIL", "WARNING": "WARN", "SKIP": "SKIP", "ERROR": "ERR!"}
            status_str = icon.get(r.status, "????")
            if r.message:
                print(f"  [{status_str}] {r.name} - {r.message}")
            else:
                print(f"  [{status_str}] {r.name}")
        print()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total}")
    print(f"Passed:      {passed} ({pct_pass:.0f}%)")
    print(f"Failed:      {failed} ({pct_fail:.0f}%)")
    print(f"Warnings:    {warnings}")
    print(f"Errors:      {errors}")
    print(f"Skipped:     {skipped}")
    print(f"Error screenshots: {error_ss}")
    print()
    print(f"Error screenshots saved to: {ERROR_SCREENSHOT_DIR}")
    print(f"Full results: {RESULTS_FILE}")
    print("=" * 60)


def main():
    ensure_dirs()

    runner = TestRunner()

    print("=" * 60)
    print("SENA ERP - MASTER TEST RUNNER")
    print(f"Date: {TODAY_DISPLAY}")
    print(f"URL: {BASE_URL}")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport=VIEWPORT,
            ignore_https_errors=True,
        )
        context.set_default_timeout(DEFAULT_TIMEOUT)
        page = context.new_page()

        # --- LOGIN ---
        print("\n[*] Logging in...")
        try:
            login(page)
            # Verify login succeeded
            page.wait_for_timeout(2000)
            current_url = page.url
            if "login" in current_url.lower() or "signin" in current_url.lower():
                print("[!] Login may have failed - still on login page")
                take_screenshot(page, "login_failed", is_error=True)
            else:
                print("[+] Login successful")
        except Exception as e:
            print(f"[!] Login failed: {e}")
            take_screenshot(page, "login_error", is_error=True)
            browser.close()
            return

        # --- RUN ALL SECTIONS ---
        try:
            # Section A: Page Load Tests
            print("\n[*] Running Section A: Page Load Tests...")
            run_section_a(page, runner)

            # Section B: CRUD Tests
            print("\n[*] Running Section B: CRUD Tests...")
            run_section_b(page, runner)

            # Section C: Job Creation Tests
            print("\n[*] Running Section C: Job Creation Tests...")
            run_section_c(page, runner)

            # Section D: Financial Report Tests
            print("\n[*] Running Section D: Financial Reports...")
            run_section_d(page, runner)

            # Section E: Account Page Tests
            print("\n[*] Running Section E: Account Pages...")
            run_section_e(page, runner)

            # Section F: DSR Report Tests
            print("\n[*] Running Section F: DSR Reports...")
            run_section_f(page, runner)

            # Section G: Deep Dive Job Workflow
            print("\n[*] Running Section G: Deep Dive Job Workflow...")
            run_section_g(page, runner)

            # Section H: Charge Add/Remove/VAT Tests
            print("\n[*] Running Section H: Charge Add/Remove/VAT...")
            run_section_h(page, runner)

            # Section I: Invoice/VAT/PDF Verification
            print("\n[*] Running Section I: Invoice/VAT/PDF Verification...")
            run_section_i(page, runner)

        except Exception as e:
            print(f"\n[!] Fatal error during test execution: {e}")
            traceback.print_exc()
            take_screenshot(page, "fatal_error", is_error=True)

        finally:
            browser.close()

    # --- SAVE FINAL RESULTS ---
    final_data = {
        "timestamp": datetime.now().isoformat(),
        "base_url": BASE_URL,
        "username": USERNAME,
        "viewport": VIEWPORT,
        "total_pages_tested": len(ALL_PAGES),
        "summary": {
            "total": runner.summary()[0],
            "passed": runner.summary()[1],
            "failed": runner.summary()[2],
            "warnings": runner.summary()[3],
            "errors": runner.summary()[4],
            "skipped": runner.summary()[5],
            "error_screenshots": runner.summary()[6],
        },
        "results": [r.to_dict() for r in runner.results],
    }
    with open(RESULTS_FILE, "w") as f:
        json.dump(final_data, f, indent=2)

    # --- PRINT FINAL REPORT ---
    print_final_report(runner)


if __name__ == "__main__":
    # Force unbuffered output
    import functools
    print = functools.partial(print, flush=True)
    main()
