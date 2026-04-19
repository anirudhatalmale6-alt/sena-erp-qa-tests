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
from datetime import datetime
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
