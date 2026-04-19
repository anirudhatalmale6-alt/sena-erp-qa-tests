#!/usr/bin/env python3
"""
Rescan Sena ERP menu structure, compare with previous scan, and screenshot new pages.
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

BASE_URL = "http://13.210.47.18:8088"
OLD_MENU_PATH = "/var/lib/freelancer/projects/40298427/erp-test/menu_structure.json"
NEW_MENU_PATH = "/var/lib/freelancer/projects/40298427/erp-test/menu_structure_v2.json"
SCREENSHOT_DIR = "/var/lib/freelancer/projects/40298427/erp-test/screenshots/new_sections"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def extract_all_urls(menu_items, prefix=""):
    """Recursively extract all URLs with their labels from menu structure."""
    urls = {}
    for item in menu_items:
        text = item.get("text", "")
        href = item.get("href", "#")
        path = f"{prefix} > {text}" if prefix else text

        if href and href != "#":
            urls[href] = path

        # Check subItems (new format)
        for sub in item.get("subItems", []):
            sub_text = sub.get("text", "")
            sub_href = sub.get("href", "#")
            sub_path = f"{path} > {sub_text}"

            if sub_href and sub_href != "#":
                urls[sub_href] = sub_path

            # Check sub-sub items
            for subsub in sub.get("subItems", []):
                subsub_text = subsub.get("text", "")
                subsub_href = subsub.get("href", "#")
                subsub_path = f"{sub_path} > {subsub_text}"
                if subsub_href and subsub_href != "#":
                    urls[subsub_href] = subsub_path

    return urls


def extract_old_urls(old_data):
    """Extract URLs from the old menu format (which may differ)."""
    urls = {}
    items = old_data if isinstance(old_data, list) else old_data.get("menu_tree", [])
    for item in items:
        text = item.get("text", "")
        href = item.get("href", "#")
        if href and href != "#":
            urls[href] = text
        for sub in item.get("subItems", []):
            sub_text = sub.get("text", "")
            sub_href = sub.get("href", "#")
            if sub_href and sub_href != "#":
                urls[sub_href] = f"{text} > {sub_text}"
            # sub-sub items in old format
            for subsub in sub.get("subItems", sub.get("subSubItems", [])):
                if isinstance(subsub, dict):
                    subsub_text = subsub.get("text", "")
                    subsub_href = subsub.get("href", "#")
                    if subsub_href and subsub_href != "#":
                        urls[subsub_href] = f"{text} > {sub_text} > {subsub_text}"
    return urls


def print_menu_tree(items, indent=0):
    """Print menu tree in readable format."""
    for item in items:
        text = item.get("text", "")
        href = item.get("href", "#")
        prefix = "  " * indent + ("├── " if indent > 0 else "")
        url_display = f" [{href}]" if href and href != "#" else ""
        print(f"{prefix}{text}{url_display}")
        for sub in item.get("subItems", []):
            sub_text = sub.get("text", "")
            sub_href = sub.get("href", "#")
            sub_prefix = "  " * (indent + 1) + "├── "
            sub_url = f" [{sub_href}]" if sub_href and sub_href != "#" else ""
            print(f"{sub_prefix}{sub_text}{sub_url}")
            for subsub in sub.get("subItems", []):
                subsub_text = subsub.get("text", "")
                subsub_href = subsub.get("href", "#")
                subsub_prefix = "  " * (indent + 2) + "├── "
                subsub_url = f" [{subsub_href}]" if subsub_href and subsub_href != "#" else ""
                print(f"{subsub_prefix}{subsub_text}{subsub_url}")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()

        # ---- LOGIN ----
        print("=" * 70)
        print("SENA ERP MENU RESCAN")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        print("\n[1] Logging in...")
        await page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        await page.evaluate("""
            document.getElementById("username").value = "superadmin";
            document.getElementById("password").value = "Nick@#24";
            document.getElementById("signupForm").submit();
        """)
        await page.wait_for_timeout(8000)
        print(f"    Current URL: {page.url}")

        # ---- EXTRACT MENU ----
        print("\n[2] Extracting sidebar menu...")
        menu_data = await page.evaluate("""() => {
            const items = [];
            document.querySelectorAll('.sidebar-menu > .nav-item').forEach(item => {
                const link = item.querySelector(':scope > .nav-link');
                if (!link) return;
                const text = link.querySelector('p') ? link.querySelector('p').textContent.trim() : link.textContent.trim();
                const href = link.getAttribute('href') || '#';
                const subItems = [];
                item.querySelectorAll(':scope > .nav-treeview > .nav-item').forEach(sub => {
                    const subLink = sub.querySelector(':scope > .nav-link');
                    if (!subLink) return;
                    const subText = subLink.querySelector('p') ? subLink.querySelector('p').textContent.trim() : subLink.textContent.trim();
                    const subHref = subLink.getAttribute('href') || '#';
                    const subSubItems = [];
                    sub.querySelectorAll(':scope > .nav-treeview > .nav-item').forEach(subsub => {
                        const ssubLink = subsub.querySelector(':scope > .nav-link');
                        if (!ssubLink) return;
                        const ssubText = ssubLink.querySelector('p') ? ssubLink.querySelector('p').textContent.trim() : ssubLink.textContent.trim();
                        const ssubHref = ssubLink.getAttribute('href') || '#';
                        subSubItems.push({text: ssubText, href: ssubHref});
                    });
                    subItems.push({text: subText, href: subHref, subItems: subSubItems});
                });
                items.push({text: text, href: href, subItems: subItems});
            });
            return items;
        }""")

        # Save new menu
        with open(NEW_MENU_PATH, "w") as f:
            json.dump(menu_data, f, indent=2)
        print(f"    Saved to: {NEW_MENU_PATH}")

        # Count items
        total_top = len(menu_data)
        total_sub = sum(len(item.get("subItems", [])) for item in menu_data)
        total_subsub = sum(
            len(sub.get("subItems", []))
            for item in menu_data
            for sub in item.get("subItems", [])
        )
        print(f"    Top-level items: {total_top}")
        print(f"    Sub-items: {total_sub}")
        print(f"    Sub-sub-items: {total_subsub}")
        print(f"    Total: {total_top + total_sub + total_subsub}")

        # ---- PRINT FULL TREE ----
        print("\n[3] Full Menu Tree:")
        print("-" * 70)
        print_menu_tree(menu_data)
        print("-" * 70)

        # ---- COMPARE WITH OLD ----
        print("\n[4] Comparing with old menu...")
        new_urls = extract_all_urls(menu_data)

        old_urls = {}
        if os.path.exists(OLD_MENU_PATH):
            with open(OLD_MENU_PATH, "r") as f:
                old_data = json.load(f)
            old_urls = extract_old_urls(old_data)
            print(f"    Old menu URLs: {len(old_urls)}")
        else:
            print("    WARNING: Old menu file not found!")

        print(f"    New menu URLs: {len(new_urls)}")

        # Find differences
        added_urls = {url: label for url, label in new_urls.items() if url not in old_urls}
        removed_urls = {url: label for url, label in old_urls.items() if url not in new_urls}

        print(f"\n    NEW items ({len(added_urls)}):")
        if added_urls:
            for url, label in sorted(added_urls.items(), key=lambda x: x[1]):
                print(f"      + {label}")
                print(f"        {url}")
        else:
            print("      (none)")

        print(f"\n    REMOVED items ({len(removed_urls)}):")
        if removed_urls:
            for url, label in sorted(removed_urls.items(), key=lambda x: x[1]):
                print(f"      - {label}")
                print(f"        {url}")
        else:
            print("      (none)")

        # ---- SCREENSHOT NEW PAGES ----
        if added_urls:
            print(f"\n[5] Scanning {len(added_urls)} new page(s)...")
            new_page_results = []

            for url, label in sorted(added_urls.items(), key=lambda x: x[1]):
                print(f"\n    Navigating: {label}")
                print(f"    URL: {url}")

                result = {
                    "label": label,
                    "url": url,
                    "title": "",
                    "status": "unknown",
                    "has_table": False,
                    "has_form": False,
                    "has_buttons": False,
                    "screenshot": "",
                    "error": ""
                }

                try:
                    response = await page.goto(url, wait_until="networkidle", timeout=20000)
                    status = response.status if response else "no response"
                    result["status"] = status
                    await page.wait_for_timeout(2000)

                    result["title"] = await page.title()

                    # Check page elements
                    page_info = await page.evaluate("""
                        () => ({
                            hasTable: document.querySelectorAll('table').length > 0,
                            hasForm: document.querySelectorAll('form').length > 0,
                            hasButtons: document.querySelectorAll('button, .btn, input[type="submit"]').length > 0,
                            tableCount: document.querySelectorAll('table').length,
                            formCount: document.querySelectorAll('form').length,
                            buttonCount: document.querySelectorAll('button, .btn, input[type="submit"]').length
                        })
                    """)
                    result["has_table"] = page_info["hasTable"]
                    result["has_form"] = page_info["hasForm"]
                    result["has_buttons"] = page_info["hasButtons"]

                    # Screenshot
                    safe_name = label.replace(" > ", "_").replace(" ", "_").replace("/", "_")[:60]
                    screenshot_path = os.path.join(SCREENSHOT_DIR, f"{safe_name}.png")
                    await page.screenshot(path=screenshot_path, full_page=False)
                    result["screenshot"] = screenshot_path

                    print(f"    Status: {status} | Title: {result['title']}")
                    print(f"    Tables: {page_info['tableCount']}, Forms: {page_info['formCount']}, Buttons: {page_info['buttonCount']}")
                    print(f"    Screenshot: {screenshot_path}")

                except Exception as e:
                    result["error"] = str(e)
                    print(f"    ERROR: {e}")

                new_page_results.append(result)

            # Save results
            results_path = os.path.join(SCREENSHOT_DIR, "new_pages_report.json")
            with open(results_path, "w") as f:
                json.dump(new_page_results, f, indent=2)
            print(f"\n    Results saved: {results_path}")
        else:
            print("\n[5] No new pages to scan.")

        # ---- SUMMARY ----
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total menu items (v2): {total_top + total_sub + total_subsub}")
        print(f"Total navigable URLs (v2): {len(new_urls)}")
        print(f"Total navigable URLs (v1): {len(old_urls)}")
        print(f"New pages: {len(added_urls)}")
        print(f"Removed pages: {len(removed_urls)}")
        print(f"Menu saved to: {NEW_MENU_PATH}")
        print("=" * 70)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
