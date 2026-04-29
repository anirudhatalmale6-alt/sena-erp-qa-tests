#!/usr/bin/env python3
"""
Sena ERP - Deep Functional Test of ALL Job Tabs & Document Generation
Tests: Clearing Instructions, Delivery Notes, Invoices, Purchase Orders
Detects: PDF errors, 500s, permission denied, Symfony exceptions
"""

import json
import os
import re
import time
import traceback
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

# ── Config ──────────────────────────────────────────────────────────────────
BASE_URL = "http://13.210.47.18:8088"
SCREENSHOT_DIR = "/var/lib/freelancer/projects/40298427/erp-test/screenshots/functional_deep"
RESULTS_FILE = "/var/lib/freelancer/projects/40298427/erp-test/results_functional_deep.json"
HEADLESS = True
VIEWPORT = {"width": 1280, "height": 720}
DEFAULT_TIMEOUT = 60000

JOB_ROUTES = {
    "ocean_import_open":   "/9dddd5ce1b1375bc497feeb871842d4b",
    "ocean_import_closed": "/670effb783ab68c5759f4523c9ad5185",
    "air_import_open":     "/951733b073f499bd67fa764d38df48a8",
    "air_import_closed":   "/3092560bb3f11343b8ceb0e02a739a01",
    "ocean_export_open":   "/ddc5bbfa18cf713c1478e511ea7455a7",
    "ocean_export_closed": "/12d57e567d9ab44399006309b5d542a4",
    "air_export_open":     "/8b574ca0cd37f8b76897ecc0f9d9ad34",
    "air_export_closed":   "/8ec1c8a3d9ad635d8fd2adb2c583b7c0",
    "land_import_open":    "/8013f48199799dce7a1fde812910a496",
    "land_import_closed":  "/ad661c9739fbf14ddd1802a6cc8c15c9",
    "land_export_open":    "/2ca1dbee9121459dedd8cf2e88823068",
    "land_export_closed":  "/2785ba86aa37c0a8ff38e247afd5c2af",
}

results = {
    "run_time": datetime.now().isoformat(),
    "phases": {},
    "errors": [],
    "summary": {"total_tests": 0, "passed": 0, "failed": 0, "warnings": 0},
}
screenshot_counter = 0


def ss(name):
    global screenshot_counter
    screenshot_counter += 1
    safe = re.sub(r'[^a-zA-Z0-9_\-]', '_', name)[:80]
    return os.path.join(SCREENSHOT_DIR, f"{screenshot_counter:03d}_{safe}.png")


def save():
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2, default=str)


def check_errors(page):
    """Check page for known ERP errors."""
    errors = []
    try:
        body = page.locator("body").inner_text(timeout=5000)
    except Exception:
        return errors
    bl = body.lower()
    checks = [
        ("file wasn't available",     "FILE_NOT_AVAILABLE"),
        ("file wasnt available",      "FILE_NOT_AVAILABLE"),
        ("file was not available",    "FILE_NOT_AVAILABLE"),
        ("permission denied",         "PERMISSION_DENIED"),
        ("storage/logs/laravel.log",  "LARAVEL_LOG_PERMISSION"),
        ("symfony exception",         "SYMFONY_EXCEPTION"),
        ("whoops",                    "SYMFONY_EXCEPTION"),
        ("unexpectedvalueexception",  "UNEXPECTED_VALUE_EXCEPTION"),
        ("errorexception",            "ERROR_EXCEPTION"),
        ("sqlstate",                  "SQL_ERROR"),
    ]
    for needle, code in checks:
        if needle in bl and code not in errors:
            errors.append(code)
    if "500" in body and ("internal server error" in bl or "server error" in bl):
        errors.append("HTTP_500")
    if "not found" in bl and ("view" in bl or "route" in bl):
        errors.append("VIEW_NOT_FOUND")
    return errors


def rec(phase, test, status, detail="", shot=""):
    results["summary"]["total_tests"] += 1
    if status == "PASS": results["summary"]["passed"] += 1
    elif status == "FAIL": results["summary"]["failed"] += 1
    elif status == "WARN": results["summary"]["warnings"] += 1
    e = {"test": test, "status": status, "detail": detail, "screenshot": shot, "ts": datetime.now().isoformat()}
    results.setdefault("phases", {}).setdefault(phase, []).append(e)
    icon = {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]", "INFO": "[INFO]"}.get(status, "[----]")
    print(f"  {icon} {test}: {detail[:200]}")
    if status == "FAIL":
        results["errors"].append(e)


def login(page):
    print("\n=== LOGIN ===")
    page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
    time.sleep(2)
    page.evaluate("""
        document.getElementById("username").value = "superadmin";
        document.getElementById("password").value = "Nick@#24";
        document.getElementById("signupForm").submit();
    """)
    print("  Waiting 8s after login...")
    time.sleep(8)
    s = ss("after_login")
    page.screenshot(path=s, full_page=True)
    url = page.url
    if "login" in url.lower():
        rec("login", "Login", "WARN", f"Still on login? URL: {url}", s)
    else:
        rec("login", "Login", "PASS", f"OK. URL: {url}", s)
    return "login" not in url.lower()


def handle_popup(popup, phase, label):
    """Check new popup/tab for errors."""
    try:
        popup.wait_for_load_state("domcontentloaded", timeout=15000)
        time.sleep(2)
        url = popup.url
        s = ss(f"popup_{label}")
        try: popup.screenshot(path=s, full_page=True)
        except: pass
        errs = check_errors(popup)
        if errs:
            rec(phase, f"Popup {label}", "FAIL", f"Errors: {errs}, URL: {url}", s)
        else:
            # Check if it's a PDF (content type or embed)
            content = ""
            try: content = popup.locator("body").inner_text(timeout=3000)
            except: pass
            if len(content.strip()) < 20 and ("pdf" in url.lower() or popup.url.endswith(".pdf")):
                rec(phase, f"Popup {label}", "PASS", f"PDF opened: {url}", s)
            elif len(content.strip()) < 10:
                rec(phase, f"Popup {label}", "WARN", f"Popup empty. URL: {url}", s)
            else:
                rec(phase, f"Popup {label}", "PASS", f"Loaded OK. URL: {url}", s)
        try: popup.close()
        except: pass
    except Exception as e:
        rec(phase, f"Popup {label}", "WARN", f"Error: {str(e)[:200]}")


def navigate_job_list(page, key, path):
    """Navigate to job list, return row count."""
    print(f"\n  Navigating to {key}...")
    try:
        page.goto(f"{BASE_URL}{path}", wait_until="networkidle", timeout=30000)
        time.sleep(3)
        s = ss(f"list_{key}")
        page.screenshot(path=s, full_page=True)
        errs = check_errors(page)
        if errs:
            rec("job_lists", f"List {key}", "FAIL", f"Errors: {errs}", s)
            return 0
        rows = page.evaluate("""() => {
            let max = 0;
            document.querySelectorAll('table').forEach(t => {
                const r = t.querySelectorAll('tbody tr').length;
                if (r > max) max = r;
            });
            return max;
        }""")
        rec("job_lists", f"List {key}", "PASS" if rows > 0 else "WARN", f"{rows} jobs", s)
        return rows
    except Exception as e:
        rec("job_lists", f"List {key}", "FAIL", f"Error: {str(e)[:200]}")
        return 0


def click_into_first_job(page, key):
    """Click the first job in a list. Returns True if successful."""
    try:
        first_link = page.locator("table tbody tr:first-child a").first
        if first_link.is_visible(timeout=3000):
            href = first_link.get_attribute("href") or ""
            print(f"    Clicking first job link: {href[:80]}")
            first_link.click(timeout=10000)
            time.sleep(3)
            s = ss(f"detail_{key}")
            page.screenshot(path=s, full_page=True)
            errs = check_errors(page)
            if errs:
                rec("navigation", f"Detail {key}", "FAIL", f"Errors: {errs}", s)
            else:
                rec("navigation", f"Detail {key}", "PASS", f"URL: {page.url}", s)
            return True
    except Exception:
        pass

    # Fallback: use href from evaluate
    try:
        href = page.evaluate("""() => {
            const t = document.querySelector('table');
            if (!t) return null;
            const r = t.querySelector('tbody tr');
            if (!r) return null;
            const a = r.querySelector('a');
            return a ? a.href : null;
        }""")
        if href:
            page.goto(href, wait_until="networkidle", timeout=30000)
            time.sleep(3)
            s = ss(f"detail_{key}")
            page.screenshot(path=s, full_page=True)
            rec("navigation", f"Detail {key}", "PASS", f"URL: {page.url}", s)
            return True
    except Exception:
        pass

    rec("navigation", f"Detail {key}", "WARN", "No clickable job found")
    return False


def find_step_tabs(page):
    """Find the step wizard tabs on the job detail page (NOT sidebar)."""
    return page.evaluate("""() => {
        const steps = [];
        // Look for step wizard elements in the main content area
        // These are typically: .step, .wizard-step, .nav-tabs within .content/.main-content,
        // or numbered circles/pills
        const mainContent = document.querySelector('.content-wrapper, .main-content, .content, #content, .container-fluid, main');
        const root = mainContent || document;

        // Strategy 1: Look for step indicators (numbered circles)
        root.querySelectorAll('.step, .wizard-step, .stepper-step, .bs-stepper-step, [class*="step"]').forEach(el => {
            if (el.offsetParent !== null) {
                steps.push({
                    text: (el.textContent || '').trim().substring(0, 150),
                    className: (el.className || '').substring(0, 200),
                    id: el.id || '',
                    tag: el.tagName,
                    outerHTML: el.outerHTML.substring(0, 500),
                });
            }
        });

        // Strategy 2: Look for nav-tabs ONLY within the main content (not sidebar)
        if (steps.length === 0) {
            root.querySelectorAll('.nav-tabs:not(.sidebar .nav-tabs) .nav-link, .tab-header a').forEach(el => {
                const text = (el.textContent || '').trim();
                // Filter out sidebar items
                if (text && el.offsetParent !== null && !el.closest('.sidebar') && !el.closest('.main-sidebar') && !el.closest('nav.navbar')) {
                    steps.push({
                        text: text.substring(0, 150),
                        className: (el.className || '').substring(0, 200),
                        id: el.id || '',
                        href: el.getAttribute('href') || '',
                        tag: el.tagName,
                        outerHTML: el.outerHTML.substring(0, 500),
                    });
                }
            });
        }

        // Strategy 3: Look for <li> items that look like steps (with numbers)
        if (steps.length === 0) {
            root.querySelectorAll('ul.nav:not(.sidebar ul) li a, ul.steps li, .progressbar li, ol.steps li').forEach(el => {
                const text = (el.textContent || '').trim();
                if (text && el.offsetParent !== null && !el.closest('.sidebar') && !el.closest('.main-sidebar')) {
                    steps.push({
                        text: text.substring(0, 150),
                        className: (el.className || '').substring(0, 200),
                        id: el.id || '',
                        href: el.getAttribute('href') || '',
                        tag: el.tagName,
                        outerHTML: el.outerHTML.substring(0, 500),
                    });
                }
            });
        }

        return steps;
    }""")


def find_step_links_by_text(page):
    """Find step links by their visible text labels in the main content."""
    known_steps = [
        "Basic", "Clearing", "Delivery", "Buying", "Selling",
        "Purchase", "Sale", "Invoice", "Supporting", "Files", "Charges",
    ]
    return page.evaluate("""(knownSteps) => {
        const results = [];
        // Find all clickable elements in the page
        const allClickable = document.querySelectorAll('a, button, [onclick], [role="tab"], li[class*="step"]');
        for (const el of allClickable) {
            const text = (el.textContent || '').trim();
            if (!text || text.length > 80) continue;
            // Check if it's a step-related element
            const isStep = knownSteps.some(kw => text.toLowerCase().includes(kw.toLowerCase()));
            if (!isStep) continue;
            // Skip sidebar items
            if (el.closest('.sidebar') || el.closest('.main-sidebar') || el.closest('nav.navbar')) continue;
            if (el.offsetParent === null && el.offsetWidth === 0) continue;

            results.push({
                text: text,
                tag: el.tagName,
                href: el.getAttribute('href') || '',
                className: (el.className || '').substring(0, 200),
                id: el.id || '',
                onclick: el.getAttribute('onclick') || '',
                outerHTML: el.outerHTML.substring(0, 500),
            });
        }
        return results;
    }""", known_steps)


def dump_page_structure(page, label):
    """Get comprehensive page structure for debugging."""
    info = page.evaluate("""() => {
        const result = {
            title: document.title,
            url: location.href,
            mainContentHTML: '',
            allTabLike: [],
            allButtons: [],
            allForms: [],
        };

        // Get main content area HTML (first 5000 chars)
        const mc = document.querySelector('.content-wrapper, .main-content, .content, #content, .container-fluid');
        if (mc) {
            result.mainContentHTML = mc.innerHTML.substring(0, 5000);
        }

        // All tab-like elements
        document.querySelectorAll('[role="tab"], .nav-link, [data-toggle="tab"], [data-bs-toggle="tab"]').forEach(el => {
            const text = (el.textContent || '').trim();
            if (text && text.length < 100) {
                const inSidebar = !!(el.closest('.sidebar') || el.closest('.main-sidebar'));
                result.allTabLike.push({
                    text, inSidebar,
                    href: el.getAttribute('href') || '',
                    class: (el.className || '').substring(0, 100),
                });
            }
        });

        // All buttons in main content
        const mainEl = mc || document.body;
        mainEl.querySelectorAll('button, a.btn, input[type="submit"], input[type="button"]').forEach(el => {
            if (el.offsetParent !== null || el.offsetWidth > 0) {
                result.allButtons.push({
                    tag: el.tagName,
                    text: (el.textContent || '').trim().substring(0, 100),
                    href: el.href || '',
                    id: el.id || '',
                    class: (el.className || '').substring(0, 100),
                    onclick: el.getAttribute('onclick') || '',
                });
            }
        });

        // All forms
        document.querySelectorAll('form').forEach(f => {
            result.allForms.push({
                id: f.id || '',
                action: f.action || '',
                method: f.method || '',
                fields: f.querySelectorAll('input, select, textarea').length,
            });
        });

        return result;
    }""")

    print(f"\n    === Page Structure: {label} ===")
    print(f"    Title: {info.get('title')}")
    print(f"    URL: {info.get('url')}")
    print(f"    Tab-like elements ({len(info.get('allTabLike', []))}):")
    for t in info.get('allTabLike', []):
        sidebar = " [SIDEBAR]" if t.get('inSidebar') else ""
        print(f"      '{t.get('text','')[:50]}' href='{t.get('href','')[:50]}'{sidebar}")
    print(f"    Buttons ({len(info.get('allButtons', []))}):")
    for b in info.get('allButtons', []):
        print(f"      [{b.get('tag')}] '{b.get('text','')[:50]}' id='{b.get('id','')}' href='{b.get('href','')[:50]}' onclick='{b.get('onclick','')[:50]}'")
    print(f"    Forms ({len(info.get('allForms', []))}):")
    for f in info.get('allForms', []):
        print(f"      id='{f.get('id','')}' action='{f.get('action','')[:80]}' fields={f.get('fields')}")

    # Print main content HTML excerpt for step detection
    html = info.get('mainContentHTML', '')
    if html:
        print(f"    Main content HTML (first 2000 chars):")
        print(f"    {html[:2000]}")

    return info


def click_step_by_text(page, step_text, step_num):
    """Click a step tab by its text content, scoped to main content area."""
    try:
        # Try multiple strategies to click the step
        clicked = page.evaluate(f"""(stepText) => {{
            // Find all clickable elements
            const allEls = document.querySelectorAll('a, button, li, span, div, [onclick], [role="tab"]');
            for (const el of allEls) {{
                // Skip sidebar
                if (el.closest('.sidebar') || el.closest('.main-sidebar') || el.closest('nav.navbar')) continue;
                const text = (el.textContent || '').trim();
                if (text.toLowerCase().includes(stepText.toLowerCase())) {{
                    // Check if it's visible
                    if (el.offsetParent !== null || el.offsetWidth > 0) {{
                        el.click();
                        return true;
                    }}
                }}
            }}
            return false;
        }}""", step_text)
        return clicked
    except Exception as e:
        print(f"    Error clicking step '{step_text}': {e}")
        return False


def test_doc_generation(page, phase, context, job_url):
    """Find and click document generation buttons, check for errors and popups."""
    # Find ALL visible buttons/links
    buttons = page.evaluate("""() => {
        const btns = [];
        document.querySelectorAll('button, a.btn, a[href], input[type="button"], input[type="submit"]').forEach(el => {
            // Skip sidebar items
            if (el.closest('.sidebar') || el.closest('.main-sidebar')) return;
            if (el.offsetParent === null && el.offsetWidth === 0) return;
            const text = (el.textContent || '').trim();
            const href = el.href || '';
            const onclick = el.getAttribute('onclick') || '';
            btns.push({
                text: text.substring(0, 150),
                href: href,
                onclick: onclick,
                id: el.id || '',
                tag: el.tagName,
                class: (el.className || '').substring(0, 150),
                title: el.getAttribute('title') || '',
                target: el.getAttribute('target') || '',
            });
        });
        return btns;
    }""")

    # Filter for document-related buttons
    doc_kw = ["generate", "print", "pdf", "download", "view", "save",
              "clearing", "delivery", "invoice", "credit note", "debit note",
              "purchase order", "export", "preview", "submit"]
    skip_kw = ["logout", "delete", "remove", "toggle", "dropdown", "collapse",
               "sidebar", "step", "next step", "prev"]

    doc_btns = []
    for btn in buttons:
        combined = f"{btn.get('text','')} {btn.get('href','')} {btn.get('onclick','')} {btn.get('title','')}".lower()
        text_l = btn.get('text','').lower().strip()
        if not text_l or len(text_l) > 120:
            continue
        if any(kw in combined for kw in doc_kw):
            if not any(kw in text_l for kw in skip_kw):
                doc_btns.append(btn)

    # Also add any button with class btn-primary, btn-success, btn-info that has short text
    for btn in buttons:
        cls = btn.get('class','').lower()
        text_l = btn.get('text','').lower().strip()
        if ('btn-primary' in cls or 'btn-success' in cls or 'btn-info' in cls):
            if text_l and len(text_l) < 40 and btn not in doc_btns:
                if not any(kw in text_l for kw in skip_kw):
                    doc_btns.append(btn)

    print(f"    Document buttons found: {len(doc_btns)}")
    for b in doc_btns:
        print(f"      [{b.get('tag')}] '{b.get('text','')[:50]}' href='{b.get('href','')[:60]}' id='{b.get('id','')}'")

    if not doc_btns:
        print(f"    All buttons on page ({len(buttons)}):")
        for b in buttons[:15]:
            text = b.get('text','').strip()[:50]
            if text:
                print(f"      [{b.get('tag')}] '{text}' href='{b.get('href','')[:50]}' class='{b.get('class','')[:40]}'")
        return

    for i, btn in enumerate(doc_btns):
        label = btn.get('text','').strip()[:40] or btn.get('id','') or f"btn_{i}"
        print(f"\n    Clicking [{i+1}/{len(doc_btns)}]: '{label}'")

        popups = []
        def on_page(p): popups.append(p)
        page.context.on("page", on_page)

        try:
            clicked = False
            btn_id = btn.get('id','')
            btn_href = btn.get('href','')

            # By ID
            if btn_id and not clicked:
                try:
                    el = page.locator(f"#{btn_id}")
                    if el.is_visible(timeout=2000):
                        el.click(timeout=5000)
                        clicked = True
                except: pass

            # By text within btn class
            if not clicked and label:
                try:
                    loc = page.locator(f"button:has-text('{label[:30]}'), a.btn:has-text('{label[:30]}')").first
                    if loc.is_visible(timeout=2000):
                        loc.click(timeout=5000)
                        clicked = True
                except: pass

            # By href (direct navigate for PDFs)
            if not clicked and btn_href and btn_href != "#" and "javascript:" not in btn_href:
                try:
                    loc = page.locator(f"a[href='{btn_href}']").first
                    if loc.is_visible(timeout=2000):
                        loc.click(timeout=5000)
                        clicked = True
                except: pass

            # JS fallback
            if not clicked:
                try:
                    page.evaluate(f"""() => {{
                        const els = document.querySelectorAll('button, a.btn, a[href], input[type="button"]');
                        for (const el of els) {{
                            if (el.closest('.sidebar') || el.closest('.main-sidebar')) continue;
                            const t = (el.textContent || '').trim();
                            if (t.includes('{label[:20].replace("'", "")}') && (el.offsetParent !== null || el.offsetWidth > 0)) {{
                                el.click();
                                return true;
                            }}
                        }}
                        return false;
                    }}""")
                    clicked = True
                except: pass

            if not clicked:
                rec(phase, f"{context} - {label}", "WARN", "Could not click")
                continue

            time.sleep(3)

            # Handle popups
            if popups:
                for p in popups:
                    handle_popup(p, phase, f"{context}_{label}")
            else:
                s = ss(f"{context}_{label}")
                page.screenshot(path=s, full_page=True)
                errs = check_errors(page)
                cur = page.url
                if errs:
                    rec(phase, f"{context} - {label}", "FAIL", f"Errors: {errs}", s)
                else:
                    rec(phase, f"{context} - {label}", "PASS", f"OK. URL: {cur}", s)

                # Navigate back if we left the job page
                if job_url and cur != job_url and "login" not in cur.lower():
                    try:
                        page.goto(job_url, wait_until="networkidle", timeout=20000)
                        time.sleep(2)
                    except: pass

        except Exception as e:
            s = ss(f"{context}_error")
            try: page.screenshot(path=s, full_page=True)
            except: pass
            rec(phase, f"{context} - {label}", "WARN", f"Exception: {str(e)[:200]}", s)
            if job_url and page.url != job_url:
                try:
                    page.goto(job_url, wait_until="networkidle", timeout=20000)
                    time.sleep(2)
                except: pass
        finally:
            try: page.context.remove_listener("page", on_page)
            except: pass


def test_job_detail(page, phase, job_type):
    """Test all step tabs on a job detail page."""
    job_url = page.url
    print(f"\n  === Testing Job Detail: {job_type} ===")
    print(f"    URL: {job_url}")

    # First, dump page structure
    info = dump_page_structure(page, f"Job Detail {job_type}")

    # Try to find step tabs
    step_tabs = find_step_tabs(page)
    step_links = find_step_links_by_text(page)

    print(f"\n    Step tabs found: {len(step_tabs)}")
    for s in step_tabs:
        print(f"      '{s.get('text','')[:60]}' class='{s.get('className','')[:60]}'")

    print(f"    Step links by text: {len(step_links)}")
    for s in step_links:
        print(f"      '{s.get('text','')[:60]}' tag={s.get('tag')} href='{s.get('href','')[:40]}'")

    # Define the known steps to test based on the screenshot observation
    known_steps = [
        ("Basic Details", "basic"),
        ("Clearing Instructions", "clearing"),
        ("Clearing Instruction", "clearing"),
        ("Delivery Note", "delivery"),
        ("Delivery Notes", "delivery"),
        ("Buying Charges", "buying"),
        ("Selling Charges", "selling"),
        ("Purchase Charges", "purchase_charges"),
        ("Sales Charges", "sales_charges"),
        ("Purchase Invoice", "purchase_inv"),
        ("Sale Invoice", "sale_inv"),
        ("Sales Invoice", "sales_inv"),
        ("Job Supporting", "supporting"),
        ("Files", "files"),
        ("Supporting Documents", "supporting_docs"),
    ]

    # Attempt to click each known step
    tested_steps = set()
    for step_text, step_key in known_steps:
        if step_key in tested_steps:
            continue

        print(f"\n  --- Testing Step: {step_text} ({step_key}) ---")

        # Ensure we're on the job detail page
        if page.url != job_url:
            try:
                page.goto(job_url, wait_until="networkidle", timeout=20000)
                time.sleep(2)
            except:
                continue

        # Try clicking the step
        clicked = click_step_by_text(page, step_text, 0)
        if not clicked:
            # Try partial text match
            short = step_text.split()[0]  # First word
            clicked = click_step_by_text(page, short, 0)

        if not clicked:
            print(f"    Could not find/click step '{step_text}'")
            continue

        tested_steps.add(step_key)
        time.sleep(2)

        s = ss(f"step_{step_key}_{job_type}")
        page.screenshot(path=s, full_page=True)

        errs = check_errors(page)
        if errs:
            rec(phase, f"Step {step_text}", "FAIL", f"Errors: {errs}", s)
        else:
            rec(phase, f"Step {step_text}", "PASS", f"Step loaded", s)

        # Test document generation on this step
        test_doc_generation(page, phase, f"Step_{step_key}", job_url)

    # If no known steps were found, test the page as-is
    if not tested_steps:
        print("\n    No step tabs found - testing page directly")
        # Screenshot and test all buttons on the current page
        s = ss(f"no_steps_{job_type}")
        page.screenshot(path=s, full_page=True)
        test_doc_generation(page, phase, f"Direct_{job_type}", job_url)

    # Final check: try to find Save button and any remaining action buttons
    print(f"\n    Final: checking for Save/Submit/Print buttons...")
    if page.url != job_url:
        try:
            page.goto(job_url, wait_until="networkidle", timeout=20000)
            time.sleep(2)
        except: pass


def test_job_type_full(page, job_type, route_key, phase):
    """Test a complete job type: list -> first job -> all tabs."""
    print(f"\n{'='*60}")
    print(f"  TESTING: {job_type} (Phase: {phase})")
    print(f"{'='*60}")

    path = JOB_ROUTES.get(route_key)
    if not path:
        rec(phase, f"{job_type}", "WARN", f"No route for {route_key}")
        return False

    rows = navigate_job_list(page, route_key, path)
    if rows == 0:
        # Try closed variant
        closed_key = route_key.replace("_open", "_closed")
        if closed_key in JOB_ROUTES and closed_key != route_key:
            print(f"    No open jobs, trying closed...")
            rows = navigate_job_list(page, closed_key, JOB_ROUTES[closed_key])
            if rows == 0:
                rec(phase, f"{job_type} - No Jobs", "WARN", "No jobs available")
                return False
        else:
            rec(phase, f"{job_type} - No Jobs", "WARN", "No jobs available")
            return False

    if click_into_first_job(page, route_key):
        test_job_detail(page, phase, job_type)
        return True
    return False


def test_additional_routes(page, phase):
    """Test routes discovered from sidebar that show the Symfony error."""
    problem_routes = {
        "Ocean Import Closed": "/670effb783ab68c5759f4523c9ad5185",
        "Ocean Export Open": "/ddc5bbfa18cf713c1478e511ea7455a7",
        "Ocean Export Closed": "/12d57e567d9ab44399006309b5d542a4",
        "Air Import Closed": "/3092560bb3f11343b8ceb0e02a739a01",
        "Air Export Open": "/8b574ca0cd37f8b76897ecc0f9d9ad34",
        "Air Export Closed": "/8ec1c8a3d9ad635d8fd2adb2c583b7c0",
        "Land Import Open": "/8013f48199799dce7a1fde812910a496",
        "Land Import Closed": "/ad661c9739fbf14ddd1802a6cc8c15c9",
        "Land Export Open": "/2ca1dbee9121459dedd8cf2e88823068",
        "Land Export Closed": "/2785ba86aa37c0a8ff38e247afd5c2af",
        "Ocean Import Booking": "/e14e00f9b8b4f2a0fbce2a5f843a543d",
        "Ocean Export Booking": "/a77dd96ff658388a662b311c5bbd1a75",
        "Air Import Booking": "/6e2cac0a97967fe9b38243a12ec09be0",
        "Air Export Booking": "/7d27d418fe920b6bc9230e81ef3a9bae",
        "Purchase Invoice Report": "/purchase-invoice",
        "Sales Invoice Report": "/sales-invoice",
        "Purchase Invoice w/ VAT": "/purchase-invoice-with-vat",
        "Sales Invoice w/ VAT": "/sales-invoice/with-vat",
        "Ledger": "/ledger",
        "Customer Ageing": "/reports/customer-aging",
        "Supplier Ageing": "/reports/supplier-ageing",
        "Purchase Invoice Missing": "/purchase-invoice-missing",
        "Sales Charges w/o Invoice": "/sales-charges-without-invoice",
        "Activity Log": "/activity-log",
        "Credit Note Register": "/credit-note-register",
    }

    print(f"\n{'='*60}")
    print(f"  TESTING: Additional Routes & Reports")
    print(f"{'='*60}")

    for name, path in problem_routes.items():
        try:
            resp = page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)
            status = resp.status if resp else "unknown"
            s = ss(f"route_{name}")
            page.screenshot(path=s, full_page=True)
            errs = check_errors(page)
            if errs:
                rec(phase, f"Route: {name}", "FAIL", f"HTTP {status}, Errors: {errs}", s)
            elif status >= 400:
                rec(phase, f"Route: {name}", "FAIL", f"HTTP {status}", s)
            else:
                rec(phase, f"Route: {name}", "PASS", f"HTTP {status}, loaded OK", s)
        except PwTimeout:
            rec(phase, f"Route: {name}", "WARN", "Timeout")
        except Exception as e:
            rec(phase, f"Route: {name}", "WARN", f"Error: {str(e)[:150]}")

        # Re-login if we got kicked out
        if "login" in page.url.lower():
            print("    Got logged out, re-logging in...")
            login(page)

    save()


def main():
    print("=" * 70)
    print("  SENA ERP - Deep Functional Test: Job Tabs & Document Generation")
    print(f"  Started: {datetime.now().isoformat()}")
    print("=" * 70)

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        ctx = browser.new_context(viewport=VIEWPORT, ignore_https_errors=True, accept_downloads=True)
        ctx.set_default_timeout(DEFAULT_TIMEOUT)
        page = ctx.new_page()

        # Login
        if not login(page):
            save()
            browser.close()
            return

        # Phase 1: Ocean Import
        try:
            test_job_type_full(page, "Ocean Import", "ocean_import_open", "ocean_import")
        except Exception as e:
            rec("ocean_import", "Phase Error", "FAIL", f"{str(e)[:300]}")
            traceback.print_exc()
        save()

        # Re-login if needed
        if "login" in page.url.lower():
            login(page)

        # Phase 2: Air Import
        try:
            test_job_type_full(page, "Air Import", "air_import_open", "air_import")
        except Exception as e:
            rec("air_import", "Phase Error", "FAIL", f"{str(e)[:300]}")
            traceback.print_exc()
        save()

        if "login" in page.url.lower():
            login(page)

        # Phase 3: Ocean Export
        try:
            test_job_type_full(page, "Ocean Export", "ocean_export_open", "ocean_export")
        except Exception as e:
            rec("ocean_export", "Phase Error", "FAIL", f"{str(e)[:300]}")
            traceback.print_exc()
        save()

        if "login" in page.url.lower():
            login(page)

        # Phase 4: Air Export
        try:
            test_job_type_full(page, "Air Export", "air_export_open", "air_export")
        except Exception as e:
            rec("air_export", "Phase Error", "FAIL", f"{str(e)[:300]}")
            traceback.print_exc()
        save()

        if "login" in page.url.lower():
            login(page)

        # Phase 5: Land Import
        try:
            test_job_type_full(page, "Land Import", "land_import_open", "land_import")
        except Exception as e:
            rec("land_import", "Phase Error", "FAIL", f"{str(e)[:300]}")
            traceback.print_exc()
        save()

        if "login" in page.url.lower():
            login(page)

        # Phase 6: Land Export
        try:
            test_job_type_full(page, "Land Export", "land_export_open", "land_export")
        except Exception as e:
            rec("land_export", "Phase Error", "FAIL", f"{str(e)[:300]}")
            traceback.print_exc()
        save()

        if "login" in page.url.lower():
            login(page)

        # Phase 7: Test all routes for errors
        try:
            test_additional_routes(page, "all_routes")
        except Exception as e:
            rec("all_routes", "Phase Error", "FAIL", f"{str(e)[:300]}")
            traceback.print_exc()
        save()

        browser.close()

    # Summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    s = results["summary"]
    print(f"  Total: {s['total_tests']}  Passed: {s['passed']}  Failed: {s['failed']}  Warnings: {s['warnings']}")
    print(f"\n  ALL ERRORS ({len(results['errors'])}):")
    for e in results["errors"]:
        print(f"    [FAIL] {e.get('test','')}: {e.get('detail','')[:150]}")
    print(f"\n  Results: {RESULTS_FILE}")
    print(f"  Screenshots: {SCREENSHOT_DIR}/")
    print(f"  Completed: {datetime.now().isoformat()}")
    save()


if __name__ == "__main__":
    main()
