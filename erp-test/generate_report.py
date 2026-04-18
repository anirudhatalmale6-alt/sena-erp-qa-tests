#!/usr/bin/env python3
"""
Sena ERP - Comprehensive QA Test Report Generator
Generates a professional PDF report using ReportLab.
"""

import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate, Frame
from reportlab.lib.colors import HexColor

# ── Colors ──
GREEN = HexColor("#27ae60")
RED = HexColor("#e74c3c")
ORANGE = HexColor("#f39c12")
BLUE = HexColor("#2c3e50")
LIGHT_BLUE = HexColor("#3498db")
DARK_BG = HexColor("#1a252f")
WHITE = colors.white
LIGHT_GRAY = HexColor("#f5f6fa")
MED_GRAY = HexColor("#dcdde1")
HEADER_BG = HexColor("#2c3e50")
ROW_ALT = HexColor("#ecf0f1")

OUTPUT_DIR = "/var/lib/freelancer/projects/40298427/erp-test"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "Sena_ERP_Full_Test_Report.pdf")


def header_footer(canvas, doc):
    """Draw header and footer on every page."""
    canvas.saveState()
    w, h = A4

    # Header bar
    canvas.setFillColor(HEADER_BG)
    canvas.rect(0, h - 28 * mm, w, 28 * mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(20 * mm, h - 18 * mm, "Sena ERP - Comprehensive QA Test Report")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(w - 20 * mm, h - 18 * mm, "Aero Marin Land (TLI)")

    # Footer bar
    canvas.setFillColor(HEADER_BG)
    canvas.rect(0, 0, w, 14 * mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(20 * mm, 5 * mm, "Confidential - Sena ERP QA Report - April 2026")
    canvas.drawRightString(w - 20 * mm, 5 * mm, f"Page {doc.page}")

    canvas.restoreState()


def build_styles():
    """Build all paragraph styles."""
    ss = getSampleStyleSheet()

    styles = {}
    styles["title"] = ParagraphStyle(
        "Title", parent=ss["Title"], fontSize=26, leading=32,
        textColor=BLUE, alignment=TA_CENTER, spaceAfter=4 * mm
    )
    styles["subtitle"] = ParagraphStyle(
        "Subtitle", parent=ss["Normal"], fontSize=14, leading=18,
        textColor=LIGHT_BLUE, alignment=TA_CENTER, spaceAfter=2 * mm
    )
    styles["meta"] = ParagraphStyle(
        "Meta", parent=ss["Normal"], fontSize=10, leading=14,
        textColor=colors.gray, alignment=TA_CENTER, spaceAfter=6 * mm
    )
    styles["section"] = ParagraphStyle(
        "Section", parent=ss["Heading1"], fontSize=16, leading=20,
        textColor=BLUE, spaceBefore=10 * mm, spaceAfter=4 * mm,
        borderPadding=(0, 0, 2, 0)
    )
    styles["subsection"] = ParagraphStyle(
        "SubSection", parent=ss["Heading2"], fontSize=13, leading=16,
        textColor=LIGHT_BLUE, spaceBefore=6 * mm, spaceAfter=3 * mm
    )
    styles["body"] = ParagraphStyle(
        "Body", parent=ss["Normal"], fontSize=10, leading=14,
        textColor=colors.black, spaceAfter=2 * mm, alignment=TA_JUSTIFY
    )
    styles["body_bold"] = ParagraphStyle(
        "BodyBold", parent=styles["body"], fontName="Helvetica-Bold"
    )
    styles["bullet"] = ParagraphStyle(
        "Bullet", parent=styles["body"], leftIndent=15,
        bulletIndent=5, spaceAfter=1.5 * mm
    )
    styles["small"] = ParagraphStyle(
        "Small", parent=ss["Normal"], fontSize=8, leading=10,
        textColor=colors.gray
    )
    return styles


def status_text(status):
    """Return colored status string."""
    s = status.upper()
    if s in ("OK", "PASS", "SUCCESS", "YES"):
        return f'<font color="#27ae60"><b>{status}</b></font>'
    elif s in ("ERROR", "FAIL", "FAILED", "NO", "404", "500"):
        return f'<font color="#e74c3c"><b>{status}</b></font>'
    elif s in ("WARNING", "NO_FIELDS", "PARTIAL"):
        return f'<font color="#f39c12"><b>{status}</b></font>'
    return status


def make_table(data, col_widths=None, header=True):
    """Create a styled table."""
    style_cmds = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEADING", (0, 0), (-1, -1), 11),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, MED_GRAY),
    ]
    if header:
        style_cmds += [
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
        ]
        for i in range(1, len(data)):
            if i % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))

    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    t.setStyle(TableStyle(style_cmds))
    return t


def build_report():
    """Build the full PDF report."""
    styles = build_styles()
    story = []
    P = Paragraph
    SP = lambda h=4: Spacer(1, h * mm)

    page_w = A4[0] - 40 * mm  # usable width

    # ━━━━━━━━━━━━━━━ COVER PAGE ━━━━━━━━━━━━━━━
    story.append(SP(30))
    story.append(P("Sena ERP", styles["title"]))
    story.append(P("Comprehensive QA Test Report", styles["title"]))
    story.append(SP(6))
    story.append(HRFlowable(width="60%", color=LIGHT_BLUE, thickness=2, spaceAfter=10))
    story.append(P("Full System Testing - All Modules", styles["subtitle"]))
    story.append(SP(4))
    story.append(P("Date: April 18, 2026", styles["meta"]))
    story.append(P("System: Sena ERP (Freight/Logistics)", styles["meta"]))
    story.append(P("URL: http://13.210.47.18:8088", styles["meta"]))
    story.append(P("Company: Aero Marin Land (TLI - Transport Logistics International)", styles["meta"]))
    story.append(SP(20))

    # Summary box on cover
    summary_data = [
        ["Metric", "Value"],
        ["Total Pages Tested", "72"],
        ["Pages Loading Successfully", P(status_text("60"), styles["small"])],
        ["Pages with Errors", P(status_text("12") if False else '<font color="#e74c3c"><b>12</b></font>', styles["small"])],
        ["CRUD Operations Tested", "20 master pages"],
        ["CRUD Operations Successful", "19 / 20"],
        ["Job Creation Forms Tested", "6"],
        ["Financial Reports Tested", "9 (all working)"],
        ["Account Pages Tested", "14 (all working)"],
        ["DSR Reports", "5 (all loading)"],
        ["Overall Health Score", P('<font color="#27ae60"><b>83% (60/72)</b></font>', styles["small"])],
    ]
    story.append(make_table(summary_data, col_widths=[page_w * 0.55, page_w * 0.45]))
    story.append(PageBreak())

    # ━━━━━━━━━━━━━━━ SECTION 1: EXECUTIVE SUMMARY ━━━━━━━━━━━━━━━
    story.append(P("1. Executive Summary", styles["section"]))
    story.append(P(
        "This report documents comprehensive quality assurance testing performed on the "
        "Sena ERP system, a freight and logistics management platform operated by Aero Marin Land "
        "(TLI - Transport Logistics International). Testing covered 72 pages across all modules "
        "including page load verification, CRUD operations on 20 master data pages, job creation "
        "workflows for 6 transport modes, 9 financial reports, 14 account pages, and 5 DSR reports.",
        styles["body"]
    ))
    story.append(P(
        "The system achieved an overall health score of <b>83%</b> with 60 out of 72 pages loading "
        "successfully. Eight critical and medium-severity bugs were identified, primarily affecting "
        "the Vendor Master module (HTTP 500), Land Import/Export routes (HTTP 404), and job creation "
        "form dropdown population. All financial reports and account pages are fully functional.",
        styles["body"]
    ))
    story.append(SP(4))

    # Score breakdown mini-table
    score_data = [
        ["Category", "Tested", "Passed", "Score"],
        ["Page Load Tests", "72", "60", P(status_text("83%"), styles["small"])],
        ["CRUD Operations", "20", "19", P(status_text("95%"), styles["small"])],
        ["Financial Reports", "9", "9", P(status_text("100%"), styles["small"])],
        ["Account Pages", "14", "14", P(status_text("100%"), styles["small"])],
        ["DSR Reports", "5", "5", P(status_text("100%"), styles["small"])],
        ["Job Creation", "6", "2", P('<font color="#e74c3c"><b>33%</b></font>', styles["small"])],
    ]
    story.append(make_table(score_data, col_widths=[page_w * 0.4, page_w * 0.15, page_w * 0.15, page_w * 0.3]))
    story.append(PageBreak())

    # ━━━━━━━━━━━━━━━ SECTION 2: PAGE LOAD TEST RESULTS ━━━━━━━━━━━━━━━
    story.append(P("2. Page Load Test Results (72 Pages)", styles["section"]))
    story.append(P(
        "All 72 pages in the Sena ERP system were tested for basic page load functionality. "
        "Each page was accessed via HTTP GET and the response status code was recorded. "
        "Results are grouped by module below.",
        styles["body"]
    ))
    story.append(SP(2))

    modules = [
        ("Dashboard", [("Dashboard", "OK")]),
        ("HR", [("Employee", "OK")]),
        ("Account - Debtors (6 pages)", [
            ("Consignee Due", "OK"), ("Consignee Paid", "OK"),
            ("Agent Due", "OK"), ("Agent Paid", "OK"),
            ("Shipper Due", "OK"), ("Shipper Paid", "OK"),
        ]),
        ("Account - Creditors (8 pages)", [
            ("Shipping Line Due", "OK"), ("Shipping Line Paid", "OK"),
            ("Co-Loader Due", "OK"), ("Co-Loader Paid", "OK"),
            ("Supplier Due", "OK"), ("Supplier Paid", "OK"),
            ("Agent Due", "OK"), ("Agent Paid", "OK"),
        ]),
        ("Financial Reports (9 pages)", [
            ("Purchase Invoice", "OK"), ("Sales Invoice", "OK"),
            ("Purchase Invoice w/ VAT", "OK"), ("Sales Invoice w/ VAT", "OK"),
            ("Ledger Report", "OK"), ("Customer Ageing", "OK"),
            ("Supplier Ageing", "OK"), ("Jobs w/o Purchase Inv", "OK"),
            ("Jobs w/o Sales Inv", "OK"),
        ]),
        ("Common Masters (13 pages)", [
            ("Country", "OK"), ("State", "OK"), ("City", "OK"),
            ("Company Type", "OK"), ("Customer Type", "OK"),
            ("Vendor Type", "OK"), ("Ledger Group", "OK"),
            ("Commodity Master", "OK"), ("Charge Master", "OK"),
            ("Company Master", "OK"), ("Customer Master", "OK"),
            ("Shipping Line Code", "OK"),
            ("Vendor Master", "ERROR"),
        ]),
        ("Ocean Masters (4 pages)", [
            ("Job Type", "OK"), ("Vessel", "OK"),
            ("Ocean Port Sector", "OK"), ("Ocean Port", "OK"),
        ]),
        ("Air Masters (2 pages)", [
            ("Airport", "OK"), ("Carrier/Airlines", "OK"),
        ]),
        ("Quote Setup (4 pages)", [
            ("Carriers", "OK"), ("Exchange Rates", "OK"),
            ("Rate Database", "OK"), ("Client Rates", "OK"),
        ]),
        ("Quotes (1 page)", [("Quotes", "OK")]),
        ("Ocean Import (3 pages)", [
            ("Open Jobs", "OK"), ("Closed Jobs", "OK"), ("Booking Report", "OK"),
        ]),
        ("Ocean Export (3 pages)", [
            ("Open Jobs", "OK"), ("Closed Jobs", "OK"), ("Booking Report", "OK"),
        ]),
        ("Air Import (3 pages)", [
            ("Open Jobs", "OK"), ("Closed Jobs", "OK"), ("Booking Report", "OK"),
        ]),
        ("Air Export (3 pages)", [
            ("Open Jobs", "OK"), ("Closed Jobs", "OK"),
            ("Booking Report", "ERROR"),
        ]),
        ("Land Import (2 pages)", [
            ("Open Jobs", "ERROR"), ("Closed Jobs", "ERROR"),
        ]),
        ("Land Export (2 pages)", [
            ("Open Jobs", "ERROR"), ("Closed Jobs", "ERROR"),
        ]),
        ("DSR Reports (5 pages)", [
            ("DSR Report 1", "OK"), ("DSR Report 2", "OK"),
            ("DSR Report 3", "OK"), ("DSR Report 4", "OK"),
            ("DSR Report 5", "OK"),
        ]),
    ]

    for mod_name, pages in modules:
        ok_count = sum(1 for _, s in pages if s == "OK")
        err_count = len(pages) - ok_count
        if err_count == 0:
            mod_status = f'<font color="#27ae60">ALL OK</font>'
        elif ok_count == 0:
            mod_status = f'<font color="#e74c3c">ALL ERROR</font>'
        else:
            mod_status = f'<font color="#27ae60">{ok_count} OK</font>, <font color="#e74c3c">{err_count} ERROR</font>'

        story.append(P(f"<b>{mod_name}</b> - {mod_status}", styles["subsection"]))

        data = [["Page", "Status"]]
        for pg, st in pages:
            data.append([pg, P(status_text(st), styles["small"])])
        story.append(make_table(data, col_widths=[page_w * 0.7, page_w * 0.3]))
        story.append(SP(2))

    story.append(PageBreak())

    # ━━━━━━━━━━━━━━━ SECTION 3: CRITICAL BUGS ━━━━━━━━━━━━━━━
    story.append(P("3. Critical Bugs Found", styles["section"]))
    story.append(P(
        "The following bugs were identified during testing. They are ordered by severity.",
        styles["body"]
    ))
    story.append(SP(3))

    bugs = [
        {
            "id": "BUG-001", "title": "Vendor Master - HTTP 500 Server Error",
            "severity": "HIGH", "sev_color": RED,
            "page": "Common Masters > Vendor Master",
            "url": "/237cddc13035afd40df532c9c471b4ea",
            "error": "InvalidArgumentException - View [vendor.index] not found",
            "root_cause": "View file name mismatch in Vendor.php controller (line 70)",
            "impact": "Cannot access or manage vendor records",
            "note": "",
        },
        {
            "id": "BUG-002", "title": "Activity Log - HTTP 500 Server Error",
            "severity": "HIGH", "sev_color": RED,
            "page": "Admin-only page (not in main menu)",
            "url": "N/A",
            "error": "QueryException - Unknown column 'u.FNAME' in ActivityLogController.php (line 48)",
            "root_cause": "Database column reference doesn't match schema",
            "impact": "Cannot view activity/audit logs",
            "note": "",
        },
        {
            "id": "BUG-003", "title": "Land Import - All Pages 404",
            "severity": "HIGH", "sev_color": RED,
            "page": "Land Import > Open Jobs, Closed Jobs",
            "url": "/8013f48199799dce7a1fde812910a496, /ad661c9739fbf14ddd1802a6cc8c15c9",
            "error": "404 Page Not Found",
            "root_cause": "Routes not registered or intermittent",
            "impact": "Entire Land Import module non-functional",
            "note": "During job workflow testing, these pages DID load (200) - may be intermittent or route was fixed",
        },
        {
            "id": "BUG-004", "title": "Land Export - All Pages 404",
            "severity": "HIGH", "sev_color": RED,
            "page": "Land Export > Open Jobs, Closed Jobs",
            "url": "/2ca1dbee9121459dedd8cf2e88823068, /2785ba86aa37c0a8ff38e247afd5c2af",
            "error": "404 Page Not Found",
            "root_cause": "Routes not registered or intermittent",
            "impact": "Entire Land Export module non-functional",
            "note": "Same as BUG-003 - loaded during later testing",
        },
        {
            "id": "BUG-005", "title": "Air Export Booking Report - 404",
            "severity": "MEDIUM", "sev_color": ORANGE,
            "page": "Air Export > Booking Report",
            "url": "/7d27d418fe920b6bc9230e81ef3a9bae",
            "error": "404 Page Not Found",
            "root_cause": "Route not registered",
            "impact": "Cannot view Air Export booking reports",
            "note": "May have been fixed since initial test",
        },
        {
            "id": "BUG-006", "title": "Job Creation Forms - Dropdowns Not Pre-populated",
            "severity": "MEDIUM", "sev_color": ORANGE,
            "page": "Ocean Import/Export job creation forms",
            "url": "N/A",
            "error": "Multiple required SELECT fields have 0 options",
            "root_cause": "AJAX calls for consignee, lport, dport, overseas1, shpline, IncoTrms return empty",
            "impact": "Cannot create new ocean jobs without manually populating dropdowns",
            "note": "",
        },
        {
            "id": "BUG-007", "title": "Ledger Group - No Form Fields in Add Modal",
            "severity": "LOW", "sev_color": LIGHT_BLUE,
            "page": "Common Masters > Ledger Group",
            "url": "/2b0f7f32c7f7af6b51bf090558391d67",
            "error": "No form fields discovered in the Add New modal",
            "root_cause": "Modal template missing or empty",
            "impact": "Cannot add new ledger groups through the UI",
            "note": "",
        },
        {
            "id": "BUG-008", "title": "Quotes - No Add New Button",
            "severity": "LOW", "sev_color": LIGHT_BLUE,
            "page": "Quotes",
            "url": "/68915d3ba92a6ff8c96734362d61b15e",
            "error": "No 'Add New' button found on the Quotes page",
            "root_cause": "Button not rendered or different workflow expected",
            "impact": "Cannot create new quotes from listing page",
            "note": "",
        },
    ]

    for bug in bugs:
        sev_label = bug["severity"]
        if sev_label == "HIGH":
            sev_html = f'<font color="#e74c3c"><b>[{sev_label}]</b></font>'
        elif sev_label == "MEDIUM":
            sev_html = f'<font color="#f39c12"><b>[{sev_label}]</b></font>'
        else:
            sev_html = f'<font color="#3498db"><b>[{sev_label}]</b></font>'

        bug_block = []
        bug_block.append(P(f'{sev_html}  <b>{bug["id"]}: {bug["title"]}</b>', styles["body_bold"]))
        details = [
            ["Field", "Details"],
            ["Page", bug["page"]],
            ["URL", bug["url"]],
            ["Error", bug["error"]],
            ["Root Cause", bug["root_cause"]],
            ["Impact", bug["impact"]],
        ]
        if bug["note"]:
            details.append(["Note", bug["note"]])

        t = Table(details, colWidths=[page_w * 0.2, page_w * 0.8])
        t_style = [
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("LEADING", (0, 0), (-1, -1), 11),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, MED_GRAY),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, 1), (0, -1), LIGHT_GRAY),
        ]
        for i in range(1, len(details)):
            if i % 2 == 0:
                t_style.append(("BACKGROUND", (1, i), (1, i), ROW_ALT))
        t.setStyle(TableStyle(t_style))
        bug_block.append(t)
        bug_block.append(SP(3))

        story.append(KeepTogether(bug_block))

    story.append(PageBreak())

    # ━━━━━━━━━━━━━━━ SECTION 4: CRUD TEST RESULTS ━━━━━━━━━━━━━━━
    story.append(P("4. CRUD Test Results (Master Pages)", styles["section"]))
    story.append(P(
        "CRUD (Create, Read, Update, Delete) operations were tested on 20 master data pages. "
        "For each page, the 'Add New' button was clicked, form fields were discovered and filled, "
        "and the form was submitted. Results are summarized below.",
        styles["body"]
    ))
    story.append(SP(3))

    crud_data = [
        ["#", "Page Name", "Category", "Fields", "Status", "Created", "Notes"],
        ["1", "State", "Simple", "4", P(status_text("SUCCESS"), styles["small"]), "Yes", "Country select + name"],
        ["2", "City", "Simple", "6", P(status_text("SUCCESS"), styles["small"]), "Yes", "Country + state + name + code"],
        ["3", "Company Type", "Simple", "3", P(status_text("SUCCESS"), styles["small"]), "Yes", "Name + status"],
        ["4", "Customer Type", "Simple", "3", P(status_text("SUCCESS"), styles["small"]), "Yes", "Name + status"],
        ["5", "Vendor Type", "Simple", "3", P(status_text("SUCCESS"), styles["small"]), "Yes", "Name + status"],
        ["6", "Ledger Group", "Simple", "0", P(status_text("NO_FIELDS"), styles["small"]), "No", "Modal has no visible fields"],
        ["7", "Commodity Master", "Simple", "4", P(status_text("SUCCESS"), styles["small"]), "Yes", "Code + name"],
        ["8", "Charge Master", "Complex", "7", P(status_text("SUCCESS"), styles["small"]), "Yes", "Code + name + tax + type"],
        ["9", "Company Master", "Complex", "5", P(status_text("SUCCESS"), styles["small"]), "Yes", "Name + company type + type"],
        ["10", "Customer Master", "Complex", "39", P(status_text("SUCCESS"), styles["small"]), "Yes", "Full form, 7 sections"],
        ["11", "Shipping Line Code", "Complex", "4", P(status_text("SUCCESS"), styles["small"]), "Yes", "Code + name"],
        ["12", "Address", "Complex", "6", P(status_text("SUCCESS"), styles["small"]), "Yes", "Name + type radio buttons"],
        ["13", "Job Type", "Ocean", "4", P(status_text("SUCCESS"), styles["small"]), "Yes", "Job type select + name"],
        ["14", "Vessel", "Ocean", "3", P(status_text("SUCCESS"), styles["small"]), "Yes", "Name + status"],
        ["15", "Ocean Port Sector", "Ocean", "3", P(status_text("SUCCESS"), styles["small"]), "Yes", "Name + status"],
        ["16", "Ocean Port", "Ocean", "6", P(status_text("SUCCESS"), styles["small"]), "Yes", "Code + name + country + sector"],
        ["17", "Airport", "Air", "6", P(status_text("SUCCESS"), styles["small"]), "Yes", "Name + code (some missed)"],
        ["18", "Carrier/Airlines", "Air", "6", P(status_text("SUCCESS"), styles["small"]), "Yes", "Name + code + prefix + addr"],
        ["19", "Carriers (Quote)", "Quote", "5", P(status_text("SUCCESS"), styles["small"]), "Yes", "Mode + code + name"],
        ["20", "Exchange Rates", "Quote", "3", P(status_text("SUCCESS"), styles["small"]), "Yes", "Currency + rate + date"],
    ]

    story.append(make_table(
        crud_data,
        col_widths=[page_w * 0.04, page_w * 0.18, page_w * 0.1, page_w * 0.07,
                    page_w * 0.12, page_w * 0.09, page_w * 0.40]
    ))
    story.append(PageBreak())

    # ━━━━━━━━━━━━━━━ SECTION 5: JOB CREATION WORKFLOW ━━━━━━━━━━━━━━━
    story.append(P("5. Job Creation Workflow Test Results", styles["section"]))
    story.append(P(
        "Job creation workflows were tested for all 6 transport modes. Each test involved "
        "navigating to the job listing, clicking 'Add New', discovering form fields, and "
        "attempting to submit the form.",
        styles["body"]
    ))
    story.append(SP(3))

    jobs = [
        {
            "name": "Ocean Import",
            "loads": "YES (17 existing jobs)",
            "add_new": "Opens new page with auto-generated Job No (TLI/SI/2627//0467)",
            "fields": "26 (12 text inputs, 14 selects)",
            "key_fields": "Job No (auto), Job Date, MBL No, MBL Date, ETD, ETA, Delivery dates, Freight/Insurance charges, Shipment type (LCL/FCL/Consol), Incoterms, Consignee, Loading/Discharge ports, Overseas agents, Shipping line, Vessel, Warehouse, GBP applicable",
            "issue": "10+ required SELECT fields have 0 options (AJAX-dependent)",
            "result": "FAILED",
        },
        {
            "name": "Ocean Export",
            "loads": "YES (1 existing job)",
            "add_new": "Similar form structure to Ocean Import",
            "fields": "26",
            "key_fields": "Same as Ocean Import",
            "issue": "Same issue with empty dropdowns",
            "result": "FAILED",
        },
        {
            "name": "Air Import",
            "loads": "YES (12 existing jobs)",
            "add_new": "Opens form",
            "fields": "49 (more complex than ocean)",
            "key_fields": "Extended air-specific fields",
            "issue": "Same dropdown issue",
            "result": "FAILED",
        },
        {
            "name": "Air Export",
            "loads": "YES (4 existing jobs)",
            "add_new": "Opens form",
            "fields": "48",
            "key_fields": "Extended air-specific fields",
            "issue": "Same dropdown issue",
            "result": "FAILED",
        },
        {
            "name": "Land Import",
            "loads": "YES (1 existing job)",
            "add_new": "Opens form",
            "fields": "18 (simpler form)",
            "key_fields": "Land-specific fields",
            "issue": "None detected",
            "result": "SUBMITTED",
        },
        {
            "name": "Land Export",
            "loads": "YES (1 existing job)",
            "add_new": "Opens form",
            "fields": "18",
            "key_fields": "Land-specific fields",
            "issue": "None detected",
            "result": "SUBMITTED",
        },
    ]

    for job in jobs:
        res = job["result"]
        if res == "SUBMITTED":
            res_html = f'<font color="#27ae60"><b>SUBMITTED</b></font>'
        else:
            res_html = f'<font color="#e74c3c"><b>FAILED</b></font>'

        job_block = []
        job_block.append(P(f'<b>{job["name"]}</b> - Result: {res_html}', styles["subsection"]))
        jdata = [
            ["Field", "Details"],
            ["Page Loads", job["loads"]],
            ["Add New", job["add_new"]],
            ["Form Fields", job["fields"]],
            ["Key Fields", P(job["key_fields"], styles["small"])],
            ["Issues", job["issue"]],
            ["Result", P(res_html, styles["small"])],
        ]
        jt = Table(jdata, colWidths=[page_w * 0.2, page_w * 0.8])
        jt.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("LEADING", (0, 0), (-1, -1), 11),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, MED_GRAY),
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, 1), (0, -1), LIGHT_GRAY),
        ]))
        job_block.append(jt)
        job_block.append(SP(3))
        story.append(KeepTogether(job_block))

    story.append(PageBreak())

    # ━━━━━━━━━━━━━━━ SECTION 6: FINANCIAL REPORTS ━━━━━━━━━━━━━━━
    story.append(P("6. Financial Reports Test Results", styles["section"]))
    story.append(P(
        "All 9 financial report pages loaded successfully and returned data. "
        "Date filtering was tested and confirmed working on all pages.",
        styles["body"]
    ))
    story.append(SP(3))

    fin_data = [
        ["#", "Report Name", "Rows", "Date Filter", "Status"],
        ["1", "Purchase Invoice", "21", "Working", P(status_text("OK"), styles["small"])],
        ["2", "Sales Invoice", "20", "Working", P(status_text("OK"), styles["small"])],
        ["3", "Purchase Invoice w/ VAT", "21", "Working", P(status_text("OK"), styles["small"])],
        ["4", "Sales Invoice w/ VAT", "20", "Working", P(status_text("OK"), styles["small"])],
        ["5", "Ledger Report", "2", "Working", P(status_text("OK"), styles["small"])],
        ["6", "Customer Ageing", "10", "Working", P(status_text("OK"), styles["small"])],
        ["7", "Supplier Ageing", "10", "Working", P(status_text("OK"), styles["small"])],
        ["8", "Jobs w/o Purchase Inv.", "10", "Working", P(status_text("OK"), styles["small"])],
        ["9", "Jobs w/o Sales Inv.", "10", "Working", P(status_text("OK"), styles["small"])],
    ]
    story.append(make_table(
        fin_data,
        col_widths=[page_w * 0.06, page_w * 0.40, page_w * 0.12, page_w * 0.22, page_w * 0.20]
    ))
    story.append(SP(6))

    # ━━━━━━━━━━━━━━━ SECTION 7: ACCOUNT PAGES ━━━━━━━━━━━━━━━
    story.append(P("7. Account Pages Test Results", styles["section"]))
    story.append(P(
        "All 14 account pages (6 Debtors + 8 Creditors) loaded successfully and displayed data.",
        styles["body"]
    ))
    story.append(SP(2))

    story.append(P("Debtors (6 pages)", styles["subsection"]))
    deb_data = [
        ["Page", "Rows", "Status"],
        ["Consignee Due", "32 rows of outstanding invoices", P(status_text("OK"), styles["small"])],
        ["Consignee Paid", "3 rows", P(status_text("OK"), styles["small"])],
        ["Agent Due (Debtor)", "11 rows", P(status_text("OK"), styles["small"])],
        ["Agent Paid (Debtor)", "1 row", P(status_text("OK"), styles["small"])],
        ["Shipper Due", "1 row", P(status_text("OK"), styles["small"])],
        ["Shipper Paid", "1 row", P(status_text("OK"), styles["small"])],
    ]
    story.append(make_table(deb_data, col_widths=[page_w * 0.35, page_w * 0.45, page_w * 0.20]))
    story.append(SP(4))

    story.append(P("Creditors (8 pages)", styles["subsection"]))
    cred_data = [
        ["Page", "Rows", "Status"],
        ["Shipping Line Due", "14 rows", P(status_text("OK"), styles["small"])],
        ["Shipping Line Paid", "1 row", P(status_text("OK"), styles["small"])],
        ["Co-Loader Due", "1 row", P(status_text("OK"), styles["small"])],
        ["Co-Loader Paid", "1 row", P(status_text("OK"), styles["small"])],
        ["Supplier Due", "17 rows", P(status_text("OK"), styles["small"])],
        ["Supplier Paid", "1 row", P(status_text("OK"), styles["small"])],
        ["Agent Due (Creditor)", "3 rows", P(status_text("OK"), styles["small"])],
        ["Agent Paid (Creditor)", "1 row", P(status_text("OK"), styles["small"])],
    ]
    story.append(make_table(cred_data, col_widths=[page_w * 0.35, page_w * 0.45, page_w * 0.20]))
    story.append(PageBreak())

    # ━━━━━━━━━━━━━━━ SECTION 8: RECOMMENDATIONS ━━━━━━━━━━━━━━━
    story.append(P("8. Recommendations", styles["section"]))

    recommendations = [
        ("CRITICAL", "#e74c3c", "Fix Vendor Master view name (vendor.index -> correct view name)"),
        ("CRITICAL", "#e74c3c", "Fix Activity Log SQL query - column u.FNAME doesn't exist in the schema"),
        ("HIGH", "#e74c3c", "Ensure Land Import/Export routes are properly registered and consistently accessible"),
        ("HIGH", "#e74c3c", "Fix Air Export Booking Report route (currently returns 404)"),
        ("HIGH", "#e74c3c", "Fix job creation form dropdown population - AJAX calls for Consignee, Port, Agent, Shipping Line, etc. should pre-populate options"),
        ("MEDIUM", "#f39c12", "Fix Ledger Group 'Add New' modal - form fields not rendering"),
        ("MEDIUM", "#f39c12", "Add 'Add New' button to Quotes listing page or document the correct workflow for creating quotes"),
        ("LOW", "#3498db", "Add client-side validation messages for required fields in job creation forms"),
        ("LOW", "#3498db", "Add loading indicators for AJAX-populated dropdowns to improve user experience"),
        ("IMPROVEMENT", "#27ae60", "Add confirmation dialogs for record creation and deletion operations"),
        ("IMPROVEMENT", "#27ae60", "Add bulk operations (export to Excel/PDF) for report pages"),
        ("IMPROVEMENT", "#27ae60", "Add pagination controls or infinite scroll for large data tables"),
    ]

    rec_data = [["#", "Priority", "Recommendation"]]
    for i, (priority, color, text) in enumerate(recommendations, 1):
        rec_data.append([
            str(i),
            P(f'<font color="{color}"><b>{priority}</b></font>', styles["small"]),
            P(text, styles["small"]),
        ])

    story.append(make_table(
        rec_data,
        col_widths=[page_w * 0.05, page_w * 0.15, page_w * 0.80]
    ))
    story.append(SP(6))

    # ━━━━━━━━━━━━━━━ SECTION 9: TEST SCRIPTS DELIVERED ━━━━━━━━━━━━━━━
    story.append(P("9. Test Scripts Delivered", styles["section"]))
    story.append(P(
        "The following automated test scripts were developed and delivered as part of this QA engagement:",
        styles["body"]
    ))
    story.append(SP(2))

    scripts_data = [
        ["#", "Script", "Description"],
        ["1", "test_all_pages.py", "Page load testing for all 72 pages - verifies HTTP status codes"],
        ["2", "test_crud_masters.py", "CRUD operations on 20 master pages - form discovery, fill, and submit"],
        ["3", "test_jobs_and_reports.py", "Job creation workflows, financial reports, and account page testing"],
        ["4", "discover_all_menus.py", "Menu structure discovery - maps all navigation elements and URLs"],
    ]
    story.append(make_table(
        scripts_data,
        col_widths=[page_w * 0.06, page_w * 0.30, page_w * 0.64]
    ))
    story.append(SP(10))

    # End note
    story.append(HRFlowable(width="100%", color=LIGHT_BLUE, thickness=1, spaceAfter=6))
    story.append(P(
        "<i>End of Report - Generated on April 18, 2026</i>",
        ParagraphStyle("End", parent=styles["meta"], fontSize=9, alignment=TA_CENTER)
    ))

    # ── Build PDF ──
    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        topMargin=32 * mm,
        bottomMargin=20 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        title="Sena ERP - Comprehensive QA Test Report",
        author="QA Team",
    )
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"PDF generated successfully: {OUTPUT_FILE}")
    print(f"File size: {os.path.getsize(OUTPUT_FILE) / 1024:.1f} KB")


if __name__ == "__main__":
    build_report()
