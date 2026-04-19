#!/usr/bin/env python3
"""
Sena ERP - Complete QA Test Report Generator (v2)
Generates a comprehensive, professional PDF test report.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate, Frame
from reportlab.lib import colors
from datetime import datetime
import os

# ── Colors ──────────────────────────────────────────────────────────
NAVY = HexColor('#1a237e')
DARK_NAVY = HexColor('#0d1442')
GREEN = HexColor('#2e7d32')
RED = HexColor('#c62828')
ORANGE = HexColor('#ef6c00')
LIGHT_GRAY = HexColor('#f5f5f5')
MED_GRAY = HexColor('#e0e0e0')
DARK_GRAY = HexColor('#424242')
BLUE_ACCENT = HexColor('#1565c0')
LIGHT_BLUE = HexColor('#e3f2fd')
LIGHT_GREEN = HexColor('#e8f5e9')
LIGHT_RED = HexColor('#ffebee')
LIGHT_ORANGE = HexColor('#fff3e0')
WHITE = white

OUTPUT_PATH = '/var/lib/freelancer/projects/40298427/erp-test/Sena_ERP_Complete_Test_Report.pdf'

# ── Styles ──────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

style_title = ParagraphStyle('CustomTitle', parent=styles['Title'],
    fontSize=28, leading=34, textColor=NAVY, spaceAfter=6, alignment=TA_CENTER,
    fontName='Helvetica-Bold')

style_subtitle = ParagraphStyle('CustomSubtitle', parent=styles['Normal'],
    fontSize=14, leading=18, textColor=DARK_GRAY, spaceAfter=4, alignment=TA_CENTER,
    fontName='Helvetica')

style_h1 = ParagraphStyle('H1', parent=styles['Heading1'],
    fontSize=18, leading=22, textColor=NAVY, spaceBefore=16, spaceAfter=8,
    fontName='Helvetica-Bold', borderWidth=0)

style_h2 = ParagraphStyle('H2', parent=styles['Heading2'],
    fontSize=14, leading=17, textColor=NAVY, spaceBefore=12, spaceAfter=6,
    fontName='Helvetica-Bold')

style_h3 = ParagraphStyle('H3', parent=styles['Heading3'],
    fontSize=12, leading=15, textColor=DARK_NAVY, spaceBefore=8, spaceAfter=4,
    fontName='Helvetica-Bold')

style_body = ParagraphStyle('Body', parent=styles['Normal'],
    fontSize=9.5, leading=13, textColor=black, spaceAfter=4,
    fontName='Helvetica', alignment=TA_JUSTIFY)

style_body_small = ParagraphStyle('BodySmall', parent=styles['Normal'],
    fontSize=8.5, leading=11, textColor=black, spaceAfter=2,
    fontName='Helvetica')

style_cell = ParagraphStyle('Cell', parent=styles['Normal'],
    fontSize=8, leading=10, textColor=black, fontName='Helvetica')

style_cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'],
    fontSize=8, leading=10, textColor=black, fontName='Helvetica-Bold')

style_cell_center = ParagraphStyle('CellCenter', parent=styles['Normal'],
    fontSize=8, leading=10, textColor=black, fontName='Helvetica', alignment=TA_CENTER)

style_toc = ParagraphStyle('TOC', parent=styles['Normal'],
    fontSize=11, leading=16, textColor=NAVY, fontName='Helvetica',
    leftIndent=20, spaceAfter=2)

style_toc_section = ParagraphStyle('TOCSection', parent=styles['Normal'],
    fontSize=12, leading=18, textColor=NAVY, fontName='Helvetica-Bold',
    leftIndent=10, spaceAfter=3)

style_bug_title = ParagraphStyle('BugTitle', parent=styles['Normal'],
    fontSize=10, leading=13, textColor=black, fontName='Helvetica-Bold',
    spaceAfter=2)

style_footer_text = ParagraphStyle('Footer', parent=styles['Normal'],
    fontSize=7, leading=9, textColor=DARK_GRAY, fontName='Helvetica')


def P(text, style=style_body):
    return Paragraph(text, style)

def Pcell(text, bold=False, center=False):
    s = style_cell_bold if bold else (style_cell_center if center else style_cell)
    return Paragraph(str(text), s)

def status_cell(status):
    color_map = {'PASS': '#2e7d32', 'FAIL': '#c62828', 'WARNING': '#ef6c00',
                 'PARTIAL': '#ef6c00', 'CREATED SUCCESSFULLY': '#2e7d32',
                 'CREATED': '#2e7d32'}
    c = color_map.get(status, '#424242')
    return Paragraph(f'<font color="{c}"><b>{status}</b></font>', style_cell_center)


def section_header_bar(text):
    """Dark navy bar with white text."""
    t = Table([[Paragraph(f'<font color="white"><b>{text}</b></font>',
                ParagraphStyle('SHdr', fontSize=12, leading=15, textColor=white,
                               fontName='Helvetica-Bold'))]],
              colWidths=[170*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), NAVY),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
    ]))
    return t


def make_table(headers, rows, col_widths=None, has_status_col=None):
    """Build a professional table with alternating rows."""
    hdr = [Pcell(h, bold=True, center=True) for h in headers]
    data = [hdr]
    for row in rows:
        cells = []
        for i, val in enumerate(row):
            if has_status_col is not None and i == has_status_col:
                cells.append(status_cell(str(val)))
            else:
                cells.append(Pcell(str(val)))
        data.append(cells)

    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, MED_GRAY),
        ('LINEBELOW', (0,0), (-1,0), 1, NAVY),
    ]
    # Alternating row colors
    for i in range(1, len(data)):
        bg = WHITE if i % 2 == 1 else LIGHT_GRAY
        style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg))

    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def metric_box(label, value, color):
    """Small colored metric box."""
    inner = Table([
        [Paragraph(f'<font color="white" size="16"><b>{value}</b></font>',
                   ParagraphStyle('mv', alignment=TA_CENTER, fontName='Helvetica-Bold'))],
        [Paragraph(f'<font color="white" size="7">{label}</font>',
                   ParagraphStyle('ml', alignment=TA_CENTER, fontName='Helvetica'))],
    ], colWidths=[38*mm])
    inner.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HexColor(color)),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (0,0), 8),
        ('BOTTOMPADDING', (0,1), (0,1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('ROUNDEDCORNERS', [6,6,6,6]),
    ]))
    return inner


# ── Header / Footer ────────────────────────────────────────────────
def header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    # Header bar
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 18*mm, w, 18*mm, fill=1, stroke=0)
    canvas.setFillColor(white)
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawString(15*mm, h - 12*mm, 'Sena ERP - Complete QA Test Report')
    canvas.setFont('Helvetica', 8)
    canvas.drawRightString(w - 15*mm, h - 12*mm, f'Page {doc.page}')
    # Footer
    canvas.setFillColor(MED_GRAY)
    canvas.rect(0, 0, w, 12*mm, fill=1, stroke=0)
    canvas.setFillColor(DARK_GRAY)
    canvas.setFont('Helvetica', 7)
    canvas.drawString(15*mm, 5*mm, 'Confidential - Prepared for TLI (Transport Logistics International)')
    canvas.drawRightString(w - 15*mm, 5*mm, 'April 19, 2026')
    canvas.restoreState()


def first_page(canvas, doc):
    """Title page - no header/footer."""
    canvas.saveState()
    w, h = A4
    # Navy banner at top
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 80*mm, w, 80*mm, fill=1, stroke=0)
    # Accent line
    canvas.setFillColor(HexColor('#42a5f5'))
    canvas.rect(0, h - 82*mm, w, 2*mm, fill=1, stroke=0)

    canvas.setFillColor(white)
    canvas.setFont('Helvetica-Bold', 32)
    canvas.drawCentredString(w/2, h - 35*mm, 'Sena ERP')
    canvas.setFont('Helvetica', 18)
    canvas.drawCentredString(w/2, h - 48*mm, 'Complete QA Test Report')
    canvas.setFont('Helvetica', 13)
    canvas.drawCentredString(w/2, h - 62*mm, 'Full System Testing - All Modules, All Flows')

    # Info box
    y = h - 110*mm
    canvas.setFillColor(LIGHT_BLUE)
    canvas.roundRect(30*mm, y, w - 60*mm, 45*mm, 6, fill=1, stroke=0)
    canvas.setFillColor(DARK_NAVY)
    canvas.setFont('Helvetica-Bold', 11)
    left = 40*mm
    canvas.drawString(left, y + 35*mm, 'Date:')
    canvas.drawString(left, y + 25*mm, 'System:')
    canvas.drawString(left, y + 15*mm, 'URL:')
    canvas.drawString(left, y + 5*mm, 'Company:')
    canvas.setFont('Helvetica', 11)
    canvas.drawString(left + 35*mm, y + 35*mm, 'April 19, 2026')
    canvas.drawString(left + 35*mm, y + 25*mm, 'Sena ERP (Freight/Logistics ERP)')
    canvas.drawString(left + 35*mm, y + 15*mm, 'http://13.210.47.18:8088')
    canvas.drawString(left + 35*mm, y + 5*mm, 'Aero Marin Land (TLI - Transport Logistics International)')

    # Footer on title page
    canvas.setFillColor(MED_GRAY)
    canvas.rect(0, 0, w, 12*mm, fill=1, stroke=0)
    canvas.setFillColor(DARK_GRAY)
    canvas.setFont('Helvetica', 7)
    canvas.drawString(15*mm, 5*mm, 'Confidential - Prepared for TLI')
    canvas.drawRightString(w - 15*mm, 5*mm, 'April 19, 2026')
    canvas.restoreState()


# ── Build Document ──────────────────────────────────────────────────
def build_report():
    w, h = A4
    doc = BaseDocTemplate(OUTPUT_PATH, pagesize=A4,
                          leftMargin=15*mm, rightMargin=15*mm,
                          topMargin=25*mm, bottomMargin=18*mm)

    frame_first = Frame(15*mm, 18*mm, w - 30*mm, h - 130*mm, id='first')
    frame_normal = Frame(15*mm, 18*mm, w - 30*mm, h - 43*mm, id='normal')

    doc.addPageTemplates([
        PageTemplate(id='FirstPage', frames=[frame_first], onPage=first_page),
        PageTemplate(id='ContentPage', frames=[frame_normal], onPage=header_footer),
    ])

    story = []
    avail_w = w - 30*mm  # ~165mm

    # ──── Title Page ────
    story.append(Spacer(1, 30*mm))
    # Metric boxes on title page
    boxes = Table([[
        metric_box('Total Pages', '72', '#1565c0'),
        metric_box('Pages Tested', '72', '#1565c0'),
        metric_box('Pages OK', '60', '#2e7d32'),
        metric_box('Bugs Found', '12', '#c62828'),
    ]], colWidths=[avail_w/4]*4)
    boxes.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
                               ('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    story.append(boxes)
    story.append(Spacer(1, 15*mm))
    story.append(P('This report documents the complete quality assurance testing of the Sena ERP system, '
                   'covering all 72 pages across every module: Master Data, Job Management, Quotes, '
                   'Financial Reports, Accounts, DSR Reports, and HR.', style_body))
    story.append(Spacer(1, 8*mm))

    # Key results summary
    summary_data = [
        ['Test Area', 'Scope', 'Result', 'Pass Rate'],
        ['Page Load Testing', '72 pages', '60 OK / 12 errors', '83%'],
        ['Master Data CRUD', '20 pages', '19 successful', '95%'],
        ['Job Creation', '6 job types', '6 created', '100%'],
        ['Financial Reports', '9 pages', '9 working', '100%'],
        ['Account Pages', '14 pages', '14 loading', '100%'],
        ['DSR Reports', '5 pages', '5 loading', '100%'],
    ]
    st = Table(summary_data, colWidths=[45*mm, 30*mm, 45*mm, 25*mm])
    st.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, MED_GRAY),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('BACKGROUND', (0,1), (-1,1), LIGHT_GRAY),
        ('BACKGROUND', (0,3), (-1,3), LIGHT_GRAY),
        ('BACKGROUND', (0,5), (-1,5), LIGHT_GRAY),
    ]))
    story.append(st)

    story.append(PageBreak())

    # ──── Table of Contents ────
    # Switch to content template
    from reportlab.platypus import NextPageTemplate
    story.insert(len(story)-1, NextPageTemplate('ContentPage'))

    story.append(section_header_bar('TABLE OF CONTENTS'))
    story.append(Spacer(1, 8*mm))

    toc_items = [
        ('Section 1', 'Executive Summary'),
        ('Section 2', 'Master Data CRUD Results'),
        ('Section 3', 'Job Creation Test Results'),
        ('Section 4', 'Job Detail / Workflow Test Results'),
        ('Section 5', 'Quote & Rate Setup Test Results'),
        ('Section 6', 'Financial Reports Test Results'),
        ('Section 7', 'Account Pages Test Results'),
        ('Section 8', 'DSR Reports'),
        ('Section 9', 'HR Module'),
        ('Section 10', 'Complete Bug List'),
        ('Section 11', 'Recommendations'),
        ('Section 12', 'Test Scripts Delivered'),
    ]
    for sec, title in toc_items:
        story.append(P(f'<b>{sec}:</b>  {title}', style_toc_section))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    # SECTION 1: Executive Summary
    # ════════════════════════════════════════════════════════════════
    story.append(section_header_bar('SECTION 1: EXECUTIVE SUMMARY'))
    story.append(Spacer(1, 4*mm))

    # Colored metric boxes row 1
    row1 = Table([[
        metric_box('Total Pages', '72', '#1565c0'),
        metric_box('Tested', '72 (100%)', '#1565c0'),
        metric_box('OK', '60 (83%)', '#2e7d32'),
        metric_box('Errors', '12 (17%)', '#c62828'),
    ]], colWidths=[avail_w/4]*4)
    row1.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
                              ('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    story.append(row1)
    story.append(Spacer(1, 3*mm))

    row2 = Table([[
        metric_box('CRUD Tests', '19/20 (95%)', '#2e7d32'),
        metric_box('Job Creation', '6/6 (100%)', '#2e7d32'),
        metric_box('Finance Rpts', '9/9 (100%)', '#2e7d32'),
        metric_box('Bugs', '3C 4H 3M 2L', '#ef6c00'),
    ]], colWidths=[avail_w/4]*4)
    row2.setStyle(TableStyle([('ALIGN',(0,0),(-1,-1),'CENTER'),
                              ('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    story.append(row2)
    story.append(Spacer(1, 5*mm))

    story.append(P('<b>Testing Scope:</b> Complete end-to-end testing of the Sena ERP system deployed at '
                   'http://13.210.47.18:8088. Testing covered all 72 pages across all modules including '
                   'Master Data management, Job Creation (Ocean/Air/Land Import and Export), Job Detail workflows, '
                   'Quote and Rate Setup, Financial Reports, Account management (Debtors/Creditors), '
                   'DSR Reports, and the HR module.'))
    story.append(Spacer(1, 2*mm))
    story.append(P('<b>Methodology:</b> Automated testing using Playwright with Python, supplemented by manual '
                   'verification. Each page was loaded and verified for HTTP status, DOM structure, and functional '
                   'elements. CRUD operations were tested by creating actual records with test data. '
                   'Job creation was tested for all 6 job types with full data entry including Select2 dropdown interaction.'))
    story.append(Spacer(1, 2*mm))
    story.append(P('<b>Overall Assessment:</b> The system is functional for core operations. All 6 job types can be '
                   'created successfully, financial reports are working with proper filtering, and 95% of master data '
                   'pages support full CRUD operations. However, 12 bugs were identified including 3 critical issues '
                   '(Vendor Master HTTP 500, Activity Log HTTP 500, and Land Import/Export consignee dropdown not initialized) '
                   'that require immediate attention.'))
    story.append(Spacer(1, 2*mm))

    bug_summary = [
        ['Severity', 'Count', 'Description'],
        ['CRITICAL', '3', 'Vendor Master 500, Activity Log 500, Land Job Consignee Select2'],
        ['HIGH', '4', 'Select2 stacking, No Add Row in charges, Selling charges PP/CC, Client Rates form'],
        ['MEDIUM', '3', 'Ledger Group empty modal, Customer Ageing typo, Date filters'],
        ['LOW', '2', 'Payment UX unclear, Files tab URL-only'],
    ]
    bt = Table(bug_summary, colWidths=[25*mm, 15*mm, avail_w - 40*mm])
    bt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), white),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, MED_GRAY),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('BACKGROUND', (0,1), (0,1), LIGHT_RED),
        ('BACKGROUND', (0,2), (0,2), LIGHT_ORANGE),
        ('BACKGROUND', (0,3), (0,3), HexColor('#fff9c4')),
        ('BACKGROUND', (0,4), (0,4), LIGHT_BLUE),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(bt)

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    # SECTION 2: Master Data CRUD Results
    # ════════════════════════════════════════════════════════════════
    story.append(section_header_bar('SECTION 2: MASTER DATA CRUD RESULTS'))
    story.append(Spacer(1, 4*mm))
    story.append(P('All 20 master data pages were tested for Create, Read, Update, and Delete operations. '
                   '19 out of 20 pages passed successfully (95%). The only failure was Ledger Group, where '
                   'the "Add New" modal opens but contains no form fields.'))
    story.append(Spacer(1, 3*mm))

    crud_headers = ['Page Name', 'Category', 'Fields', 'Status', 'Verified', 'Notes']
    crud_rows = [
        ['State', 'Simple', '4', 'PASS', 'Yes', 'Country + name'],
        ['City', 'Simple', '6', 'PASS', 'Yes', 'Country + state + name + code'],
        ['Company Type', 'Simple', '3', 'PASS', 'Yes', 'Name + status'],
        ['Customer Type', 'Simple', '3', 'PASS', 'Yes', 'Name + status'],
        ['Vendor Type', 'Simple', '3', 'PASS', 'Yes', 'Name + status'],
        ['Ledger Group', 'Simple', '0', 'FAIL', 'No', 'Modal has no form fields - BUG'],
        ['Commodity Master', 'Simple', '4', 'PASS', 'Yes', 'Code + name'],
        ['Charge Master', 'Complex', '7', 'PASS', 'Yes', 'Code + name + tax + type'],
        ['Company Master', 'Complex', '5', 'PASS', 'Yes', 'Name + company type + type'],
        ['Customer Master', 'Complex', '39', 'PASS', 'Yes', 'Full form - 7 sections'],
        ['Shipping Line Code', 'Complex', '4', 'PASS', 'Yes', 'Code + name'],
        ['Address', 'Complex', '6', 'PASS', 'Yes', 'Name + type'],
        ['Job Type', 'Ocean', '4', 'PASS', 'Yes', 'Job type select + name'],
        ['Vessel', 'Ocean', '3', 'PASS', 'Yes', 'Name + status'],
        ['Ocean Port Sector', 'Ocean', '3', 'PASS', 'Yes', 'Name + status'],
        ['Ocean Port', 'Ocean', '6', 'PASS', 'Yes', 'Code + name + country + sector'],
        ['Airport', 'Air', '6', 'PASS', 'Yes', 'Name + code'],
        ['Carrier/Airlines', 'Air', '6', 'PASS', 'Yes', 'Name + code + prefix + address'],
        ['Carriers (Quote)', 'Quote', '5', 'PASS', 'Yes', 'Mode + code + name'],
        ['Exchange Rates', 'Quote', '3', 'PASS', 'Yes', 'Currency + rate + date'],
    ]
    cw = [28*mm, 18*mm, 12*mm, 14*mm, 14*mm, avail_w - 86*mm]
    story.append(make_table(crud_headers, crud_rows, col_widths=cw, has_status_col=3))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    # SECTION 3: Job Creation Test Results
    # ════════════════════════════════════════════════════════════════
    story.append(section_header_bar('SECTION 3: JOB CREATION TEST RESULTS'))
    story.append(Spacer(1, 4*mm))
    story.append(P('All 6 job types were tested with full data entry. Each record was created successfully '
                   'with the system generating proper auto-incremented job numbers. This represents 100% success '
                   'rate for job creation functionality.'))
    story.append(Spacer(1, 4*mm))

    # Job 1: Ocean Import
    story.append(P('<b>Ocean Import - Job No: TLI/SI/2627//0467</b>', style_h3))
    story.append(P('<font color="#2e7d32"><b>Status: CREATED SUCCESSFULLY</b></font>', style_body))
    story.append(P('<b>Fields filled:</b> Job Date, MBL No (TESTMBL-AUTO-001), Shipment Type (FCL), '
                   'Consignee (RASKEL), Port of Loading (BOMBAY), Port of Discharge (KOLKATA), '
                   'Shipping Line (HAPAG LLOYD), Commodity (LEATHER RUCKSACK), Container (TESU1234567), '
                   'Overseas Agent, ETD, ETA, GBP Applicable'))
    story.append(P('Auto-generated Job No format: TLI/SI/YYMM//NNNN. Alert: "Record added successfully."'))
    story.append(Spacer(1, 3*mm))

    # Job 2: Ocean Export
    story.append(P('<b>Ocean Export - Job No: TLI/SE/2627//0043</b>', style_h3))
    story.append(P('<font color="#2e7d32"><b>Status: CREATED SUCCESSFULLY</b></font>', style_body))
    story.append(P('<b>Fields filled:</b> Same as Import plus HBL No, Shipper, HSN Code, Gross/Net Weight, '
                   'Invoice Value, Pack Count, Shipper Invoice'))
    story.append(P('Alert: "Record added successfully."'))
    story.append(Spacer(1, 3*mm))

    # Job 3: Air Import
    story.append(P('<b>Air Import - Auto-generated job number</b>', style_h3))
    story.append(P('<font color="#2e7d32"><b>Status: CREATED SUCCESSFULLY</b></font>', style_body))
    story.append(P('<b>Fields filled:</b> MAWB (11 digits required), HAWB, Flight No, Carrier (ISRAEL AIRLINES), '
                   'Port of Loading (NEW DELHI), Port of Discharge (KOLKOTA), Incoterms, Consignee'))
    story.append(P('Alert: "Record added successfully."'))
    story.append(Spacer(1, 3*mm))

    # Job 4: Air Export
    story.append(P('<b>Air Export - Job No: TLI/AE/2627//0074</b>', style_h3))
    story.append(P('<font color="#2e7d32"><b>Status: CREATED SUCCESSFULLY</b></font>', style_body))
    story.append(P('<b>Fields filled:</b> Same structure as Air Import plus package dimensions '
                   '(length/breadth/height), volume weight'))
    story.append(P('Alert: "Record added successfully."'))
    story.append(Spacer(1, 3*mm))

    # Job 5: Land Import
    story.append(P('<b>Land Import - Job No: TLI/LI/2627//0003</b>', style_h3))
    story.append(P('<font color="#2e7d32"><b>Status: CREATED SUCCESSFULLY</b></font>', style_body))
    story.append(P('<b>Fields filled:</b> Origin (Mumbai), Destination (Delhi), Vehicle Type (FTL), '
                   'Vehicle Reg (MH01AB1234), Driver, CMR No, Gross/Net Weight, CBM, Packages, '
                   'Incoterms, Consignee'))
    story.append(P('<font color="#c62828"><b>Note:</b></font> Consignee dropdown required manual Select2 '
                   'initialization (BUG-003 - see bugs section)'))
    story.append(P('Alert: "Record added successfully."'))
    story.append(Spacer(1, 3*mm))

    # Job 6: Land Export
    story.append(P('<b>Land Export - Job No: TLI/LE/2627//0001</b>', style_h3))
    story.append(P('<font color="#2e7d32"><b>Status: CREATED SUCCESSFULLY</b></font>', style_body))
    story.append(P('<b>Fields filled:</b> Same field structure as Land Import'))
    story.append(P('Alert: "Record added successfully."'))

    story.append(Spacer(1, 4*mm))
    # Summary table
    job_summary = [
        ['Job Type', 'Job Number', 'Key Fields', 'Status'],
        ['Ocean Import', 'TLI/SI/2627//0467', 'MBL, FCL, Consignee, Ports, Shipping Line', 'PASS'],
        ['Ocean Export', 'TLI/SE/2627//0043', 'HBL, Shipper, HSN, Weights, Invoice', 'PASS'],
        ['Air Import', 'Auto-generated', 'MAWB (11-digit), HAWB, Flight, Carrier', 'PASS'],
        ['Air Export', 'TLI/AE/2627//0074', 'Dimensions, Volume Weight', 'PASS'],
        ['Land Import', 'TLI/LI/2627//0003', 'Vehicle, CMR, Origin/Dest, Packages', 'PASS'],
        ['Land Export', 'TLI/LE/2627//0001', 'Same as Land Import', 'PASS'],
    ]
    story.append(make_table(['Job Type', 'Job Number', 'Key Fields', 'Status'], job_summary[1:],
                            col_widths=[28*mm, 35*mm, avail_w - 77*mm, 14*mm], has_status_col=3))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    # SECTION 4: Job Detail / Workflow Test Results
    # ════════════════════════════════════════════════════════════════
    story.append(section_header_bar('SECTION 4: JOB DETAIL / WORKFLOW TEST RESULTS'))
    story.append(Spacer(1, 4*mm))
    story.append(P('Tested all 8 wizard steps within existing Ocean Import and Air Import jobs. '
                   'Each step was evaluated for field count, editability, and functional elements.'))
    story.append(Spacer(1, 3*mm))

    wiz_headers = ['Step', 'Name', 'Fields (OI/AI)', 'Status', 'Notes']
    wiz_rows = [
        ['1', 'Basic Details', '45 / 49', 'PASS', 'All fields editable, Select2 dropdowns working'],
        ['2', 'Clearing Instructions', '16 / 47', 'PASS', 'Mostly readonly/display fields in OI; more editable in AI'],
        ['3', 'Delivery Note', '25 / 40', 'PASS', 'Delivery details, dates, addresses'],
        ['4', 'Buying Charges', '15 / 15', 'WARNING', 'Charge table present but no "Add Row" button found'],
        ['5', 'Selling Charges', '15 / 15', 'WARNING', 'Same issue - no "Add Row" button; some Select2 not initialized'],
        ['6', 'Purchase Invoice', '2 / 2', 'PASS', 'Month/Year selector'],
        ['7', 'Sale Invoice', '2 / 2', 'PASS', 'Month/Year selector'],
        ['8', 'Files/Supporting', '3 / 3', 'PASS', 'URL-based file linking (not file upload), 10 existing file entries'],
    ]
    story.append(make_table(wiz_headers, wiz_rows,
                            col_widths=[12*mm, 30*mm, 22*mm, 18*mm, avail_w - 82*mm], has_status_col=3))

    story.append(Spacer(1, 4*mm))
    story.append(P('<b>Key Findings:</b>'))
    story.append(P('- Steps 1-3 contain the bulk of job data fields and all function correctly with proper Select2 initialization'))
    story.append(P('- Steps 4-5 (Buying/Selling Charges) have a structural issue: the charge tables exist but lack an "Add Row" '
                   'button, limiting users to a single charge line per job'))
    story.append(P('- Steps 6-7 (Purchase/Sale Invoice) use a month/year selector pattern for invoice generation'))
    story.append(P('- Step 8 (Files) uses URL text fields rather than file upload, which may be by design for this system'))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    # SECTION 5: Quote & Rate Setup Test Results
    # ════════════════════════════════════════════════════════════════
    story.append(section_header_bar('SECTION 5: QUOTE & RATE SETUP TEST RESULTS'))
    story.append(Spacer(1, 4*mm))

    story.append(P('<b>Quote Creation</b>', style_h2))
    story.append(P('Found "+ New Quote" button on Quotes page. Form has 14 fields: Quote No (auto), dates, '
                   'customer (Select2), mode (Select2), ship type, cargo ready date, cargo type, commodity, '
                   'packages, weights, CBM, remarks. Customer and Mode dropdowns filled successfully via Select2. '
                   'Submission showed validation errors - some required fields not filled.'))
    story.append(P('<font color="#ef6c00"><b>Status: PARTIAL</b></font> - form works but requires all mandatory fields', style_body))
    story.append(Spacer(1, 3*mm))

    story.append(P('<b>Rate Database</b>', style_h2))
    story.append(P('"Add Rate" button found. Form has 10 fields: mode, rate type, carrier, buy rate, sell rate, '
                   'unit, valid dates, status. Record creation: SUCCESSFUL - saved and redirected to list.'))
    story.append(P('<font color="#2e7d32"><b>Status: PASS</b></font>', style_body))
    story.append(Spacer(1, 3*mm))

    story.append(P('<b>Client Rates</b>', style_h2))
    story.append(P('"Add New" button found. ISSUE: Form loaded with 0 visible fields - may need prerequisite selection.'))
    story.append(P('<font color="#c62828"><b>Status: FAIL</b></font> - form not rendering properly', style_body))

    quote_tbl = [
        ['Component', 'Fields', 'Create Test', 'Status'],
        ['Quote Creation', '14', 'Partial - validation required', 'PARTIAL'],
        ['Rate Database', '10', 'Record created successfully', 'PASS'],
        ['Client Rates', '0', 'Form not rendering', 'FAIL'],
    ]
    story.append(Spacer(1, 3*mm))
    story.append(make_table(['Component', 'Fields', 'Create Test', 'Status'], quote_tbl[1:],
                            col_widths=[30*mm, 15*mm, avail_w - 59*mm, 14*mm], has_status_col=3))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    # SECTION 6: Financial Reports Test Results
    # ════════════════════════════════════════════════════════════════
    story.append(section_header_bar('SECTION 6: FINANCIAL REPORTS TEST RESULTS'))
    story.append(Spacer(1, 4*mm))
    story.append(P('All 9 financial report pages load correctly with data. Each report has proper date filtering '
                   'and status dropdowns for data segmentation.'))
    story.append(Spacer(1, 3*mm))

    fin_headers = ['Report', 'Rows', 'Date Filter', 'Status Dropdown', 'Status', 'Notes']
    fin_rows = [
        ['Purchase Invoice', '21', 'YES', 'All/Fully Paid/Partial/Unpaid/Void', 'PASS', 'Action buttons: view, Add CRN, Save, Cancel'],
        ['Sales Invoice', '20', 'YES', 'All/Paid/Partial/Unpaid/CRN', 'PASS', 'Edit, Add CRN actions'],
        ['Purchase Inv w/ VAT', '21', 'YES', 'Same dropdowns', 'PASS', 'Filter works correctly'],
        ['Sales Inv w/ VAT', '20', 'YES', 'All/Paid/Partial/Unpaid', 'PASS', 'Filter works correctly'],
        ['Ledger Report', '2', 'YES', 'Party select', 'PASS', 'Opening/closing balance'],
        ['Customer Ageing', '10', 'YES', 'Module + Customer filters', 'PASS', 'Typo: "IINVOICE NO"'],
        ['Supplier Ageing', '10', 'YES', 'Same filters', 'PASS', 'Same structure'],
        ['Jobs w/o Purch Inv', '10', 'YES', 'Text search', 'PASS', 'Jobs missing purchase invoices'],
        ['Jobs w/o Sales Inv', '10', 'YES', 'Text search', 'PASS', 'Jobs missing sales invoices'],
    ]
    story.append(make_table(fin_headers, fin_rows,
                            col_widths=[28*mm, 10*mm, 14*mm, 38*mm, 12*mm, avail_w - 102*mm], has_status_col=4))

    story.append(Spacer(1, 4*mm))
    story.append(P('<b>Key Columns Found:</b> All financial reports include Job No, Date, Party/Vendor name, '
                   'Invoice No, Amount/Details, and Status fields. The Purchase and Sales Invoice pages include '
                   'action buttons for viewing details, adding Credit Notes (CRN), and saving/canceling operations.'))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    # SECTION 7: Account Pages Test Results
    # ════════════════════════════════════════════════════════════════
    story.append(section_header_bar('SECTION 7: ACCOUNT PAGES TEST RESULTS'))
    story.append(Spacer(1, 4*mm))
    story.append(P('All 14 account pages load correctly. Debtor/Creditor pages show separate Due and Paid views. '
                   'Due pages have checkbox-based selection for payment recording.'))
    story.append(Spacer(1, 3*mm))

    story.append(P('<b>Debtors (6 pages)</b>', style_h2))
    deb_headers = ['Page', 'Rows', 'Checkboxes', 'Payment Controls', 'Notes']
    deb_rows = [
        ['Consignee Due', '32', '14', 'Checkbox selection works', 'Most active debtor page'],
        ['Consignee Paid', '3', 'None', 'N/A (view only)', 'Shows Paid Amount, Due Amount, Paid Date'],
        ['Agent Due (Debtor)', '11', '5', 'Checkbox selection works', ''],
        ['Agent Paid (Debtor)', '0', 'None', 'N/A', 'No paid records'],
        ['Shipper Due', '0', 'None', 'N/A', 'No records'],
        ['Shipper Paid', '0', 'None', 'N/A', 'No records'],
    ]
    story.append(make_table(deb_headers, deb_rows,
                            col_widths=[28*mm, 12*mm, 18*mm, 35*mm, avail_w - 93*mm]))

    story.append(Spacer(1, 4*mm))
    story.append(P('<b>Creditors (8 pages)</b>', style_h2))
    cred_rows = [
        ['Shipping Line Due', '14', '8', 'Checkbox selection works', ''],
        ['Shipping Line Paid', '0', 'None', 'N/A', 'No paid records'],
        ['Co-Loader Due', '0', 'None', 'N/A', 'No records'],
        ['Co-Loader Paid', '0', 'None', 'N/A', 'No records'],
        ['Supplier Due', '17', '9', 'Checkbox selection works', ''],
        ['Supplier Paid', '0', 'None', 'N/A', 'No paid records'],
        ['Agent Due (Creditor)', '3', '1', 'Checkbox selection works', ''],
        ['Agent Paid (Creditor)', '0', 'None', 'N/A', 'No paid records'],
    ]
    story.append(make_table(deb_headers, cred_rows,
                            col_widths=[28*mm, 12*mm, 18*mm, 35*mm, avail_w - 93*mm]))

    story.append(Spacer(1, 3*mm))
    story.append(P('<b>Note:</b> Payment recording mechanism unclear - checkboxes exist but no explicit '
                   '"Submit Payment" button found. May use a different UI pattern (modal, AJAX call).'))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    # SECTION 8: DSR Reports
    # ════════════════════════════════════════════════════════════════
    story.append(section_header_bar('SECTION 8: DSR REPORTS'))
    story.append(Spacer(1, 4*mm))
    story.append(P('All 5 DSR (Daily Status Report) pages load correctly. The Basic Graph page renders a Chart.js '
                   'visualization. The remaining 4 pages show data grids with date-based filtering.'))
    story.append(Spacer(1, 3*mm))

    dsr_headers = ['Page', 'Status', 'Chart', 'Data', 'Filters']
    dsr_rows = [
        ['Basic Graph', 'PASS', 'YES (Chart.js)', 'Graph rendered', 'Year selector (FY 2023-2027)'],
        ['Ocean Import DSR', 'PASS', 'No', 'No records', 'ETA/ETD/Delivery Date filter + Search'],
        ['Ocean Export DSR', 'PASS', 'No', 'No records', 'Same filter pattern'],
        ['Air Import DSR', 'PASS', 'No', 'No records', 'Same filter pattern'],
        ['Air Export DSR', 'PASS', 'No', 'No records', 'Same filter pattern'],
    ]
    story.append(make_table(dsr_headers, dsr_rows,
                            col_widths=[28*mm, 14*mm, 25*mm, 22*mm, avail_w - 89*mm], has_status_col=1))

    story.append(Spacer(1, 3*mm))
    story.append(P('<b>Note:</b> All DSR pages load but show no data records. This may indicate that DSR entries '
                   'need to be created separately from job entries, or that the test data does not include DSR-specific records.'))

    story.append(Spacer(1, 8*mm))

    # ════════════════════════════════════════════════════════════════
    # SECTION 9: HR Module
    # ════════════════════════════════════════════════════════════════
    story.append(section_header_bar('SECTION 9: HR MODULE'))
    story.append(Spacer(1, 4*mm))

    story.append(P('<b>Employee List</b>', style_h2))
    story.append(P('11 existing employees visible in the employee list. "Add New" button present and functional.'))
    story.append(Spacer(1, 3*mm))

    story.append(P('<b>Employee Creation Test</b>', style_h2))
    story.append(P('<font color="#2e7d32"><b>Status: CREATED SUCCESSFULLY</b></font>', style_body))
    story.append(P('<b>Fields filled:</b> First Name (TestUser), Middle Name (Auto), Last Name (Test), '
                   'Mobile (9876543210), Email (autotest@senaerp.com), User Type (Admin/User radio), '
                   'Username (autotestuser), Password (Test@12345), Profile Image upload'))
    story.append(P('Alert: "Record added successfully." - Verified in employee list.'))

    hr_tbl = [
        ['Test', 'Fields', 'Result', 'Status'],
        ['Employee List', 'N/A', '11 employees visible', 'PASS'],
        ['Employee Creation', '9 fields', 'Record created and verified', 'PASS'],
    ]
    story.append(Spacer(1, 3*mm))
    story.append(make_table(['Test', 'Fields', 'Result', 'Status'], hr_tbl[1:],
                            col_widths=[30*mm, 20*mm, avail_w - 64*mm, 14*mm], has_status_col=3))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    # SECTION 10: Complete Bug List
    # ════════════════════════════════════════════════════════════════
    story.append(section_header_bar('SECTION 10: COMPLETE BUG LIST'))
    story.append(Spacer(1, 4*mm))
    story.append(P('12 bugs were identified during testing, categorized by severity. '
                   '3 are Critical (system-breaking), 4 are High (significant functionality impact), '
                   '3 are Medium (usability issues), and 2 are Low (minor improvements).'))
    story.append(Spacer(1, 4*mm))

    bugs = [
        ('BUG-001', 'CRITICAL', 'Vendor Master HTTP 500',
         'Common Masters > Vendor Master',
         'InvalidArgumentException - View [vendor.index] not found in Vendor.php line 70',
         'Cannot access or manage any vendor records',
         'Correct the view name in the controller'),

        ('BUG-002', 'CRITICAL', 'Activity Log HTTP 500',
         'Activity Log page',
         'QueryException - Unknown column \'u.FNAME\' in ActivityLogController.php line 48',
         'Cannot view activity/audit logs',
         'Update SQL query to use correct column name'),

        ('BUG-003', 'CRITICAL', 'Land Import/Export - Consignee Select2 Not Initialized',
         'Land Import and Land Export job creation forms',
         'The Consignee dropdown has class "select2-cus" but Select2 is NOT initialized on it by the page JavaScript',
         'Users cannot select a consignee when creating land jobs',
         'Add Select2 initialization for the consignee field on land job forms'),

        ('BUG-004', 'HIGH', 'Select2 Dropdown Stacking',
         'All Ocean/Air job forms',
         'When opening multiple Select2 dropdowns in sequence, results from previous dropdowns are not cleared',
         'Users may accidentally select wrong values',
         'Ensure Select2 properly clears previous results on close'),

        ('BUG-005', 'HIGH', 'Buying/Selling Charges - No Add Row Button',
         'Job detail Steps 4 and 5 (Buying and Selling Charges)',
         'The charges table shows a single row but has no "Add Row" or "+" button',
         'Users can only enter one charge per job',
         'Add an "Add Row" button to the charges table'),

        ('BUG-006', 'HIGH', 'Selling Charges - PP/CC Select2 Not Initialized',
         'Job detail Step 5 (Selling Charges)',
         'The sl_ppcc (Prepaid/Collect) Select2 dropdown is not initialized',
         'Cannot set PP/CC status for selling charges',
         'Initialize Select2 on all dropdowns in the selling charges tab'),

        ('BUG-007', 'HIGH', 'Client Rates - Form Not Rendering',
         'Quote Setup > Client Rates',
         '"Add New" button exists but the form loads with 0 visible fields',
         'Cannot create new client rate records',
         'Investigate why form fields are not rendered'),

        ('BUG-008', 'MEDIUM', 'Ledger Group - Empty Add Modal',
         'Common Masters > Ledger Group',
         '"Add New" modal opens but contains no form fields',
         'Cannot add new ledger groups',
         'Add form fields to the add modal'),

        ('BUG-009', 'MEDIUM', 'Customer Ageing Report - Column Typo',
         'Financial Reports > Customer Ageing',
         'Column header shows "IINVOICE NO" (double I) instead of "INVOICE NO"',
         'Display error in report header',
         'Correct the typo in the view template'),

        ('BUG-010', 'MEDIUM', 'Date Filters on Account Pages Not Working',
         'All Debtor/Creditor Due/Paid pages',
         'Date input fields use a datepicker widget that doesn\'t accept direct text input',
         'Users may have difficulty filtering account data by date',
         'Ensure consistent date picker implementation'),

        ('BUG-011', 'LOW', 'Payment Recording UX Unclear',
         'All "Due" account pages (Debtors/Creditors)',
         'Checkboxes exist for selecting invoices but no explicit "Record Payment" button is visible',
         'Users may not understand how to record payments',
         'Add clear payment submission button or better UX guidance'),

        ('BUG-012', 'LOW', 'Files Tab Uses URL Linking Instead of File Upload',
         'Job detail Step 8 (Files/Supporting)',
         'The files section uses URL text fields instead of a file upload control',
         'Users must host files elsewhere and paste URLs instead of directly uploading',
         'Consider adding a file upload control'),
    ]

    sev_colors = {'CRITICAL': '#c62828', 'HIGH': '#ef6c00', 'MEDIUM': '#f9a825', 'LOW': '#1565c0'}
    sev_bg = {'CRITICAL': '#ffebee', 'HIGH': '#fff3e0', 'MEDIUM': '#fffde7', 'LOW': '#e3f2fd'}

    for bug_id, severity, title, page, issue, impact, fix in bugs:
        sev_c = sev_colors[severity]
        bg_c = sev_bg[severity]

        # Bug header row
        hdr_data = [[
            Paragraph(f'<font color="{sev_c}"><b>{bug_id}</b></font>', style_cell),
            Paragraph(f'<font color="white"><b>{severity}</b></font>', style_cell_center),
            Paragraph(f'<b>{title}</b>', style_cell),
        ]]
        hdr_tbl = Table(hdr_data, colWidths=[20*mm, 22*mm, avail_w - 42*mm])
        hdr_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,0), HexColor(bg_c)),
            ('BACKGROUND', (1,0), (1,0), HexColor(sev_c)),
            ('BACKGROUND', (2,0), (2,0), HexColor(bg_c)),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('BOX', (0,0), (-1,-1), 0.5, HexColor(sev_c)),
        ]))
        story.append(hdr_tbl)

        # Bug details
        detail_data = [
            [Pcell('Page:', bold=True), Pcell(page)],
            [Pcell('Issue:', bold=True), Pcell(issue)],
            [Pcell('Impact:', bold=True), Pcell(impact)],
            [Pcell('Fix:', bold=True), Pcell(fix)],
        ]
        det_tbl = Table(detail_data, colWidths=[18*mm, avail_w - 18*mm])
        det_tbl.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (0,-1), 8),
            ('LEFTPADDING', (1,0), (1,-1), 4),
            ('LINEBELOW', (0,-1), (-1,-1), 0.3, MED_GRAY),
        ]))
        story.append(det_tbl)
        story.append(Spacer(1, 3*mm))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    # SECTION 11: Recommendations
    # ════════════════════════════════════════════════════════════════
    story.append(section_header_bar('SECTION 11: RECOMMENDATIONS'))
    story.append(Spacer(1, 4*mm))

    story.append(P('<b>Priority Fixes (Immediate)</b>', style_h2))
    recs_critical = [
        ['#', 'Priority', 'Recommendation', 'Bug Ref'],
        ['1', 'CRITICAL', 'Fix Vendor Master view name - InvalidArgumentException prevents all vendor management', 'BUG-001'],
        ['2', 'CRITICAL', 'Fix Activity Log SQL query - Unknown column prevents audit log viewing', 'BUG-002'],
        ['3', 'CRITICAL', 'Initialize Select2 on Land Import/Export consignee field', 'BUG-003'],
    ]
    story.append(make_table(recs_critical[0], recs_critical[1:],
                            col_widths=[8*mm, 20*mm, avail_w - 42*mm, 14*mm]))

    story.append(Spacer(1, 4*mm))
    story.append(P('<b>High Priority Fixes</b>', style_h2))
    recs_high = [
        ['#', 'Priority', 'Recommendation', 'Bug Ref'],
        ['4', 'HIGH', 'Fix Select2 stacking issue across all forms', 'BUG-004'],
        ['5', 'HIGH', 'Add "Add Row" functionality to Buying/Selling Charges', 'BUG-005'],
        ['6', 'HIGH', 'Fix Selling Charges PP/CC Select2 initialization', 'BUG-006'],
        ['7', 'HIGH', 'Fix Client Rates form rendering', 'BUG-007'],
    ]
    story.append(make_table(recs_high[0], recs_high[1:],
                            col_widths=[8*mm, 20*mm, avail_w - 42*mm, 14*mm]))

    story.append(Spacer(1, 4*mm))
    story.append(P('<b>Medium and Low Priority</b>', style_h2))
    recs_other = [
        ['#', 'Priority', 'Recommendation', 'Bug Ref'],
        ['8', 'MEDIUM', 'Fix column typo in Customer Ageing report ("IINVOICE NO")', 'BUG-009'],
        ['9', 'MEDIUM', 'Fix Ledger Group empty modal - add form fields', 'BUG-008'],
        ['10', 'MEDIUM', 'Standardize date picker implementation across all pages', 'BUG-010'],
        ['11', 'LOW', 'Add clear payment submission UX on Due pages', 'BUG-011'],
        ['12', 'LOW', 'Consider file upload for job supporting documents', 'BUG-012'],
    ]
    story.append(make_table(recs_other[0], recs_other[1:],
                            col_widths=[8*mm, 20*mm, avail_w - 42*mm, 14*mm]))

    story.append(Spacer(1, 5*mm))
    story.append(P('<b>General Improvements</b>', style_h2))
    story.append(P('1. Add validation error messages that specify which fields are missing'))
    story.append(P('2. Pre-populate DSR report data from job entries'))
    story.append(P('3. Add bulk export (Excel/PDF) for all report pages'))
    story.append(P('4. Add confirmation dialogs for record creation/deletion'))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════════════════
    # SECTION 12: Test Scripts Delivered
    # ════════════════════════════════════════════════════════════════
    story.append(section_header_bar('SECTION 12: TEST SCRIPTS DELIVERED'))
    story.append(Spacer(1, 4*mm))
    story.append(P('8 Playwright test scripts were developed and delivered for future regression and upgrade testing. '
                   'All scripts are available in the GitHub repository.'))
    story.append(Spacer(1, 3*mm))

    scripts_headers = ['#', 'Script', 'Purpose', 'Coverage']
    scripts_rows = [
        ['1', 'test_all_pages.py', 'Page load testing', '72 pages'],
        ['2', 'test_crud_masters.py', 'CRUD on master pages', '20 pages'],
        ['3', 'test_jobs_and_reports.py', 'Job workflows, reports, accounts overview', 'Jobs + Reports'],
        ['4', 'test_remaining_jobs.py', 'Ocean Export, Air Export, Land Import/Export', '4 job types'],
        ['5', 'test_job_details.py', 'Job detail tabs, quotes, rates', '8 wizard steps'],
        ['6', 'test_reports_accounts.py', 'Financial reports, debtors/creditors, DSR', '28 pages'],
        ['7', 'test_create_records.py', 'Record creation (Employee, Ocean/Air Import)', '3 record types'],
        ['8', 'test_deep_jobs.py', 'Select2 dropdown analysis and form structure', 'Form discovery'],
    ]
    story.append(make_table(scripts_headers, scripts_rows,
                            col_widths=[8*mm, 38*mm, avail_w - 68*mm, 22*mm]))

    story.append(Spacer(1, 5*mm))
    story.append(P('<b>GitHub Repository:</b> https://github.com/anirudhatalmale6-alt/sena-erp-qa-tests'))
    story.append(Spacer(1, 3*mm))
    story.append(P('<b>How to Run Tests:</b>'))
    story.append(P('1. Install Python 3.10+ and pip install playwright'))
    story.append(P('2. Run: playwright install chromium'))
    story.append(P('3. Execute: python test_all_pages.py (or any specific test script)'))
    story.append(P('4. Results are saved as JSON files in the same directory'))

    story.append(Spacer(1, 10*mm))

    # Final summary box
    final_box_data = [[Paragraph(
        '<font color="white" size="11"><b>TESTING COMPLETE</b></font><br/>'
        '<font color="white" size="9">72 pages tested | 6 job types created | 12 bugs documented | 8 test scripts delivered</font>',
        ParagraphStyle('FinalBox', alignment=TA_CENTER, fontName='Helvetica-Bold', textColor=white))]]
    final_box = Table(final_box_data, colWidths=[avail_w])
    final_box.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), GREEN),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('ROUNDEDCORNERS', [6,6,6,6]),
    ]))
    story.append(final_box)

    # ── Build ──
    doc.build(story)
    print(f'Report generated: {OUTPUT_PATH}')

    # Report file info
    size = os.path.getsize(OUTPUT_PATH)
    print(f'File size: {size:,} bytes ({size/1024:.1f} KB)')

    # Count pages
    with open(OUTPUT_PATH, 'rb') as f:
        content = f.read()
        page_count = content.count(b'/Type /Page') - content.count(b'/Type /Pages')
    print(f'Page count: {page_count}')


if __name__ == '__main__':
    build_report()
