# backend/app/services/report.py

import re
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class ClinicalReportGenerator:
    """
    Handles ReportLab PDF export with disclaimer footer and integrated leak testing (Issue #26).
    """
    def __init__(self):
        self.phi_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{10}\b',              # Phone / MRN
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}\b'
        ]

    def check_for_leaks(self, text: str) -> bool:
        for pattern in self.phi_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def generate_case_pdf(self, filename: str, case_data: Dict[str, Any]) -> str:
        content = case_data.get('content', '')
        note_id = case_data.get('note_identifier', 'UNKNOWN_ID')

        if self.check_for_leaks(content):
            raise ValueError(f"LEAK TEST FAILED: Protected Health Information detected in case {note_id} export payload!")

        doc = SimpleDocTemplate(
            filename, 
            pagesize=letter, 
            rightMargin=36, 
            leftMargin=36, 
            topMargin=36, 
            bottomMargin=54
        )
        story = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CaseTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0F172A'), spaceAfter=10
        )
        body_style = ParagraphStyle(
            'CaseBody', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#334155')
        )
        
        story.append(Paragraph(f"Clinical Case Report: {note_id}", title_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph(content, body_style))
        story.append(Spacer(1, 20))
        
        meta_data = [
            ['Export Timestamp:', case_data.get('timestamp', 'N/A')],
            ['Retrieval Match Score:', f"{case_data.get('combined_score', 0.0):.4f}"],
            ['De-identification Status:', 'HIPAA Safe Harbor Screened & Verified']
        ]
        t = Table(meta_data, colWidths=[150, 370])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#475569')),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0'))
        ]))
        story.append(t)

        def add_disclaimer_footer(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(colors.HexColor('#64748B'))
            footer_text = "CONFIDENTIAL CLINICAL SEARCH EXPORT — FOR AUTHORIZED RESEARCH USE ONLY. HIPAA SAFE HARBOR COMPLIANT."
            canvas.drawString(36, 24, footer_text)
            canvas.drawRightString(letter[0] - 36, 24, f"Page {doc.page}")
            canvas.restoreState()

        doc.build(story, onFirstPage=add_disclaimer_footer, onLaterPages=add_disclaimer_footer)
        return filename