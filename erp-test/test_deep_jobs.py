"""
Deep test of job creation workflows on Sena ERP system.
Tests Select2/AJAX dropdowns, form filling, and submission across all job types.
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

BASE_URL = "http://13.210.47.18:8088"
SCREENSHOT_DIR = "/var/lib/freelancer/projects/40298427/erp-test/screenshots/deep_jobs"
RESULTS_FILE = "/var/lib/freelancer/projects/40298427/erp-test/results_deep_jobs.json"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

results = {}


def ss_path(name):
    return os.path.join(SCREENSHOT_DIR, f"{name}.png")


async def login(page):
    print("[LOGIN] Navigating to login page...")
    await page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
    await page.screenshot(path=ss_path("00_login_page"))

    await page.evaluate('''() => {
        document.getElementById("username").value = "superadmin";
        document.getElementById("password").value = "Nick@#24";
        document.getElementById("signupForm").submit();
    }''')
    print("[LOGIN] Credentials submitted, waiting 8 seconds...")
    await asyncio.sleep(8)
    await page.screenshot(path=ss_path("01_after_login"))
    print(f"[LOGIN] Current URL: {page.url}")


async def discover_form_controls(page, prefix):
    """Discover all form elements including Select2/AJAX dropdowns."""
    print(f"\n[{prefix}] === Discovering form controls ===")

    info = await page.evaluate('''() => {
        const result = {
            selects: [],
            select2_containers: [],
            inputs: [],
            textareas: [],
            select2_present: false,
            chosen_present: false,
        };

        // Check for Select2
        const s2containers = document.querySelectorAll('.select2-container, .select2, [data-toggle="select2"]');
        result.select2_present = s2containers.length > 0;
        result.select2_container_count = s2containers.length;

        // Check for Chosen
        const chosen = document.querySelectorAll('.chosen-container, .chosen-select');
        result.chosen_present = chosen.length > 0;

        // All select elements
        document.querySelectorAll('select').forEach(sel => {
            const parent = sel.parentElement;
            const hasSelect2 = parent ? parent.querySelector('.select2-container') !== null : false;
            const options = Array.from(sel.options).map(o => ({value: o.value, text: o.text.trim().substring(0, 50)}));
            result.selects.push({
                id: sel.id,
                name: sel.name,
                className: sel.className,
                optionCount: sel.options.length,
                firstOptions: options.slice(0, 5),
                hasSelect2Wrapper: hasSelect2,
                isHidden: sel.offsetParent === null || sel.style.display === 'none',
                dataAttrs: Object.keys(sel.dataset),
                visible: sel.offsetWidth > 0 || sel.offsetHeight > 0
            });
        });

        // Select2 containers
        document.querySelectorAll('.select2-container').forEach(c => {
            const selectId = c.getAttribute('data-select2-id') || '';
            const prevSibling = c.previousElementSibling;
            result.select2_containers.push({
                id: c.id,
                selectId: selectId,
                linkedSelectId: prevSibling ? prevSibling.id : '',
                linkedSelectName: prevSibling ? prevSibling.name : '',
                text: c.textContent.trim().substring(0, 50),
                classes: c.className
            });
        });

        // Input fields
        document.querySelectorAll('input:not([type="hidden"])').forEach(inp => {
            if (inp.type === 'submit' || inp.type === 'button') return;
            result.inputs.push({
                id: inp.id,
                name: inp.name,
                type: inp.type,
                value: inp.value,
                placeholder: inp.placeholder,
                className: inp.className.substring(0, 80),
                readonly: inp.readOnly,
                required: inp.required
            });
        });

        // Textareas
        document.querySelectorAll('textarea').forEach(ta => {
            result.textareas.push({
                id: ta.id,
                name: ta.name,
                value: ta.value
            });
        });

        return result;
    }''')

    print(f"  Select2 present: {info['select2_present']} ({info.get('select2_container_count', 0)} containers)")
    print(f"  Chosen present: {info['chosen_present']}")
    print(f"  Total selects: {len(info['selects'])}")
    print(f"  Total inputs: {len(info['inputs'])}")
    print(f"  Total textareas: {len(info['textareas'])}")

    print(f"\n  --- SELECT elements ---")
    for s in info['selects']:
        s2_mark = " [SELECT2]" if s['hasSelect2Wrapper'] else ""
        hidden_mark = " [HIDDEN]" if s['isHidden'] else ""
        print(f"    #{s['id']} name={s['name']} options={s['optionCount']}{s2_mark}{hidden_mark}")
        if s['optionCount'] <= 5:
            for opt in s['firstOptions']:
                print(f"      -> {opt['value']}: {opt['text']}")

    print(f"\n  --- SELECT2 containers ---")
    for c in info['select2_containers']:
        print(f"    linked=#{c['linkedSelectId']} name={c['linkedSelectName']} text='{c['text']}'")

    print(f"\n  --- INPUT fields ---")
    for inp in info['inputs']:
        print(f"    #{inp['id']} name={inp['name']} type={inp['type']} value='{inp['value']}' placeholder='{inp['placeholder']}'")

    print(f"\n  --- TEXTAREA fields ---")
    for ta in info['textareas']:
        print(f"    #{ta['id']} name={ta['name']}")

    return info


async def fill_select2(page, select_id, search_text, prefix, step_name):
    """Try to interact with a Select2 dropdown."""
    print(f"  [{prefix}] Filling Select2 for #{select_id} with search='{search_text}'...")
    try:
        # Find the Select2 container associated with this select
        container = await page.evaluate(f'''() => {{
            const sel = document.getElementById("{select_id}");
            if (!sel) return null;
            const container = sel.nextElementSibling;
            if (container && container.classList.contains('select2-container')) {{
                return {{
                    id: container.id,
                    classes: container.className
                }};
            }}
            // Try parent
            const parent = sel.closest('.form-group, .col-md-6, .col-md-4, .col-md-3, div');
            if (parent) {{
                const c = parent.querySelector('.select2-container');
                if (c) return {{ id: c.id, classes: c.className }};
            }}
            return null;
        }}''')

        if not container:
            print(f"    No Select2 container found for #{select_id}")
            return False

        # Click to open the Select2 dropdown
        # Use the selection renderer to click
        await page.evaluate(f'''() => {{
            const sel = document.getElementById("{select_id}");
            const container = sel.nextElementSibling || sel.closest('div').querySelector('.select2-container');
            if (container) {{
                const selection = container.querySelector('.select2-selection');
                if (selection) selection.click();
            }}
        }}''')
        await asyncio.sleep(0.5)

        # Alternative: use jQuery/Select2 API to open
        await page.evaluate(f'''() => {{
            if (typeof $ !== 'undefined') {{
                try {{ $("#{select_id}").select2("open"); }} catch(e) {{}}
            }}
        }}''')
        await asyncio.sleep(0.5)

        # Check if dropdown is open
        is_open = await page.evaluate('''() => {
            const dropdown = document.querySelector('.select2-dropdown, .select2-container--open');
            return dropdown !== null;
        }''')

        if not is_open:
            print(f"    Could not open Select2 for #{select_id}")
            await page.screenshot(path=ss_path(f"{prefix}_{step_name}_failed_open"))
            return False

        # Type in the search field
        search_field = page.locator('.select2-search__field')
        if await search_field.count() > 0:
            await search_field.first.fill(search_text)
            await asyncio.sleep(1.5)  # Wait for AJAX results

        await page.screenshot(path=ss_path(f"{prefix}_{step_name}_dropdown_open"))

        # Check for results
        options = await page.evaluate('''() => {
            const opts = document.querySelectorAll('.select2-results__option');
            return Array.from(opts).map(o => ({
                text: o.textContent.trim().substring(0, 80),
                disabled: o.classList.contains('select2-results__option--disabled') ||
                          o.getAttribute('aria-disabled') === 'true'
            }));
        }''')

        print(f"    Found {len(options)} options:")
        for o in options[:5]:
            print(f"      - {o['text']} {'[disabled]' if o['disabled'] else ''}")

        # Click first non-disabled option
        clicked = await page.evaluate('''() => {
            const opts = document.querySelectorAll('.select2-results__option');
            for (const o of opts) {
                if (!o.classList.contains('select2-results__option--disabled') &&
                    o.getAttribute('aria-disabled') !== 'true' &&
                    o.textContent.trim() !== '' &&
                    o.textContent.trim() !== 'Searching…' &&
                    o.textContent.trim() !== 'No results found') {
                    o.click();
                    return o.textContent.trim();
                }
            }
            return null;
        }''')

        if clicked:
            print(f"    Selected: '{clicked}'")
            await asyncio.sleep(0.5)
            return True
        else:
            print(f"    No selectable option found")
            # Close the dropdown
            await page.evaluate('''() => {
                if (typeof $ !== 'undefined') {
                    try { $(".select2").select2("close"); } catch(e) {}
                }
            }''')
            return False

    except Exception as e:
        print(f"    Error with Select2 for #{select_id}: {e}")
        return False


async def fill_regular_select(page, select_id, value_or_index):
    """Fill a regular select element."""
    try:
        result = await page.evaluate(f'''() => {{
            const sel = document.getElementById("{select_id}");
            if (!sel) return "not_found";
            if (sel.options.length <= 1) return "no_options";
            // Try by value first
            for (let i = 0; i < sel.options.length; i++) {{
                if (sel.options[i].value === "{value_or_index}") {{
                    sel.selectedIndex = i;
                    sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return "selected_" + sel.options[i].text;
                }}
            }}
            // Select second option (first is usually placeholder)
            if (sel.options.length > 1) {{
                sel.selectedIndex = 1;
                sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return "selected_index1_" + sel.options[1].text;
            }}
            return "failed";
        }}''')
        print(f"    Regular select #{select_id}: {result}")
        return "selected" in result
    except Exception as e:
        print(f"    Error filling select #{select_id}: {e}")
        return False


async def fill_input(page, input_id, value):
    """Fill an input field by ID."""
    try:
        result = await page.evaluate(f'''() => {{
            const inp = document.getElementById("{input_id}");
            if (!inp) return "not_found";
            inp.value = "{value}";
            inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
            inp.dispatchEvent(new Event('change', {{ bubbles: true }}));
            return "filled";
        }}''')
        print(f"    Input #{input_id}: {result}")
        return result == "filled"
    except Exception as e:
        print(f"    Error filling #{input_id}: {e}")
        return False


async def test_job_creation(page, job_type, url_path, prefix, step_offset):
    """Test job creation for a specific job type."""
    result = {
        "job_type": job_type,
        "url": url_path,
        "form_controls": {},
        "fields_filled": [],
        "fields_failed": [],
        "select2_results": {},
        "validation_errors": [],
        "success": False,
        "notes": []
    }

    print(f"\n{'='*60}")
    print(f"[{prefix}] Testing {job_type} Job Creation")
    print(f"{'='*60}")

    # Navigate to open jobs page
    full_url = f"{BASE_URL}/{url_path}"
    print(f"[{prefix}] Navigating to {full_url}")
    await page.goto(full_url, wait_until="networkidle", timeout=30000)
    await asyncio.sleep(2)
    await page.screenshot(path=ss_path(f"{step_offset:02d}_{prefix}_open_jobs"))

    # Look for Add New button
    add_btn = None
    for selector in ['a:has-text("Add New")', 'button:has-text("Add New")',
                      'a:has-text("Add")', '.btn-primary:has-text("Add")',
                      'a.btn-success', 'a.btn-primary', '.btn:has-text("New")']:
        try:
            loc = page.locator(selector)
            if await loc.count() > 0:
                add_btn = loc.first
                print(f"[{prefix}] Found Add button with selector: {selector}")
                break
        except:
            continue

    if not add_btn:
        # Try finding any link/button that opens a form
        links = await page.evaluate('''() => {
            const links = document.querySelectorAll('a.btn, button.btn');
            return Array.from(links).map(l => ({
                text: l.textContent.trim().substring(0, 50),
                href: l.href || '',
                classes: l.className
            }));
        }''')
        print(f"[{prefix}] Available buttons: {json.dumps(links, indent=2)}")
        result["notes"].append("Could not find Add New button")
        result["notes"].append(f"Available buttons: {links}")
        await page.screenshot(path=ss_path(f"{step_offset:02d}_{prefix}_no_add_btn"))
        results[prefix] = result
        return result

    # Click Add New
    print(f"[{prefix}] Clicking Add New button...")
    await add_btn.click()
    await asyncio.sleep(3)
    await page.screenshot(path=ss_path(f"{step_offset+1:02d}_{prefix}_add_form"))
    print(f"[{prefix}] Current URL after click: {page.url}")

    # Discover all form controls
    info = await discover_form_controls(page, prefix)
    result["form_controls"] = {
        "selects": len(info['selects']),
        "inputs": len(info['inputs']),
        "textareas": len(info['textareas']),
        "select2_present": info['select2_present'],
        "select2_count": info.get('select2_container_count', 0),
        "select_details": info['selects'],
        "input_details": info['inputs']
    }

    # Fill Select2 dropdowns
    select2_selects = [s for s in info['selects'] if s['hasSelect2Wrapper'] and s['optionCount'] <= 1]
    regular_selects = [s for s in info['selects'] if not s['hasSelect2Wrapper'] or s['optionCount'] > 1]

    print(f"\n[{prefix}] --- Filling Select2 AJAX dropdowns ({len(select2_selects)}) ---")
    step = 0
    for sel in select2_selects:
        if not sel['id']:
            continue
        search_char = "a"  # Generic search
        success = await fill_select2(page, sel['id'], search_char, prefix, f"s2_{sel['id']}")
        result["select2_results"][sel['id']] = success
        if success:
            result["fields_filled"].append(f"select2:{sel['id']}")
        else:
            # Try with empty search (just open and pick first)
            success2 = await fill_select2(page, sel['id'], "", prefix, f"s2_{sel['id']}_empty")
            result["select2_results"][sel['id']] = success2
            if success2:
                result["fields_filled"].append(f"select2:{sel['id']}")
            else:
                result["fields_failed"].append(f"select2:{sel['id']}")
        step += 1
        if step % 3 == 0:
            await page.screenshot(path=ss_path(f"{step_offset+2:02d}_{prefix}_select2_progress_{step}"))

    await page.screenshot(path=ss_path(f"{step_offset+3:02d}_{prefix}_after_select2"))

    # Fill regular selects
    print(f"\n[{prefix}] --- Filling regular selects ({len(regular_selects)}) ---")
    for sel in regular_selects:
        if not sel['id'] or sel['optionCount'] <= 1:
            continue
        # Special handling for known fields
        value = ""
        if 'sptmnt' in sel['id'].lower() or 'shipment' in sel['id'].lower():
            value = "FCL"
        elif 'gbp' in sel['id'].lower():
            value = "No"

        success = await fill_regular_select(page, sel['id'], value)
        if success:
            result["fields_filled"].append(f"select:{sel['id']}")
        else:
            result["fields_failed"].append(f"select:{sel['id']}")

    # Fill text inputs
    today = datetime.now()
    eta = (today + timedelta(days=14)).strftime("%Y-%m-%d")
    etd = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")

    field_values = {
        "jbdte": today_str,
        "mblno": "TESTMBL001",
        "hblno": "TESTHBL001",
        "etd": etd,
        "eta": eta,
        "freight": "500",
        "insurance": "100",
        "marks": "TEST MARKS",
        "goods": "TEST GOODS DESCRIPTION",
        "noofpkgs": "10",
        "grosswt": "1000",
        "volume": "50",
        "cbm": "25",
        "chgwt": "1200",
        "vessel": "TEST VESSEL",
        "voyage": "V001",
        "mawbno": "TESTMAWB001",
        "hawbno": "TESTHAWB001",
        "flightno": "TF001",
    }

    print(f"\n[{prefix}] --- Filling text inputs ---")
    for inp in info['inputs']:
        inp_id = inp['id']
        inp_name = inp['name']
        if not inp_id:
            continue
        if inp['readonly']:
            continue
        if inp['type'] in ('checkbox', 'radio', 'file'):
            continue

        # Find value to fill
        value = None
        for key, val in field_values.items():
            if key.lower() in inp_id.lower() or key.lower() in inp_name.lower():
                value = val
                break

        if not value:
            # Generic fill based on type
            if inp['type'] == 'date' or 'date' in inp_id.lower() or 'dte' in inp_id.lower():
                value = today_str
            elif inp['type'] == 'number' or 'charge' in inp_id.lower() or 'amount' in inp_id.lower():
                value = "100"
            elif inp['type'] == 'email':
                value = "test@test.com"
            elif 'phone' in inp_id.lower() or 'mobile' in inp_id.lower():
                value = "1234567890"
            elif 'name' in inp_id.lower():
                value = "Test"
            elif 'pass' in inp_id.lower():
                value = "Test@1234"
            elif 'user' in inp_id.lower():
                value = "testuser"

        if value:
            success = await fill_input(page, inp_id, value)
            if success:
                result["fields_filled"].append(f"input:{inp_id}={value}")
            else:
                result["fields_failed"].append(f"input:{inp_id}")

    await page.screenshot(path=ss_path(f"{step_offset+4:02d}_{prefix}_form_filled"), full_page=True)

    # Try to submit
    print(f"\n[{prefix}] --- Attempting to submit ---")
    submitted = False
    for selector in ['button[type="submit"]', 'input[type="submit"]',
                      'button:has-text("Save")', 'button:has-text("Submit")',
                      'a:has-text("Save")', '.btn-success:has-text("Save")',
                      '#btnsave', '#btnsubmit', '.btn-primary[type="submit"]']:
        try:
            loc = page.locator(selector)
            if await loc.count() > 0:
                print(f"  Found submit button: {selector}")
                await loc.first.click()
                submitted = True
                break
        except:
            continue

    if not submitted:
        # Try finding any save/submit button via JS
        btn_text = await page.evaluate('''() => {
            const btns = document.querySelectorAll('button, input[type="submit"], a.btn');
            return Array.from(btns).map(b => ({
                text: b.textContent.trim().substring(0, 50),
                type: b.type,
                id: b.id,
                classes: b.className.substring(0, 50)
            }));
        }''')
        print(f"  All buttons on page: {json.dumps(btn_text, indent=2)}")
        result["notes"].append("Could not find submit button")

    await asyncio.sleep(3)
    await page.screenshot(path=ss_path(f"{step_offset+5:02d}_{prefix}_after_submit"), full_page=True)

    # Check for validation errors
    errors = await page.evaluate('''() => {
        const errors = [];
        // Check for various error display patterns
        document.querySelectorAll('.text-danger, .error, .invalid-feedback, .help-block, .alert-danger, .parsley-errors-list li, .error-message').forEach(el => {
            const text = el.textContent.trim();
            if (text) errors.push(text.substring(0, 100));
        });
        // Check for toastr/notification
        document.querySelectorAll('.toast-error, .toast-message, .swal2-content, .noty_body').forEach(el => {
            const text = el.textContent.trim();
            if (text) errors.push("TOAST: " + text.substring(0, 100));
        });
        return errors;
    }''')

    if errors:
        print(f"\n[{prefix}] Validation errors found:")
        for e in errors:
            print(f"    - {e}")
        result["validation_errors"] = errors

    # Check for success message
    success_msg = await page.evaluate('''() => {
        const msgs = [];
        document.querySelectorAll('.alert-success, .toast-success, .swal2-success').forEach(el => {
            msgs.push(el.textContent.trim().substring(0, 100));
        });
        return msgs;
    }''')

    if success_msg:
        print(f"\n[{prefix}] Success messages: {success_msg}")
        result["success"] = True
        result["notes"].append(f"Success: {success_msg}")

    result["final_url"] = page.url
    results[prefix] = result
    return result


async def test_hr_employee(page):
    """Test HR Employee creation."""
    prefix = "HR"
    result = {
        "section": "HR Employee Creation",
        "fields_filled": [],
        "fields_failed": [],
        "validation_errors": [],
        "success": False,
        "notes": []
    }

    print(f"\n{'='*60}")
    print(f"[HR] Testing HR Employee Creation")
    print(f"{'='*60}")

    url = f"{BASE_URL}/51564f2eb2d3a1bca494e86b1c67635e"
    print(f"[HR] Navigating to {url}")
    await page.goto(url, wait_until="networkidle", timeout=30000)
    await asyncio.sleep(2)
    await page.screenshot(path=ss_path("60_hr_employee_list"))

    # Find Add New button
    add_btn = None
    for selector in ['a:has-text("Add New")', 'button:has-text("Add New")', 'a:has-text("Add")',
                      'a.btn-success', 'a.btn-primary']:
        try:
            loc = page.locator(selector)
            if await loc.count() > 0:
                add_btn = loc.first
                break
        except:
            continue

    if not add_btn:
        print("[HR] No Add button found")
        result["notes"].append("No Add button found")

        # Check what's on the page
        buttons = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a.btn, button.btn')).map(b => ({
                text: b.textContent.trim().substring(0, 50),
                href: b.href || ''
            }));
        }''')
        print(f"[HR] Available buttons: {json.dumps(buttons, indent=2)}")
        results["HR"] = result
        return result

    await add_btn.click()
    await asyncio.sleep(3)
    await page.screenshot(path=ss_path("61_hr_add_form"))

    info = await discover_form_controls(page, "HR")
    result["form_controls"] = {
        "selects": len(info['selects']),
        "inputs": len(info['inputs']),
        "select2_present": info['select2_present']
    }

    # Fill employee fields
    employee_data = {
        "firstname": "John",
        "middlename": "M",
        "lastname": "TestDoe",
        "mobile": "9876543210",
        "email": "john.testdoe@example.com",
        "username": "johntestdoe",
        "password": "Test@12345",
    }

    for inp in info['inputs']:
        if not inp['id']:
            continue
        for key, val in employee_data.items():
            if key.lower() in inp['id'].lower() or key.lower() in inp['name'].lower():
                success = await fill_input(page, inp['id'], val)
                if success:
                    result["fields_filled"].append(f"{inp['id']}={val}")
                else:
                    result["fields_failed"].append(inp['id'])
                break

    # Handle Select2 dropdowns
    for sel in info['selects']:
        if sel['hasSelect2Wrapper'] and sel['optionCount'] <= 1 and sel['id']:
            await fill_select2(page, sel['id'], "a", "HR", f"s2_{sel['id']}")
        elif sel['optionCount'] > 1 and sel['id']:
            await fill_regular_select(page, sel['id'], "")

    await page.screenshot(path=ss_path("62_hr_form_filled"), full_page=True)

    # Submit
    for selector in ['button[type="submit"]', 'input[type="submit"]',
                      'button:has-text("Save")', '#btnsave']:
        try:
            loc = page.locator(selector)
            if await loc.count() > 0:
                await loc.first.click()
                break
        except:
            continue

    await asyncio.sleep(3)
    await page.screenshot(path=ss_path("63_hr_after_submit"), full_page=True)

    errors = await page.evaluate('''() => {
        const errors = [];
        document.querySelectorAll('.text-danger, .error, .invalid-feedback, .alert-danger, .parsley-errors-list li').forEach(el => {
            const text = el.textContent.trim();
            if (text) errors.push(text.substring(0, 100));
        });
        return errors;
    }''')

    if errors:
        result["validation_errors"] = errors
        print(f"[HR] Validation errors: {errors}")

    results["HR"] = result
    return result


async def test_existing_job_view(page):
    """Test viewing/editing an existing job."""
    prefix = "VIEW_JOB"
    result = {
        "section": "View Existing Job",
        "fields": [],
        "tabs": [],
        "notes": []
    }

    print(f"\n{'='*60}")
    print(f"[{prefix}] Testing View/Edit Existing Job")
    print(f"{'='*60}")

    url = f"{BASE_URL}/9dddd5ce1b1375bc497feeb871842d4b"
    print(f"[{prefix}] Navigating to Ocean Import Open Jobs...")
    await page.goto(url, wait_until="networkidle", timeout=30000)
    await asyncio.sleep(2)
    await page.screenshot(path=ss_path("70_existing_jobs_list"))

    # Find table rows or edit buttons
    row_info = await page.evaluate('''() => {
        const table = document.querySelector('table');
        if (!table) return { hasTable: false };
        const rows = table.querySelectorAll('tbody tr');
        const result = {
            hasTable: true,
            rowCount: rows.length,
            firstRowCells: [],
            editButtons: []
        };
        if (rows.length > 0) {
            rows[0].querySelectorAll('td').forEach(td => {
                result.firstRowCells.push(td.textContent.trim().substring(0, 50));
            });
            rows[0].querySelectorAll('a, button').forEach(btn => {
                result.editButtons.push({
                    text: btn.textContent.trim().substring(0, 30),
                    href: btn.href || '',
                    title: btn.title || '',
                    classes: btn.className.substring(0, 50)
                });
            });
        }
        return result;
    }''')

    print(f"[{prefix}] Table: {row_info.get('hasTable')}, Rows: {row_info.get('rowCount', 0)}")
    if row_info.get('firstRowCells'):
        print(f"[{prefix}] First row: {row_info['firstRowCells']}")
    if row_info.get('editButtons'):
        print(f"[{prefix}] Edit buttons: {json.dumps(row_info['editButtons'], indent=2)}")

    result["table_info"] = row_info

    # Try to click edit on first row
    clicked = False
    if row_info.get('editButtons'):
        for btn in row_info['editButtons']:
            if btn['href'] and btn['href'] != '#' and btn['href'] != 'javascript:void(0)':
                print(f"[{prefix}] Clicking edit link: {btn['href']}")
                await page.goto(btn['href'], wait_until="networkidle", timeout=30000)
                clicked = True
                break

    if not clicked:
        # Try clicking first row
        try:
            first_row = page.locator('table tbody tr').first
            # Look for edit icon/link
            edit_link = first_row.locator('a').first
            if await edit_link.count() > 0:
                await edit_link.click()
                clicked = True
        except:
            pass

    if not clicked:
        # Try clicking the row itself
        try:
            await page.locator('table tbody tr').first.click()
            clicked = True
        except:
            pass

    if clicked:
        await asyncio.sleep(3)
        await page.screenshot(path=ss_path("71_existing_job_detail"), full_page=True)

        # Discover form fields
        info = await discover_form_controls(page, prefix)
        result["fields"] = info

        # Look for tabs
        tabs = await page.evaluate('''() => {
            const tabs = [];
            document.querySelectorAll('.nav-tabs .nav-link, .nav-tabs a, .tab-pane, [data-toggle="tab"]').forEach(t => {
                tabs.push({
                    text: t.textContent.trim().substring(0, 50),
                    href: t.getAttribute('href') || '',
                    active: t.classList.contains('active')
                });
            });
            return tabs;
        }''')

        if tabs:
            print(f"\n[{prefix}] Tabs found: {len(tabs)}")
            for t in tabs:
                print(f"    {t['text']} {'[ACTIVE]' if t['active'] else ''}")
            result["tabs"] = tabs

            # Click each tab and screenshot
            for i, tab in enumerate(tabs):
                if tab['href'] and tab['href'] != '#':
                    try:
                        await page.click(f'a[href="{tab["href"]}"]')
                        await asyncio.sleep(1)
                        await page.screenshot(path=ss_path(f"72_existing_job_tab_{i}_{tab['text'][:20].replace(' ','_')}"))
                    except:
                        pass
    else:
        result["notes"].append("Could not click into any existing job")

    results["VIEW_JOB"] = result
    return result


async def test_airport_record(page):
    """Test viewing/editing an airport record."""
    prefix = "AIRPORT"
    result = {
        "section": "Airport Record",
        "notes": []
    }

    print(f"\n{'='*60}")
    print(f"[{prefix}] Testing Airport Record View/Edit")
    print(f"{'='*60}")

    url = f"{BASE_URL}/d1ed858f6d8126a814e31f18a7de5f8e"
    print(f"[{prefix}] Navigating to {url}")
    await page.goto(url, wait_until="networkidle", timeout=30000)
    await asyncio.sleep(2)
    await page.screenshot(path=ss_path("80_airport_list"))

    # Find edit button
    row_info = await page.evaluate('''() => {
        const table = document.querySelector('table');
        if (!table) return { hasTable: false };
        const rows = table.querySelectorAll('tbody tr');
        return {
            hasTable: true,
            rowCount: rows.length,
            firstRowLinks: Array.from(rows.length > 0 ? rows[0].querySelectorAll('a, button') : []).map(a => ({
                text: a.textContent.trim().substring(0, 30),
                href: a.href || '',
                title: a.title || ''
            }))
        };
    }''')

    print(f"[{prefix}] Table rows: {row_info.get('rowCount', 0)}")
    result["table_info"] = row_info

    if row_info.get('firstRowLinks'):
        for link in row_info['firstRowLinks']:
            if link['href'] and link['href'] != '#':
                print(f"[{prefix}] Clicking: {link['text']} -> {link['href']}")
                await page.goto(link['href'], wait_until="networkidle", timeout=30000)
                await asyncio.sleep(2)
                await page.screenshot(path=ss_path("81_airport_edit"), full_page=True)

                info = await discover_form_controls(page, prefix)
                result["form_controls"] = info
                break

    results["AIRPORT"] = result
    return result


async def main():
    print("=" * 60)
    print("SENA ERP DEEP JOB CREATION TEST")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()

        # Login
        await login(page)

        # Job type tests
        job_configs = [
            ("Ocean Import", "9dddd5ce1b1375bc497feeb871842d4b", "OI", 10),
            ("Ocean Export", "ddc5bbfa18cf713c1478e511ea7455a7", "OE", 20),
            ("Air Import", "951733b073f499bd67fa764d38df48a8", "AI", 30),
            ("Air Export", "8b574ca0cd37f8b76897ecc0f9d9ad34", "AE", 40),
            ("Land Import", "8013f48199799dce7a1fde812910a496", "LI", 50),
            ("Land Export", "2ca1dbee9121459dedd8cf2e88823068", "LE", 55),
        ]

        for job_type, url_path, prefix, step_offset in job_configs:
            try:
                await test_job_creation(page, job_type, url_path, prefix, step_offset)
            except Exception as e:
                print(f"\n[{prefix}] ERROR: {e}")
                results[prefix] = {"error": str(e), "job_type": job_type}
                await page.screenshot(path=ss_path(f"{step_offset:02d}_{prefix}_error"))

        # HR Employee
        try:
            await test_hr_employee(page)
        except Exception as e:
            print(f"\n[HR] ERROR: {e}")
            results["HR"] = {"error": str(e)}
            await page.screenshot(path=ss_path("60_hr_error"))

        # View existing job
        try:
            await test_existing_job_view(page)
        except Exception as e:
            print(f"\n[VIEW_JOB] ERROR: {e}")
            results["VIEW_JOB"] = {"error": str(e)}

        # Airport record
        try:
            await test_airport_record(page)
        except Exception as e:
            print(f"\n[AIRPORT] ERROR: {e}")
            results["AIRPORT"] = {"error": str(e)}

        await browser.close()

    # Save results
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n{'='*60}")
    print("TEST COMPLETE")
    print(f"Results saved to: {RESULTS_FILE}")
    print(f"Screenshots saved to: {SCREENSHOT_DIR}")
    print(f"Finished: {datetime.now().isoformat()}")
    print(f"{'='*60}")

    # Summary
    print("\n=== SUMMARY ===")
    for key, val in results.items():
        if "error" in val:
            print(f"  {key}: ERROR - {val['error']}")
        else:
            filled = len(val.get('fields_filled', []))
            failed = len(val.get('fields_failed', []))
            errors = len(val.get('validation_errors', []))
            success = val.get('success', False)
            print(f"  {key}: filled={filled} failed={failed} validation_errors={errors} success={success}")


if __name__ == "__main__":
    asyncio.run(main())
