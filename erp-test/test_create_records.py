#!/usr/bin/env python3
"""
Sena ERP - Create Records Test Script
Tests: HR Employee, Ocean Import, Air Import, Land Import, Job Details, Quote Flow
"""

import json
import traceback
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "http://13.210.47.18:8088"
SCREENSHOT_DIR = Path("/var/lib/freelancer/projects/40298427/erp-test/screenshots/create_records")
RESULTS_FILE = Path("/var/lib/freelancer/projects/40298427/erp-test/results_create_records.json")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

results = {}


def screenshot(page, name):
    path = SCREENSHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path))
    print(f"  [Screenshot] {path}")
    return str(path)


def login(page):
    print("[Login] Navigating to ERP...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    page.evaluate("""
        document.getElementById("username").value = "superadmin";
        document.getElementById("password").value = "Nick@#24";
        document.getElementById("signupForm").submit();
    """)
    print("[Login] Submitted credentials, waiting 8s...")
    page.wait_for_timeout(8000)
    page.wait_for_load_state("networkidle")
    screenshot(page, "00_after_login")
    print("[Login] Done.")


def click_add_new_button(page):
    """Click the green Add New / Add Rate / + New Quote button in the content area."""
    clicked = page.evaluate("""
        () => {
            const allBtns = document.querySelectorAll('a.btn, button.btn, a.btn-success, button.btn-success, a.btn-info, button.btn-info');
            for (const el of allBtns) {
                const text = el.textContent.trim().toLowerCase();
                if ((text.includes('add') || text.includes('new') || text.includes('create')) &&
                    el.offsetParent !== null && !el.classList.contains('nav-link') &&
                    !el.closest('.sidebar') && !el.closest('.side-menu')) {
                    el.click();
                    return el.textContent.trim();
                }
            }
            return null;
        }
    """)
    if clicked:
        print(f"  Clicked button: '{clicked}'")
        return True
    print("  WARNING: Could not find Add button")
    return False


def fill_select2(page, select_id, search_text, label=""):
    """Fill a Select2 dropdown by opening, searching, and selecting first result."""
    print(f"  [Select2] {label or select_id}: searching '{search_text}'...")
    try:
        # Close any open select2 first
        page.evaluate("try { $('.select2-container--open').length && $('select').select2('close'); } catch(e) {}")
        page.wait_for_timeout(500)

        # Check if this element exists and has select2
        exists = page.evaluate(f"""
            (() => {{
                var el = document.getElementById('{select_id}');
                if (!el) return 'not_found';
                try {{ $(el).select2('open'); return 'opened'; }}
                catch(e) {{ return 'no_select2: ' + e.message; }}
            }})()
        """)
        if exists == 'not_found':
            print(f"  [Select2] {label or select_id}: element not found")
            return None
        if exists.startswith('no_select2'):
            print(f"  [Select2] {label or select_id}: {exists}")
            return None

        page.wait_for_timeout(500)

        # Type search text
        search_input = page.locator('.select2-search__field')
        if search_input.count() > 0:
            search_input.fill(search_text)
            page.wait_for_timeout(2000)

        # Click first result
        results_opts = page.locator('.select2-results__option:not(.select2-results__message)')
        if results_opts.count() > 0:
            first_text = results_opts.first.text_content()
            results_opts.first.click()
            page.wait_for_timeout(500)
            print(f"  [Select2] {label or select_id}: selected '{first_text}'")
            return first_text
        else:
            page.evaluate(f"try {{ $('#{select_id}').select2('close'); }} catch(e) {{}}")
            print(f"  [Select2] {label or select_id}: no results found")
            return None
    except Exception as e:
        print(f"  [Select2] {label or select_id}: ERROR - {e}")
        try:
            page.evaluate("try { $('select').select2('close'); } catch(e) {}")
        except:
            pass
        return None


def fill_date_js(page, field_id, date_str):
    """Fill a date field via JS and dispatch change event."""
    found = page.evaluate(f"""
        (() => {{
            var el = document.getElementById('{field_id}');
            if (!el) el = document.querySelector('[name="{field_id}"]');
            if (el) {{
                el.value = '{date_str}';
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return true;
            }}
            return false;
        }})()
    """)
    if found:
        print(f"  [Date] {field_id} = {date_str}")
    else:
        print(f"  [Date] {field_id} not found")


def fill_field_js(page, field_id, value):
    """Fill a field using JavaScript - safe for values with special characters."""
    # Use arguments passing to avoid template literal issues
    found = page.evaluate("""
        (args) => {
            var fid = args[0], val = args[1];
            var el = document.getElementById(fid);
            if (!el) el = document.querySelector('[name="' + fid + '"]');
            if (el && el.offsetParent !== null) {
                // Use native input value setter to work with React/Vue/etc
                var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                nativeInputValueSetter.call(el, val);
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                return 'filled';
            }
            if (el) {
                el.value = val;
                el.dispatchEvent(new Event('change', { bubbles: true }));
                return 'filled_hidden';
            }
            return 'not_found';
        }
    """, [field_id, value])
    if found.startswith('filled'):
        print(f"  Filled {field_id} = {value}")
        return True
    else:
        print(f"  Field {field_id} not found")
        return False


def fill_field(page, field_id, value, by_name=False):
    """Fill a field by ID or name, using Playwright locators first, JS fallback."""
    try:
        if by_name:
            el = page.locator(f'[name="{field_id}"]')
        else:
            el = page.locator(f'#{field_id}')
        if el.count() > 0 and el.first.is_visible():
            el.first.fill(value)
            print(f"  Filled {'[name=' + field_id + ']' if by_name else '#' + field_id} = {value}")
            return True
        # Try the other selector
        alt = page.locator(f'[name="{field_id}"]' if not by_name else f'#{field_id}')
        if alt.count() > 0 and alt.first.is_visible():
            alt.first.fill(value)
            print(f"  Filled (alt) {field_id} = {value}")
            return True
    except:
        pass
    # JS fallback
    return fill_field_js(page, field_id, value)


def click_save_submit(page):
    """Click Save/Submit/Create button in the form."""
    clicked = page.evaluate("""
        () => {
            var submits = document.querySelectorAll('button[type="submit"], input[type="submit"]');
            for (var el of submits) {
                if (el.offsetParent !== null) {
                    el.click();
                    return (el.textContent || el.value || 'submit').trim();
                }
            }
            var btns = document.querySelectorAll('button, input[type="button"]');
            for (var el of btns) {
                var text = (el.textContent || el.value || '').trim().toLowerCase();
                if ((text.includes('save') || text.includes('submit') || text.includes('create job') || text === 'create')
                    && el.offsetParent !== null && !el.classList.contains('nav-link')) {
                    el.click();
                    return (el.textContent || el.value).trim();
                }
            }
            return null;
        }
    """)
    if clicked:
        print(f"  Clicked Save/Submit: '{clicked}'")
        return True
    print("  WARNING: No Save/Submit button found")
    return False


def check_result(page, test_result):
    """Check for SweetAlert, validation errors, success/error messages."""
    # Check SweetAlert
    try:
        swal = page.locator('.swal2-popup')
        if swal.count() > 0 and swal.first.is_visible():
            swal_text = swal.first.text_content().strip()
            print(f"  SweetAlert: {swal_text}")
            test_result["swal_message"] = swal_text
            if 'success' in swal_text.lower() or 'created' in swal_text.lower() or 'saved' in swal_text.lower():
                test_result["status"] = "success"
            else:
                test_result["status"] = "error"
            ok_btn = page.locator('.swal2-confirm')
            if ok_btn.count() > 0:
                ok_btn.first.click()
                page.wait_for_timeout(1000)
            return
    except:
        pass

    # Check alert divs
    alerts = page.locator('.alert:visible')
    for i in range(min(alerts.count(), 5)):
        msg = alerts.nth(i).text_content().strip()
        if msg:
            print(f"  Alert: {msg[:120]}")
            if 'success' in msg.lower() or 'added' in msg.lower():
                test_result["status"] = "success"
            elif 'error' in msg.lower() or 'fail' in msg.lower():
                test_result["status"] = "error"
                test_result["errors"].append(msg[:200])

    # Check validation error messages - "This field is required." type
    val_errors = page.evaluate("""
        () => {
            var errors = [];
            // Parsley errors
            var parsley = document.querySelectorAll('.parsley-errors-list li, .parsley-required');
            for (var el of parsley) {
                if (el.textContent.trim()) errors.push(el.textContent.trim());
            }
            // Generic required field indicators
            var reqd = document.querySelectorAll('.text-danger, .field-error, .invalid-feedback');
            for (var el of reqd) {
                var t = el.textContent.trim();
                if (t && t.includes('required') && el.offsetParent !== null) errors.push(t);
            }
            // Browser validation tooltips / required fields with :invalid
            var invalids = document.querySelectorAll(':invalid');
            for (var el of invalids) {
                if (el.name || el.id) errors.push('Required: ' + (el.name || el.id) + ' (' + (el.labels?.[0]?.textContent?.trim() || '') + ')');
            }
            return errors.slice(0, 20);
        }
    """)
    if val_errors:
        for e in val_errors:
            print(f"  Validation: {e}")
            test_result["errors"].append(e)

    if test_result["status"] == "unknown":
        body = page.locator('body').text_content().lower()
        if 'successfully' in body or 'has been created' in body or 'record added' in body:
            test_result["status"] = "success"
        elif val_errors:
            test_result["status"] = "validation_error"
        else:
            test_result["status"] = "submitted"


def select_option_js(page, field_id, value):
    """Select an option in a regular <select> element."""
    result = page.evaluate(f"""
        (() => {{
            var el = document.getElementById('{field_id}') || document.querySelector('[name="{field_id}"]');
            if (!el) return 'not_found';
            el.value = '{value}';
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            return 'selected';
        }})()
    """)
    print(f"  Select {field_id} = {value}: {result}")
    return result == 'selected'


# ============================================================
# TEST 1: Create HR Employee
# ============================================================
def test_create_employee(page):
    print("\n" + "=" * 60)
    print("TEST 1: Create HR Employee")
    print("=" * 60)
    test_result = {"test": "Create HR Employee", "status": "unknown", "errors": [], "screenshots": []}

    try:
        page.goto(f"{BASE_URL}/51564f2eb2d3a1bca494e86b1c67635e")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        test_result["screenshots"].append(screenshot(page, "01_employee_list"))

        click_add_new_button(page)
        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")
        test_result["screenshots"].append(screenshot(page, "02_employee_form"))
        print(f"  URL: {page.url}")

        # Fill form - use unique values to avoid duplicates
        import random
        unique_id = random.randint(1000, 9999)
        unique_mob = f'99{random.randint(10000000, 99999999)}'
        for fid, val in [
            ('fname', 'TestUser'), ('mname', 'Auto'), ('lname', 'Test'),
            ('Mob', unique_mob), ('Email', f'autotest{unique_id}@senaerp.com'),
            ('uname', f'autotest{unique_id}'), ('pwd', 'Test@12345'),
        ]:
            fill_field(page, fid, val)

        # User Type radio
        try:
            page.locator('input[name="UType"]').first.click(force=True)
            print("  Selected UType radio")
        except Exception as e:
            print(f"  UType radio: {e}")

        page.wait_for_timeout(1000)
        test_result["screenshots"].append(screenshot(page, "03_employee_filled"))

        click_save_submit(page)
        page.wait_for_timeout(3000)
        test_result["screenshots"].append(screenshot(page, "04_employee_result"))
        check_result(page, test_result)

        # Verify in list
        page.goto(f"{BASE_URL}/51564f2eb2d3a1bca494e86b1c67635e")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        test_result["screenshots"].append(screenshot(page, "05_employee_list_after"))

        body = page.locator('body').text_content()
        test_result["verified_in_list"] = 'TestUser' in body or 'autotestuser' in body
        print(f"  Verified in list: {test_result['verified_in_list']}")

    except Exception as e:
        test_result["status"] = "exception"
        test_result["errors"].append(str(e))
        print(f"  EXCEPTION: {e}")
        traceback.print_exc()
        try:
            screenshot(page, "01_employee_exception")
        except:
            pass

    results["test1_employee"] = test_result


# ============================================================
# TEST 2: Create Ocean Import Job
# ============================================================
def test_create_ocean_import(page):
    print("\n" + "=" * 60)
    print("TEST 2: Create Ocean Import Job")
    print("=" * 60)
    test_result = {"test": "Create Ocean Import Job", "status": "unknown", "errors": [], "screenshots": []}

    try:
        page.goto(f"{BASE_URL}/9dddd5ce1b1375bc497feeb871842d4b")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        test_result["screenshots"].append(screenshot(page, "10_ocean_list"))

        click_add_new_button(page)
        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")
        test_result["screenshots"].append(screenshot(page, "11_ocean_form"))
        print(f"  URL: {page.url}")

        # BASIC DETAILS section
        # Shipment Type select
        select_option_js(page, 'SptmntId', '2')  # FCL
        select_option_js(page, 'gbpapplicable', 'no')

        # Dates
        today = "18/04/2026"
        for d in ['jbdte', 'mbldte', 'etd', 'eta']:
            fill_date_js(page, d, today)

        # MBL NO
        fill_field(page, 'mblno', 'TESTMBL-AUTO-001')

        # Select2 dropdowns for basic details
        s2_basic = [
            ('IncoTrms', 'f', 'Incoterms'),
            ('consigne', 'a', 'Consignee'),
            ('lport', 'bomb', 'Port of Loading'),
            ('dport', 'kol', 'Port of Discharge'),
            ('overseas1', 'a', 'Overseas Agent'),
            ('shpline', 'a', 'Shipping Line'),
        ]
        for sel_id, search, label in s2_basic:
            r = fill_select2(page, sel_id, search, label)
            if r:
                test_result[f"select2_{sel_id}"] = r
            page.wait_for_timeout(300)

        # SHIPMENT RELATED DETAILS section
        # Field IDs have _1 suffix (shipment 1) and _addcmdt_1 for commodity section

        # Shipper (select2 with ID shipper_1)
        r = fill_select2(page, 'shipper_1', 'a', 'Shipper')
        if r:
            test_result["select2_shipper"] = r

        # HBL NO (ID: hblno_1) and HBL Date (ID: hbldte_1)
        fill_field_js(page, 'hblno_1', 'HBL-AUTO-001')
        fill_date_js(page, 'hbldte_1', today)

        # Commodity (select2 with ID cmdty_1_addcmdt_1)
        fill_select2(page, 'cmdty_1_addcmdt_1', 'a', 'Commodity')

        # HSN (ID: hsn_cmdty_1_addcmdt_1)
        fill_field_js(page, 'hsn_cmdty_1_addcmdt_1', '84719000')

        # Gross/Net Weight in commodity section
        fill_field_js(page, 'grswght_1_addcmdt_1', '100')
        fill_field_js(page, 'ntwght_1_addcmdt_1', '80')

        # Invoice Value in commodity section (ID: spinval_1_addcmdt_1)
        fill_field_js(page, 'spinval_1_addcmdt_1', '5000')

        # No. of Packs in commodity (ID: pkno_1_addcmdt_1)
        fill_field_js(page, 'pkno_1_addcmdt_1', '10')

        # No. of Pallets/Pack (ID: packno_1)
        fill_field_js(page, 'packno_1', '5')

        # Freight and Insurance
        fill_field(page, 'frghtchrg', '500')
        fill_field(page, 'inschrg', '100')

        # Shipper Invoice fields (IDs with _1 suffix)
        fill_field_js(page, 'shpinvval_1', '5000')
        fill_field_js(page, 'shpinvno_1', 'SINV-001')
        fill_date_js(page, 'shpinvdte_1', today)

        # Container No (ID: contno_1) - must be 11 characters
        fill_field_js(page, 'contno_1', 'TESU1234567')

        # Check remaining unfilled required fields
        page.wait_for_timeout(500)
        unfilled = page.evaluate("""
            () => {
                var fields = [];
                var inputs = document.querySelectorAll('input[required], select[required], textarea[required], input.required, select.required');
                for (var el of inputs) {
                    if (!el.value && el.offsetParent !== null) {
                        fields.push({id: el.id, name: el.name, type: el.type, tag: el.tagName});
                    }
                }
                return fields;
            }
        """)
        if unfilled:
            print(f"  Unfilled required fields: {json.dumps(unfilled, indent=2)}")
            test_result["unfilled_required"] = unfilled

        test_result["screenshots"].append(screenshot(page, "12_ocean_filled_top"))
        page.evaluate("window.scrollTo(0, 500)")
        page.wait_for_timeout(300)
        test_result["screenshots"].append(screenshot(page, "12b_ocean_filled_mid"))
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(300)
        test_result["screenshots"].append(screenshot(page, "12c_ocean_filled_bottom"))

        click_save_submit(page)
        page.wait_for_timeout(3000)
        test_result["screenshots"].append(screenshot(page, "13_ocean_result"))

        # Scroll to see validation errors
        page.evaluate("window.scrollTo(0, 500)")
        page.wait_for_timeout(300)
        test_result["screenshots"].append(screenshot(page, "13b_ocean_result_mid"))

        check_result(page, test_result)

        # Check list
        page.goto(f"{BASE_URL}/9dddd5ce1b1375bc497feeb871842d4b")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        test_result["screenshots"].append(screenshot(page, "14_ocean_list_after"))

        body = page.locator('body').text_content()
        test_result["verified_in_list"] = 'TESTMBL-AUTO-001' in body
        print(f"  Verified in list: {test_result['verified_in_list']}")

    except Exception as e:
        test_result["status"] = "exception"
        test_result["errors"].append(str(e))
        print(f"  EXCEPTION: {e}")
        traceback.print_exc()
        try:
            screenshot(page, "10_ocean_exception")
        except:
            pass

    results["test2_ocean_import"] = test_result


# ============================================================
# TEST 3: Create Air Import Job
# ============================================================
def test_create_air_import(page):
    print("\n" + "=" * 60)
    print("TEST 3: Create Air Import Job")
    print("=" * 60)
    test_result = {"test": "Create Air Import Job", "status": "unknown", "errors": [], "screenshots": []}

    try:
        page.goto(f"{BASE_URL}/951733b073f499bd67fa764d38df48a8")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        test_result["screenshots"].append(screenshot(page, "20_air_list"))

        click_add_new_button(page)
        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")
        test_result["screenshots"].append(screenshot(page, "21_air_form"))
        print(f"  URL: {page.url}")

        # Discover the form fields first
        form_fields = page.evaluate("""
            () => {
                var fields = [];
                var inputs = document.querySelectorAll('input, select, textarea');
                for (var el of inputs) {
                    if (el.offsetParent !== null && el.type !== 'hidden') {
                        fields.push({id: el.id, name: el.name, type: el.type, tag: el.tagName, required: el.required});
                    }
                }
                return fields;
            }
        """)
        print(f"  Visible form fields ({len(form_fields)}):")
        for f in form_fields[:30]:
            print(f"    {f}")
        test_result["form_fields"] = form_fields[:30]

        # Fill dates
        today = "18/04/2026"
        for d in ['jbdte', 'hawbdte', 'mawbdte', 'etd', 'eta']:
            fill_date_js(page, d, today)

        # BASIC DETAILS - text fields with correct IDs
        # MAWB NO must be 11 digits
        fill_field_js(page, 'mawbno', '12345678901')
        fill_field_js(page, 'hawbno', 'HAWB-A-001')
        fill_field_js(page, 'flght_no', 'AI-101')  # Correct ID: flght_no
        fill_field_js(page, 'frghtchrg', '800')
        fill_field_js(page, 'inschrg', '150')
        fill_field_js(page, 'shpinvno', 'AINV-001')  # Shipper Invoice No (required)

        # GBP applicable select
        select_option_js(page, 'gbpapplicable', 'no')

        # Select2 dropdowns for basic details
        for sel_id, search, label in [
            ('IncoTrms', 'f', 'Incoterms'),
            ('consigne', 'a', 'Consignee'),
            ('lport', 'del', 'Air Port of Loading'),
            ('dport', 'kol', 'Air Port of Discharge'),
            ('overseas1', 'a', 'Overseas Agent'),
            ('splierId', 'a', 'Carrier Name'),  # Correct ID: splierId
            ('shipper_1', 'a', 'Shipper'),  # Correct ID: shipper_1
        ]:
            fill_select2(page, sel_id, search, label)
            page.wait_for_timeout(300)

        # SHIPMENT RELATED DETAILS - commodity section
        fill_select2(page, 'cmdty_1', 'a', 'Commodity')  # Correct ID: cmdty_1
        fill_field_js(page, 'hsn_cmdty_1', '84719000')  # HSN
        fill_field_js(page, 'packno_1', '5')  # Packages
        fill_field_js(page, 'lngth_1', '100')  # Length
        fill_field_js(page, 'brdth_1', '50')  # Breadth
        fill_field_js(page, 'hght_1', '30')  # Height

        # Volume select (ID: volume_1) - try to select first option
        select_option_js(page, 'volume_1', 'CBM')
        # Also try other values if CBM doesn't work
        page.evaluate("""
            (() => {
                var el = document.getElementById('volume_1');
                if (el && !el.value) {
                    for (var o of el.options) {
                        if (o.value) { el.value = o.value; el.dispatchEvent(new Event('change', {bubbles:true})); break; }
                    }
                }
            })()
        """)

        fill_field_js(page, 'spinval_1', '10000')  # Invoice Value
        fill_field_js(page, 'grswght_1', '250')  # Gross Weight
        fill_field_js(page, 'ntwght_1', '200')  # Net Weight
        fill_field_js(page, 'vlmwght_1', '150')  # Volume Weight
        fill_field_js(page, 'chrgwght_1', '300')  # Chargeable Weight
        fill_field_js(page, 'totvlght', '150')  # Total Volume Weight

        # Shipper invoice date
        fill_date_js(page, 'shpinvdte', today)

        # Check unfilled required
        unfilled = page.evaluate("""
            () => {
                var fields = [];
                var inputs = document.querySelectorAll('input[required], select[required]');
                for (var el of inputs) {
                    if (!el.value && el.offsetParent !== null) {
                        fields.push({id: el.id, name: el.name, type: el.type});
                    }
                }
                return fields;
            }
        """)
        if unfilled:
            print(f"  Unfilled required: {json.dumps(unfilled)}")
            test_result["unfilled_required"] = unfilled

        page.wait_for_timeout(1000)
        test_result["screenshots"].append(screenshot(page, "22_air_filled"))
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(300)
        test_result["screenshots"].append(screenshot(page, "22b_air_filled_bottom"))

        click_save_submit(page)
        page.wait_for_timeout(3000)
        test_result["screenshots"].append(screenshot(page, "23_air_result"))

        check_result(page, test_result)

    except Exception as e:
        test_result["status"] = "exception"
        test_result["errors"].append(str(e))
        print(f"  EXCEPTION: {e}")
        traceback.print_exc()
        try:
            screenshot(page, "20_air_exception")
        except:
            pass

    results["test3_air_import"] = test_result


# ============================================================
# TEST 4: Create Land Import Job
# ============================================================
def test_create_land_import(page):
    print("\n" + "=" * 60)
    print("TEST 4: Create Land Import Job")
    print("=" * 60)
    test_result = {"test": "Create Land Import Job", "status": "unknown", "errors": [], "screenshots": []}

    try:
        page.goto(f"{BASE_URL}/8013f48199799dce7a1fde812910a496")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        test_result["screenshots"].append(screenshot(page, "30_land_list"))

        click_add_new_button(page)
        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")
        test_result["screenshots"].append(screenshot(page, "31_land_form"))
        print(f"  URL: {page.url}")

        # Discover form fields
        form_fields = page.evaluate("""
            () => {
                var fields = [];
                var inputs = document.querySelectorAll('input, select, textarea');
                for (var el of inputs) {
                    if (el.offsetParent !== null && el.type !== 'hidden') {
                        fields.push({id: el.id, name: el.name, type: el.type, tag: el.tagName, required: el.required, placeholder: el.placeholder || ''});
                    }
                }
                return fields;
            }
        """)
        print(f"  Visible form fields ({len(form_fields)}):")
        for f in form_fields:
            print(f"    {f}")
        test_result["form_fields"] = form_fields

        # Fill fields by name - correct field names from discovery
        for fname, val in [
            ('origin', 'Mumbai'),
            ('destination', 'Delhi'),
            ('veh_reg', 'MH01AB1234'),
            ('driver', 'Test Driver'),
            ('cmr_no', 'CMR-AUTO-001'),  # Correct: cmr_no not cmrno
            ('gw', '500'),  # Correct: gw not grosswt
            ('nw', '400'),  # Correct: nw not netwt
            ('cbm', '10'),
            ('pkgs', '20'),  # Correct: pkgs not packages
            ('remarks', 'Auto test land import job'),
        ]:
            fill_field(page, fname, val, by_name=True)

        # Incoterms - regular select (from screenshot: "-- Select --")
        # Find the Incoterms select element
        inco_result = page.evaluate("""
            () => {
                var selects = document.querySelectorAll('select');
                for (var sel of selects) {
                    var label = sel.closest('.form-group')?.querySelector('label')?.textContent || '';
                    if (label.toLowerCase().includes('inco') || sel.name.toLowerCase().includes('inco') || sel.id.toLowerCase().includes('inco')) {
                        // Get available options
                        var opts = [];
                        for (var o of sel.options) {
                            opts.push({value: o.value, text: o.textContent.trim()});
                        }
                        return {id: sel.id, name: sel.name, options: opts};
                    }
                }
                return null;
            }
        """)
        if inco_result:
            print(f"  Incoterms select: {json.dumps(inco_result)}")
            # Select first non-empty option
            opts = inco_result.get('options', [])
            for opt in opts:
                if opt['value'] and opt['value'] != '':
                    sel_name = inco_result.get('name') or inco_result.get('id')
                    page.evaluate(f"""
                        (() => {{
                            var el = document.getElementById('{inco_result.get("id", "")}') || document.querySelector('[name="{inco_result.get("name", "")}"]');
                            if (el) {{
                                el.value = '{opt["value"]}';
                                el.dispatchEvent(new Event('change', {{bubbles: true}}));
                            }}
                        }})()
                    """)
                    print(f"  Selected Incoterms: {opt['text']} (value={opt['value']})")
                    break

        # Customer/Consignee - select with ID 'consigne'
        # This shows "-- Type to search --" - it uses select2 but needs special handling
        consignee_filled = False

        # Detect what kind of widget this is
        widget_info = page.evaluate("""
            (() => {
                var el = document.getElementById('consigne');
                if (!el) return {error: 'not found'};
                var info = {tag: el.tagName, type: el.type, classes: el.className};
                // Check for select2 container next to it
                var next = el.nextElementSibling;
                if (next) info.next = {tag: next.tagName, classes: next.className, id: next.id};
                // Check parent
                info.parentClasses = el.parentElement?.className || '';
                // Check if select2 data attached
                try {
                    var s2data = $(el).data('select2');
                    info.hasSelect2Data = !!s2data;
                } catch(e) {
                    info.hasSelect2Data = false;
                    info.s2error = e.message;
                }
                return info;
            })()
        """)
        print(f"  Consignee widget info: {json.dumps(widget_info)}")

        # Try clicking the rendered select2 span container
        try:
            # The select2 renders a span.select2-container after the original select
            clicked_s2 = page.evaluate("""
                (() => {
                    var el = document.getElementById('consigne');
                    if (!el) return 'not_found';
                    var container = el.nextElementSibling;
                    if (container && container.classList.contains('select2-container')) {
                        var selection = container.querySelector('.select2-selection');
                        if (selection) {
                            selection.click();
                            return 'clicked';
                        }
                    }
                    // Try: initialize select2 on the element first, then open
                    try {
                        $(el).select2({
                            placeholder: '-- Type to search --',
                            ajax: {
                                url: window.location.origin + '/getCustomers',
                                dataType: 'json',
                                delay: 250,
                                data: function(params) { return { q: params.term }; },
                                processResults: function(data) { return { results: data }; }
                            }
                        });
                        $(el).select2('open');
                        return 'initialized_and_opened';
                    } catch(e) {
                        return 'init_error: ' + e.message;
                    }
                })()
            """)
            print(f"  Consignee click result: {clicked_s2}")

            if 'clicked' in str(clicked_s2) or 'opened' in str(clicked_s2):
                page.wait_for_timeout(500)
                search = page.locator('.select2-search__field')
                if search.count() > 0 and search.first.is_visible():
                    search.fill('a')
                    page.wait_for_timeout(2000)
                    opts = page.locator('.select2-results__option:not(.select2-results__message)')
                    if opts.count() > 0:
                        first_text = opts.first.text_content()
                        opts.first.click()
                        page.wait_for_timeout(500)
                        consignee_filled = True
                        print(f"  Selected consignee: {first_text}")
                    else:
                        print("  No consignee results")
                        page.evaluate("try { $('#consigne').select2('close'); } catch(e) {}")
        except Exception as e:
            print(f"  Consignee error: {e}")

        if not consignee_filled:
            print("  WARNING: Could not fill consignee - land form select2 initialization issue")

        # Vehicle Type select
        vtype_result = page.evaluate("""
            () => {
                var selects = document.querySelectorAll('select');
                for (var sel of selects) {
                    var label = sel.closest('.form-group')?.querySelector('label')?.textContent || '';
                    if (label.toLowerCase().includes('vehicle type') || sel.name.toLowerCase().includes('veh_type') || sel.name.toLowerCase().includes('vehicletype')) {
                        var opts = [];
                        for (var o of sel.options) {
                            if (o.value) opts.push({value: o.value, text: o.textContent.trim()});
                        }
                        if (opts.length > 0) {
                            sel.value = opts[0].value;
                            sel.dispatchEvent(new Event('change', {bubbles: true}));
                            return 'Selected: ' + opts[0].text;
                        }
                        return {id: sel.id, name: sel.name, options: opts};
                    }
                }
                return 'not_found';
            }
        """)
        print(f"  Vehicle Type: {vtype_result}")

        # Dates
        today = "18/04/2026"
        fill_date_js(page, 'etd', today)
        fill_date_js(page, 'eta', today)

        page.wait_for_timeout(1000)
        test_result["screenshots"].append(screenshot(page, "32_land_filled"))

        click_save_submit(page)
        page.wait_for_timeout(3000)
        test_result["screenshots"].append(screenshot(page, "33_land_result"))

        check_result(page, test_result)

        # If still on form, check what's needed
        if test_result["status"] in ["validation_error", "submitted", "unknown"]:
            unfilled = page.evaluate("""
                () => {
                    var msgs = [];
                    var errs = document.querySelectorAll('.text-danger, .parsley-errors-list li, .invalid-feedback');
                    for (var el of errs) {
                        if (el.textContent.trim() && el.offsetParent !== null) msgs.push(el.textContent.trim());
                    }
                    return msgs;
                }
            """)
            if unfilled:
                print(f"  Visible validation messages: {unfilled}")
                test_result["visible_validation_errors"] = unfilled

    except Exception as e:
        test_result["status"] = "exception"
        test_result["errors"].append(str(e))
        print(f"  EXCEPTION: {e}")
        traceback.print_exc()
        try:
            screenshot(page, "30_land_exception")
        except:
            pass

    results["test4_land_import"] = test_result


# ============================================================
# TEST 5: View/Navigate Ocean Import Job Details
# ============================================================
def test_view_job_details(page):
    print("\n" + "=" * 60)
    print("TEST 5: View/Navigate Ocean Import Job Details")
    print("=" * 60)
    test_result = {"test": "View Ocean Import Job Details", "status": "unknown", "errors": [], "screenshots": [], "tabs_found": []}

    try:
        page.goto(f"{BASE_URL}/9dddd5ce1b1375bc497feeb871842d4b")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        test_result["screenshots"].append(screenshot(page, "40_ocean_jobs_list"))

        rows = page.locator('table tbody tr')
        row_count = rows.count()
        print(f"  Found {row_count} rows in table")
        test_result["job_count"] = row_count

        if row_count > 0:
            # Click the job number link (2nd column)
            job_link = page.locator('table tbody tr:first-child td:nth-child(2) a')
            if job_link.count() > 0:
                job_link.first.click()
                print("  Clicked job number link")
            else:
                # Fallback: find any link in first row
                page.evaluate("""
                    () => {
                        var row = document.querySelector('table tbody tr');
                        if (row) {
                            var links = row.querySelectorAll('a');
                            for (var a of links) {
                                if (a.href && a.href.includes('8088') && a.offsetParent !== null) {
                                    a.click();
                                    return true;
                                }
                            }
                        }
                        return false;
                    }
                """)

            page.wait_for_timeout(3000)
            page.wait_for_load_state("networkidle")
            test_result["screenshots"].append(screenshot(page, "41_job_detail"))
            print(f"  URL: {page.url}")

            # Find steps/tabs
            step_names = ['Basic Details', 'Clearing Instructions', 'Delivery Note',
                         'Buying Charges', 'Selling Charges', 'Purchase Invoice',
                         'Sale Invoice', 'Job Supporting', 'Files']

            for step_name in step_names:
                try:
                    el = page.locator(f'text="{step_name}"')
                    if el.count() > 0 and el.first.is_visible():
                        test_result["tabs_found"].append(step_name)
                except:
                    pass

            print(f"  Found tabs: {test_result['tabs_found']}")

            # Click each tab and screenshot
            for step_name in step_names[1:]:  # Skip Basic Details (already shown)
                try:
                    el = page.locator(f'text="{step_name}"').first
                    if el.is_visible():
                        el.click()
                        page.wait_for_timeout(1500)
                        safe = step_name.replace(' ', '_')[:20]
                        test_result["screenshots"].append(screenshot(page, f"42_step_{safe}"))
                        print(f"    Clicked: {step_name}")
                except:
                    pass

            test_result["status"] = "success"
        else:
            test_result["status"] = "no_jobs"

    except Exception as e:
        test_result["status"] = "exception"
        test_result["errors"].append(str(e))
        print(f"  EXCEPTION: {e}")
        traceback.print_exc()

    results["test5_view_details"] = test_result


# ============================================================
# TEST 6: Verify Quote Creation Flow
# ============================================================
def test_quote_flow(page):
    print("\n" + "=" * 60)
    print("TEST 6: Verify Quote Creation Flow")
    print("=" * 60)
    test_result = {"test": "Quote Creation Flow", "status": "unknown", "errors": [], "screenshots": [], "pages_checked": []}

    pages = [
        ("Quotes", "/68915d3ba92a6ff8c96734362d61b15e"),
        ("Rate Database", "/95ea21eb539e083e42f57313509a93ed"),
        ("Client Rates", "/db6f53167f5911e700a4b3aae0352572"),
    ]

    for page_name, path in pages:
        print(f"\n  --- {page_name} ---")
        info = {"name": page_name, "url": path, "buttons_found": [], "has_add": False}

        try:
            page.goto(f"{BASE_URL}{path}")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)

            safe = page_name.replace(' ', '_').lower()
            test_result["screenshots"].append(screenshot(page, f"50_{safe}"))

            btns = page.evaluate("""
                () => {
                    var r = [];
                    var btns = document.querySelectorAll('a.btn, button.btn, .btn-success, .btn-primary, .btn-info');
                    for (var el of btns) {
                        var t = el.textContent.trim();
                        if (t && el.offsetParent !== null && !el.closest('.sidebar')) r.push(t);
                    }
                    return r;
                }
            """)
            info["buttons_found"] = btns
            print(f"    Buttons: {btns}")

            has_add = any(w in ' '.join(btns).lower() for w in ['add', 'new', 'create'])
            info["has_add"] = has_add

            if has_add:
                click_add_new_button(page)
                page.wait_for_timeout(3000)
                page.wait_for_load_state("networkidle")
                test_result["screenshots"].append(screenshot(page, f"51_{safe}_form"))
                print(f"    Form URL: {page.url}")

                page.evaluate("window.scrollTo(0, 500)")
                page.wait_for_timeout(300)
                test_result["screenshots"].append(screenshot(page, f"51b_{safe}_form_scroll"))

                # Discover form fields
                fields = page.evaluate("""
                    () => {
                        var f = [];
                        var inputs = document.querySelectorAll('input, select, textarea');
                        for (var el of inputs) {
                            if (el.offsetParent !== null && el.type !== 'hidden') {
                                f.push({id: el.id, name: el.name, type: el.type, required: el.required});
                            }
                        }
                        return f;
                    }
                """)
                info["form_fields"] = fields[:20]
                for f in fields[:15]:
                    print(f"      Field: {f}")

        except Exception as e:
            info["error"] = str(e)
            print(f"    ERROR: {e}")

        test_result["pages_checked"].append(info)

    test_result["status"] = "completed"
    results["test6_quote_flow"] = test_result


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("Sena ERP - Create Records Test Suite")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        context.set_default_timeout(60000)
        page = context.new_page()

        login(page)

        test_create_employee(page)
        test_create_ocean_import(page)
        test_create_air_import(page)
        test_create_land_import(page)
        test_view_job_details(page)
        test_quote_flow(page)

        browser.close()

    results["timestamp"] = datetime.now().isoformat()
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n\nResults saved to {RESULTS_FILE}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for key, val in results.items():
        if key == "timestamp":
            continue
        status = val.get("status", "?")
        swal = val.get("swal_message", "")
        errors = val.get("errors", [])
        verified = val.get("verified_in_list")
        print(f"  {val.get('test', key)}: {status}")
        if swal:
            print(f"    SweetAlert: {swal[:100]}")
        if errors:
            for e in errors[:5]:
                print(f"    - {str(e)[:120]}")
        if verified is not None:
            print(f"    Verified in list: {verified}")
        unfilled = val.get("unfilled_required")
        if unfilled:
            print(f"    Unfilled required fields: {len(unfilled)}")
            for u in unfilled[:5]:
                print(f"      {u}")


if __name__ == "__main__":
    main()
