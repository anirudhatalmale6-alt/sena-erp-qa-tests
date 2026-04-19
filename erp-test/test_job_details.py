#!/usr/bin/env python3
"""
Sena ERP - Comprehensive Job Details Tab Testing
Tests all step-wizard tabs within Ocean Import and Air Import jobs,
plus Quote creation, Rate Database, and Client Rates.
"""

import json
import os
import sys
import time
import traceback
from datetime import datetime
from playwright.sync_api import sync_playwright

BASE_URL = "http://13.210.47.18:8088"
SCREENSHOT_DIR = "/var/lib/freelancer/projects/40298427/erp-test/screenshots/job_details"
RESULTS_FILE = "/var/lib/freelancer/projects/40298427/erp-test/results_job_details.json"

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

results = {
    "test_run": datetime.now().isoformat(),
    "tests": [],
    "summary": {"passed": 0, "failed": 0, "warnings": 0}
}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def screenshot(page, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=True)
    log(f"  Screenshot: {name}.png")
    return path

def add_result(name, status, details=None, fields=None):
    entry = {"test": name, "status": status}
    if details:
        entry["details"] = details
    if fields:
        entry["fields"] = fields
    results["tests"].append(entry)
    if status == "PASS":
        results["summary"]["passed"] += 1
    elif status == "FAIL":
        results["summary"]["failed"] += 1
    else:
        results["summary"]["warnings"] += 1
    log(f"  [{status}] {name}: {details or ''}")

def discover_fields_in_container(page, container_selector=None):
    """Discover all form fields in a container or the main content area."""
    js = """(containerSel) => {
        let container;
        if (containerSel) {
            container = document.querySelector(containerSel);
        }
        if (!container) {
            // Try step content / active tab / main content
            container = document.querySelector('.tab-pane.active, .tab-pane.show.active, .step-content .active, .wizard-content .active');
        }
        if (!container) {
            container = document.querySelector('.content-wrapper, .main-content, #content, .container-fluid');
        }
        if (!container) container = document.body;
        return Array.from(container.querySelectorAll('input:not([type="hidden"]), select, textarea')).map(el => ({
            tag: el.tagName,
            type: el.type || '',
            name: el.name || '',
            id: el.id || '',
            value: el.value || '',
            placeholder: el.placeholder || '',
            readonly: el.readOnly || false,
            disabled: el.disabled || false,
            visible: el.offsetParent !== null,
            label: el.id ? (document.querySelector('label[for="' + el.id + '"]') || {}).textContent || '' : '',
            closest_label: el.closest('.form-group, .mb-3, .row')?.querySelector('label')?.textContent?.trim() || ''
        }));
    }"""
    return page.evaluate(js, container_selector)

def discover_all_visible_fields(page):
    """Discover ALL visible form fields on the page."""
    return page.evaluate("""() => {
        return Array.from(document.querySelectorAll('input:not([type="hidden"]), select, textarea')).filter(el => el.offsetParent !== null).map(el => ({
            tag: el.tagName,
            type: el.type || '',
            name: el.name || '',
            id: el.id || '',
            value: el.value || '',
            placeholder: el.placeholder || '',
            readonly: el.readOnly || false,
            disabled: el.disabled || false,
            visible: true,
            label: el.id ? (document.querySelector('label[for="' + el.id + '"]') || {}).textContent || '' : '',
            closest_label: el.closest('.form-group, .mb-3, .row')?.querySelector('label')?.textContent?.trim() || ''
        }));
    }""")

def fill_select2(page, select_id, search_text):
    """Fill a Select2 AJAX dropdown."""
    try:
        page.evaluate("try { $('.select2-container--open').length && $('select.select2-hidden-accessible').select2('close'); } catch(e) {}")
        page.wait_for_timeout(300)
        page.evaluate(f"$('#{select_id}').select2('open')")
        page.wait_for_timeout(500)
        search_field = page.locator('.select2-search__field')
        if search_field.count() > 0:
            search_field.fill(search_text)
            page.wait_for_timeout(2000)
        res = page.locator('.select2-results__option:not(.select2-results__message)')
        if res.count() > 0:
            text = res.first.text_content()
            res.first.click()
            page.wait_for_timeout(500)
            return text
        page.evaluate(f"try {{ $('#{select_id}').select2('close'); }} catch(e) {{}}")
    except Exception as e:
        log(f"    Select2 fill error for #{select_id}: {e}")
    return None

def try_fill_field(page, f):
    """Try to fill a single field with test data. Returns True if filled."""
    if f['readonly'] or f['disabled'] or f['value']:
        return False
    fid = f['id']
    fname = f['name']
    if not fid and not fname:
        return False
    selector = f"#{fid}" if fid else f"[name='{fname}']"
    name_lower = (fname or fid or '').lower()

    try:
        if f['tag'] == 'SELECT':
            if fid:
                result = fill_select2(page, fid, "a")
                if result:
                    log(f"      Filled Select2 #{fid}: {result}")
                    return True
            # Try regular select
            sel_id = fid or fname
            options = page.evaluate(f"""() => {{
                const sel = document.getElementById('{sel_id}') || document.querySelector("[name='{fname}']");
                if (!sel) return [];
                return Array.from(sel.options).filter(o => o.value).map(o => ({{value: o.value, text: o.text}}));
            }}""")
            if options:
                page.select_option(selector, options[0]['value'])
                return True
        elif f['type'] in ('text', ''):
            if 'date' in name_lower:
                page.locator(selector).first.fill("19 Apr 2026")
            elif 'email' in name_lower:
                page.locator(selector).first.fill("test@test.com")
            elif 'phone' in name_lower or 'tel' in name_lower:
                page.locator(selector).first.fill("1234567890")
            elif 'amount' in name_lower or 'rate' in name_lower or 'price' in name_lower or 'charge' in name_lower:
                page.locator(selector).first.fill("100")
            elif 'weight' in name_lower or 'qty' in name_lower or 'quantity' in name_lower:
                page.locator(selector).first.fill("10")
            else:
                page.locator(selector).first.fill("Test Data")
            return True
        elif f['type'] == 'number':
            page.locator(selector).first.fill("100")
            return True
        elif f['type'] == 'date':
            page.locator(selector).first.fill("2026-04-19")
            return True
        elif f['tag'] == 'TEXTAREA':
            page.locator(selector).first.fill("Test notes for ERP testing")
            return True
    except Exception as e:
        log(f"      Could not fill {selector}: {e}")
    return False

def login(page):
    """Login to the ERP system."""
    log("Logging in...")
    page.goto(f"{BASE_URL}/")
    page.wait_for_timeout(2000)
    page.evaluate("""() => {
        document.getElementById("username").value = "superadmin";
        document.getElementById("password").value = "Nick@#24";
        document.getElementById("signupForm").submit();
    }""")
    page.wait_for_timeout(8000)
    screenshot(page, "00_after_login")
    log("Login complete.")

def get_wizard_steps(page):
    """Get the wizard/step navigation items on the job detail page."""
    return page.evaluate("""() => {
        // Look for step wizard circles/links - these are typically in a ul.nav or div with step indicators
        // Based on the screenshot, they appear as circles with numbers at the top

        // Try multiple possible selectors for step wizards
        const selectors = [
            '.steps ul li a',
            '.wizard .steps li a',
            '.wizard-steps li a',
            '.step-wizard li a',
            '.nav-pills.nav-justified li a',
            '.nav-pills li a',
            'ul.steps li a',
            '.steps li a',
            // Bootstrap wizard
            '.bs-stepper .step-trigger',
            '.bs-stepper-header .step-trigger',
            // jQuery steps
            '.wizard > .steps > ul > li > a',
            // Generic step indicators
            '.step-indicator a',
            '.step a',
            // Breadcrumb-style steps
            '.steps-container a',
            '.progress-steps a',
        ];

        for (const sel of selectors) {
            const items = document.querySelectorAll(sel);
            if (items.length >= 3 && items.length <= 15) {
                return Array.from(items).map((a, i) => ({
                    index: i,
                    text: a.textContent.trim().replace(/\\n/g, ' ').replace(/\\s+/g, ' '),
                    href: a.getAttribute('href') || '',
                    id: a.id || '',
                    class: a.className || '',
                    parentClass: a.parentElement?.className || '',
                    selector: sel
                }));
            }
        }

        // Also try looking for the specific step elements visible in the screenshot
        const stepLinks = document.querySelectorAll('a[href*="#step"]');
        if (stepLinks.length >= 3) {
            return Array.from(stepLinks).map((a, i) => ({
                index: i,
                text: a.textContent.trim().replace(/\\n/g, ' ').replace(/\\s+/g, ' '),
                href: a.getAttribute('href') || '',
                id: a.id || '',
                class: a.className || '',
                parentClass: a.parentElement?.className || '',
                selector: 'a[href*="#step"]'
            }));
        }

        return [];
    }""")

def get_page_structure(page):
    """Debug: Get the main structural elements on the page."""
    return page.evaluate("""() => {
        const info = {};

        // All nav elements
        info.navs = Array.from(document.querySelectorAll('ul.nav, .nav, .steps, .wizard')).map(el => ({
            tag: el.tagName,
            class: el.className,
            childCount: el.children.length,
            id: el.id || '',
            children: Array.from(el.children).slice(0, 15).map(c => ({
                tag: c.tagName,
                class: c.className?.substring(0, 50) || '',
                text: c.textContent?.trim().substring(0, 40) || ''
            }))
        }));

        // Step-like elements
        info.steps = Array.from(document.querySelectorAll('[class*="step"], [class*="wizard"], [role="tablist"]')).map(el => ({
            tag: el.tagName,
            class: el.className?.substring(0, 80) || '',
            id: el.id || '',
            childCount: el.children.length
        }));

        // Title/heading
        info.title = document.querySelector('h1, h2, h3, .page-title, .content-header')?.textContent?.trim()?.substring(0, 100) || '';

        return info;
    }""")

def click_wizard_step(page, step_index, step_selector):
    """Click a wizard step by index using the discovered selector."""
    page.evaluate(f"""(idx) => {{
        const items = document.querySelectorAll('{step_selector}');
        if (items[idx]) items[idx].click();
    }}""", step_index)
    page.wait_for_timeout(2000)

def find_buttons_in_content(page):
    """Find save/submit/add buttons in the main content area (not sidebar)."""
    return page.evaluate("""() => {
        const content = document.querySelector('.content-wrapper, .main-content, #content, .container-fluid, .tab-content, .step-content');
        const container = content || document.body;
        const buttons = container.querySelectorAll('button, input[type="submit"], a.btn');
        return Array.from(buttons).filter(b => {
            const t = b.textContent.toLowerCase().trim();
            return (t.includes('save') || t.includes('submit') || t.includes('add') ||
                    t.includes('update') || t.includes('next') || t.includes('create') ||
                    t.includes('+') || t.includes('new')) && b.offsetParent !== null;
        }).map(b => ({
            text: b.textContent.trim().substring(0, 50),
            type: b.type || '',
            class: b.className || '',
            id: b.id || '',
            tag: b.tagName,
            href: b.getAttribute('href') || ''
        }));
    }""")

def test_job_detail_tabs(page, job_type, job_list_url):
    """Navigate to job list, open first job, test all wizard steps."""
    log(f"\n{'='*60}")
    log(f"TESTING {job_type.upper()} JOB DETAILS")
    log(f"{'='*60}")

    # Navigate to job list
    page.goto(f"{BASE_URL}/{job_list_url}")
    page.wait_for_timeout(4000)
    screenshot(page, f"{job_type}_01_job_list")

    # Count rows
    row_count = page.evaluate("document.querySelectorAll('table tbody tr').length")
    log(f"  Found {row_count} rows in job list table")

    if row_count == 0:
        add_result(f"{job_type} - Job List", "FAIL", "No jobs found in table")
        return {}

    add_result(f"{job_type} - Job List", "PASS", f"Found {row_count} jobs")

    # Get info about links in first row
    first_row_links = page.evaluate("""() => {
        const row = document.querySelector('table tbody tr:first-child');
        if (!row) return [];
        return Array.from(row.querySelectorAll('a, button, [onclick]')).map(el => ({
            tag: el.tagName,
            text: el.textContent.trim().substring(0, 50),
            href: el.getAttribute('href') || '',
            onclick: el.getAttribute('onclick') || '',
            class: el.className || '',
            title: el.getAttribute('title') || '',
            innerHTML: el.innerHTML.substring(0, 100)
        }));
    }""")
    log(f"  First row links: {json.dumps(first_row_links, indent=2)}")

    # Click on first job - try the job number link (usually first cell)
    clicked = False
    for link in first_row_links:
        if link['href'] and link['href'] != '#' and link['tag'] == 'A':
            href = link['href']
            if href.startswith('/'):
                page.goto(f"{BASE_URL}{href}")
            else:
                page.goto(href)
            clicked = True
            log(f"  Navigated to: {href}")
            break

    if not clicked:
        # Click the first link in the row
        page.evaluate("""() => {
            const row = document.querySelector('table tbody tr:first-child');
            if (row) {
                const link = row.querySelector('a');
                if (link) link.click();
            }
        }""")
        clicked = True

    page.wait_for_timeout(4000)
    screenshot(page, f"{job_type}_02_job_detail")
    current_url = page.url
    log(f"  Job detail URL: {current_url}")
    add_result(f"{job_type} - Navigate to Job Detail", "PASS", f"URL: {current_url}")

    # Debug: Get page structure
    structure = get_page_structure(page)
    log(f"  Page title: {structure.get('title', 'N/A')}")
    log(f"  Nav elements: {len(structure.get('navs', []))}")
    for nav in structure.get('navs', []):
        log(f"    Nav: class={nav['class'][:60]} children={nav['childCount']} id={nav['id']}")
        for child in nav.get('children', [])[:5]:
            log(f"      Child: {child['tag']} class={child['class'][:40]} text={child['text'][:30]}")
    log(f"  Step elements: {len(structure.get('steps', []))}")
    for step in structure.get('steps', []):
        log(f"    Step: {step['tag']} class={step['class']} children={step['childCount']}")

    # Discover wizard steps
    steps = get_wizard_steps(page)
    log(f"  Wizard steps found: {len(steps)}")
    for s in steps:
        log(f"    Step {s['index']}: '{s['text']}' href={s['href']} selector={s.get('selector','')}")

    if not steps:
        log("  No wizard steps found. Trying to find step navigation via broader search...")
        # Try to find by looking at the visual step indicators
        steps = page.evaluate("""() => {
            // Look for any nav-like structure in the content area (not sidebar)
            const sidebar = document.querySelector('.sidebar, .left-sidebar, #sidebar, .main-sidebar, nav.sidebar');
            const allNavLinks = document.querySelectorAll('.nav-tabs > li > a, .nav-pills > li > a, .nav > li > a');

            const filtered = Array.from(allNavLinks).filter(a => {
                // Exclude links that are inside the sidebar
                if (sidebar && sidebar.contains(a)) return false;
                // Only include if in main content area
                const parent = a.closest('.content-wrapper, .main-content, #content, main, .container-fluid, .card, .panel');
                return parent !== null;
            });

            if (filtered.length >= 2) {
                return filtered.map((a, i) => ({
                    index: i,
                    text: a.textContent.trim().replace(/\\n/g, ' ').replace(/\\s+/g, ' '),
                    href: a.getAttribute('href') || '',
                    id: a.id || '',
                    class: a.className || '',
                    parentClass: a.parentElement?.className || '',
                    selector: 'content-nav-link'
                }));
            }
            return [];
        }""")
        log(f"  Content-area nav links found: {len(steps)}")
        for s in steps:
            log(f"    Step {s['index']}: '{s['text']}' href={s['href']}")

    if not steps:
        log("  Still no steps. Trying all clickable elements with step-like text...")
        # Just find and click step-like elements
        steps = page.evaluate("""() => {
            const all = document.querySelectorAll('a, button, li');
            const stepTexts = ['basic', 'clearing', 'shipping', 'delivery', 'buying', 'selling',
                             'purchase', 'sale', 'invoice', 'supporting', 'document', 'file'];
            const found = Array.from(all).filter(el => {
                const t = el.textContent.toLowerCase().trim();
                return stepTexts.some(st => t.includes(st)) && t.length < 50 && el.offsetParent !== null;
            });
            return found.map((el, i) => ({
                index: i,
                text: el.textContent.trim().replace(/\\n/g, ' ').replace(/\\s+/g, ' '),
                href: el.getAttribute('href') || '',
                tag: el.tagName,
                class: el.className || '',
                selector: 'step-text-match'
            }));
        }""")
        log(f"  Step-text matches: {len(steps)}")
        for s in steps:
            log(f"    {s['index']}: '{s['text']}'")

    # If we found steps, test each one
    all_step_fields = {}
    if steps:
        step_selector = steps[0].get('selector', '')
        add_result(f"{job_type} - Step Discovery", "PASS",
                   f"Found {len(steps)} steps: {[s['text'][:30] for s in steps]}")

        for step in steps:
            step_name = step['text'][:40]
            step_clean = step_name.replace(' ', '_').replace('/', '_').replace('.', '')[:25]
            idx = step['index']
            log(f"\n  --- Step {idx+1}: {step_name} ---")

            try:
                # Click the step
                if step_selector == 'content-nav-link':
                    page.evaluate(f"""(idx) => {{
                        const sidebar = document.querySelector('.sidebar, .left-sidebar, #sidebar, .main-sidebar, nav.sidebar');
                        const allNavLinks = document.querySelectorAll('.nav-tabs > li > a, .nav-pills > li > a, .nav > li > a');
                        const filtered = Array.from(allNavLinks).filter(a => {{
                            if (sidebar && sidebar.contains(a)) return false;
                            const parent = a.closest('.content-wrapper, .main-content, #content, main, .container-fluid, .card, .panel');
                            return parent !== null;
                        }});
                        if (filtered[idx]) filtered[idx].click();
                    }}""", idx)
                elif step_selector == 'step-text-match':
                    # Click by matching text
                    page.evaluate(f"""() => {{
                        const all = document.querySelectorAll('a, button, li');
                        const target = Array.from(all).find(el => el.textContent.trim().replace(/\\n/g, ' ').replace(/\\s+/g, ' ') === `{step_name}`);
                        if (target) target.click();
                    }}""")
                else:
                    click_wizard_step(page, idx, step_selector)

                page.wait_for_timeout(2000)
                screenshot(page, f"{job_type}_step_{idx+1:02d}_{step_clean}")

                # Discover fields
                fields = discover_all_visible_fields(page)
                log(f"    Visible fields: {len(fields)}")
                for f in fields[:15]:
                    log(f"      {f['tag']} name={f['name']} id={f['id']} type={f['type']} val='{f['value'][:25]}' label='{f['closest_label'][:25]}' ro={f['readonly']}")

                all_step_fields[step_name] = fields
                add_result(f"{job_type} - Step '{step_name}'", "PASS",
                           f"{len(fields)} visible fields", fields=fields)

                # Try filling empty non-readonly fields
                filled = 0
                for f in fields:
                    if try_fill_field(page, f):
                        filled += 1
                if filled > 0:
                    log(f"    Filled {filled} fields")
                    screenshot(page, f"{job_type}_step_{idx+1:02d}_{step_clean}_filled")

                # Find buttons
                buttons = find_buttons_in_content(page)
                if buttons:
                    log(f"    Buttons: {[b['text'] for b in buttons]}")

                # Special: Buying/Selling Charges
                name_lower = step_name.lower()
                if 'buying' in name_lower or 'selling' in name_lower or 'charge' in name_lower:
                    test_charges_step(page, job_type, step_name, idx)

                # Special: Files/Documents
                if 'file' in name_lower or 'document' in name_lower or 'supporting' in name_lower:
                    test_files_step(page, job_type, step_name, idx)

            except Exception as e:
                add_result(f"{job_type} - Step '{step_name}'", "FAIL", str(e))
                log(f"    ERROR: {e}")
                traceback.print_exc()
    else:
        log("  No wizard steps found. Testing the page as-is with all visible fields.")
        add_result(f"{job_type} - Step Discovery", "WARNING", "No wizard steps found")

        # Just document whatever fields are visible
        fields = discover_all_visible_fields(page)
        log(f"  Total visible fields on page: {len(fields)}")
        for f in fields[:20]:
            log(f"    {f['tag']} name={f['name']} id={f['id']} type={f['type']} val='{f['value'][:25]}' label='{f['closest_label'][:25]}'")
        all_step_fields["main_page"] = fields
        add_result(f"{job_type} - Page Fields", "PASS", f"{len(fields)} fields found", fields=fields)

        # Try clicking on step circles if they exist as numbered elements
        page.evaluate("""() => {
            // Try to find and log any numbered step indicators
            const circles = document.querySelectorAll('[class*="step"] a, [class*="step"] span, .wizard a');
            console.log('Step circles:', circles.length);
        }""")

    return all_step_fields

def test_charges_step(page, job_type, step_name, step_index):
    """Test adding charge lines."""
    log(f"    [Charges] Looking for Add button...")

    add_btns = page.evaluate("""() => {
        const buttons = document.querySelectorAll('button, a.btn, input[type="button"]');
        return Array.from(buttons).filter(b => {
            const t = b.textContent.toLowerCase().trim();
            return (t.includes('add') || t.includes('+') || t.includes('new row') ||
                    b.querySelector('i.fa-plus, i.fa-plus-circle')) && b.offsetParent !== null;
        }).map(b => ({
            text: b.textContent.trim().substring(0, 50),
            class: b.className || '',
            id: b.id || '',
            tag: b.tagName
        }));
    }""")

    log(f"    [Charges] Add buttons: {json.dumps(add_btns)}")

    if add_btns:
        try:
            page.evaluate("""() => {
                const buttons = document.querySelectorAll('button, a.btn, input[type="button"]');
                const btn = Array.from(buttons).find(b => {
                    const t = b.textContent.toLowerCase().trim();
                    return (t.includes('add') || t.includes('+') || t.includes('new row') ||
                            b.querySelector('i.fa-plus, i.fa-plus-circle')) && b.offsetParent !== null;
                });
                if (btn) btn.click();
            }""")
            page.wait_for_timeout(2000)
            screenshot(page, f"{job_type}_charges_{step_name.replace(' ','_')[:20]}_add")

            fields = discover_all_visible_fields(page)
            editable = [f for f in fields if not f['readonly'] and not f['disabled'] and not f['value']]
            log(f"    [Charges] Editable fields after add: {len(editable)}")

            # Try to fill charge fields
            filled = 0
            for f in editable[:5]:
                if try_fill_field(page, f):
                    filled += 1

            if filled:
                screenshot(page, f"{job_type}_charges_{step_name.replace(' ','_')[:20]}_filled")

            add_result(f"{job_type} - {step_name} Add Row", "PASS",
                       f"Added row, {len(editable)} editable fields, filled {filled}")
        except Exception as e:
            add_result(f"{job_type} - {step_name} Add Row", "FAIL", str(e))
    else:
        # Check for table with inline editing
        tables = page.evaluate("""() => {
            const tables = document.querySelectorAll('table');
            return Array.from(tables).filter(t => t.offsetParent !== null).map(t => ({
                rows: t.querySelectorAll('tbody tr').length,
                headers: Array.from(t.querySelectorAll('th')).map(h => h.textContent.trim().substring(0, 30)),
                class: t.className || ''
            }));
        }""")
        log(f"    [Charges] Tables found: {json.dumps(tables)}")
        add_result(f"{job_type} - {step_name} Add Row", "WARNING",
                   f"No Add button found. Tables: {len(tables)}")

def test_files_step(page, job_type, step_name, step_index):
    """Document the files/documents step."""
    log(f"    [Files] Documenting structure...")

    file_info = page.evaluate("""() => {
        const fileInputs = document.querySelectorAll('input[type="file"]');
        const dropzones = document.querySelectorAll('.dropzone, [class*="upload"], [class*="drop-area"]');
        const existingFiles = document.querySelectorAll('table tbody tr, .file-item, .file-list li, .document-item');

        return {
            file_inputs: Array.from(fileInputs).map(el => ({
                id: el.id || '',
                name: el.name || '',
                accept: el.getAttribute('accept') || '',
                multiple: el.multiple || false,
                visible: el.offsetParent !== null
            })),
            dropzones: Array.from(dropzones).map(el => ({
                class: el.className?.substring(0, 80) || '',
                id: el.id || '',
                text: el.textContent?.trim().substring(0, 100) || ''
            })),
            existing_files: Array.from(existingFiles).slice(0, 10).map(el => ({
                text: el.textContent?.trim().substring(0, 100) || ''
            }))
        };
    }""")

    log(f"    [Files] File inputs: {len(file_info['file_inputs'])}")
    log(f"    [Files] Dropzones: {len(file_info['dropzones'])}")
    log(f"    [Files] Existing files: {len(file_info['existing_files'])}")

    add_result(f"{job_type} - {step_name} Structure", "PASS",
               f"Inputs: {len(file_info['file_inputs'])}, Dropzones: {len(file_info['dropzones'])}, Existing: {len(file_info['existing_files'])}",
               fields=file_info)

def test_quote_creation(page):
    """Test Quote creation flow."""
    log(f"\n{'='*60}")
    log("TESTING QUOTE CREATION")
    log(f"{'='*60}")

    page.goto(f"{BASE_URL}/68915d3ba92a6ff8c96734362d61b15e")
    page.wait_for_timeout(4000)
    screenshot(page, "quote_01_list")

    # Find buttons
    all_btns = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a.btn, button, a[class*="btn"]')).filter(b => b.offsetParent !== null).map(b => ({
            text: b.textContent.trim().substring(0, 50),
            href: b.getAttribute('href') || '',
            id: b.id || '',
            class: b.className || '',
            tag: b.tagName
        }));
    }""")
    log(f"  All visible buttons: {json.dumps(all_btns[:15], indent=2)}")

    # Click "New Quote" or similar
    new_btn = None
    for btn in all_btns:
        t = btn['text'].lower()
        if ('new' in t or 'add' in t or 'create' in t or '+' in t) and len(btn['text']) < 40:
            new_btn = btn
            break

    if not new_btn:
        add_result("Quote Creation - Find Button", "FAIL", f"No New button found. Buttons: {[b['text'] for b in all_btns[:10]]}")
        return

    log(f"  Clicking: '{new_btn['text']}' href={new_btn['href']}")
    if new_btn['href'] and new_btn['href'] != '#':
        href = new_btn['href']
        page.goto(f"{BASE_URL}{href}" if href.startswith('/') else href)
    else:
        page.evaluate(f"""() => {{
            const btns = document.querySelectorAll('a.btn, button, a[class*="btn"]');
            const b = Array.from(btns).find(b => b.textContent.trim().substring(0, 50) === `{new_btn['text']}`);
            if (b) b.click();
        }}""")

    page.wait_for_timeout(4000)
    screenshot(page, "quote_02_form")
    log(f"  Quote form URL: {page.url}")
    add_result("Quote Creation - Navigate", "PASS", f"URL: {page.url}")

    # Discover fields
    fields = discover_all_visible_fields(page)
    log(f"  Quote form: {len(fields)} visible fields")
    for f in fields:
        log(f"    {f['tag']} name={f['name']} id={f['id']} type={f['type']} val='{f['value'][:20]}' label='{f['closest_label'][:25]}'")

    add_result("Quote Creation - Form Fields", "PASS", f"{len(fields)} visible fields", fields=fields)

    # Fill fields
    filled = 0
    for f in fields:
        if try_fill_field(page, f):
            filled += 1

    log(f"  Filled {filled} fields")
    if filled:
        screenshot(page, "quote_03_filled")

    # Submit
    try:
        submit = page.locator('button[type="submit"], input[type="submit"]')
        if submit.count() == 0:
            submit = page.locator('.btn-primary:visible, .btn-success:visible')
        if submit.count() > 0:
            # Find the save/submit button specifically
            for i in range(submit.count()):
                txt = submit.nth(i).text_content().lower()
                if 'save' in txt or 'submit' in txt or 'create' in txt:
                    submit.nth(i).click()
                    break
            else:
                submit.first.click()

            page.wait_for_timeout(4000)
            screenshot(page, "quote_04_after_submit")

            errors = page.evaluate("""() => {
                const alerts = document.querySelectorAll('.alert-danger, .text-danger, .error, .invalid-feedback, .parsley-error, .has-error');
                return Array.from(alerts).filter(a => a.offsetParent !== null).map(a => a.textContent.trim().substring(0, 100));
            }""")
            if errors and any(e.strip() for e in errors):
                add_result("Quote Creation - Submit", "WARNING", f"Validation errors: {errors[:5]}")
            else:
                add_result("Quote Creation - Submit", "PASS", f"Submitted. URL: {page.url}")
        else:
            add_result("Quote Creation - Submit", "WARNING", "No submit button found")
    except Exception as e:
        add_result("Quote Creation - Submit", "FAIL", str(e))

def test_rate_database(page):
    """Test Rate Database entry."""
    log(f"\n{'='*60}")
    log("TESTING RATE DATABASE")
    log(f"{'='*60}")

    page.goto(f"{BASE_URL}/95ea21eb539e083e42f57313509a93ed")
    page.wait_for_timeout(4000)
    screenshot(page, "rate_db_01_list")

    all_btns = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a.btn, button, a[class*="btn"]')).filter(b => b.offsetParent !== null).map(b => ({
            text: b.textContent.trim().substring(0, 50),
            href: b.getAttribute('href') || '',
            id: b.id || '',
            class: b.className || ''
        }));
    }""")
    log(f"  Buttons: {json.dumps(all_btns[:10])}")

    new_btn = None
    for btn in all_btns:
        t = btn['text'].lower()
        if ('add' in t or 'new' in t or 'create' in t or '+' in t) and len(btn['text']) < 40:
            new_btn = btn
            break

    if not new_btn:
        add_result("Rate Database - Find Button", "FAIL", f"No Add button. Buttons: {[b['text'] for b in all_btns[:10]]}")
        return

    log(f"  Clicking: '{new_btn['text']}' href={new_btn['href']}")
    if new_btn['href'] and new_btn['href'] != '#':
        href = new_btn['href']
        page.goto(f"{BASE_URL}{href}" if href.startswith('/') else href)
    else:
        page.evaluate(f"""() => {{
            const btns = document.querySelectorAll('a.btn, button, a[class*="btn"]');
            const b = Array.from(btns).find(b => b.textContent.trim().substring(0, 50) === `{new_btn['text']}`);
            if (b) b.click();
        }}""")

    page.wait_for_timeout(3000)
    screenshot(page, "rate_db_02_form")

    fields = discover_all_visible_fields(page)
    log(f"  Rate DB form: {len(fields)} visible fields")
    for f in fields:
        log(f"    {f['tag']} name={f['name']} id={f['id']} type={f['type']} val='{f['value'][:20]}' label='{f['closest_label'][:25]}'")

    add_result("Rate Database - Form", "PASS", f"{len(fields)} visible fields", fields=fields)

    filled = 0
    for f in fields:
        if try_fill_field(page, f):
            filled += 1
    log(f"  Filled {filled} fields")
    if filled:
        screenshot(page, "rate_db_03_filled")

    # Submit
    try:
        submit = page.locator('button[type="submit"], input[type="submit"]')
        if submit.count() == 0:
            submit = page.locator('.btn-primary:visible, .btn-success:visible')
        if submit.count() > 0:
            for i in range(submit.count()):
                txt = submit.nth(i).text_content().lower()
                if 'save' in txt or 'submit' in txt or 'add' in txt:
                    submit.nth(i).click()
                    break
            else:
                submit.first.click()
            page.wait_for_timeout(3000)
            screenshot(page, "rate_db_04_submitted")
            add_result("Rate Database - Submit", "PASS", f"URL: {page.url}")
        else:
            add_result("Rate Database - Submit", "WARNING", "No submit button found")
    except Exception as e:
        add_result("Rate Database - Submit", "FAIL", str(e))

def test_client_rates(page):
    """Test Client Rates entry."""
    log(f"\n{'='*60}")
    log("TESTING CLIENT RATES")
    log(f"{'='*60}")

    page.goto(f"{BASE_URL}/db6f53167f5911e700a4b3aae0352572")
    page.wait_for_timeout(4000)
    screenshot(page, "client_rates_01_list")

    all_btns = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a.btn, button, a[class*="btn"]')).filter(b => b.offsetParent !== null).map(b => ({
            text: b.textContent.trim().substring(0, 50),
            href: b.getAttribute('href') || '',
            id: b.id || '',
            class: b.className || ''
        }));
    }""")
    log(f"  Buttons: {json.dumps(all_btns[:10])}")

    new_btn = None
    for btn in all_btns:
        t = btn['text'].lower()
        if ('add' in t or 'new' in t or 'create' in t or '+' in t) and len(btn['text']) < 40:
            new_btn = btn
            break

    if not new_btn:
        add_result("Client Rates - Find Button", "FAIL", f"No Add button. Buttons: {[b['text'] for b in all_btns[:10]]}")
        return

    log(f"  Clicking: '{new_btn['text']}' href={new_btn['href']}")
    if new_btn['href'] and new_btn['href'] != '#':
        href = new_btn['href']
        page.goto(f"{BASE_URL}{href}" if href.startswith('/') else href)
    else:
        page.evaluate(f"""() => {{
            const btns = document.querySelectorAll('a.btn, button, a[class*="btn"]');
            const b = Array.from(btns).find(b => b.textContent.trim().substring(0, 50) === `{new_btn['text']}`);
            if (b) b.click();
        }}""")

    page.wait_for_timeout(3000)
    screenshot(page, "client_rates_02_form")

    fields = discover_all_visible_fields(page)
    log(f"  Client Rates form: {len(fields)} visible fields")
    for f in fields:
        log(f"    {f['tag']} name={f['name']} id={f['id']} type={f['type']} val='{f['value'][:20]}' label='{f['closest_label'][:25]}'")

    add_result("Client Rates - Form", "PASS", f"{len(fields)} visible fields", fields=fields)

    filled = 0
    for f in fields:
        if try_fill_field(page, f):
            filled += 1
    log(f"  Filled {filled} fields")
    if filled:
        screenshot(page, "client_rates_03_filled")

    # Submit
    try:
        submit = page.locator('button[type="submit"], input[type="submit"]')
        if submit.count() == 0:
            submit = page.locator('.btn-primary:visible, .btn-success:visible')
        if submit.count() > 0:
            for i in range(submit.count()):
                txt = submit.nth(i).text_content().lower()
                if 'save' in txt or 'submit' in txt or 'add' in txt:
                    submit.nth(i).click()
                    break
            else:
                submit.first.click()
            page.wait_for_timeout(3000)
            screenshot(page, "client_rates_04_submitted")
            add_result("Client Rates - Submit", "PASS", f"URL: {page.url}")
        else:
            add_result("Client Rates - Submit", "WARNING", "No submit button found")
    except Exception as e:
        add_result("Client Rates - Submit", "FAIL", str(e))

def main():
    log("Starting Sena ERP Job Details Test Suite")
    log(f"Screenshots: {SCREENSHOT_DIR}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        context.set_default_timeout(60000)
        page = context.new_page()

        try:
            login(page)

            # Step 1-4: Test Ocean Import job detail tabs
            ocean_fields = test_job_detail_tabs(page, "ocean_import", "9dddd5ce1b1375bc497feeb871842d4b")

            # Step 5: Test Air Import job detail tabs
            air_fields = test_job_detail_tabs(page, "air_import", "951733b073f499bd67fa764d38df48a8")

            # Compare
            if ocean_fields and air_fields:
                ocean_tabs = set(ocean_fields.keys())
                air_tabs = set(air_fields.keys())
                diff = {
                    "ocean_only": list(ocean_tabs - air_tabs),
                    "air_only": list(air_tabs - ocean_tabs),
                    "common": list(ocean_tabs & air_tabs)
                }
                log(f"\n  Ocean vs Air tab comparison: {json.dumps(diff, indent=2)}")
                add_result("Ocean vs Air Comparison", "PASS", json.dumps(diff))

            # Step 6: Quote creation
            test_quote_creation(page)

            # Step 7: Rate Database
            test_rate_database(page)

            # Step 8: Client Rates
            test_client_rates(page)

        except Exception as e:
            log(f"FATAL ERROR: {e}")
            traceback.print_exc()
            try:
                screenshot(page, "error_fatal")
            except:
                pass
            add_result("Fatal Error", "FAIL", str(e))
        finally:
            browser.close()

    # Save results
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    log(f"\n{'='*60}")
    log("TEST SUMMARY")
    log(f"{'='*60}")
    log(f"  Passed:   {results['summary']['passed']}")
    log(f"  Failed:   {results['summary']['failed']}")
    log(f"  Warnings: {results['summary']['warnings']}")
    log(f"  Results:  {RESULTS_FILE}")
    log(f"  Screenshots: {SCREENSHOT_DIR}")

    # Print all test results
    log(f"\n  Detailed Results:")
    for t in results['tests']:
        log(f"    [{t['status']}] {t['test']}: {t.get('details', '')[:100]}")

if __name__ == "__main__":
    main()
