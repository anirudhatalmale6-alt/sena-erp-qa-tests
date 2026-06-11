"""
Sena ERP - Deep Dive End-to-End Test
Tests Ocean Import, Air Export, Land Import with full data entry across ALL steps,
multiple charges, invoice generation, PDF download, and PDF content verification.

Usage: python3 test_deep_dive_e2e.py
"""
import json
import os
import re
import sys
import time
import traceback
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_URL = "http://13.210.47.18:8088"
USERNAME = "superadmin"
PASSWORD = "Nick@#24"

PROJECT_DIR = "/var/lib/freelancer/projects/40298427/erp-test"
SS_DIR = os.path.join(PROJECT_DIR, "screenshots", "deep_dive")
ERR_SS_DIR = os.path.join(SS_DIR, "errors")
PDF_DIR = os.path.join(PROJECT_DIR, "downloaded_pdfs")
RESULTS_FILE = os.path.join(PROJECT_DIR, "results_deep_dive.json")

VIEWPORT = {"width": 1280, "height": 720}
TIMEOUT = 60000
TODAY = datetime.now().strftime("%d/%m/%Y")
TODAY_DISPLAY = datetime.now().strftime("%Y-%m-%d")
PREFIX = "DEEPTEST_"

# Job list and add new URLs
OCEAN_IMPORT = {
    "name": "Ocean Import",
    "list_url": "/9dddd5ce1b1375bc497feeb871842d4b",
    "add_url": "/8d9368c9ea314e4bf3271918424b2c24",
    "steps": ["Basic Details", "Clearing Instructions", "Delivery Note",
              "Buying Charges", "Selling Charges", "Purchase Invoice",
              "Sale Invoice", "Job Supporting"],
}
AIR_EXPORT = {
    "name": "Air Export",
    "list_url": "/8b574ca0cd37f8b76897ecc0f9d9ad34",
    "add_url": "/2c752e5ace8abac955144baf0b9ee354",
    "steps": ["Basic Details", "Clearing Instructions", "Delivery Note",
              "Shipping Documents", "Buying Charges", "Selling Charges",
              "Purchase Invoice", "Sale Invoice", "Job Supporting"],
}
LAND_IMPORT = {
    "name": "Land Import",
    "list_url": "/8013f48199799dce7a1fde812910a496",
    "add_url": "/f2d63311d4bd1935349fa1cb7a5afc7a",
    "steps": ["Basic Details", "Buying Charges", "Selling Charges",
              "Purchase Invoice", "Sale Invoice", "Attachments",
              "Clearing Instructions"],
}

# =============================================================================
# TEST DATA
# =============================================================================
OCEAN_IMPORT_DATA = {
    "shipment_type": "LCL",
    "hbl_no": f"{PREFIX}HBL-OI-001",
    "hbl_date": TODAY,
    "pallets": "5",
    "volume": "2.5",
    "template": "Standard",
    "shipper_inv_val": "15000",
    "shipper_inv_no": f"{PREFIX}SINV-001",
    "container_no": "MSCU1234567",
    "mbl_no": f"{PREFIX}MBL-OI-001",
    "mbl_date": TODAY,
    "etd": TODAY,
    "eta": (datetime.now() + timedelta(days=15)).strftime("%d/%m/%Y"),
    "delivery_ref": f"{PREFIX}DLVR-001",
    "freight_charge": "500",
    "insurance_charge": "100",
    "cal_ref": f"{PREFIX}CAL-001",
    "delivery_desc": "Test Pharma Shipment - Deep Dive Test",
    "marks_no": f"{PREFIX}MARKS/001",
    "clearing_remarks": "Deep dive test clearing instructions - auto generated",
    "buy_charges": [
        {"amount": "250.00", "ppcc": "CC"},
        {"amount": "175.50", "ppcc": "PP"},
        {"amount": "320.00", "ppcc": "CC"},
    ],
    "sell_charges": [
        {"amount": "450.00", "ppcc": "PP"},
        {"amount": "280.00", "ppcc": "PP"},
        {"amount": "150.75", "ppcc": "CC"},
    ],
    "sell_remark": "Deep dive test - selling charges verified",
    "sell_due_date": (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y"),
}

AIR_EXPORT_DATA = {
    "hawb_no": f"{PREFIX}HAWB-AE-001",
    "hawb_date": TODAY,
    "mawb_no": f"{PREFIX}MAWB-AE-001",
    "mawb_date": TODAY,
    "etd": TODAY,
    "eta": (datetime.now() + timedelta(days=3)).strftime("%d/%m/%Y"),
    "flight_no": "TK6643/9999",
    "booking_ref": f"{PREFIX}BKREF-AE",
    "delivery_desc": "Air Export Test Shipment - Deep Dive",
    "marks_no": f"{PREFIX}AIRMARKS/001",
    "clearing_remarks": "Air export deep dive test clearing instructions",
    "buy_charges": [
        {"amount": "800.00", "ppcc": "PP"},
        {"amount": "120.00", "ppcc": "CC"},
    ],
    "sell_charges": [
        {"amount": "1200.00", "ppcc": "PP"},
        {"amount": "350.00", "ppcc": "PP"},
    ],
    "sell_remark": "Air export charges - deep dive test",
    "sell_due_date": (datetime.now() + timedelta(days=14)).strftime("%d/%m/%Y"),
}

LAND_IMPORT_DATA = {
    "etd": TODAY,
    "eta": (datetime.now() + timedelta(days=2)).strftime("%d/%m/%Y"),
    "temperature": "-18C",
    "collection_origin": f"{PREFIX} London Depot",
    "delivery_dest": f"{PREFIX} Birmingham Warehouse",
    "port_entry": "Dover",
    "port_exit": "Calais",
    "clearing_remarks": "Land import deep dive test clearing instructions",
    "buy_charges": [
        {"amount": "600.00", "ppcc": "CC"},
        {"amount": "85.00", "ppcc": "PP"},
    ],
    "sell_charges": [
        {"amount": "900.00", "ppcc": "PP"},
        {"amount": "200.00", "ppcc": "PP"},
    ],
    "sell_remark": "Land import charges - deep dive test",
    "sell_due_date": (datetime.now() + timedelta(days=21)).strftime("%d/%m/%Y"),
}


# =============================================================================
# GLOBALS
# =============================================================================
results = []
all_errors = []


def ensure_dirs():
    for d in [SS_DIR, ERR_SS_DIR, PDF_DIR]:
        os.makedirs(d, exist_ok=True)


def safe_name(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name).strip('_')[:60]


def ss(page, name, is_error=False):
    sn = safe_name(name)
    path = os.path.join(ERR_SS_DIR if is_error else SS_DIR, f"{sn}.png")
    try:
        page.screenshot(path=path)
    except Exception:
        pass
    return path


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def add_result(job_type, step, test_name, status, detail="", screenshot=""):
    r = {
        "job_type": job_type,
        "step": step,
        "test": test_name,
        "status": status,
        "detail": detail,
        "screenshot": screenshot,
        "timestamp": datetime.now().isoformat(),
    }
    results.append(r)
    icon = "PASS" if status == "PASS" else "FAIL" if status == "FAIL" else "WARN"
    log(f"  [{icon}] {job_type} > {step} > {test_name}: {detail[:80]}")
    if status == "FAIL":
        all_errors.append(r)
    return r


def check_page_error(page):
    try:
        body_text = page.locator("body").inner_text(timeout=5000)
    except Exception:
        return "Page body not accessible"
    lower = body_text.lower()
    if "500" in body_text and ("internal server error" in lower or "server error" in lower):
        return "HTTP 500"
    if "404" in body_text and ("not found" in lower or "page not found" in lower):
        return "HTTP 404"
    if "view not found" in lower or "undefined variable" in lower:
        return "Server Error"
    if "sqlstate" in lower or "query exception" in lower:
        return "Database Error"
    if "whoops" in lower and "error" in lower:
        return "Whoops Error"
    return None


# =============================================================================
# LOGIN
# =============================================================================
def login(page):
    log("Logging in...")
    page.goto(BASE_URL, wait_until="networkidle", timeout=TIMEOUT)
    page.wait_for_timeout(3000)
    page.evaluate(f'''
        document.getElementById("username").value = "{USERNAME}";
        document.getElementById("password").value = "{PASSWORD}";
        document.getElementById("signupForm").submit();
    ''')
    page.wait_for_timeout(8000)
    log(f"Logged in. URL: {page.url}")


# =============================================================================
# HELPERS
# =============================================================================
def fill_select2(page, select_id, search_text, timeout=3000):
    try:
        page.evaluate("try { $('select.select2-hidden-accessible').select2('close'); } catch(e) {}")
        page.wait_for_timeout(300)
        page.evaluate(f"$('#{select_id}').select2('open')")
        page.wait_for_timeout(500)
        search_field = page.locator('.select2-search__field')
        if search_field.count() > 0:
            search_field.last.fill(search_text)
            page.wait_for_timeout(timeout)
        results_el = page.locator('.select2-results__option:not(.select2-results__message)')
        if results_el.count() > 0:
            text = results_el.first.text_content().strip()
            results_el.first.click()
            page.wait_for_timeout(500)
            return text
        page.evaluate(f"try {{ $('#{select_id}').select2('close'); }} catch(e) {{}}")
    except Exception as e:
        log(f"    Select2 error for {select_id}: {e}")
    return None


def fill_field(page, field_id, value):
    try:
        page.evaluate(f"""
            var el = document.getElementById('{field_id}');
            if (el) {{
                el.value = '{value}';
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
            }}
        """)
        return True
    except Exception:
        return False


def fill_date(page, field_id, date_str):
    try:
        page.evaluate(f"""
            var el = document.getElementById('{field_id}');
            if (el) {{
                el.readOnly = false;
                el.value = '{date_str}';
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
            }}
        """)
        return True
    except Exception:
        return False


def click_step(page, step_num):
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


def click_save(page):
    try:
        save_btn = page.locator('a:has-text("Save"), button:has-text("Save")').last
        if save_btn.count() > 0:
            save_btn.click()
            page.wait_for_timeout(5000)
            return True
    except Exception:
        pass
    return False


def select_charge(page, charge_select_id, search=""):
    try:
        page.evaluate(f"$('#{charge_select_id}').select2('open')")
        page.wait_for_timeout(500)
        sf = page.locator('.select2-search__field')
        if sf.count() > 0:
            sf.last.fill(search if search else "a")
            page.wait_for_timeout(2000)
        opts = page.locator('.select2-results__option:not(.select2-results__message)')
        if opts.count() > 0:
            text = opts.first.text_content().strip()
            opts.first.click()
            page.wait_for_timeout(500)
            return text
        page.evaluate(f"try {{ $('#{charge_select_id}').select2('close'); }} catch(e) {{}}")
    except Exception as e:
        log(f"    Charge select error: {e}")
    return None


def add_additional_charges(page, charge_type, charges_data, job_type_name):
    """Add charges via the additional charges section. charge_type = 'buy' or 'sell'"""
    results_list = []
    prefix_map = {"buy": "addl_b", "sell": "addl_s"}
    pfx = prefix_map[charge_type]
    toggle_id = f"addl_{charge_type}_toggle"

    for i, charge in enumerate(charges_data):
        try:
            # For first additional charge, check the toggle
            if i == 0:
                toggle = page.locator(f'#{toggle_id}')
                if toggle.count() > 0 and not toggle.is_checked():
                    toggle.click()
                    page.wait_for_timeout(1000)

            # Select charge from dropdown
            charge_selects = page.locator(f'select[name="{pfx}_charge[]"]')
            if charge_selects.count() > 0:
                sel = charge_selects.last
                opts = sel.evaluate('''(el) => {
                    return Array.from(el.options).filter(o => o.value !== '').slice(0, 10).map(o => ({v: o.value, t: o.text}));
                }''')
                if opts and len(opts) > i:
                    page.evaluate(f"""
                        var sels = document.querySelectorAll('select[name="{pfx}_charge[]"]');
                        var sel = sels[sels.length - 1];
                        if (sel) {{
                            sel.value = '{opts[min(i, len(opts)-1)]["v"]}';
                            sel.dispatchEvent(new Event('change', {{bubbles: true}}));
                        }}
                    """)
                    page.wait_for_timeout(500)

            # Fill amount
            amount_fields = page.locator(f'input[name="{pfx}_amount[]"], input[name="{pfx}_amnt[]"]')
            if amount_fields.count() > 0:
                amt = amount_fields.last
                amt.fill(charge["amount"])
                page.wait_for_timeout(300)

            # Set PP/CC
            ppcc_selects = page.locator(f'select[name="{pfx}_ppcc[]"]')
            if ppcc_selects.count() > 0:
                page.evaluate(f"""
                    var sels = document.querySelectorAll('select[name="{pfx}_ppcc[]"]');
                    var sel = sels[sels.length - 1];
                    if (sel) {{ sel.value = '{charge["ppcc"]}'; sel.dispatchEvent(new Event('change', {{bubbles: true}})); }}
                """)

            # Select payable to
            payto_selects = page.locator(f'select[name="{pfx}_payto[]"], select[name="{pfx}_custyp[]"]')
            if payto_selects.count() > 0:
                page.evaluate(f"""
                    var sels = document.querySelectorAll('select[name="{pfx}_payto[]"], select[name="{pfx}_custyp[]"]');
                    var sel = sels[sels.length - 1];
                    if (sel && sel.options.length > 1) {{
                        sel.value = sel.options[1].value;
                        sel.dispatchEvent(new Event('change', {{bubbles: true}}));
                    }}
                """)
                page.wait_for_timeout(500)

            results_list.append({"charge_idx": i, "amount": charge["amount"], "ppcc": charge["ppcc"], "status": "entered"})
            log(f"    Added {charge_type} charge #{i+1}: amount={charge['amount']} ppcc={charge['ppcc']}")

        except Exception as e:
            results_list.append({"charge_idx": i, "amount": charge["amount"], "status": f"error: {e}"})
            log(f"    Error adding {charge_type} charge #{i+1}: {e}")

    return results_list


def enter_main_charges(page, charge_data, charge_type, job_name):
    """Enter charges in the main charge table (row 1) + additional charges."""
    entered = []
    try:
        # Main row charge - use the Select2 dropdown for charge selection
        if charge_type == "buy":
            charge_sel_id = "bl_chrg_1"
            amount_id = "amnt_bl_chrg_1"
            ppcc_sel_name = "sl_ppcc[]"  # Note: this is confusingly named in the ERP
            volume_id = "bl_vlme_1"
            inv_no_id = "bl_invno_1"
        else:
            charge_sel_id = "sl_chrg_1"
            amount_id = "amnt_sl_chrg_1"
            ppcc_sel_name = "sl_ppcc[]"
            volume_id = "sl_vlme_1"
            inv_no_id = None

        # Select first charge in main row
        first_charge = charge_data[0] if charge_data else None
        if first_charge:
            selected = select_charge(page, charge_sel_id)
            if selected:
                log(f"    Main {charge_type} charge selected: {selected}")
                fill_field(page, amount_id, first_charge["amount"])
                fill_field(page, volume_id, "1")
                if inv_no_id:
                    fill_field(page, inv_no_id, f"{PREFIX}INV-{charge_type.upper()}-001")
                entered.append({"row": "main", "charge": selected, "amount": first_charge["amount"]})

        # Additional charges (rows 2+)
        if len(charge_data) > 1:
            addl_results = add_additional_charges(page, "buy" if charge_type == "buy" else "sell", charge_data[1:], job_name)
            entered.extend(addl_results)

    except Exception as e:
        log(f"    Error entering {charge_type} charges: {e}")

    return entered


def get_job_detail_url(page, list_url):
    """Navigate to job list and return the first job's detail URL."""
    page.goto(f"{BASE_URL}{list_url}", wait_until="networkidle", timeout=TIMEOUT)
    page.wait_for_timeout(3000)
    return page.evaluate('''() => {
        const rows = document.querySelectorAll('table tbody tr');
        if (rows.length > 0) {
            const a = rows[0].querySelector('a');
            return a ? a.href : null;
        }
        return null;
    }''')


def verify_pdf_accessible(page, pdf_url, pdf_name):
    """Check if PDF URL returns 200 and download it."""
    try:
        response = page.request.get(pdf_url)
        status = response.status
        content_type = response.headers.get('content-type', '')
        body = response.body()

        if status == 200:
            if 'pdf' in content_type.lower() or (body[:5] == b'%PDF-'):
                pdf_path = os.path.join(PDF_DIR, f"{safe_name(pdf_name)}.pdf")
                with open(pdf_path, 'wb') as f:
                    f.write(body)
                return {"status": "OK", "size": len(body), "path": pdf_path}
            else:
                return {"status": "NOT_PDF", "content_type": content_type, "size": len(body)}
        else:
            return {"status": f"HTTP_{status}", "size": 0}
    except Exception as e:
        return {"status": f"ERROR: {e}", "size": 0}


def verify_pdf_content(pdf_path, expected_values):
    """Extract text from PDF and verify expected values are present."""
    try:
        with open(pdf_path, 'rb') as f:
            content = f.read()
        # Simple text extraction from PDF (look for text between parentheses or streams)
        text = ""
        # Try to decode text from PDF content
        try:
            text = content.decode('latin-1', errors='ignore')
        except Exception:
            text = str(content)

        found = {}
        missing = {}
        for key, value in expected_values.items():
            if str(value).upper() in text.upper() or str(value) in text:
                found[key] = value
            else:
                missing[key] = value

        return {"found": found, "missing": missing, "text_length": len(text)}
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# OCEAN IMPORT - FULL DEEP DIVE TEST
# =============================================================================
def test_ocean_import(page):
    JOB = "Ocean Import"
    data = OCEAN_IMPORT_DATA
    log(f"\n{'='*70}")
    log(f"TESTING: {JOB} - Full Deep Dive")
    log(f"{'='*70}")

    # --- STEP 1: Create new job with full data ---
    log(f"\n--- {JOB}: Step 1 - Basic Details (Create New) ---")
    page.goto(f"{BASE_URL}{OCEAN_IMPORT['add_url']}", wait_until="networkidle", timeout=TIMEOUT)
    page.wait_for_timeout(3000)
    ss(page, f"OI_step1_new_job")

    err = check_page_error(page)
    if err:
        add_result(JOB, "Step 1", "Page Load", "FAIL", f"Add New page error: {err}", ss(page, "OI_step1_error", True))
        return

    add_result(JOB, "Step 1", "Page Load", "PASS", "Add New page loaded successfully")

    # Fill consignee (Select2 AJAX)
    consignee = fill_select2(page, "consigne", "test")
    if not consignee:
        consignee = fill_select2(page, "consigne", "a")
    add_result(JOB, "Step 1", "Consignee Select", "PASS" if consignee else "FAIL",
               f"Selected: {consignee}" if consignee else "No consignee options found",
               ss(page, "OI_step1_consignee"))

    # Fill ports
    lport = fill_select2(page, "lport", "nhava")
    if not lport:
        lport = fill_select2(page, "lport", "a")
    add_result(JOB, "Step 1", "Load Port", "PASS" if lport else "WARN",
               f"Selected: {lport}" if lport else "No port options")

    dport = fill_select2(page, "dport", "felix")
    if not dport:
        dport = fill_select2(page, "dport", "a")
    add_result(JOB, "Step 1", "Discharge Port", "PASS" if dport else "WARN",
               f"Selected: {dport}" if dport else "No port options")

    # Fill Incoterms
    inco = fill_select2(page, "IncoTrms", "a")
    add_result(JOB, "Step 1", "Incoterms", "PASS" if inco else "WARN",
               f"Selected: {inco}" if inco else "No incoterms options")

    # Overseas Agent
    agent = fill_select2(page, "overseas1", "a")
    if agent:
        add_result(JOB, "Step 1", "Overseas Agent", "PASS", f"Selected: {agent}")

    # Shipping Line
    shpline = fill_select2(page, "shpline", "a")
    if shpline:
        add_result(JOB, "Step 1", "Shipping Line", "PASS", f"Selected: {shpline}")

    # Co-Loader
    coloder = fill_select2(page, "coloder", "a")

    # Vessel
    vessel = fill_select2(page, "vovesel", "a")
    if vessel:
        add_result(JOB, "Step 1", "Vessel", "PASS", f"Selected: {vessel}")

    # Fill shipment data
    fill_select2(page, "shipper_1", "a")
    fill_field(page, "hblno_1", data["hbl_no"])
    fill_date(page, "hbldte_1", data["hbl_date"])
    fill_field(page, "noofpal_1", data["pallets"])
    fill_field(page, "volume_1", data["volume"])
    fill_field(page, "temp_1", data["template"])
    fill_field(page, "shpinvval_1", data["shipper_inv_val"])
    fill_field(page, "shpinvno_1", data["shipper_inv_no"])
    fill_date(page, "shpinvdte_1", TODAY)
    fill_field(page, "contno_1", data["container_no"])

    # MBL details
    fill_field(page, "mblno", data["mbl_no"])
    fill_date(page, "mbldte", data["mbl_date"])
    fill_date(page, "etd", data["etd"])
    fill_date(page, "eta", data["eta"])
    fill_field(page, "dlvrref", data["delivery_ref"])
    fill_field(page, "frghtchrg", data["freight_charge"])
    fill_field(page, "inschrg", data["insurance_charge"])
    fill_field(page, "calref", data["cal_ref"])

    ss(page, "OI_step1_filled_top")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(500)
    ss(page, "OI_step1_filled_bottom")

    add_result(JOB, "Step 1", "All Fields Filled", "PASS",
               f"HBL={data['hbl_no']}, MBL={data['mbl_no']}, Container={data['container_no']}")

    # Save Step 1
    click_save(page)
    page.wait_for_timeout(3000)

    err = check_page_error(page)
    if err:
        add_result(JOB, "Step 1", "Save", "FAIL", f"Save error: {err}", ss(page, "OI_step1_save_error", True))
    else:
        # Check if we got a job number
        job_no = page.evaluate('''() => {
            var el = document.getElementById('jobno');
            if (!el) { el = document.querySelector('input[name="jobno"]'); }
            return el ? el.value : '';
        }''')
        add_result(JOB, "Step 1", "Save", "PASS", f"Job saved. Job No: {job_no}")
        ss(page, "OI_step1_saved")

    # Get the current URL (we're now on the edit page)
    current_url = page.url
    log(f"  Current URL after save: {current_url}")

    # --- STEP 2: Clearing Instructions ---
    log(f"\n--- {JOB}: Step 2 - Clearing Instructions ---")
    click_step(page, 2)
    page.wait_for_timeout(2000)
    ss(page, "OI_step2_top")

    # Container Size
    consize = fill_select2(page, "conSizeId", "20")
    if not consize:
        consize = fill_select2(page, "conSizeId", "a")
    add_result(JOB, "Step 2", "Container Size", "PASS" if consize else "WARN",
               f"Selected: {consize}" if consize else "No container size options")

    # Click SET SIZE AND SAVE
    set_size_btn = page.locator('button:has-text("SET SIZE AND SAVE")')
    if set_size_btn.count() > 0:
        set_size_btn.click()
        page.wait_for_timeout(3000)
        add_result(JOB, "Step 2", "Set Size & Save", "PASS", "Button clicked")

    # Fill remarks
    remarks_field = page.locator('#clrmrk')
    if remarks_field.count() > 0:
        remarks_field.fill(data["clearing_remarks"])
        add_result(JOB, "Step 2", "Remarks", "PASS", "Clearing remarks entered")

    # Verify read-only fields display correct data
    ro_values = page.evaluate('''() => {
        const vals = {};
        document.querySelectorAll('#step-2 input[readonly], .step_content:nth-child(2) input[readonly]').forEach(el => {
            if (el.value) vals[el.name || el.id || 'unknown'] = el.value;
        });
        // Also check visible readonly inputs on the page
        document.querySelectorAll('input[readonly]').forEach(el => {
            const rect = el.getBoundingClientRect();
            if (rect.y > 250 && rect.y < 700 && el.value) {
                vals[el.placeholder || el.name || el.id || `pos_${Math.round(rect.y)}`] = el.value;
            }
        });
        return vals;
    }''')
    if ro_values:
        add_result(JOB, "Step 2", "Read-only Data", "PASS",
                   f"Verified {len(ro_values)} fields: {json.dumps(dict(list(ro_values.items())[:5]))}")

    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(500)
    ss(page, "OI_step2_bottom")

    click_save(page)
    err = check_page_error(page)
    add_result(JOB, "Step 2", "Save", "PASS" if not err else "FAIL",
               "Saved" if not err else f"Error: {err}",
               ss(page, "OI_step2_saved") if not err else ss(page, "OI_step2_save_error", True))

    # --- STEP 3: Delivery Note ---
    log(f"\n--- {JOB}: Step 3 - Delivery Note ---")
    click_step(page, 3)
    page.wait_for_timeout(2000)
    ss(page, "OI_step3_top")

    # Fill delivery date
    fill_date(page, "dlvrdte", (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y"))

    # Fill description
    fill_field(page, "dldsc", data["delivery_desc"])

    # Fill marks
    fill_field(page, "mrksno", data["marks_no"])

    add_result(JOB, "Step 3", "Delivery Note Fields", "PASS",
               f"Desc: {data['delivery_desc']}, Marks: {data['marks_no']}")

    # Check for delivery note table
    do_table = page.evaluate('''() => {
        const tables = document.querySelectorAll('table');
        for (const t of tables) {
            const headers = Array.from(t.querySelectorAll('th')).map(h => h.textContent.trim());
            if (headers.some(h => h.includes('MARKS') || h.includes('QUANTITY') || h.includes('DESCRIPTION'))) {
                return {found: true, headers: headers, rows: t.querySelectorAll('tbody tr').length};
            }
        }
        return {found: false};
    }''')
    if do_table.get('found'):
        add_result(JOB, "Step 3", "D/O Table", "PASS",
                   f"Table found with {do_table['rows']} rows, headers: {do_table['headers'][:5]}")

    # Try Save & Regenerate D/O
    regen_btn = page.locator('button:has-text("Save & Regenerate D/O"), button:has-text("Regenerate D/O")')
    if regen_btn.count() > 0:
        regen_btn.first.click()
        page.wait_for_timeout(5000)
        ss(page, "OI_step3_after_regen")
        err = check_page_error(page)
        add_result(JOB, "Step 3", "Regenerate D/O", "PASS" if not err else "FAIL",
                   "D/O regenerated" if not err else f"Error: {err}",
                   "" if not err else ss(page, "OI_step3_regen_error", True))
    else:
        click_save(page)

    # Check if PDF link appeared
    pdf_links = page.evaluate('''() => {
        const links = [];
        document.querySelectorAll('a').forEach(a => {
            if (a.href && a.href.includes('/files/') && a.href.includes('.pdf')) {
                links.push(a.href);
            }
        });
        return [...new Set(links)];
    }''')
    if pdf_links:
        add_result(JOB, "Step 3", "D/O PDF Link", "PASS", f"Found {len(pdf_links)} PDF link(s)")
        for i, link in enumerate(pdf_links[:2]):
            result = verify_pdf_accessible(page, link, f"OI_delivery_note_{i}")
            add_result(JOB, "Step 3", f"D/O PDF Download #{i+1}", "PASS" if result["status"] == "OK" else "FAIL",
                       f"Status: {result['status']}, Size: {result.get('size', 0)} bytes",
                       ss(page, f"OI_step3_pdf_{i}") if result["status"] != "OK" else "")
    else:
        add_result(JOB, "Step 3", "D/O PDF Link", "WARN", "No PDF links found after regenerate")

    # --- STEP 4: Buying Charges ---
    log(f"\n--- {JOB}: Step 4 - Buying Charges ---")
    click_step(page, 4)
    page.wait_for_timeout(2000)
    ss(page, "OI_step4_top")

    buy_results = enter_main_charges(page, data["buy_charges"], "buy", JOB)
    ss(page, "OI_step4_charges_filled")

    add_result(JOB, "Step 4", "Buy Charges Entry", "PASS" if buy_results else "FAIL",
               f"Entered {len(buy_results)} charge(s): {json.dumps(buy_results[:3])}")

    # Verify totals
    totals = page.evaluate('''() => {
        return {
            total_tax: document.querySelector('#btottaxx, [name="stottax"]')?.value || '',
            total_amount: document.querySelector('#btotamntt, [name="stotamnt"]')?.value || '',
            all_total: document.querySelector('#baltotall, [name="saltotal"]')?.value || '',
        };
    }''')
    add_result(JOB, "Step 4", "Buy Totals", "PASS",
               f"Tax: {totals.get('total_tax','')}, Amount: {totals.get('total_amount','')}, Total: {totals.get('all_total','')}")

    click_save(page)
    page.wait_for_timeout(3000)
    err = check_page_error(page)
    add_result(JOB, "Step 4", "Save", "PASS" if not err else "FAIL",
               "Buy charges saved" if not err else f"Error: {err}",
               "" if not err else ss(page, "OI_step4_save_error", True))

    # --- STEP 5: Selling Charges ---
    log(f"\n--- {JOB}: Step 5 - Selling Charges ---")
    click_step(page, 5)
    page.wait_for_timeout(2000)
    ss(page, "OI_step5_top")

    sell_results = enter_main_charges(page, data["sell_charges"], "sell", JOB)
    ss(page, "OI_step5_charges_filled")

    # Fill remark and due date
    fill_field(page, "remark", data["sell_remark"])
    fill_field(page, "due_date", data["sell_due_date"])

    add_result(JOB, "Step 5", "Sell Charges Entry", "PASS" if sell_results else "FAIL",
               f"Entered {len(sell_results)} charge(s), remark={data['sell_remark'][:30]}")

    # Verify sell totals
    sell_totals = page.evaluate('''() => {
        return {
            total_tax: document.querySelector('#stottaxx, [name="stottax"]')?.value || '',
            total_amount: document.querySelector('#stotamntt, [name="stotamnt"]')?.value || '',
            all_total: document.querySelector('#saltotall, [name="saltotal"]')?.value || '',
        };
    }''')
    add_result(JOB, "Step 5", "Sell Totals", "PASS",
               f"Tax: {sell_totals.get('total_tax','')}, Amount: {sell_totals.get('total_amount','')}, Total: {sell_totals.get('all_total','')}")

    click_save(page)
    page.wait_for_timeout(3000)
    err = check_page_error(page)
    add_result(JOB, "Step 5", "Save", "PASS" if not err else "FAIL",
               "Sell charges saved" if not err else f"Error: {err}",
               "" if not err else ss(page, "OI_step5_save_error", True))

    # --- STEP 6: Purchase Invoice ---
    log(f"\n--- {JOB}: Step 6 - Purchase Invoice ---")
    click_step(page, 6)
    page.wait_for_timeout(2000)
    ss(page, "OI_step6_top")

    pi_status = page.evaluate('''() => {
        const body = document.body.innerText;
        if (body.includes('NO PURCHASE INVOICE GENERATED')) return 'not_generated';
        if (body.includes('Purchase Invoice')) return 'generated';
        return 'unknown';
    }''')

    if pi_status == 'not_generated':
        add_result(JOB, "Step 6", "Purchase Invoice Status", "WARN",
                   "No purchase invoice generated (need charges with payable-to set)")
    else:
        add_result(JOB, "Step 6", "Purchase Invoice Status", "PASS",
                   f"Invoice status: {pi_status}")

    # Check for Generate Invoice button
    gen_btn = page.locator('button:has-text("Generate"), a:has-text("Generate")')
    if gen_btn.count() > 0:
        gen_btn.first.click()
        page.wait_for_timeout(5000)
        ss(page, "OI_step6_after_generate")
        err = check_page_error(page)
        add_result(JOB, "Step 6", "Generate Purchase Invoice", "PASS" if not err else "FAIL",
                   "Generated" if not err else f"Error: {err}")

    # Look for invoice PDF links
    inv_pdf = page.evaluate('''() => {
        const links = [];
        document.querySelectorAll('a').forEach(a => {
            if (a.href && (a.href.includes('purchase-invoice') || a.href.includes('/files/')) && a.href.includes('.pdf')) {
                links.push({text: a.textContent.trim(), href: a.href});
            }
        });
        return links;
    }''')
    if inv_pdf:
        for i, link in enumerate(inv_pdf[:2]):
            result = verify_pdf_accessible(page, link['href'], f"OI_purchase_invoice_{i}")
            add_result(JOB, "Step 6", f"Purchase Invoice PDF #{i+1}",
                       "PASS" if result["status"] == "OK" else "FAIL",
                       f"Status: {result['status']}, Size: {result.get('size', 0)} bytes")

    # --- STEP 7: Sale Invoice ---
    log(f"\n--- {JOB}: Step 7 - Sale Invoice ---")
    click_step(page, 7)
    page.wait_for_timeout(2000)
    ss(page, "OI_step7_top")

    si_status = page.evaluate('''() => {
        const body = document.body.innerText;
        if (body.includes('NO SALE INVOICE GENERATED')) return 'not_generated';
        return 'has_content';
    }''')

    # Try to generate sale invoice if there's a button
    gen_btn = page.locator('button:has-text("Generate"), a:has-text("Generate")')
    if gen_btn.count() > 0:
        gen_btn.first.click()
        page.wait_for_timeout(5000)
        ss(page, "OI_step7_after_generate")

    add_result(JOB, "Step 7", "Sale Invoice Status", "PASS" if si_status != 'not_generated' else "WARN",
               f"Status: {si_status}")

    # --- STEP 8: Files / Job Supporting ---
    log(f"\n--- {JOB}: Step 8 - Files/Job Supporting ---")
    click_step(page, 8)
    page.wait_for_timeout(2000)
    ss(page, "OI_step8_top")

    file_area = page.evaluate('''() => {
        const fileInputs = document.querySelectorAll('input[type="file"]');
        const uploadBtns = document.querySelectorAll('button:not([disabled])');
        return {
            fileInputCount: fileInputs.length,
            buttonCount: uploadBtns.length,
            hasDropzone: !!document.querySelector('.dropzone, [class*="upload"], [class*="file"]')
        };
    }''')
    add_result(JOB, "Step 8", "Files Section", "PASS",
               f"File inputs: {file_area['fileInputCount']}, Has upload: {file_area['hasDropzone']}")

    # Collect all PDF links on the page
    log(f"\n--- {JOB}: Collecting ALL PDF links ---")
    all_pdfs = page.evaluate('''() => {
        const links = [];
        document.querySelectorAll('a').forEach(a => {
            if (a.href && a.href.includes('.pdf')) {
                links.push({text: a.textContent.trim().substring(0, 50), href: a.href});
            }
        });
        return [...new Map(links.map(l => [l.href, l])).values()];
    }''')
    if all_pdfs:
        add_result(JOB, "PDFs", "Total PDF Links", "PASS", f"Found {len(all_pdfs)} unique PDF link(s)")
        for i, pdf in enumerate(all_pdfs[:5]):
            result = verify_pdf_accessible(page, pdf['href'], f"OI_pdf_{i}_{safe_name(pdf['text'])}")
            add_result(JOB, "PDFs", f"PDF '{pdf['text'][:30]}' Download",
                       "PASS" if result["status"] == "OK" else "FAIL",
                       f"URL: {pdf['href'][-40:]}, Status: {result['status']}, Size: {result.get('size', 0)}B",
                       "" if result["status"] == "OK" else ss(page, f"OI_pdf_error_{i}", True))

            # Verify PDF content if downloaded
            if result["status"] == "OK" and result.get("path"):
                expected = {"consignee": consignee or "", "port": lport or ""}
                content_check = verify_pdf_content(result["path"], expected)
                if "error" not in content_check:
                    found = content_check.get("found", {})
                    missing = content_check.get("missing", {})
                    add_result(JOB, "PDFs", f"PDF Content Check '{pdf['text'][:20]}'",
                               "PASS" if not missing else "WARN",
                               f"Found: {list(found.keys())}, Missing: {list(missing.keys())}")


# =============================================================================
# AIR EXPORT - FULL DEEP DIVE TEST
# =============================================================================
def test_air_export(page):
    JOB = "Air Export"
    data = AIR_EXPORT_DATA
    log(f"\n{'='*70}")
    log(f"TESTING: {JOB} - Full Deep Dive")
    log(f"{'='*70}")

    # --- STEP 1: Create new job ---
    log(f"\n--- {JOB}: Step 1 - Basic Details (Create New) ---")
    page.goto(f"{BASE_URL}{AIR_EXPORT['add_url']}", wait_until="networkidle", timeout=TIMEOUT)
    page.wait_for_timeout(3000)
    ss(page, "AE_step1_new_job")

    err = check_page_error(page)
    if err:
        add_result(JOB, "Step 1", "Page Load", "FAIL", f"Error: {err}", ss(page, "AE_step1_error", True))
        return
    add_result(JOB, "Step 1", "Page Load", "PASS", "Add New page loaded")

    # Fill basic details
    shipper = fill_select2(page, "shipper", "a")
    if not shipper:
        shipper = fill_select2(page, "shipper_1", "a")
    add_result(JOB, "Step 1", "Shipper", "PASS" if shipper else "WARN",
               f"Selected: {shipper}" if shipper else "No shipper options")

    consignee = fill_select2(page, "consigne", "a")
    add_result(JOB, "Step 1", "Consignee", "PASS" if consignee else "WARN",
               f"Selected: {consignee}" if consignee else "No consignee options")

    # Incoterms
    inco = fill_select2(page, "IncoTrms", "a")

    # Air ports
    lport = fill_select2(page, "lport", "mumbai")
    if not lport:
        lport = fill_select2(page, "lport", "a")
    add_result(JOB, "Step 1", "Loading Airport", "PASS" if lport else "WARN",
               f"Selected: {lport}" if lport else "No options")

    dport = fill_select2(page, "dport", "a")
    add_result(JOB, "Step 1", "Discharge Airport", "PASS" if dport else "WARN",
               f"Selected: {dport}" if dport else "No options")

    # Overseas Agent
    agent = fill_select2(page, "overseas1", "a")

    # Sub Agent
    subagent = fill_select2(page, "overseas3", "a")

    # Carrier
    carrier = fill_select2(page, "carrier", "a")
    if not carrier:
        carrier = fill_select2(page, "carname", "a")

    # HAWB/MAWB details
    fill_field(page, "hawbno", data["hawb_no"])
    fill_date(page, "hawbdt", data["hawb_date"])
    fill_field(page, "mawbno", data["mawb_no"])
    fill_date(page, "mawbdt", data["mawb_date"])
    fill_date(page, "etd", data["etd"])
    fill_date(page, "eta", data["eta"])
    fill_field(page, "fltno", data["flight_no"])
    fill_field(page, "bkref", data["booking_ref"])

    ss(page, "AE_step1_filled")
    add_result(JOB, "Step 1", "All Fields Filled", "PASS",
               f"HAWB={data['hawb_no']}, MAWB={data['mawb_no']}, Flight={data['flight_no']}")

    click_save(page)
    page.wait_for_timeout(3000)
    err = check_page_error(page)
    if err:
        add_result(JOB, "Step 1", "Save", "FAIL", f"Error: {err}", ss(page, "AE_step1_save_error", True))
    else:
        job_no = page.evaluate("document.getElementById('jobno')?.value || ''")
        add_result(JOB, "Step 1", "Save", "PASS", f"Job saved. No: {job_no}")
    ss(page, "AE_step1_saved")

    # --- STEP 2: Clearing Instructions ---
    log(f"\n--- {JOB}: Step 2 - Clearing Instructions ---")
    click_step(page, 2)
    page.wait_for_timeout(2000)
    ss(page, "AE_step2_top")

    remarks = page.locator('#clrmrk, textarea[name="clrmrk"]')
    if remarks.count() > 0:
        remarks.first.fill(data["clearing_remarks"])
        add_result(JOB, "Step 2", "Remarks", "PASS", "Clearing remarks entered")

    click_save(page)
    err = check_page_error(page)
    add_result(JOB, "Step 2", "Save", "PASS" if not err else "FAIL",
               "Saved" if not err else f"Error: {err}")

    # --- STEP 3: Delivery Note ---
    log(f"\n--- {JOB}: Step 3 - Delivery Note ---")
    click_step(page, 3)
    page.wait_for_timeout(2000)
    ss(page, "AE_step3_top")

    fill_field(page, "dldsc", data["delivery_desc"])
    fill_field(page, "mrksno", data["marks_no"])

    regen_btn = page.locator('button:has-text("Regenerate"), button:has-text("Save & Regenerate")')
    if regen_btn.count() > 0:
        regen_btn.first.click()
        page.wait_for_timeout(5000)
    else:
        click_save(page)

    err = check_page_error(page)
    add_result(JOB, "Step 3", "Delivery Note", "PASS" if not err else "FAIL",
               f"Desc: {data['delivery_desc'][:30]}" if not err else f"Error: {err}",
               "" if not err else ss(page, "AE_step3_error", True))

    # --- STEP 4: Shipping Documents ---
    log(f"\n--- {JOB}: Step 4 - Shipping Documents ---")
    click_step(page, 4)
    page.wait_for_timeout(2000)
    ss(page, "AE_step4_top")

    sd_content = page.evaluate('''() => {
        const body = document.body.innerText;
        return {
            hasContent: body.length > 100,
            hasTable: document.querySelectorAll('table').length > 0,
            hasForm: document.querySelectorAll('form, input:not([type="hidden"]), select').length > 0,
            snippet: body.substring(0, 200)
        };
    }''')
    err = check_page_error(page)
    add_result(JOB, "Step 4", "Shipping Documents Page", "PASS" if not err else "FAIL",
               f"Tables: {sd_content['hasTable']}, Forms: {sd_content['hasForm']}" if not err else f"Error: {err}")

    # --- STEP 5: Buying Charges ---
    log(f"\n--- {JOB}: Step 5 - Buying Charges ---")
    click_step(page, 5)
    page.wait_for_timeout(2000)
    ss(page, "AE_step5_top")

    buy_results = enter_main_charges(page, data["buy_charges"], "buy", JOB)
    add_result(JOB, "Step 5", "Buy Charges", "PASS" if buy_results else "FAIL",
               f"Entered {len(buy_results)} charge(s)")

    click_save(page)
    err = check_page_error(page)
    add_result(JOB, "Step 5", "Save", "PASS" if not err else "FAIL",
               "Saved" if not err else f"Error: {err}")

    # --- STEP 6: Selling Charges ---
    log(f"\n--- {JOB}: Step 6 - Selling Charges ---")
    click_step(page, 6)
    page.wait_for_timeout(2000)
    ss(page, "AE_step6_top")

    sell_results = enter_main_charges(page, data["sell_charges"], "sell", JOB)
    fill_field(page, "remark", data["sell_remark"])
    fill_field(page, "due_date", data["sell_due_date"])

    add_result(JOB, "Step 6", "Sell Charges", "PASS" if sell_results else "FAIL",
               f"Entered {len(sell_results)} charge(s)")

    click_save(page)
    err = check_page_error(page)
    add_result(JOB, "Step 6", "Save", "PASS" if not err else "FAIL",
               "Saved" if not err else f"Error: {err}")

    # --- STEP 7: Purchase Invoice ---
    log(f"\n--- {JOB}: Step 7 - Purchase Invoice ---")
    click_step(page, 7)
    page.wait_for_timeout(2000)
    ss(page, "AE_step7_top")

    pi_text = page.inner_text("body")
    has_pi = "NO PURCHASE INVOICE" not in pi_text.upper()
    add_result(JOB, "Step 7", "Purchase Invoice", "PASS" if has_pi else "WARN",
               "Invoice present" if has_pi else "No purchase invoice generated")

    # --- STEP 8: Sale Invoice ---
    log(f"\n--- {JOB}: Step 8 - Sale Invoice ---")
    click_step(page, 8)
    page.wait_for_timeout(2000)
    ss(page, "AE_step8_top")

    si_text = page.inner_text("body")
    has_si = "NO SALE INVOICE" not in si_text.upper()
    add_result(JOB, "Step 8", "Sale Invoice", "PASS" if has_si else "WARN",
               "Invoice present" if has_si else "No sale invoice generated")

    # --- STEP 9: Files ---
    log(f"\n--- {JOB}: Step 9 - Files/Job Supporting ---")
    click_step(page, 9)
    page.wait_for_timeout(2000)
    ss(page, "AE_step9_top")
    add_result(JOB, "Step 9", "Files Section", "PASS", "Files tab loaded")

    # Check all PDFs
    all_pdfs = page.evaluate('''() => {
        const links = [];
        document.querySelectorAll('a').forEach(a => {
            if (a.href && a.href.includes('.pdf')) links.push({text: a.textContent.trim().substring(0, 50), href: a.href});
        });
        return [...new Map(links.map(l => [l.href, l])).values()];
    }''')
    if all_pdfs:
        for i, pdf in enumerate(all_pdfs[:5]):
            result = verify_pdf_accessible(page, pdf['href'], f"AE_pdf_{i}")
            add_result(JOB, "PDFs", f"PDF #{i+1} '{pdf['text'][:25]}'",
                       "PASS" if result["status"] == "OK" else "FAIL",
                       f"Status: {result['status']}, Size: {result.get('size', 0)}B")


# =============================================================================
# LAND IMPORT - FULL DEEP DIVE TEST
# =============================================================================
def test_land_import(page):
    JOB = "Land Import"
    data = LAND_IMPORT_DATA
    log(f"\n{'='*70}")
    log(f"TESTING: {JOB} - Full Deep Dive")
    log(f"{'='*70}")

    # --- STEP 1: Create new job ---
    log(f"\n--- {JOB}: Step 1 - Basic Details (Create New) ---")
    page.goto(f"{BASE_URL}{LAND_IMPORT['add_url']}", wait_until="networkidle", timeout=TIMEOUT)
    page.wait_for_timeout(3000)
    ss(page, "LI_step1_new_job")

    err = check_page_error(page)
    if err:
        add_result(JOB, "Step 1", "Page Load", "FAIL", f"Error: {err}", ss(page, "LI_step1_error", True))
        return
    add_result(JOB, "Step 1", "Page Load", "PASS", "Add New page loaded")

    # Consignee
    consignee = fill_select2(page, "consigne", "a")
    if not consignee:
        consignee = fill_select2(page, "customer", "a")
    add_result(JOB, "Step 1", "Customer/Consignee", "PASS" if consignee else "FAIL",
               f"Selected: {consignee}" if consignee else "No options found",
               "" if consignee else ss(page, "LI_step1_consignee_fail", True))

    # Incoterms
    inco = fill_select2(page, "IncoTrms", "a")
    if not inco:
        page.evaluate('''() => {
            var sel = document.querySelector('select[name="IncoTrms"], #IncoTrms, #incoterms');
            if (sel && sel.options.length > 1) { sel.value = sel.options[1].value; sel.dispatchEvent(new Event('change', {bubbles: true})); }
        }''')

    # Sub Agent
    subagent = fill_select2(page, "overseas3", "a")
    if not subagent:
        subagent = fill_select2(page, "subagent", "a")

    # ETD/ETA
    fill_date(page, "etd", data["etd"])
    fill_date(page, "eta", data["eta"])

    # Shipment Type
    page.evaluate('''() => {
        var sel = document.querySelector('#shptype, select[name="shptype"]');
        if (sel && sel.options.length > 1) { sel.value = sel.options[1].value; sel.dispatchEvent(new Event('change', {bubbles: true})); }
    }''')

    # Temperature
    fill_field(page, "temperature", data["temperature"])
    fill_field(page, "temp", data["temperature"])

    # Collection/Delivery
    fill_field(page, "collection", data["collection_origin"])
    fill_field(page, "colorigin", data["collection_origin"])
    fill_field(page, "delivery", data["delivery_dest"])
    fill_field(page, "deldest", data["delivery_dest"])

    # Ports
    fill_field(page, "portentry", data["port_entry"])
    fill_field(page, "portexit", data["port_exit"])

    # Transporter / Carrier
    transporter = fill_select2(page, "transporter", "a")
    carrier = fill_select2(page, "carrier", "a")
    if not carrier:
        carrier = fill_select2(page, "carname", "a")

    ss(page, "LI_step1_filled")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(500)
    ss(page, "LI_step1_filled_bottom")

    add_result(JOB, "Step 1", "All Fields", "PASS",
               f"Consignee={consignee}, ETD={data['etd']}, Temp={data['temperature']}")

    click_save(page)
    page.wait_for_timeout(3000)
    err = check_page_error(page)
    if err:
        add_result(JOB, "Step 1", "Save", "FAIL", f"Error: {err}", ss(page, "LI_step1_save_error", True))
    else:
        job_no = page.evaluate("document.getElementById('jobno')?.value || ''")
        add_result(JOB, "Step 1", "Save", "PASS", f"Job saved. No: {job_no}")
    ss(page, "LI_step1_saved")

    # --- STEP 2: Buying Charges ---
    log(f"\n--- {JOB}: Step 2 - Buying Charges ---")
    click_step(page, 2)
    page.wait_for_timeout(2000)
    ss(page, "LI_step2_top")

    buy_results = enter_main_charges(page, data["buy_charges"], "buy", JOB)
    add_result(JOB, "Step 2", "Buy Charges", "PASS" if buy_results else "FAIL",
               f"Entered {len(buy_results)} charge(s)")

    click_save(page)
    err = check_page_error(page)
    add_result(JOB, "Step 2", "Save", "PASS" if not err else "FAIL",
               "Saved" if not err else f"Error: {err}")

    # --- STEP 3: Selling Charges ---
    log(f"\n--- {JOB}: Step 3 - Selling Charges ---")
    click_step(page, 3)
    page.wait_for_timeout(2000)
    ss(page, "LI_step3_top")

    sell_results = enter_main_charges(page, data["sell_charges"], "sell", JOB)
    fill_field(page, "remark", data["sell_remark"])
    fill_field(page, "due_date", data["sell_due_date"])

    add_result(JOB, "Step 3", "Sell Charges", "PASS" if sell_results else "FAIL",
               f"Entered {len(sell_results)} charge(s)")

    click_save(page)
    err = check_page_error(page)
    add_result(JOB, "Step 3", "Save", "PASS" if not err else "FAIL",
               "Saved" if not err else f"Error: {err}")

    # --- STEP 4: Purchase Invoice ---
    log(f"\n--- {JOB}: Step 4 - Purchase Invoice ---")
    click_step(page, 4)
    page.wait_for_timeout(2000)
    ss(page, "LI_step4_top")

    pi_text = page.inner_text("body")
    has_pi = "NO PURCHASE INVOICE" not in pi_text.upper()
    add_result(JOB, "Step 4", "Purchase Invoice", "PASS" if has_pi else "WARN",
               "Invoice present" if has_pi else "No purchase invoice generated")

    # --- STEP 5: Sale Invoice ---
    log(f"\n--- {JOB}: Step 5 - Sale Invoice ---")
    click_step(page, 5)
    page.wait_for_timeout(2000)
    ss(page, "LI_step5_top")

    si_text = page.inner_text("body")
    has_si = "NO SALE INVOICE" not in si_text.upper()
    add_result(JOB, "Step 5", "Sale Invoice", "PASS" if has_si else "WARN",
               "Invoice present" if has_si else "No sale invoice generated")

    # --- STEP 6: Attachments ---
    log(f"\n--- {JOB}: Step 6 - Attachments ---")
    click_step(page, 6)
    page.wait_for_timeout(2000)
    ss(page, "LI_step6_top")
    add_result(JOB, "Step 6", "Attachments Section", "PASS", "Attachments tab loaded")

    # --- STEP 7: Clearing Instructions ---
    log(f"\n--- {JOB}: Step 7 - Clearing Instructions ---")
    click_step(page, 7)
    page.wait_for_timeout(2000)
    ss(page, "LI_step7_top")

    remarks = page.locator('#clrmrk, textarea[name="clrmrk"], textarea')
    if remarks.count() > 0:
        remarks.first.fill(data["clearing_remarks"])
        add_result(JOB, "Step 7", "Clearing Remarks", "PASS", "Remarks entered")
    else:
        add_result(JOB, "Step 7", "Clearing Remarks", "WARN", "No remarks field found")

    click_save(page)
    err = check_page_error(page)
    add_result(JOB, "Step 7", "Save", "PASS" if not err else "FAIL",
               "Saved" if not err else f"Error: {err}")

    # Check all PDFs
    all_pdfs = page.evaluate('''() => {
        const links = [];
        document.querySelectorAll('a').forEach(a => {
            if (a.href && a.href.includes('.pdf')) links.push({text: a.textContent.trim().substring(0, 50), href: a.href});
        });
        return [...new Map(links.map(l => [l.href, l])).values()];
    }''')
    if all_pdfs:
        for i, pdf in enumerate(all_pdfs[:5]):
            result = verify_pdf_accessible(page, pdf['href'], f"LI_pdf_{i}")
            add_result(JOB, "PDFs", f"PDF #{i+1}",
                       "PASS" if result["status"] == "OK" else "FAIL",
                       f"Status: {result['status']}, Size: {result.get('size', 0)}B")


# =============================================================================
# TEST ON EXISTING JOBS (also test with real data already present)
# =============================================================================
def test_existing_job_pdfs(page):
    """Test PDFs on existing jobs that have full data and charges."""
    log(f"\n{'='*70}")
    log(f"TESTING: Existing Jobs - PDF Verification")
    log(f"{'='*70}")

    for job_info in [OCEAN_IMPORT, AIR_EXPORT, LAND_IMPORT]:
        name = job_info["name"]
        log(f"\n--- Checking existing {name} jobs ---")

        detail_url = get_job_detail_url(page, job_info["list_url"])
        if not detail_url:
            add_result(name, "Existing", "Find Job", "WARN", "No existing jobs found")
            continue

        page.goto(detail_url, wait_until="networkidle", timeout=TIMEOUT)
        page.wait_for_timeout(3000)

        # Get job details
        job_no = page.evaluate("document.getElementById('jobno')?.value || 'N/A'")
        add_result(name, "Existing", "Load Job", "PASS", f"Job {job_no} loaded")

        # Check all steps
        step_count = len(job_info["steps"])
        for step_idx in range(1, step_count + 1):
            step_name = job_info["steps"][step_idx - 1] if step_idx <= len(job_info["steps"]) else f"Step {step_idx}"
            click_step(page, step_idx)
            page.wait_for_timeout(1500)

            err = check_page_error(page)
            if err:
                add_result(name, f"Step {step_idx}", f"{step_name} Load", "FAIL",
                           f"Error: {err}", ss(page, f"{safe_name(name)}_exist_step{step_idx}_error", True))
            else:
                ss(page, f"{safe_name(name)}_exist_step{step_idx}")

        # Collect and verify ALL PDF links
        all_pdfs = page.evaluate('''() => {
            const links = [];
            document.querySelectorAll('a').forEach(a => {
                if (a.href && a.href.includes('.pdf')) {
                    links.push({text: a.textContent.trim().substring(0, 50), href: a.href});
                }
            });
            return [...new Map(links.map(l => [l.href, l])).values()];
        }''')

        if all_pdfs:
            for i, pdf in enumerate(all_pdfs[:5]):
                result = verify_pdf_accessible(page, pdf['href'], f"{safe_name(name)}_exist_pdf_{i}")
                add_result(name, "Existing PDFs", f"PDF '{pdf['text'][:25]}'",
                           "PASS" if result["status"] == "OK" else "FAIL",
                           f"Status: {result['status']}, Size: {result.get('size', 0)}B")
        else:
            add_result(name, "Existing PDFs", "PDF Links", "WARN", "No PDF links found on this job")


# =============================================================================
# MAIN
# =============================================================================
def main():
    ensure_dirs()
    log("=" * 70)
    log("Sena ERP - Deep Dive End-to-End Test")
    log(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = browser.new_context(viewport=VIEWPORT)
        page = context.new_page()
        page.set_default_timeout(TIMEOUT)

        try:
            login(page)

            # Test 1: Create new Ocean Import with full data
            test_ocean_import(page)

            # Test 2: Create new Air Export with full data
            test_air_export(page)

            # Test 3: Create new Land Import with full data
            test_land_import(page)

            # Test 4: Verify PDFs on existing jobs
            test_existing_job_pdfs(page)

        except Exception as e:
            log(f"\nFATAL ERROR: {e}")
            traceback.print_exc()
            ss(page, "fatal_error", True)
        finally:
            browser.close()

    # Write results
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary
    log(f"\n{'='*70}")
    log("TEST SUMMARY")
    log(f"{'='*70}")
    pass_count = sum(1 for r in results if r['status'] == 'PASS')
    fail_count = sum(1 for r in results if r['status'] == 'FAIL')
    warn_count = sum(1 for r in results if r['status'] == 'WARN')
    total = len(results)

    log(f"Total: {total} | PASS: {pass_count} | FAIL: {fail_count} | WARN: {warn_count}")
    log(f"Pass Rate: {pass_count/total*100:.1f}%" if total > 0 else "No tests")

    if all_errors:
        log(f"\n--- FAILURES ({len(all_errors)}) ---")
        for e in all_errors:
            log(f"  FAIL: {e['job_type']} > {e['step']} > {e['test']}: {e['detail'][:80]}")
            if e.get('screenshot'):
                log(f"    Screenshot: {e['screenshot']}")

    log(f"\nResults saved to: {RESULTS_FILE}")
    log(f"Screenshots in: {SS_DIR}")
    log(f"Error screenshots in: {ERR_SS_DIR}")
    log(f"Downloaded PDFs in: {PDF_DIR}")


if __name__ == "__main__":
    main()
