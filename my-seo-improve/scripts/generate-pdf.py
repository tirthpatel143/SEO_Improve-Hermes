from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def generate_professional_pdf():
    doc = SimpleDocTemplate("runtime/outputs/seo-report.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph("AI SEO Executive Report", styles['Title']), Spacer(1, 12)]
    
    # Metrics Table
    data = [["Metric", "Value"], ["Score", "82/100"], ["Potential Revenue", "+$65k"]]
    story.append(Table(data, style=[('GRID', (0,0), (-1,-1), 1, colors.black)]))
    
    doc.build(story)
    print("✅ Professional PDF generated.")

if __name__ == "__main__":
    generate_professional_pdf()