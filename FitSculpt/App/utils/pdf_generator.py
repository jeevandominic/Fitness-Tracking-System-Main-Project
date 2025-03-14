from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import os

class MentalFitnessReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the report"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#ff7700'),
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#333333'),
        ))
        
        self.styles.add(ParagraphStyle(
            name='ResultItem',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=8,
            textColor=colors.HexColor('#666666'),
        ))
        
        self.styles.add(ParagraphStyle(
            name='Suggestion',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leftIndent=20,
            textColor=colors.HexColor('#444444'),
        ))

    def _create_header(self, elements):
        """Add header section to the report"""
        title = Paragraph("Mental Fitness Assessment Report", self.styles['CustomTitle'])
        date = Paragraph(
            f"Generated on: {datetime.now().strftime('%B %d, %Y')}",
            self.styles['Normal']
        )
        elements.extend([title, date, Spacer(1, 20)])

    def _add_results_section(self, elements, predictions):
        """Add the prediction results section"""
        header = Paragraph("Assessment Results", self.styles['SectionHeader'])
        elements.extend([header, Spacer(1, 10)])

        # Create results table
        data = [[Paragraph("Metric", self.styles['Heading2']), 
                Paragraph("Value", self.styles['Heading2'])]]
        
        for key, value in predictions.items():
            formatted_key = key.replace('_', ' ').title()
            data.append([
                Paragraph(formatted_key, self.styles['Normal']),
                Paragraph(str(value), self.styles['Normal'])
            ])

        table = Table(data, colWidths=[4*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff7700')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#333333')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))
        
        elements.extend([table, Spacer(1, 20)])

    def _add_suggestions_section(self, elements, suggestions):
        """Add the suggestions section"""
        header = Paragraph("Personalized Wellness Recommendations", self.styles['SectionHeader'])
        elements.extend([header, Spacer(1, 10)])

        for category in suggestions:
            cat_header = Paragraph(category['title'], self.styles['Heading3'])
            elements.extend([cat_header, Spacer(1, 5)])

            for suggestion in category['suggestions']:
                priority_color = {
                    'high': colors.HexColor('#ff4444'),
                    'medium': colors.HexColor('#ffbb33'),
                    'low': colors.HexColor('#00C851')
                }.get(suggestion['priority'], colors.black)

                bullet_style = ParagraphStyle(
                    f'Priority{suggestion["priority"].title()}',
                    parent=self.styles['Suggestion'],
                    textColor=priority_color,
                    bulletIndent=10,
                    leftIndent=30
                )

                p = Paragraph(
                    f"• {suggestion['text']}", 
                    bullet_style
                )
                elements.append(p)
            
            elements.append(Spacer(1, 10))

    def generate_report(self, output_path, predictions, suggestions):
        """Generate the complete PDF report"""
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        elements = []
        
        # Add report sections
        self._create_header(elements)
        self._add_results_section(elements, predictions)
        self._add_suggestions_section(elements, suggestions)
        
        try:
            # Build the PDF
            doc.build(elements)
            return output_path
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            raise 