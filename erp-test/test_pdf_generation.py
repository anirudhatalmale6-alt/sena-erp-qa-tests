"""
Test Clearing Instructions, Delivery Note PDF generation, and Invoice printing
within Sena ERP Ocean Import job detail pages.

Investigates the client-reported issues:
1. Clearing Instructions PDFs show "File wasn't available on site"
2. Delivery Note PDFs show "File wasn't available on site"
3. Files like tli_si_2627_0469_2-2026-04-28-19_45_22.pdf not accessible
"""

import json
import os
import re
import sys
import time
import traceback
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

BASE_URL = "http://13.210.47.18:8088"
SCREENSHOT_DIR = "/var/lib/freelancer/projects/40298427/erp-test/screenshots/pdf_test"
RESULTS_FILE = "/var/lib/freelancer/projects/40298427/erp-test/results_pdf_test.json"
OCEAN_IMPORT_LIST = "9dddd5ce1b1375bc497feeb871842d4b"

sys.stdout.reconfigure(line_buffering=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

results = {
    "test_start": datetime.now().isoformat(),
    "jobs_tested": [],
    "pdf_tests": [],
    "direct_url_tests": [],
    "errors": [],
    "summary": {}
}


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def ss(name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    return path


def screenshot(page, name, full_page=False):
    path = ss(name)
    page.screenshot(path=path, full_page=full_page)
    log(f"  Screenshot: {name}.png")
    return path


def login(page):
    log("[LOGIN] Navigating to login page...")
    page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
    screenshot(page, "00_login_page")
    page.evaluate('''() => {
        document.getElementById("username").value = "superadmin";
        document.getElementById("password").value = "Nick@#24";
        document.getElementById("signupForm").submit();
    }''')
    log("[LOGIN] Credentials submitted, waiting 8 seconds...")
    page.wait_for_timeout(8000)
    screenshot(page, "01_after_login")
    log(f"[LOGIN] Current URL: {page.url}")


def get_wizard_steps(page):
    """Find wizard step indicators in the main content area (not sidebar)."""
    return page.evaluate("""() => {
        const sidebar = document.querySelector('.sidebar, .left-sidebar, #sidebar, .main-sidebar, nav.sidebar');
        // Look for step circles/links - the wizard uses numbered Step N circles
        const allLinks = document.querySelectorAll('a, li, div[class*="step"], span[class*="step"]');
        const steps = [];
        const seen = new Set();

        allLinks.forEach((el, i) => {
            if (sidebar && sidebar.contains(el)) return;
            const text = el.textContent.trim().replace(/\\n/g, ' ').replace(/\\s+/g, ' ');
            // Match step-like items
            if (text.match(/step\\s*\\d/i) || text.match(/^(basic|clearing|delivery|buying|selling|purchase|sale|invoice|file)/i)) {
                const key = text.substring(0, 30);
                if (!seen.has(key) && el.offsetParent !== null) {
                    seen.add(key);
                    steps.push({
                        index: steps.length,
                        text: text.substring(0, 80),
                        href: el.getAttribute('href') || '',
                        tag: el.tagName,
                        class: el.className || '',
                        id: el.id || ''
                    });
                }
            }
        });

        // Also check nav-tabs/pills in the content area
        if (steps.length === 0) {
            const navLinks = document.querySelectorAll('.nav-tabs > li > a, .nav-pills > li > a');
            navLinks.forEach((a, i) => {
                if (sidebar && sidebar.contains(a)) return;
                const parent = a.closest('.content-wrapper, .main-content, #content, main, .container-fluid, .card');
                if (parent) {
                    steps.push({
                        index: steps.length,
                        text: a.textContent.trim().substring(0, 80),
                        href: a.getAttribute('href') || '',
                        tag: 'A',
                        class: a.className || '',
                        id: a.id || ''
                    });
                }
            });
        }
        return steps;
    }""")


def click_step_by_text(page, step_text_match):
    """Click a wizard step by matching its text content."""
    page.evaluate(f"""(matchText) => {{
        const sidebar = document.querySelector('.sidebar, .left-sidebar, #sidebar, .main-sidebar, nav.sidebar');
        const allEls = document.querySelectorAll('a, li, span, div');
        for (const el of allEls) {{
            if (sidebar && sidebar.contains(el)) continue;
            const text = el.textContent.trim().replace(/\\n/g, ' ').replace(/\\s+/g, ' ');
            if (text.includes(matchText) && el.offsetParent !== null) {{
                el.click();
                return true;
            }}
        }}
        return false;
    }}""", step_text_match)


def scan_all_buttons_links(page, context_label="page"):
    """Scan ALL interactive elements on the visible page."""
    elements = page.evaluate("""() => {
        const elements = [];
        document.querySelectorAll('a, button, input[type="button"], input[type="submit"], .btn').forEach(el => {
            if (el.offsetParent !== null) {
                elements.push({
                    tag: el.tagName,
                    text: (el.textContent || '').trim().substring(0, 200),
                    href: el.href || el.getAttribute('href') || '',
                    onclick: el.getAttribute('onclick') || '',
                    cls: (el.className || '').substring(0, 100),
                    id: el.id || '',
                    name: el.name || '',
                    title: el.title || '',
                    type: el.type || '',
                    target: el.target || '',
                    dataTarget: el.getAttribute('data-target') || el.getAttribute('data-bs-target') || '',
                    outerHTML: el.outerHTML.substring(0, 300)
                });
            }
        });
        return elements;
    }""")
    return elements


def filter_pdf_related(elements):
    """Filter for PDF/print/download/clearing/delivery/invoice related elements."""
    keywords = ['print', 'pdf', 'generate', 'download', 'clearing', 'delivery',
                'invoice', 'fa-print', 'fa-download', 'fa-file-pdf', 'fa-eye',
                'report', 'export', 'view.*pdf', 'doc']
    matched = []
    for el in elements:
        search_text = f"{el.get('text','')} {el.get('href','')} {el.get('onclick','')} {el.get('cls','')} {el.get('id','')} {el.get('title','')} {el.get('outerHTML','')}".lower()
        for kw in keywords:
            if kw in search_text:
                matched.append(el)
                break
    return matched


def scan_page_html_for_pdf_patterns(page):
    """Search the raw page HTML for PDF-related URLs and patterns."""
    return page.evaluate(r"""() => {
        const html = document.documentElement.outerHTML;
        const pdfUrls = [];
        const relatedUrls = [];
        const printHandlers = [];

        // Find all href/src containing .pdf
        const pdfRegex = /(?:href|src|action|data-url|data-href)=["']([^"']*\.pdf[^"']*?)["']/gi;
        let match;
        while ((match = pdfRegex.exec(html)) !== null) {
            pdfUrls.push(match[1]);
        }

        // Find window.open calls (common for PDFs/print)
        const windowOpenRegex = /window\.open\s*\(\s*["']([^"']+)["']/gi;
        while ((match = windowOpenRegex.exec(html)) !== null) {
            relatedUrls.push({type: 'window.open', url: match[1]});
        }

        // Find fetch/ajax calls that might generate PDFs
        const fetchRegex = /(?:fetch|ajax|get|post)\s*\(\s*["']([^"']*(?:pdf|print|generate|download|clearing|delivery|invoice)[^"']*?)["']/gi;
        while ((match = fetchRegex.exec(html)) !== null) {
            relatedUrls.push({type: 'fetch/ajax', url: match[1]});
        }

        // Find onclick handlers with relevant keywords
        const onclickRegex = /onclick=["']([^"']*(?:print|pdf|generate|download|clearing|delivery|invoice)[^"']*?)["']/gi;
        while ((match = onclickRegex.exec(html)) !== null) {
            printHandlers.push(match[1]);
        }

        // Look for any route/url patterns containing relevant words
        const routeRegex = /["'](\/[^"']*(?:print|pdf|generate|download|clearing-instruction|delivery-note|invoice|document)[^"']*?)["']/gi;
        const routes = [];
        while ((match = routeRegex.exec(html)) !== null) {
            routes.push(match[1]);
        }

        // Look for JavaScript function definitions related to printing
        const funcRegex = /function\s+(\w*(?:print|pdf|generate|download)\w*)\s*\(/gi;
        const functions = [];
        while ((match = funcRegex.exec(html)) !== null) {
            functions.push(match[1]);
        }

        return {pdfUrls, relatedUrls, printHandlers, routes, functions};
    }""")


def test_pdf_click(page, context, el, label):
    """Click a PDF/print-related element and observe what happens."""
    result = {
        "label": label,
        "element_text": el.get('text', '')[:100],
        "element_href": el.get('href', '')[:200],
        "element_onclick": el.get('onclick', '')[:200],
        "element_html": el.get('outerHTML', '')[:300],
        "new_page_opened": False,
        "new_page_url": None,
        "download_triggered": False,
        "download_filename": None,
        "error_found": None,
        "is_pdf": False,
        "response_content_type": None,
        "screenshot": None,
        "page_text_preview": None
    }

    new_pages = []
    downloads = []

    def on_page(p):
        new_pages.append(p)

    def on_download(d):
        downloads.append(d)

    context.on("page", on_page)
    page.on("download", on_download)

    try:
        href = el.get('href', '')
        onclick = el.get('onclick', '')
        el_id = el.get('id', '')
        text = el.get('text', '').strip()
        original_url = page.url

        clicked = False

        # Strategy 1: By ID
        if el_id and not clicked:
            try:
                loc = page.locator(f"#{el_id}")
                if loc.count() > 0 and loc.first.is_visible():
                    loc.first.click(timeout=5000)
                    clicked = True
                    log(f"    Clicked by ID: #{el_id}")
            except Exception:
                pass

        # Strategy 2: By href
        if href and not clicked and href != '#' and 'javascript:' not in href:
            try:
                # Navigate directly via href if it's a full URL
                if href.startswith('http'):
                    page.goto(href, wait_until="domcontentloaded", timeout=15000)
                    clicked = True
                    log(f"    Navigated to href: {href[:80]}")
                elif href.startswith('/'):
                    page.goto(f"{BASE_URL}{href}", wait_until="domcontentloaded", timeout=15000)
                    clicked = True
                    log(f"    Navigated to href: {BASE_URL}{href[:80]}")
            except Exception as e:
                log(f"    Navigate failed: {e}")

        # Strategy 3: By onclick via JS eval
        if onclick and not clicked:
            try:
                page.evaluate(f"() => {{ {onclick} }}")
                clicked = True
                log(f"    Executed onclick: {onclick[:60]}")
            except Exception:
                pass

        # Strategy 4: Click by matching outerHTML
        if not clicked:
            try:
                if text:
                    loc = page.get_by_text(text[:40], exact=False)
                    if loc.count() > 0:
                        loc.first.click(timeout=5000)
                        clicked = True
                        log(f"    Clicked by text: {text[:40]}")
            except Exception:
                pass

        if not clicked:
            result["error_found"] = "Could not click element"
            return result

        page.wait_for_timeout(3000)

        # Check for new popup/tab
        if new_pages:
            result["new_page_opened"] = True
            new_page = new_pages[0]
            try:
                new_page.wait_for_load_state("domcontentloaded", timeout=10000)
            except Exception:
                pass
            result["new_page_url"] = new_page.url

            page_text = new_page.evaluate("() => document.body ? document.body.innerText.substring(0, 2000) : ''")
            result["page_text_preview"] = page_text[:500]
            content = new_page.content()

            # Check for errors
            if "File wasn't available" in page_text:
                result["error_found"] = "FILE NOT AVAILABLE: 'File wasn't available on site'"
            elif "not found" in page_text.lower() and len(page_text.strip()) < 500:
                result["error_found"] = f"NOT FOUND: {page_text[:200]}"
            elif "permission denied" in page_text.lower():
                result["error_found"] = "PERMISSION DENIED"
            elif "500" in page_text[:200] and ("error" in page_text.lower() or "exception" in page_text.lower()):
                result["error_found"] = f"500 ERROR: {page_text[:200]}"
            elif "Whoops!" in page_text or "Symfony" in page_text:
                result["error_found"] = f"LARAVEL EXCEPTION: {page_text[:300]}"

            is_pdf = '%PDF' in content[:20] or new_page.url.endswith('.pdf') or 'application/pdf' in str(content[:100])
            result["is_pdf"] = is_pdf

            ss_name = f"pdf_{label}"
            new_page.screenshot(path=ss(ss_name))
            result["screenshot"] = ss_name
            log(f"    New page: {new_page.url}")
            if result["error_found"]:
                log(f"    *** ERROR: {result['error_found']} ***")
            elif is_pdf:
                log(f"    PDF loaded successfully!")

            new_page.close()

        # Check downloads
        if downloads:
            result["download_triggered"] = True
            dl = downloads[0]
            result["download_filename"] = dl.suggested_filename
            log(f"    Download: {dl.suggested_filename}")

        # Check if same page changed
        if not new_pages and not downloads:
            current_text = page.evaluate("() => document.body ? document.body.innerText.substring(0, 2000) : ''")
            result["page_text_preview"] = current_text[:500]
            if "File wasn't available" in current_text:
                result["error_found"] = "FILE NOT AVAILABLE (same page)"
            elif "Whoops!" in current_text or "Symfony" in current_text:
                result["error_found"] = "LARAVEL EXCEPTION (same page)"
                screenshot(page, f"pdf_error_{label}")

            # If page URL changed, it might have navigated to a PDF
            if page.url != original_url:
                result["new_page_url"] = page.url
                content = page.content()
                if '%PDF' in content[:20]:
                    result["is_pdf"] = True
                    log(f"    PDF loaded in same tab: {page.url}")

    except Exception as e:
        result["error_found"] = f"EXCEPTION: {str(e)}"
        log(f"    Exception: {e}")
    finally:
        try:
            context.remove_listener("page", on_page)
        except Exception:
            pass
        try:
            page.remove_listener("download", on_download)
        except Exception:
            pass

    return result


def get_first_job_link(page):
    """Get the first clickable job link from the table."""
    links = page.evaluate("""() => {
        const row = document.querySelector('table tbody tr:first-child');
        if (!row) return [];
        return Array.from(row.querySelectorAll('a, button, [onclick]')).map(el => ({
            tag: el.tagName,
            text: (el.textContent || '').trim().substring(0, 80),
            href: el.getAttribute('href') || '',
            onclick: el.getAttribute('onclick') || '',
            cls: el.className || '',
            title: el.getAttribute('title') || '',
            outerHTML: el.outerHTML.substring(0, 300)
        }));
    }""")
    return links


def navigate_to_job_detail(page, job_list_url):
    """Navigate to the job list and click into the first job."""
    log(f"\n[NAV] Going to job listing: {BASE_URL}/{job_list_url}")
    page.goto(f"{BASE_URL}/{job_list_url}", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(3000)

    # Count rows
    row_count = page.evaluate("document.querySelectorAll('table tbody tr').length")
    log(f"  Found {row_count} rows in table")

    if row_count == 0:
        log("  ERROR: No jobs found!")
        return None

    # Get first row links
    first_links = get_first_job_link(page)
    log(f"  First row has {len(first_links)} clickable elements:")
    for link in first_links:
        log(f"    {link['tag']} text='{link['text']}' href='{link['href'][:60]}' class='{link['cls'][:40]}'")

    # Click the first valid link (usually the job number)
    job_url = None
    for link in first_links:
        href = link['href']
        if href and href != '#' and 'javascript' not in href and 'delete' not in href.lower():
            if href.startswith('/'):
                job_url = f"{BASE_URL}{href}"
            elif href.startswith('http'):
                job_url = href
            else:
                job_url = f"{BASE_URL}/{href}"
            break

    if job_url:
        log(f"  Navigating to job: {job_url}")
        page.goto(job_url, wait_until="networkidle", timeout=30000)
    else:
        # Try clicking the first link in the first row directly
        log("  No direct link found, clicking first row link via JS...")
        page.evaluate("""() => {
            const row = document.querySelector('table tbody tr:first-child');
            if (row) {
                const link = row.querySelector('a');
                if (link) link.click();
            }
        }""")

    page.wait_for_timeout(4000)
    log(f"  Job detail page URL: {page.url}")
    return page.url


def explore_job_pdfs(page, context, job_idx):
    """Explore a job detail page for all PDF/print functionality."""
    job_url = page.url
    job_result = {
        "job_url": job_url,
        "steps_found": [],
        "step_results": {},
        "all_pdf_patterns": {},
        "errors": []
    }

    log(f"\n{'='*70}")
    log(f"[JOB {job_idx}] Exploring job at: {job_url}")
    log(f"{'='*70}")

    screenshot(page, f"job{job_idx}_00_detail", full_page=True)

    # Get page title / header
    header = page.evaluate("""() => {
        const h = document.querySelector('h1, h2, .content-header, .page-title');
        return h ? h.textContent.trim() : 'Unknown';
    }""")
    log(f"  Page header: {header}")
    job_result["header"] = header

    # STEP A: Scan ALL elements on the initial page
    log(f"\n[JOB {job_idx}] === INITIAL PAGE SCAN ===")
    all_elements = scan_all_buttons_links(page, f"job{job_idx}")
    pdf_related = filter_pdf_related(all_elements)
    log(f"  Total visible interactive elements: {len(all_elements)}")
    log(f"  PDF/print related elements: {len(pdf_related)}")
    for el in pdf_related:
        log(f"    >> {el['tag']} text='{el['text'][:60]}' href='{el['href'][:60]}' onclick='{el['onclick'][:60]}'")

    # STEP B: Scan page HTML for PDF patterns
    log(f"\n[JOB {job_idx}] === HTML PATTERN SCAN ===")
    html_patterns = scan_page_html_for_pdf_patterns(page)
    log(f"  PDF URLs in HTML: {html_patterns['pdfUrls']}")
    log(f"  Related URLs: {html_patterns['relatedUrls']}")
    log(f"  Print handlers: {html_patterns['printHandlers']}")
    log(f"  Routes: {html_patterns['routes']}")
    log(f"  JS functions: {html_patterns['functions']}")
    job_result["all_pdf_patterns"] = html_patterns

    # STEP C: Find wizard steps
    log(f"\n[JOB {job_idx}] === FINDING WIZARD STEPS ===")
    steps = get_wizard_steps(page)
    log(f"  Wizard steps found: {len(steps)}")
    for s in steps:
        log(f"    Step {s['index']}: '{s['text']}' href='{s['href']}' tag={s['tag']}")
    job_result["steps_found"] = steps

    if not steps:
        log("  WARNING: No wizard steps found! Trying broader search...")
        # Try looking for step text in anchors
        steps = page.evaluate("""() => {
            const labels = ['Basic Details', 'Clearing Instructions', 'Delivery Note',
                           'Buying Charges', 'Selling Charges', 'Purchase Invoice',
                           'Sale Invoice', 'Files', 'Job Supporting'];
            const found = [];
            labels.forEach((label, i) => {
                const els = document.querySelectorAll('a, span, div, li');
                for (const el of els) {
                    if (el.textContent.trim().includes(label) && el.offsetParent !== null) {
                        found.push({
                            index: i,
                            text: el.textContent.trim().substring(0, 80),
                            href: el.getAttribute('href') || '',
                            tag: el.tagName,
                            class: el.className || '',
                            id: el.id || ''
                        });
                        break;
                    }
                }
            });
            return found;
        }""")
        log(f"  Broader step search found: {len(steps)}")
        for s in steps:
            log(f"    Step {s['index']}: '{s['text']}'")

    # STEP D: Click through each step tab
    step_labels = [
        ("Step 1", "Basic Details"),
        ("Step 2", "Clearing Instructions"),
        ("Step 3", "Delivery Note"),
        ("Step 4", "Buying Charges"),
        ("Step 5", "Selling Charges"),
        ("Step 6", "Purchase Invoice"),
        ("Step 7", "Sale Invoice"),
        ("Step 8", "Files"),
    ]

    for step_num, (step_id, step_name) in enumerate(step_labels):
        log(f"\n[JOB {job_idx}] --- {step_id}: {step_name} ---")

        # First navigate back to the job page if needed
        if page.url != job_url:
            log(f"  Navigating back to job page...")
            page.goto(job_url, wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(2000)

        # Try clicking the step
        try:
            # Method 1: Click by step text in the wizard
            step_data = {"stepId": step_id, "stepName": step_name}
            click_result = page.evaluate("""(data) => {
                const stepId = data.stepId;
                const stepName = data.stepName;
                const sidebar = document.querySelector('.sidebar, .left-sidebar, #sidebar, .main-sidebar, nav.sidebar');
                // Try clicking step circle/label - look for LI elements in the wizard
                const allEls = document.querySelectorAll('li, a, span, div');
                for (const el of allEls) {
                    if (sidebar && sidebar.contains(el)) continue;
                    const text = el.textContent.trim();
                    // Match combined "Step NStepName" (LI elements) or exact "Step N" (span)
                    const combined = stepId + stepName;
                    if ((text === combined || text === stepId) && el.offsetParent !== null) {
                        // For LI elements, try to find a clickable child first
                        const clickable = el.querySelector('a') || el;
                        clickable.click();
                        return {clicked: true, text: text, tag: el.tagName};
                    }
                }
                // Method 2: Click by step name only
                for (const el of allEls) {
                    if (sidebar && sidebar.contains(el)) continue;
                    const text = el.textContent.trim();
                    if (text === stepName && el.offsetParent !== null) {
                        el.click();
                        return {clicked: true, text: text, tag: el.tagName};
                    }
                }
                return {clicked: false};
            }""", step_data)

            if not click_result.get('clicked'):
                log(f"    Could not click step '{step_id}: {step_name}' - trying index-based click")
                # Try clicking the Nth LI element in the wizard (each step is an LI)
                page.evaluate("""(idx) => {
                    const sidebar = document.querySelector('.sidebar, .left-sidebar, #sidebar, .main-sidebar, nav.sidebar');
                    // The wizard uses <ul> with <li> items for each step
                    const wizardLists = document.querySelectorAll('ul');
                    for (const ul of wizardLists) {
                        if (sidebar && sidebar.contains(ul)) continue;
                        const lis = ul.querySelectorAll('li');
                        // If it has 7-8 LIs it's likely the step wizard
                        if (lis.length >= 7 && lis.length <= 10) {
                            const target = lis[idx];
                            if (target) {
                                const clickable = target.querySelector('a') || target;
                                clickable.click();
                                return true;
                            }
                        }
                    }
                    return false;
                }""", step_num)

            page.wait_for_timeout(2000)
            screenshot(page, f"job{job_idx}_step{step_num+1}_{step_name.replace(' ','_')}", full_page=True)

        except Exception as e:
            log(f"    Error clicking step: {e}")
            job_result["errors"].append(f"Step {step_id}: {e}")
            continue

        # Scan this step for PDF/print elements
        log(f"    Scanning step content...")
        step_elements = scan_all_buttons_links(page, f"step{step_num}")
        step_pdf = filter_pdf_related(step_elements)

        # Also look for specific buttons: Edit, Save, Generate, Print, Update
        action_buttons = [el for el in step_elements if any(kw in (el.get('text','') + el.get('cls','')).lower()
                          for kw in ['edit', 'save', 'update', 'generate', 'print', 'submit', 'create'])]

        log(f"    Total visible elements: {len(step_elements)}")
        log(f"    PDF/print related: {len(step_pdf)}")
        log(f"    Action buttons: {len(action_buttons)}")

        for el in step_pdf:
            log(f"      PDF >> {el['tag']} text='{el['text'][:60]}' href='{el['href'][:80]}' onclick='{el['onclick'][:60]}'")
        for el in action_buttons:
            log(f"      BTN >> {el['tag']} text='{el['text'][:60]}' href='{el['href'][:60]}' class='{el['cls'][:40]}'")

        # Scan HTML patterns for this step
        step_html_patterns = scan_page_html_for_pdf_patterns(page)
        if step_html_patterns['pdfUrls'] or step_html_patterns['routes'] or step_html_patterns['printHandlers']:
            log(f"    Step HTML - PDF URLs: {step_html_patterns['pdfUrls']}")
            log(f"    Step HTML - Routes: {step_html_patterns['routes']}")
            log(f"    Step HTML - Print handlers: {step_html_patterns['printHandlers']}")
            log(f"    Step HTML - Related URLs: {step_html_patterns['relatedUrls']}")
            log(f"    Step HTML - Functions: {step_html_patterns['functions']}")

        step_result = {
            "step": f"{step_id}: {step_name}",
            "pdf_elements": len(step_pdf),
            "action_buttons": [{"text": b['text'][:40], "cls": b['cls'][:40]} for b in action_buttons],
            "html_patterns": step_html_patterns,
            "pdf_click_results": [],
            "form_fields": []
        }

        # Check if step has form fields (for Clearing Instructions & Delivery Note)
        if step_name in ["Clearing Instructions", "Delivery Note"]:
            fields = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('input:not([type="hidden"]), select, textarea'))
                    .filter(el => el.offsetParent !== null)
                    .map(el => ({
                        tag: el.tagName,
                        type: el.type || '',
                        name: el.name || '',
                        id: el.id || '',
                        value: (el.value || '').substring(0, 50),
                        readonly: el.readOnly || false,
                        disabled: el.disabled || false,
                        label: el.closest('.form-group, .mb-3, .row')
                            ? (el.closest('.form-group, .mb-3, .row').querySelector('label') || {}).textContent || ''
                            : ''
                    }));
            }""")
            log(f"    Form fields: {len(fields)}")
            for f in fields[:15]:
                log(f"      {f['tag']} name='{f['name']}' id='{f['id']}' type='{f['type']}' value='{f['value']}' label='{f['label'][:30]}' ro={f['readonly']}")
            step_result["form_fields"] = fields

        # Check Purchase Invoice / Sale Invoice specific content
        if step_name in ["Purchase Invoice", "Sale Invoice"]:
            invoice_content = page.evaluate("""() => {
                const text = document.body ? document.body.innerText : '';
                const hasNoInvoice = text.includes('NO PURCHASE INVOICE GENERATED') || text.includes('NO SALE INVOICE GENERATED');
                // Look for invoice table rows
                const tables = document.querySelectorAll('table');
                const invoiceLinks = [];
                tables.forEach(table => {
                    table.querySelectorAll('a').forEach(a => {
                        if (a.offsetParent !== null) {
                            invoiceLinks.push({
                                text: (a.textContent || '').trim().substring(0, 80),
                                href: a.getAttribute('href') || '',
                                cls: a.className || '',
                                onclick: a.getAttribute('onclick') || '',
                                outerHTML: a.outerHTML.substring(0, 300)
                            });
                        }
                    });
                });
                return {hasNoInvoice, invoiceLinks, bodyText: text.substring(0, 500)};
            }""")
            log(f"    No invoice message: {invoice_content['hasNoInvoice']}")
            log(f"    Invoice links found: {len(invoice_content['invoiceLinks'])}")
            for il in invoice_content['invoiceLinks']:
                log(f"      >> text='{il['text'][:50]}' href='{il['href'][:60]}' class='{il['cls'][:40]}' onclick='{il['onclick'][:60]}'")
            step_result["invoice_content"] = invoice_content

            # Test clicking each invoice link
            for il_idx, il in enumerate(invoice_content['invoiceLinks']):
                log(f"\n    [TESTING INVOICE LINK {il_idx}] '{il['text'][:50]}'")
                pdf_result = test_pdf_click(page, context, il, f"job{job_idx}_step{step_num+1}_invoice{il_idx}")
                step_result["pdf_click_results"].append(pdf_result)
                results["pdf_tests"].append(pdf_result)

                # Navigate back if needed
                if page.url != job_url:
                    page.goto(job_url, wait_until="networkidle", timeout=20000)
                    page.wait_for_timeout(2000)
                    # Re-click the step
                    click_step_by_text(page, step_id)
                    page.wait_for_timeout(2000)

        # Test PDF-related elements in this step
        for pdf_idx, pdf_el in enumerate(step_pdf):
            # Skip sidebar/nav items
            el_text = pdf_el.get('text', '').lower()
            if any(skip in el_text for skip in ['dashboard', 'logout', 'sena erp', 'ocean import', 'air import',
                                                  'ocean export', 'air export', 'land import', 'land export',
                                                  'common masters', 'ocean masters', 'air masters', 'quote setup',
                                                  'dsr reports', 'financial reports']):
                continue

            log(f"\n    [TESTING PDF ELEMENT {pdf_idx}] '{pdf_el['text'][:50]}'")
            pdf_result = test_pdf_click(page, context, pdf_el, f"job{job_idx}_step{step_num+1}_pdf{pdf_idx}")
            step_result["pdf_click_results"].append(pdf_result)
            results["pdf_tests"].append(pdf_result)

            # Navigate back if needed
            if page.url != job_url:
                page.goto(job_url, wait_until="networkidle", timeout=20000)
                page.wait_for_timeout(2000)
                click_step_by_text(page, step_id)
                page.wait_for_timeout(2000)

        job_result["step_results"][f"{step_id}: {step_name}"] = step_result

    return job_result


def test_direct_pdf_urls(page):
    """Test direct access to known PDF URL patterns."""
    log(f"\n{'='*70}")
    log(f"[DIRECT URL] Testing direct PDF URL patterns")
    log(f"{'='*70}")

    # Known PDF URLs discovered from job 0469's HTML
    actual_pdf_urls = [
        "/files/2627/oc/469/c_663.pdf",   # Clearing instruction
        "/files/2627/oc/469/c_662.pdf",   # Clearing instruction
        "/files/2627/oc/469/d_508.pdf",   # Delivery note
        "/files/2627/oc/469/p_576.pdf",   # Purchase invoice
        "/files/2627/oc/469/p_577.pdf",   # Purchase invoice
        "/files/2627/oc/469/p_578.pdf",   # Purchase invoice
        "/files/2627/oc/469/p_1643.pdf",  # Purchase invoice
        "/files/2627/oc/469/p_1936.pdf",  # Purchase invoice
        "/files/2627/oc/469/p_1935.pdf",  # Purchase invoice
        "/files/2627/oc/469/p_1934.pdf",  # Purchase invoice
        "/files/2627/oc/469/p_1937.pdf",  # Purchase invoice
        "/files/2627/oc/469/s_503.pdf",   # Sale invoice
    ]

    # Client-reported filenames
    client_reported_files = [
        "tli_si_2627_0469_2-2026-04-28-19_45_22.pdf",
        "tli_si_2627_0469_1-2026-04-28-19_45_22.pdf",
    ]

    url_results = []

    # Test the actual PDF URLs found in the page HTML
    log(f"\n  Testing ACTUAL PDF URLs found in job HTML (from /files/ path)...")
    for pdf_path in actual_pdf_urls:
        url = f"{BASE_URL}{pdf_path}"
        log(f"\n  Testing: {pdf_path}")
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=15000)
            status = resp.status if resp else "N/A"
            content_type = resp.headers.get('content-type', 'unknown') if resp else "unknown"

            result = {
                "url": pdf_path,
                "status": status,
                "content_type": content_type,
                "is_pdf": 'pdf' in str(content_type).lower()
            }

            if 'pdf' in str(content_type).lower():
                log(f"    Status: {status}, Type: {content_type} -> PDF LOADED OK!")
                result["success"] = True
            else:
                body_text = page.evaluate("() => document.body ? document.body.innerText.substring(0, 500) : ''")
                result["body_preview"] = body_text[:200]
                log(f"    Status: {status}, Type: {content_type}")
                log(f"    Body: {body_text[:150]}")
                if "File wasn't available" in body_text:
                    result["error"] = "File wasn't available on site"
                    log(f"    *** FILE NOT AVAILABLE ***")
                    screenshot(page, f"direct_pdf_error_{pdf_path.replace('/', '_')[:40]}")
                elif status == 404:
                    result["error"] = "404 Not Found"
                elif "Whoops" in body_text or "Symfony" in body_text:
                    result["error"] = f"Laravel exception: {body_text[:100]}"
                    screenshot(page, f"direct_pdf_error_{pdf_path.replace('/', '_')[:40]}")

            url_results.append(result)
        except Exception as e:
            url_results.append({"url": pdf_path, "error": str(e)[:100]})
            log(f"    Error: {e}")

    # Test client-reported filenames across various paths
    log(f"\n  Testing client-reported filenames across path patterns...")
    test_paths = [
        "/storage/{file}", "/files/{file}", "/public/storage/{file}",
        "/pdf/{file}", "/documents/{file}", "/uploads/{file}",
    ]
    for fname in client_reported_files:
        for path_template in test_paths:
            path = path_template.replace("{file}", fname)
            url = f"{BASE_URL}{path}"
            try:
                resp = page.goto(url, wait_until="domcontentloaded", timeout=8000)
                status = resp.status if resp else "N/A"
                content_type = resp.headers.get('content-type', 'unknown') if resp else "unknown"
                result = {"url": path, "status": status, "content_type": content_type}
                if status != 404:
                    body = page.evaluate("() => document.body ? document.body.innerText.substring(0, 200) : ''")
                    result["body_preview"] = body[:100]
                    log(f"  {path} -> Status: {status}, Type: {content_type}, Body: {body[:80]}")
                url_results.append(result)
            except Exception as e:
                url_results.append({"url": path, "error": str(e)[:100]})

    # Summary
    non_404 = [r for r in url_results if r.get('status') != 404]
    pdfs_ok = [r for r in url_results if r.get('is_pdf')]
    file_errors = [r for r in url_results if r.get('error') and 'available' in str(r.get('error', '')).lower()]

    log(f"\n  Direct URL test summary:")
    log(f"    Total tested: {len(url_results)}")
    log(f"    Non-404 responses: {len(non_404)}")
    log(f"    PDFs loaded OK: {len(pdfs_ok)}")
    log(f"    'File not available' errors: {len(file_errors)}")

    for r in pdfs_ok:
        log(f"    OK: {r['url']}")
    for r in file_errors:
        log(f"    FAIL: {r['url']} -> {r.get('error')}")

    results["direct_url_tests"] = url_results


def test_multiple_jobs(page, context):
    """Test PDF generation across multiple Ocean Import jobs."""
    log(f"\n{'='*70}")
    log(f"[MULTI-JOB] Testing across multiple Ocean Import jobs")
    log(f"{'='*70}")

    # Navigate to listing
    page.goto(f"{BASE_URL}/{OCEAN_IMPORT_LIST}", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(3000)
    screenshot(page, "02_ocean_import_listing")

    # Get all job row links (up to 3 rows)
    job_links = page.evaluate("""() => {
        const rows = document.querySelectorAll('table tbody tr');
        const jobs = [];
        for (let i = 0; i < Math.min(3, rows.length); i++) {
            const row = rows[i];
            const links = Array.from(row.querySelectorAll('a')).map(a => ({
                text: (a.textContent || '').trim(),
                href: a.getAttribute('href') || ''
            }));
            const rowText = row.textContent.trim().replace(/\\n/g, ' ').replace(/\\s+/g, ' ').substring(0, 200);
            jobs.push({rowIndex: i, rowText, links});
        }
        return jobs;
    }""")

    log(f"  First {len(job_links)} job rows:")
    for job in job_links:
        log(f"    Row {job['rowIndex']}: {job['rowText'][:100]}")
        for link in job['links']:
            log(f"      Link: text='{link['text']}' href='{link['href'][:60]}'")

    # Navigate into each job
    for job_idx, job_info in enumerate(job_links):
        # Find a valid link to click
        valid_link = None
        for link in job_info['links']:
            href = link['href']
            if href and href != '#' and 'javascript' not in href and 'delete' not in href.lower():
                valid_link = href
                break

        if not valid_link:
            log(f"\n  Job {job_idx}: No valid link found, trying row click...")
            page.evaluate(f"""(idx) => {{
                const rows = document.querySelectorAll('table tbody tr');
                if (rows[idx]) {{
                    const link = rows[idx].querySelector('a');
                    if (link) link.click();
                }}
            }}""", job_info['rowIndex'])
            page.wait_for_timeout(4000)
        else:
            if valid_link.startswith('/'):
                job_url = f"{BASE_URL}{valid_link}"
            elif valid_link.startswith('http'):
                job_url = valid_link
            else:
                job_url = f"{BASE_URL}/{valid_link}"
            log(f"\n  Navigating to job {job_idx}: {job_url}")
            page.goto(job_url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)

        log(f"  Current URL: {page.url}")

        # Check if we're on a job detail page (should have wizard steps)
        title = page.evaluate("() => document.querySelector('h1, h2, .page-title') ? document.querySelector('h1, h2, .page-title').textContent.trim() : ''")
        log(f"  Page title: {title}")

        if 'import' in title.lower() or 'export' in title.lower() or 'update' in title.lower() or 'open' in title.lower():
            job_result = explore_job_pdfs(page, context, job_idx)
            results["jobs_tested"].append(job_result)
        else:
            log(f"  Not a job detail page (title: {title}), skipping...")
            screenshot(page, f"job{job_idx}_wrong_page")
            results["errors"].append(f"Job {job_idx} did not navigate to detail page. Title: {title}")

        # Go back to listing for next job
        if job_idx < len(job_links) - 1:
            page.goto(f"{BASE_URL}/{OCEAN_IMPORT_LIST}", wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(2000)


def main():
    log("=" * 70)
    log("SENA ERP - PDF Generation Test")
    log(f"Started: {datetime.now().isoformat()}")
    log("Testing: Clearing Instructions, Delivery Note PDFs, Invoice Printing")
    log("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            accept_downloads=True
        )
        context.set_default_timeout(60000)
        page = context.new_page()

        # Login
        login(page)

        # Test multiple jobs
        test_multiple_jobs(page, context)

        # Test direct PDF URL patterns
        test_direct_pdf_urls(page)

        # Summary
        total_pdf_tests = len(results["pdf_tests"])
        errors = [t for t in results["pdf_tests"] if t.get("error_found")]
        pdfs_ok = [t for t in results["pdf_tests"] if t.get("is_pdf")]

        results["summary"] = {
            "jobs_tested": len(results["jobs_tested"]),
            "total_pdf_elements_tested": total_pdf_tests,
            "pdf_errors": len(errors),
            "pdfs_ok": len(pdfs_ok),
            "direct_url_tests": len(results["direct_url_tests"]),
            "direct_url_non_404": sum(1 for t in results["direct_url_tests"] if t.get("status") != 404),
            "error_details": [{"label": e["label"], "error": e["error_found"]} for e in errors]
        }

        results["test_end"] = datetime.now().isoformat()

        log(f"\n{'='*70}")
        log(f"FINAL SUMMARY")
        log(f"{'='*70}")
        log(f"  Jobs tested: {results['summary']['jobs_tested']}")
        log(f"  PDF elements tested: {total_pdf_tests}")
        log(f"  PDF errors found: {len(errors)}")
        for e in errors:
            log(f"    ERROR: {e['label']} -> {e['error_found']}")
        log(f"  PDFs loaded OK: {len(pdfs_ok)}")
        log(f"  Direct URL tests: {results['summary']['direct_url_tests']}")
        log(f"  Direct URL non-404: {results['summary']['direct_url_non_404']}")

        # Detailed error report
        if errors:
            log(f"\n{'='*70}")
            log(f"DETAILED ERROR REPORT")
            log(f"{'='*70}")
            for e in errors:
                log(f"\n  Label: {e['label']}")
                log(f"  Element: {e.get('element_text', 'N/A')}")
                log(f"  Href: {e.get('element_href', 'N/A')}")
                log(f"  Error: {e['error_found']}")
                if e.get('new_page_url'):
                    log(f"  New page URL: {e['new_page_url']}")
                if e.get('page_text_preview'):
                    log(f"  Page text: {e['page_text_preview'][:200]}")

        with open(RESULTS_FILE, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        log(f"\nResults saved to: {RESULTS_FILE}")
        log(f"Screenshots saved to: {SCREENSHOT_DIR}")

        browser.close()


if __name__ == "__main__":
    main()
