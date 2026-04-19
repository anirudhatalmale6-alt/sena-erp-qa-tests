"""Discover form fields on Vendor Master and Ledger Group pages in Sena ERP."""

from playwright.sync_api import sync_playwright
import json, os

SCREENSHOT_DIR = "/var/lib/freelancer/projects/40298427/erp-test/screenshots/vendor_discover"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

BASE_URL = "http://13.210.47.18:8088"

FIELD_JS = """
() => {
    const fields = [];
    document.querySelectorAll('input:not([type="hidden"]), select, textarea').forEach(el => {
        if (el.offsetParent !== null || el.closest('.modal.show')) {
            fields.push({
                tag: el.tagName,
                type: el.type || '',
                name: el.name || '',
                id: el.id || '',
                placeholder: el.placeholder || '',
                required: el.required,
                label: el.id ? (document.querySelector('label[for="' + el.id + '"]')?.textContent?.trim() || '') : '',
                options: el.tagName === 'SELECT' ? Array.from(el.options).slice(0, 10).map(o => ({value: o.value, text: o.text})) : [],
                classes: el.className || ''
            });
        }
    });
    return fields;
}
"""


def print_fields(fields, title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"  Total visible fields: {len(fields)}")
    print(f"{'='*80}")
    for i, f in enumerate(fields, 1):
        print(f"\n  [{i}] <{f['tag'].lower()}> type={f['type']}")
        print(f"      name={f['name']!r}  id={f['id']!r}")
        if f.get('label'):
            print(f"      label={f['label']!r}")
        if f.get('placeholder'):
            print(f"      placeholder={f['placeholder']!r}")
        print(f"      required={f['required']}")
        if f.get('options'):
            print(f"      options (first 10): {json.dumps(f['options'], ensure_ascii=False)}")
        if f.get('classes'):
            print(f"      classes={f['classes']!r}")


def click_add_new(page):
    """Try multiple selectors to find and click Add New button."""
    selectors = [
        "a:has-text('Add New')",
        "button:has-text('Add New')",
        ".btn:has-text('Add New')",
        "a:has-text('Add')",
        "button:has-text('Add')",
        ".btn:has-text('Add')",
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=2000):
                print(f"  Clicking: {sel}")
                loc.click()
                return True
        except Exception:
            continue
    print("  WARNING: Could not find Add New button")
    return False


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        # Login
        print("Logging in...")
        page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        page.evaluate("""
            document.getElementById("username").value = "superadmin";
            document.getElementById("password").value = "Nick@#24";
            document.getElementById("signupForm").submit();
        """)
        page.wait_for_timeout(8000)
        print("  Logged in.")

        # ---- VENDOR MASTER via sidebar ----
        print("\nNavigating to Vendor Master via sidebar...")
        # First expand Common Masters if not already expanded
        try:
            cm = page.locator("text=Common Masters").first
            cm.click()
            page.wait_for_timeout(1000)
        except Exception:
            pass

        # Click Vendor Master in sidebar
        try:
            vm = page.locator("a:has-text('Vendor Master')").first
            href = vm.get_attribute("href")
            print(f"  Vendor Master link href: {href}")
            vm.click()
            page.wait_for_timeout(3000)
        except Exception as e:
            print(f"  Could not click Vendor Master sidebar: {e}")
            # Fallback to direct URL
            page.goto(f"{BASE_URL}/237cddc13035afd40df532c9c471b4ea", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

        page.screenshot(path=f"{SCREENSHOT_DIR}/vendor_list.png", full_page=True)
        print("  Screenshot: vendor_list.png")

        # Check if there's an error
        error_text = page.locator("text=Something went wrong").count()
        if error_text > 0:
            print("  ERROR: Vendor Master page shows 'Something went wrong'")
            print("  Trying to get the Vendor Master URL from sidebar...")
            # Get all sidebar links
            links = page.evaluate("""
                () => {
                    const links = [];
                    document.querySelectorAll('a').forEach(a => {
                        if (a.textContent.toLowerCase().includes('vendor')) {
                            links.push({text: a.textContent.trim(), href: a.href});
                        }
                    });
                    return links;
                }
            """)
            print(f"  Vendor-related links: {json.dumps(links, indent=2)}")
        else:
            # Try to click Add New
            if click_add_new(page):
                page.wait_for_timeout(2000)
                page.screenshot(path=f"{SCREENSHOT_DIR}/vendor_form.png", full_page=True)
                print("  Screenshot: vendor_form.png")

                vendor_fields = page.evaluate(FIELD_JS)
                print_fields(vendor_fields, "VENDOR MASTER - Form Fields")
            else:
                print("  No Add New button found on Vendor Master page")

        # ---- Also try Vendor Type ----
        print("\n\nNavigating to Vendor Type via sidebar...")
        try:
            vt = page.locator("a:has-text('Vendor Type')").first
            href_vt = vt.get_attribute("href")
            print(f"  Vendor Type link href: {href_vt}")
            vt.click()
            page.wait_for_timeout(3000)
        except Exception as e:
            print(f"  Could not click Vendor Type: {e}")

        page.screenshot(path=f"{SCREENSHOT_DIR}/vendor_type_list.png", full_page=True)
        print("  Screenshot: vendor_type_list.png")

        vt_error = page.locator("text=Something went wrong").count()
        if vt_error == 0:
            if click_add_new(page):
                page.wait_for_timeout(2000)
                page.screenshot(path=f"{SCREENSHOT_DIR}/vendor_type_form.png", full_page=True)
                print("  Screenshot: vendor_type_form.png")

                vt_fields = page.evaluate(FIELD_JS)
                print_fields(vt_fields, "VENDOR TYPE - Form Fields")
        else:
            print("  Vendor Type page also has error")

        # ---- LEDGER GROUP ----
        print("\n\nNavigating to Ledger Group...")
        page.goto(f"{BASE_URL}/2b0f7f32c7f7af6b51bf090558391d67", wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)
        page.screenshot(path=f"{SCREENSHOT_DIR}/ledger_group_list.png", full_page=True)
        print("  Screenshot: ledger_group_list.png")

        click_add_new(page)
        page.wait_for_timeout(2000)
        page.screenshot(path=f"{SCREENSHOT_DIR}/ledger_group_form.png", full_page=True)
        print("  Screenshot: ledger_group_form.png")

        ledger_fields = page.evaluate(FIELD_JS)
        print_fields(ledger_fields, "LEDGER GROUP - Form Fields")

        # Also get labels by proximity (not just for= attribute)
        print("\n\n--- Ledger Group: All visible labels/text near fields ---")
        label_info = page.evaluate("""
            () => {
                const info = [];
                document.querySelectorAll('.form-group, .form-floating, .mb-3, .col, [class*="col-"]').forEach(container => {
                    const label = container.querySelector('label, .form-label, h6, span');
                    const input = container.querySelector('input, select, textarea');
                    if (label && input) {
                        info.push({
                            labelText: label.textContent.trim(),
                            inputName: input.name || '',
                            inputId: input.id || '',
                            inputType: input.type || input.tagName
                        });
                    }
                });
                return info;
            }
        """)
        for item in label_info:
            print(f"  Label: {item['labelText']!r} -> name={item['inputName']!r} id={item['inputId']!r} type={item['inputType']}")

        # ---- Discover all sidebar menu items for reference ----
        print("\n\n--- All sidebar menu items ---")
        menu_items = page.evaluate("""
            () => {
                const items = [];
                document.querySelectorAll('.sidebar a, .nav-sidebar a, nav a, .menu a').forEach(a => {
                    const text = a.textContent.trim();
                    if (text && a.href && !a.href.includes('javascript:')) {
                        items.push({text, href: a.href});
                    }
                });
                return items;
            }
        """)
        for item in menu_items:
            print(f"  {item['text']} -> {item['href']}")

        browser.close()
        print("\n\nDone. Screenshots saved to:", SCREENSHOT_DIR)


if __name__ == "__main__":
    main()
