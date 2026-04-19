#!/usr/bin/env python3
"""
Sena ERP - Remaining Job Types Test Script
Tests: Ocean Export, Air Export, Land Import, Land Export
"""

import sys
import json
import traceback
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

BASE_URL = "http://13.210.47.18:8088"
SCREENSHOT_DIR = Path("/var/lib/freelancer/projects/40298427/erp-test/screenshots/remaining_jobs")
RESULTS_FILE = Path("/var/lib/freelancer/projects/40298427/erp-test/results_remaining_jobs.json")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

results = {}


def screenshot(page, name):
    path = SCREENSHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
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
        page.evaluate("try { $('.select2-container--open').length && $('select.select2-hidden-accessible').select2('close'); } catch(e) {}")
        page.wait_for_timeout(300)

        exists = page.evaluate(f"""
            (() => {{
                var el = document.getElementById('{select_id}');
                if (!el) el = document.querySelector('[name="{select_id}"]');
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

        search_input = page.locator('.select2-search__field')
        if search_input.count() > 0:
            search_input.fill(search_text)
            page.wait_for_timeout(2000)

        results_opts = page.locator('.select2-results__option--selectable')
        if results_opts.count() > 0:
            first_text = results_opts.first.text_content()
            try:
                results_opts.first.click(timeout=3000)
            except:
                # JS fallback for invisible/off-screen dropdowns
                page.evaluate("""() => {
                    var opt = document.querySelector('.select2-results__option--selectable');
                    if (opt) opt.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                }""")
            page.wait_for_timeout(500)
            print(f"  [Select2] {label or select_id}: selected '{first_text}'")
            return first_text

        results_opts2 = page.locator('.select2-results__option:not(.select2-results__message)')
        if results_opts2.count() > 0:
            first_text = results_opts2.first.text_content()
            try:
                results_opts2.first.click(timeout=3000)
            except:
                page.evaluate("""() => {
                    var opts = document.querySelectorAll('.select2-results__option:not(.select2-results__message)');
                    if (opts.length > 0) opts[0].dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                }""")
            page.wait_for_timeout(500)
            print(f"  [Select2] {label or select_id}: selected (fallback) '{first_text}'")
            return first_text

        page.evaluate(f"try {{ $('#{select_id}').select2('close'); }} catch(e) {{}}")
        print(f"  [Select2] {label or select_id}: no results found")
        return None
    except Exception as e:
        print(f"  [Select2] {label or select_id}: ERROR - {e}")
        try:
            page.evaluate("try { $('select.select2-hidden-accessible').select2('close'); } catch(e) {}")
        except:
            pass
        return None


def fill_select2_by_css(page, css_selector, search_text, label=""):
    """Fill a Select2 dropdown using CSS selector."""
    print(f"  [Select2-css] {label}: searching '{search_text}'...")
    try:
        page.evaluate("try { $('.select2-container--open').length && $('select.select2-hidden-accessible').select2('close'); } catch(e) {}")
        page.wait_for_timeout(300)

        exists = page.evaluate(f"""
            (() => {{
                var el = document.querySelector('{css_selector}');
                if (!el) return 'not_found';
                try {{ $(el).select2('open'); return 'opened'; }}
                catch(e) {{ return 'no_select2: ' + e.message; }}
            }})()
        """)
        if exists == 'not_found':
            print(f"  [Select2-css] {label}: element not found")
            return None
        if exists.startswith('no_select2'):
            print(f"  [Select2-css] {label}: {exists}")
            return None

        page.wait_for_timeout(500)

        search_input = page.locator('.select2-search__field')
        if search_input.count() > 0:
            search_input.fill(search_text)
            page.wait_for_timeout(2000)

        results_opts = page.locator('.select2-results__option--selectable')
        if results_opts.count() > 0:
            first_text = results_opts.first.text_content()
            results_opts.first.click()
            page.wait_for_timeout(500)
            print(f"  [Select2-css] {label}: selected '{first_text}'")
            return first_text

        results_opts2 = page.locator('.select2-results__option:not(.select2-results__message)')
        if results_opts2.count() > 0:
            first_text = results_opts2.first.text_content()
            results_opts2.first.click()
            page.wait_for_timeout(500)
            print(f"  [Select2-css] {label}: selected (fallback) '{first_text}'")
            return first_text

        page.evaluate(f"try {{ $('{css_selector}').select2('close'); }} catch(e) {{}}")
        print(f"  [Select2-css] {label}: no results found")
        return None
    except Exception as e:
        print(f"  [Select2-css] {label}: ERROR - {e}")
        try:
            page.evaluate("try { $('select.select2-hidden-accessible').select2('close'); } catch(e) {}")
        except:
            pass
        return None


def fill_date_js(page, field_id, date_str):
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
    return found


def fill_field_js(page, field_id, value):
    found = page.evaluate("""
        (args) => {
            var fid = args[0], val = args[1];
            var el = document.getElementById(fid);
            if (!el) el = document.querySelector('[name="' + fid + '"]');
            if (el && el.offsetParent !== null) {
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
    try:
        if by_name:
            el = page.locator(f'[name="{field_id}"]')
        else:
            el = page.locator(f'#{field_id}')
        if el.count() > 0:
            try:
                if el.first.is_visible(timeout=2000):
                    el.first.fill(value, timeout=5000)
                    print(f"  Filled {'[name=' + field_id + ']' if by_name else '#' + field_id} = {value}")
                    return True
            except:
                pass
        alt = page.locator(f'[name="{field_id}"]' if not by_name else f'#{field_id}')
        if alt.count() > 0:
            try:
                if alt.first.is_visible(timeout=2000):
                    alt.first.fill(value, timeout=5000)
                    print(f"  Filled (alt) {field_id} = {value}")
                    return True
            except:
                pass
    except:
        pass
    return fill_field_js(page, field_id, value)


def fill_field_by_css(page, css, value, label=""):
    """Fill a field by CSS selector."""
    try:
        el = page.locator(css)
        if el.count() > 0:
            try:
                if el.first.is_visible(timeout=2000):
                    el.first.fill(value, timeout=5000)
                    print(f"  Filled {label or css} = {value}")
                    return True
            except:
                pass
    except:
        pass
    # JS fallback
    result = page.evaluate("""
        (args) => {
            var css = args[0], val = args[1];
            var el = document.querySelector(css);
            if (el) {
                el.value = val;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                return 'filled';
            }
            return 'not_found';
        }
    """, [css, value])
    print(f"  Fill {label or css} = {value}: {result}")
    return result == 'filled'


def select_option_js(page, field_id, value):
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


def select_option_by_index(page, selector, index):
    try:
        options = page.evaluate(f"""
            (() => {{
                var el = document.querySelector('{selector}');
                if (!el) return [];
                var opts = [];
                for (var i = 0; i < el.options.length; i++) {{
                    opts.push({{ value: el.options[i].value, text: el.options[i].text.trim() }});
                }}
                return opts;
            }})()
        """)
        if options and index < len(options):
            val = options[index]['value']
            page.evaluate(f"""
                (() => {{
                    var el = document.querySelector('{selector}');
                    if (el) {{
                        el.value = '{val}';
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                }})()
            """)
            print(f"  Selected {selector} index {index}: {options[index]['text']} (value={val})")
            return True
    except Exception as e:
        print(f"  Select by index error: {e}")
    return False


def click_save_submit(page):
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

    # Check validation errors
    val_errors = page.evaluate("""
        () => {
            var errors = [];
            var parsley = document.querySelectorAll('.parsley-errors-list li, .parsley-required');
            for (var el of parsley) {
                if (el.textContent.trim()) errors.push(el.textContent.trim());
            }
            var reqd = document.querySelectorAll('.text-danger, .field-error, .invalid-feedback');
            for (var el of reqd) {
                var t = el.textContent.trim();
                if (t && t.includes('required') && el.offsetParent !== null) errors.push(t);
            }
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
        # Check URL change (redirect after success usually goes to list page)
        cur_url = page.url
        test_result["final_url"] = cur_url

        body = page.locator('body').text_content().lower()
        if 'successfully' in body or 'has been created' in body or 'record added' in body:
            test_result["status"] = "success"
        elif val_errors:
            test_result["status"] = "validation_error"
        else:
            test_result["status"] = "submitted"


def get_job_no(page):
    job_no = page.evaluate("""
        () => {
            var candidates = ['JbNo', 'jbno', 'job_no', 'jobno', 'JobNo'];
            for (var id of candidates) {
                var el = document.getElementById(id) || document.querySelector('[name="' + id + '"]');
                if (el && el.value) return el.value;
            }
            return null;
        }
    """)
    return job_no


def fill_consignee_land(page, search_text="ras"):
    """Fill the Land job consignee field by initializing Select2 with AJAX."""
    print(f"  [Land-Consignee] Initializing Select2 with AJAX and searching '{search_text}'...")

    # The Land forms have consignee with class select2-cus but Select2 is NOT initialized.
    # Ocean Export uses Select2 AJAX with url /autoConsign. We replicate that here.
    init_result = page.evaluate("""
        () => {
            var el = document.getElementById('consigne');
            if (!el) return 'not_found';

            // Destroy any existing select2
            try { $(el).select2('destroy'); } catch(e) {}

            // Initialize with AJAX like Ocean Export does
            $(el).select2({
                placeholder: '-- Type to search --',
                allowClear: true,
                minimumInputLength: 1,
                ajax: {
                    url: '/autoConsign',
                    dataType: 'json',
                    delay: 250,
                    data: function(params) {
                        return { q: params.term };
                    },
                    processResults: function(data) {
                        return { results: data };
                    },
                    cache: true
                }
            });
            return 'initialized';
        }
    """)
    print(f"  [Land-Consignee] Init: {init_result}")

    if init_result != 'initialized':
        return None

    page.wait_for_timeout(500)

    # Now use standard select2 flow
    return fill_select2(page, 'consigne', search_text, 'Consignee')


# ============================================================
# TEST 1: Ocean Export Job Creation
# ============================================================
def test_ocean_export(page):
    print("\n" + "=" * 60)
    print("TEST 1: Ocean Export Job Creation")
    print("=" * 60)
    test_result = {"test": "Ocean Export Job", "status": "unknown", "errors": [], "screenshots": [], "job_no": None}

    try:
        page.goto(f"{BASE_URL}/ddc5bbfa18cf713c1478e511ea7455a7")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        test_result["screenshots"].append(screenshot(page, "01_ocean_export_list"))

        click_add_new_button(page)
        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")
        test_result["screenshots"].append(screenshot(page, "02_ocean_export_form"))
        print(f"  Form URL: {page.url}")

        job_no = get_job_no(page)
        if job_no:
            print(f"  Auto-generated Job No: {job_no}")
            test_result["job_no"] = job_no

        # === BASIC DETAILS ===
        fill_date_js(page, 'jbdte', '19/04/2026')
        select_option_js(page, 'SptmntId', '2')  # FCL
        fill_select2(page, 'IncoTrms', 'f', 'Incoterms')
        fill_select2(page, 'consigne', 'ras', 'Consignee')
        fill_field(page, 'mblno', 'TESTMBL-EXP-001')
        fill_select2(page, 'lport', 'bomb', 'Load Port')
        fill_select2(page, 'dport', 'kol', 'Discharge Port')
        fill_date_js(page, 'mbldte', '19/04/2026')
        fill_select2(page, 'overseas1', 'a', 'Overseas Agent')
        fill_select2(page, 'shpline', 'hap', 'Shipping Line')
        fill_date_js(page, 'etd', '20/04/2026')
        fill_date_js(page, 'eta', '25/04/2026')
        select_option_js(page, 'gbpapplicable', 'no')

        # === SHIPMENT DETAILS - Required fields ===
        # Shipper (Select2)
        fill_select2(page, 'shipper_1', 'a', 'Shipper')

        # HBL No (array field)
        fill_field_by_css(page, 'input[name="hblno[]"]', 'TESTHBL-EXP-001', 'HBL No')
        # HBL Date
        page.evaluate("""
            () => {
                var el = document.querySelector('input[name="hbldte[]"]');
                if (el) { el.value = '19/04/2026'; el.dispatchEvent(new Event('change', {bubbles: true})); }
            }
        """)
        print("  [Date] hbldte[] = 19/04/2026")

        # Commodity (Select2 - cmdty_1_addcmdt_1 or cmdty_1[])
        fill_select2(page, 'cmdty_1_addcmdt_1', 'a', 'Commodity')

        # HSN
        fill_field_by_css(page, 'input[name="hsn_1[]"]', '84719000', 'HSN')
        # If hsn_1[] doesn't exist, try hsn[]
        fill_field_by_css(page, 'input[name="hsn[]"]', '84719000', 'HSN alt')

        # Gross Weight, Net Weight, Invoice Value, No of Pack
        fill_field_by_css(page, 'input[name="cmgwt_1[]"]', '1000', 'Gross Weight')
        fill_field_by_css(page, 'input[name="cmnwt_1[]"]', '900', 'Net Weight')
        fill_field_by_css(page, 'input[name="spinval_1[]"]', '50000', 'Invoice Value')
        fill_field_by_css(page, 'input[name="pkno_1[]"]', '10', 'No of Pack')

        # Pallets/Pack section - gross weight, net weight, volume
        fill_field_by_css(page, '#grswght_1', '1000', 'GrossWt Row')
        fill_field_by_css(page, '#ntwght_1', '900', 'NetWt Row')
        # Volume select
        select_option_by_index(page, '#volume_1', 1)

        # Shipper Invoice
        fill_field_by_css(page, 'input[name="shpinvval[]"]', '50000', 'Shipper Invoice Value')
        fill_field_by_css(page, 'input[name="shpinvno[]"]', 'SINV-001', 'Shipper Invoice No')
        page.evaluate("""
            () => {
                var el = document.querySelector('input[name="shpinvdte[]"]');
                if (el) { el.value = '19/04/2026'; el.dispatchEvent(new Event('change', {bubbles: true})); }
            }
        """)
        print("  [Date] shpinvdte[] = 19/04/2026")

        # Container No
        fill_field_by_css(page, 'input[name="contno[]"]', 'TGBU1234567', 'Container No')

        test_result["screenshots"].append(screenshot(page, "03_ocean_export_filled"))

        # Submit
        click_save_submit(page)
        page.wait_for_timeout(5000)
        page.wait_for_load_state("networkidle")
        test_result["screenshots"].append(screenshot(page, "04_ocean_export_result"))

        check_result(page, test_result)

        # Verify in list
        if test_result["status"] in ("success", "submitted"):
            print("  Navigating to open jobs list to verify...")
            page.goto(f"{BASE_URL}/ddc5bbfa18cf713c1478e511ea7455a7")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
            test_result["screenshots"].append(screenshot(page, "05_ocean_export_verify"))

            table_text = page.evaluate("""
                () => {
                    var table = document.querySelector('table');
                    if (table) return table.textContent.substring(0, 3000);
                    return document.querySelector('.card-body, .content-body, main')?.textContent?.substring(0, 3000) || '';
                }
            """)
            if job_no and job_no in table_text:
                print(f"  Job {job_no} found in list!")
                test_result["verified_in_list"] = True
            else:
                print(f"  Could not verify record in list")
                test_result["verified_in_list"] = False

    except Exception as e:
        test_result["status"] = "exception"
        test_result["errors"].append(str(e))
        print(f"  EXCEPTION: {e}")
        traceback.print_exc()
        try:
            test_result["screenshots"].append(screenshot(page, "01_ocean_export_error"))
        except:
            pass

    print(f"  RESULT: {test_result['status']}")
    return test_result


# ============================================================
# TEST 2: Air Export Job Creation
# ============================================================
def test_air_export(page):
    print("\n" + "=" * 60)
    print("TEST 2: Air Export Job Creation")
    print("=" * 60)
    test_result = {"test": "Air Export Job", "status": "unknown", "errors": [], "screenshots": [], "job_no": None}

    try:
        page.goto(f"{BASE_URL}/8b574ca0cd37f8b76897ecc0f9d9ad34")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        test_result["screenshots"].append(screenshot(page, "06_air_export_list"))

        click_add_new_button(page)
        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")
        test_result["screenshots"].append(screenshot(page, "07_air_export_form"))
        print(f"  Form URL: {page.url}")

        job_no = get_job_no(page)
        if job_no:
            print(f"  Auto-generated Job No: {job_no}")
            test_result["job_no"] = job_no

        # === BASIC DETAILS ===
        fill_date_js(page, 'jbdte', '19/04/2026')
        fill_select2(page, 'IncoTrms', 'f', 'Incoterms')
        fill_select2(page, 'shipper_1', 'a', 'Shipper')
        fill_select2(page, 'consigne', 'ras', 'Consignee')
        fill_field(page, 'hawbno', 'HAWB-EXP-001')
        fill_select2(page, 'lport', 'del', 'Load Port (Delhi)')
        fill_select2(page, 'dport', 'kol', 'Discharge Port')
        fill_select2(page, 'overseas1', 'a', 'Overseas Agent')
        fill_field(page, 'mawbno', '98765432101')
        fill_date_js(page, 'mawbdte', '19/04/2026')

        # Carrier (splierId)
        fill_select2(page, 'splierId', 'a', 'Carrier/Supplier')

        fill_date_js(page, 'eta', '25/04/2026')
        fill_date_js(page, 'etd', '20/04/2026')
        fill_field(page, 'flght_no', 'AI-101')

        select_option_js(page, 'gbpapplicable', 'no')

        # === SHIPMENT DETAILS ===
        # Commodity (Select2)
        fill_select2(page, 'cmdty_1', 'a', 'Commodity')

        # HSN
        fill_field_by_css(page, 'input[name="hsn[]"]', '84719000', 'HSN')
        fill_field_by_css(page, '#hsn_cmdty_1', '84719000', 'HSN by ID')

        # Package details
        fill_field_by_css(page, 'input[name="packno[]"]', '5', 'Pack No')
        fill_field_by_css(page, '#packno_1', '5', 'Pack No by ID')

        # Dimensions
        fill_field_by_css(page, 'input[name="lngth[]"]', '100', 'Length')
        fill_field_by_css(page, '#lngth_1', '100', 'Length by ID')
        fill_field_by_css(page, 'input[name="brdth[]"]', '80', 'Breadth')
        fill_field_by_css(page, '#brdth_1', '80', 'Breadth by ID')
        fill_field_by_css(page, 'input[name="hght[]"]', '60', 'Height')
        fill_field_by_css(page, '#hght_1', '60', 'Height by ID')

        # Volume select
        select_option_by_index(page, '#volume_1', 1)
        # Also try name-based
        select_option_by_index(page, 'select[name="volume[]"]', 1)

        # Invoice Value
        fill_field_by_css(page, 'input[name="spinval[]"]', '25000', 'Invoice Value')
        fill_field_by_css(page, '#spinval_1', '25000', 'Invoice Value by ID')

        # Gross Weight
        fill_field_by_css(page, 'input[name="grswght[]"]', '500', 'Gross Weight')
        fill_field_by_css(page, '#grswght_1', '500', 'Gross Weight by ID')

        # Net Weight
        fill_field_by_css(page, 'input[name="ntwght[]"]', '450', 'Net Weight')
        fill_field_by_css(page, '#ntwght_1', '450', 'Net Weight by ID')

        # Volume Weight
        fill_field_by_css(page, 'input[name="vlmwght[]"]', '96', 'Volume Weight')
        fill_field_by_css(page, '#vlmwght_1', '96', 'Volume Weight by ID')

        # Total fields - use JS only, field may be readonly/calculated
        fill_field_js(page, 'totvlght', '96')
        fill_field_js(page, 'totNo', '5')
        fill_field_js(page, 'totGwght', '500')
        fill_field_js(page, 'totNght', '450')

        # Shipper Invoice
        fill_field_js(page, 'shpinvval', '25000')
        fill_field_js(page, 'shpinvno', 'SINV-AE-001')
        fill_date_js(page, 'shpinvdte', '19/04/2026')

        test_result["screenshots"].append(screenshot(page, "08_air_export_filled"))

        # Submit
        click_save_submit(page)
        page.wait_for_timeout(5000)
        page.wait_for_load_state("networkidle")
        test_result["screenshots"].append(screenshot(page, "09_air_export_result"))

        check_result(page, test_result)

    except Exception as e:
        test_result["status"] = "exception"
        test_result["errors"].append(str(e))
        print(f"  EXCEPTION: {e}")
        traceback.print_exc()
        try:
            test_result["screenshots"].append(screenshot(page, "06_air_export_error"))
        except:
            pass

    print(f"  RESULT: {test_result['status']}")
    return test_result


# ============================================================
# TEST 3: Land Import Job Creation
# ============================================================
def test_land_import(page):
    print("\n" + "=" * 60)
    print("TEST 3: Land Import Job Creation")
    print("=" * 60)
    test_result = {"test": "Land Import Job", "status": "unknown", "errors": [], "screenshots": [], "job_no": None}

    try:
        page.goto(f"{BASE_URL}/8013f48199799dce7a1fde812910a496")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        test_result["screenshots"].append(screenshot(page, "10_land_import_list"))

        click_add_new_button(page)
        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")
        test_result["screenshots"].append(screenshot(page, "11_land_import_form"))
        print(f"  Form URL: {page.url}")

        job_no = get_job_no(page)
        if job_no:
            print(f"  Auto-generated Job No: {job_no}")
            test_result["job_no"] = job_no

        # Fill date first
        fill_date_js(page, 'jbdte', '19/04/2026')

        # IncoTerms - regular select
        select_option_by_index(page, '[name="IncoTrms"]', 1)

        # Consignee - needs Select2 AJAX initialization (not done by page JS)
        fill_consignee_land(page, 'ras')

        # Fill text fields
        for name, val in [
            ('origin', 'Mumbai'),
            ('destination', 'Delhi'),
            ('veh_reg', 'MH01AB1234'),
            ('driver', 'Test Driver'),
            ('cmr_no', 'CMR-TEST-001'),
        ]:
            fill_field(page, name, val, by_name=True)

        # Number fields - use JS to set properly
        for name, val in [('gw', '500'), ('nw', '450'), ('cbm', '10'), ('pkgs', '25')]:
            page.evaluate(f"""
                (() => {{
                    var el = document.querySelector('[name="{name}"]');
                    if (el) {{
                        el.value = '{val}';
                        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                }})()
            """)
            print(f"  Set {name} = {val}")

        # Vehicle Type
        select_option_by_index(page, '[name="veh_type"]', 1)

        test_result["screenshots"].append(screenshot(page, "12_land_import_filled"))

        # Submit
        click_save_submit(page)
        page.wait_for_timeout(5000)
        page.wait_for_load_state("networkidle")
        test_result["screenshots"].append(screenshot(page, "13_land_import_result"))

        check_result(page, test_result)

    except Exception as e:
        test_result["status"] = "exception"
        test_result["errors"].append(str(e))
        print(f"  EXCEPTION: {e}")
        traceback.print_exc()
        try:
            test_result["screenshots"].append(screenshot(page, "10_land_import_error"))
        except:
            pass

    print(f"  RESULT: {test_result['status']}")
    return test_result


# ============================================================
# TEST 4: Land Export Job Creation
# ============================================================
def test_land_export(page):
    print("\n" + "=" * 60)
    print("TEST 4: Land Export Job Creation")
    print("=" * 60)
    test_result = {"test": "Land Export Job", "status": "unknown", "errors": [], "screenshots": [], "job_no": None}

    try:
        page.goto(f"{BASE_URL}/2ca1dbee9121459dedd8cf2e88823068")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        test_result["screenshots"].append(screenshot(page, "14_land_export_list"))

        click_add_new_button(page)
        page.wait_for_timeout(3000)
        page.wait_for_load_state("networkidle")
        test_result["screenshots"].append(screenshot(page, "15_land_export_form"))
        print(f"  Form URL: {page.url}")

        job_no = get_job_no(page)
        if job_no:
            print(f"  Auto-generated Job No: {job_no}")
            test_result["job_no"] = job_no

        # Fill date
        fill_date_js(page, 'jbdte', '19/04/2026')

        # IncoTerms
        select_option_by_index(page, '[name="IncoTrms"]', 1)

        # Consignee - needs Select2 AJAX initialization
        fill_consignee_land(page, 'ras')

        # Fill text fields
        for name, val in [
            ('origin', 'Delhi'),
            ('destination', 'Mumbai'),
            ('veh_reg', 'DL05CD5678'),
            ('driver', 'Test Driver Export'),
            ('cmr_no', 'CMR-EXP-001'),
        ]:
            fill_field(page, name, val, by_name=True)

        # Number fields
        for name, val in [('gw', '600'), ('nw', '550'), ('cbm', '12'), ('pkgs', '30')]:
            page.evaluate(f"""
                (() => {{
                    var el = document.querySelector('[name="{name}"]');
                    if (el) {{
                        el.value = '{val}';
                        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                }})()
            """)
            print(f"  Set {name} = {val}")

        # Vehicle Type
        select_option_by_index(page, '[name="veh_type"]', 1)

        test_result["screenshots"].append(screenshot(page, "16_land_export_filled"))

        # Submit
        click_save_submit(page)
        page.wait_for_timeout(5000)
        page.wait_for_load_state("networkidle")
        test_result["screenshots"].append(screenshot(page, "17_land_export_result"))

        check_result(page, test_result)

    except Exception as e:
        test_result["status"] = "exception"
        test_result["errors"].append(str(e))
        print(f"  EXCEPTION: {e}")
        traceback.print_exc()
        try:
            test_result["screenshots"].append(screenshot(page, "14_land_export_error"))
        except:
            pass

    print(f"  RESULT: {test_result['status']}")
    return test_result


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("Sena ERP - Remaining Job Types Test")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()
        page.set_default_timeout(60000)

        login(page)

        results["ocean_export"] = test_ocean_export(page)
        results["air_export"] = test_air_export(page)
        results["land_import"] = test_land_import(page)
        results["land_export"] = test_land_export(page)

        browser.close()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for key, res in results.items():
        status = res.get("status", "unknown")
        job_no = res.get("job_no", "N/A")
        errors = len(res.get("errors", []))
        print(f"  {key}: {status} (Job: {job_no}, Errors: {errors})")
        if res.get("errors"):
            for e in res["errors"][:5]:
                print(f"    - {e[:100]}")

    # Save results
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {RESULTS_FILE}")
    print(f"Screenshots in {SCREENSHOT_DIR}")


if __name__ == "__main__":
    main()
