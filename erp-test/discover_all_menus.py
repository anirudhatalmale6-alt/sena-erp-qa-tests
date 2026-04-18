"""
Discover all submenus and pages in the ERP system.
"""
from playwright.sync_api import sync_playwright
import os
import json

URL = "http://13.210.47.18:8088/"
USER = "superadmin"
PASS = "Nick@#24"
SS_DIR = "/var/lib/freelancer/projects/40298427/erp-test/screenshots"
os.makedirs(SS_DIR, exist_ok=True)

def ss(page, name):
    page.screenshot(path=f"{SS_DIR}/{name}.png")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 720})
    page = context.new_page()
    page.set_default_timeout(30000)

    # Login
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(3000)
    page.evaluate('''() => {
        document.getElementById("username").value = "superadmin";
        document.getElementById("password").value = "Nick@#24";
        document.getElementById("signupForm").submit();
    }''')
    page.wait_for_timeout(8000)
    print(f"Logged in. URL: {page.url}")

    # Get the full sidebar HTML
    sidebar_html = page.evaluate('''() => {
        const sidebar = document.querySelector('.sidebar-wrapper, aside, .sidebar, nav');
        return sidebar ? sidebar.innerHTML : document.body.innerHTML;
    }''')

    # Parse all menu items with their submenus
    # Use JS to extract the full menu tree
    menu_tree = page.evaluate('''() => {
        const result = [];
        const topItems = document.querySelectorAll('.sidebar-item, .nav-item');

        topItems.forEach(item => {
            const link = item.querySelector('a');
            if (!link) return;

            const text = link.textContent.trim();
            const href = link.getAttribute('href') || '#';

            const submenu = item.querySelector('.submenu, .sidebar-dropdown, ul');
            const subItems = [];

            if (submenu) {
                const subLinks = submenu.querySelectorAll('a');
                subLinks.forEach(subLink => {
                    const subText = subLink.textContent.trim();
                    const subHref = subLink.getAttribute('href') || '#';
                    if (subText && subText.length < 80) {
                        subItems.push({text: subText, href: subHref});
                    }
                });
            }

            if (text && text.length < 80) {
                result.push({
                    text: text,
                    href: href,
                    hasSubmenu: subItems.length > 0,
                    subItems: subItems
                });
            }
        });

        return result;
    }''')

    print(f"\n{'='*60}")
    print("ERP SYSTEM - COMPLETE MENU STRUCTURE")
    print(f"{'='*60}")

    total_pages = 0
    module_count = 0

    for item in menu_tree:
        text = item["text"].split('\n')[0].strip()
        if not text or text in ["NICK JAIN", "Administrator"]:
            continue

        module_count += 1
        sub_items = item.get("subItems", [])

        if sub_items:
            print(f"\n{module_count}. {text} ({len(sub_items)} sub-items)")
            for sub in sub_items:
                sub_text = sub["text"].strip()
                sub_href = sub["href"]
                if sub_text:
                    print(f"   - {sub_text} | {sub_href[:80]}")
                    total_pages += 1
        else:
            print(f"\n{module_count}. {text} (no sub-items)")
            if item["href"] != "#":
                total_pages += 1

    print(f"\n{'='*60}")
    print(f"TOTAL MODULES: {module_count}")
    print(f"TOTAL PAGES/FEATURES: {total_pages}")
    print(f"{'='*60}")

    # Now let's also click each main menu to expand and see submenus properly
    print("\n\n=== EXPANDING EACH MENU ===")

    main_menus = ["HR", "Account", "Financial Reports", "Common Masters",
                  "Ocean Masters", "Air Masters", "Quote Setup",
                  "Ocean Import", "Ocean Export", "Air Import", "Air Export",
                  "Land Import", "Land Export", "DSR Reports"]

    all_submenus = {}

    for menu_name in main_menus:
        try:
            menu_link = page.locator(f'a:has-text("{menu_name}")').first
            if menu_link.is_visible(timeout=2000):
                menu_link.click()
                page.wait_for_timeout(1000)

                # Find visible submenu items
                sub_links = page.locator('.sidebar-item.active .submenu a:visible, .sidebar-item.has-sub.active a:visible').all()
                if not sub_links:
                    # Try different selector
                    sub_links = page.locator(f'.submenu a:visible').all()

                subs = []
                for sl in sub_links:
                    try:
                        t = sl.inner_text(timeout=500).strip()
                        h = sl.get_attribute("href") or ""
                        if t and len(t) < 60 and t != menu_name:
                            subs.append({"text": t, "href": h})
                    except:
                        pass

                if subs:
                    all_submenus[menu_name] = subs
                    print(f"\n{menu_name}: {len(subs)} items")
                    for s in subs:
                        print(f"  - {s['text']}")
                else:
                    print(f"\n{menu_name}: (no visible sub-items after click)")

        except Exception as e:
            print(f"\n{menu_name}: Error - {str(e)[:50]}")

    # Save menu structure
    output = {
        "menu_tree": menu_tree,
        "expanded_submenus": all_submenus,
        "total_modules": module_count,
        "total_pages": total_pages
    }
    with open("/var/lib/freelancer/projects/40298427/erp-test/menu_structure.json", "w") as f:
        json.dump(output, f, indent=2)

    # Take final sidebar screenshot with menus expanded
    ss(page, "10_sidebar_full")

    browser.close()
    print("\n\nDone!")
