"""
Pure Python PDF generation engine adhering to the PDF 1.4 standard.
Zero external dependencies required.
"""
import os
import re


class PDFDocument:
    """A lightweight, zero-dependency PDF generator for structured business and tax reports."""

    def __init__(self, title="Financial & Tax Report"):
        self.title = title
        self.objects = []
        self.page_streams = []

    def _escape_pdf_str(self, text: str) -> str:
        """Escape text for PDF literal strings in parentheses."""
        # Replace non-ASCII currency symbol ₦ with NGN for standard Type1 font compatibility
        text = text.replace("₦", "NGN ")
        text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        # Filter non-printable ASCII
        return "".join([c if 32 <= ord(c) <= 126 else " " for c in text])

    def create_report_pdf(self, file_path: str, business: dict, financial_summary: dict,
                          tax_estimate: dict, assumptions: list[str], disclaimer: str):
        """Build and write a complete, beautifully formatted PDF report."""
        # Page dimensions: A4 is 595 x 842 points
        page_width, page_height = 595, 842
        margin = 50
        y = page_height - 60

        stream_cmds = []

        def draw_text(x, y_pos, text, font="F1", size=10):
            escaped = self._escape_pdf_str(text)
            return f"BT /{font} {size} Tf {x:.1f} {y_pos:.1f} Td ({escaped}) Tj ET\n"

        def draw_line(x1, y1, x2, y2, line_width=1):
            return f"{line_width} w {x1:.1f} {y1:.1f} m {x2:.1f} {y2:.1f} l S\n"

        def draw_rect(x, y_pos, w, h, fill_rgb=None, stroke_rgb=None):
            cmds = ""
            if fill_rgb:
                cmds += f"{fill_rgb[0]} {fill_rgb[1]} {fill_rgb[2]} rg {x:.1f} {y_pos:.1f} {w:.1f} {h:.1f} re f\n"
            if stroke_rgb:
                cmds += f"{stroke_rgb[0]} {stroke_rgb[1]} {stroke_rgb[2]} RG {x:.1f} {y_pos:.1f} {w:.1f} {h:.1f} re s\n"
            return cmds

        # Header Box
        stream_cmds.append(draw_rect(margin, y - 45, page_width - 2 * margin, 50, fill_rgb=(0.08, 0.45, 0.28)))
        stream_cmds.append(f"1 1 1 rg\n")  # white text
        stream_cmds.append(draw_text(margin + 15, y - 20, "FEDERAL REPUBLIC OF NIGERIA - SMALL BUSINESS FINANCIAL REPORT", font="F2", size=12))
        stream_cmds.append(draw_text(margin + 15, y - 36, "Revenue, Profit & Configurable Tax Estimation Statement", font="F1", size=10))
        stream_cmds.append(f"0 0 0 rg\n")  # reset black

        y -= 70

        # Business Metadata
        b_name = business.get("business_name", "Registered Enterprise")
        rc_no = business.get("rc_number", "RC-PENDING")
        tin = business.get("tin", "TIN-PENDING")
        b_type = business.get("business_type", "Limited Liability Company")
        currency = business.get("currency", "NGN")

        stream_cmds.append(draw_text(margin, y, f"Business Name : {b_name}", font="F2", size=11))
        stream_cmds.append(draw_text(margin + 300, y, f"RC/BN Number : {rc_no}", font="F1", size=10))
        y -= 16
        stream_cmds.append(draw_text(margin, y, f"Tax ID (TIN)  : {tin}", font="F1", size=10))
        stream_cmds.append(draw_text(margin + 300, y, f"Business Type : {b_type}", font="F1", size=10))
        y -= 16
        stream_cmds.append(draw_text(margin, y, f"Period Range  : {tax_estimate.get('period_label', 'Financial Period')}", font="F1", size=10))
        stream_cmds.append(draw_text(margin + 300, y, f"Reporting Currency : {currency}", font="F1", size=10))

        y -= 15
        stream_cmds.append(draw_line(margin, y, page_width - margin, y, line_width=1))
        y -= 25

        # Financial Performance Summary Section
        stream_cmds.append(draw_text(margin, y, "1. FINANCIAL PERFORMANCE & PROFITABILITY", font="F2", size=11))
        y -= 16

        fin_rows = [
            ("Gross Revenue / Turnover", f"NGN {financial_summary.get('total_revenue', 0.0):,.2f}"),
            ("Cost of Goods Sold (COGS)", f"NGN {financial_summary.get('cogs', 0.0):,.2f}"),
            ("Gross Profit", f"NGN {financial_summary.get('gross_profit', 0.0):,.2f}  ({financial_summary.get('gross_margin_percent', 0.0):.1f}%)"),
            ("Operating Expenses (OpEx)", f"NGN {financial_summary.get('operating_expenses', 0.0):,.2f}"),
            ("Net Profit Before Tax", f"NGN {financial_summary.get('net_profit', 0.0):,.2f}  ({financial_summary.get('net_margin_percent', 0.0):.1f}%)"),
        ]

        table_w = page_width - 2 * margin
        for label, val in fin_rows:
            stream_cmds.append(draw_rect(margin, y - 4, table_w, 18, fill_rgb=(0.95, 0.95, 0.95)))
            stream_cmds.append(draw_text(margin + 10, y, label, font="F1", size=10))
            stream_cmds.append(draw_text(margin + 300, y, val, font="F2", size=10))
            y -= 20

        y -= 15

        # Estimated Tax Obligations Section
        stream_cmds.append(draw_text(margin, y, "2. ESTIMATED TAX OBLIGATIONS (CONFIGURABLE NIGERIAN TAX RULES)", font="F2", size=11))
        y -= 16

        tax_rows = [
            (f"Companies Income Tax (CIT @ {tax_estimate.get('cit_rate_applied', 0.0)*100:.0f}%)", f"NGN {tax_estimate.get('estimated_cit', 0.0):,.2f}"),
            ("Tertiary Education Tax (EDT @ 3% Assessable Profit)", f"NGN {tax_estimate.get('estimated_edt', 0.0):,.2f}"),
            ("Net VAT Position (Output VAT Collected)", f"NGN {tax_estimate.get('estimated_vat_collected', 0.0):,.2f}"),
            ("Minimum Tax Assessment (if applicable)", f"NGN {tax_estimate.get('estimated_minimum_tax', 0.0):,.2f}"),
            ("TOTAL ESTIMATED TAX OBLIGATION", f"NGN {tax_estimate.get('estimated_total_tax', 0.0):,.2f}"),
        ]

        for label, val in tax_rows:
            is_total = "TOTAL" in label
            fill = (0.88, 0.94, 0.90) if is_total else (0.98, 0.98, 0.98)
            font_choice = "F2" if is_total else "F1"
            stream_cmds.append(draw_rect(margin, y - 4, table_w, 18, fill_rgb=fill))
            stream_cmds.append(draw_text(margin + 10, y, label, font=font_choice, size=10))
            stream_cmds.append(draw_text(margin + 300, y, val, font="F2", size=10))
            y -= 20

        y -= 15

        # Assumptions Box
        stream_cmds.append(draw_text(margin, y, "3. KEY CALCULATION ASSUMPTIONS", font="F2", size=11))
        y -= 16
        for assumption in assumptions[:5]:
            stream_cmds.append(draw_text(margin + 10, y, f"- {assumption}", font="F1", size=8.5))
            y -= 13

        y -= 15

        # Prominent Disclaimer Box (Mandatory Requirement)
        stream_cmds.append(draw_rect(margin, y - 45, table_w, 55, fill_rgb=(1.0, 0.95, 0.85), stroke_rgb=(0.85, 0.45, 0.1)))
        stream_cmds.append(draw_text(margin + 10, y - 10, "IMPORTANT NOTICE / STATUTORY DISCLAIMER:", font="F2", size=9))

        # Split disclaimer into two lines
        stream_cmds.append(draw_text(margin + 10, y - 24, "This calculation is an indicative estimate for planning purposes only and does NOT constitute", font="F1", size=8))
        stream_cmds.append(draw_text(margin + 10, y - 36, "an official tax assessment or legal advice. Final tax liabilities must be filed with FIRS / SIRS.", font="F1", size=8))

        content_stream = "".join(stream_cmds)

        # Assemble PDF Objects
        # 1 0 obj: Catalog
        # 2 0 obj: Outlines
        # 3 0 obj: Pages
        # 4 0 obj: Page
        # 5 0 obj: Content stream
        # 6 0 obj: Font F1 (Helvetica)
        # 7 0 obj: Font F2 (Helvetica-Bold)

        stream_bytes = content_stream.encode("latin-1")
        stream_len = len(stream_bytes)

        pdf_objs = [
            # 1: Catalog
            b"<< /Type /Catalog /Pages 3 0 R >>",
            # 2: Outlines
            b"<< /Type /Outlines /Count 0 >>",
            # 3: Pages
            b"<< /Type /Pages /Kids [4 0 R] /Count 1 >>",
            # 4: Page
            f"<< /Type /Page /Parent 3 0 R /MediaBox [0 0 {page_width} {page_height}] /Contents 5 0 R /Resources << /Font << /F1 6 0 R /F2 7 0 R >> >> >>".encode("latin-1"),
            # 5: Stream
            f"<< /Length {stream_len} >>\nstream\n".encode("latin-1") + stream_bytes + b"\nendstream",
            # 6: Font F1
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            # 7: Font F2
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        ]

        # Build output with cross-reference table
        output = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
        xref_offsets = [0]  # dummy offset for object 0

        for i, obj_content in enumerate(pdf_objs, start=1):
            offset = sum(len(part) for part in output)
            xref_offsets.append(offset)
            output.append(f"{i} 0 obj\n".encode("latin-1"))
            output.append(obj_content)
            output.append(b"\nendobj\n")

        xref_pos = sum(len(part) for part in output)
        output.append(b"xref\n")
        output.append(f"0 {len(pdf_objs) + 1}\n".encode("latin-1"))
        output.append(b"0000000000 65535 f \n")
        for offset in xref_offsets[1:]:
            output.append(f"{offset:010d} 00000 n \n".encode("latin-1"))

        output.append(b"trailer\n")
        output.append(f"<< /Size {len(pdf_objs) + 1} /Root 1 0 R >>\n".encode("latin-1"))
        output.append(b"startxref\n")
        output.append(f"{xref_pos}\n".encode("latin-1"))
        output.append(b"%%EOF\n")

        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(b"".join(output))

        return file_path
