from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def euro(value): return f"EUR {value:,.2f}"


def build_payslip_pdf(entry):
    buffer = BytesIO(); styles = getSampleStyleSheet(); styles.add(ParagraphStyle(name="Right", parent=styles["BodyText"], alignment=TA_RIGHT)); brand = colors.HexColor("#126761")
    document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=18*mm, bottomMargin=18*mm, title=f"Payslip - {entry.employee_name}")
    story = [Table([[Paragraph(f"<b>{entry.period.company.name}</b>", styles["Title"]), Paragraph("PAYSLIP", styles["Right"])]], colWidths=[105*mm, 55*mm]), Paragraph(entry.period.company.address.replace("\n", "<br/>"), styles["BodyText"]), Spacer(1, 8*mm)]
    details = [["Employee", entry.employee_name, "Employee ID", entry.employee_number], ["Pay period", f"{entry.period.start_date:%d/%m/%Y} - {entry.period.end_date:%d/%m/%Y}", "Pay date", f"{entry.period.pay_date:%d/%m/%Y}"], ["Payment type", entry.get_payment_type_display(), "Frequency", entry.period.get_frequency_display()]]
    table = Table(details, colWidths=[28*mm, 55*mm, 28*mm, 49*mm]); table.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.4,colors.HexColor("#d7e1e4")),("BACKGROUND",(0,0),(0,-1),colors.HexColor("#f3f7f8")),("BACKGROUND",(2,0),(2,-1),colors.HexColor("#f3f7f8")),("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),("FONTNAME",(2,0),(2,-1),"Helvetica-Bold"),("PADDING",(0,0),(-1,-1),7)])); story.extend([table, Spacer(1,8*mm)])
    earnings = [["Earnings", "Basis", "Amount"], ["Regular pay", f"{entry.hours_worked:.2f} hours x {euro(entry.hourly_rate)}", euro(entry.gross_pay)]] if entry.payment_type == "HOURLY" else [["Earnings", "Basis", "Amount"], ["Monthly salary", "Fixed monthly salary", euro(entry.gross_pay)]]
    deductions = [["Deductions","Amount"],["PAYE",euro(entry.paye)],["USC",euro(entry.usc)],["PRSI",euro(entry.prsi)],["Other deductions",euro(entry.other_deductions)],["Total deductions",euro(entry.total_deductions)]]
    common=[("GRID",(0,0),(-1,-1),.4,colors.HexColor("#d7e1e4")),("BACKGROUND",(0,0),(-1,0),brand),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("ALIGN",(-1,1),(-1,-1),"RIGHT"),("PADDING",(0,0),(-1,-1),8)]
    earnings_table=Table(earnings,colWidths=[55*mm,65*mm,40*mm]); deductions_table=Table(deductions,colWidths=[120*mm,40*mm]); earnings_table.setStyle(TableStyle(common)); deductions_table.setStyle(TableStyle(common+[("FONTNAME",(0,-1),(-1,-1),"Helvetica-Bold")]))
    net=Table([["NET PAY",euro(entry.net_pay)]],colWidths=[120*mm,40*mm]); net.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#d5efeb")),("TEXTCOLOR",(0,0),(-1,-1),colors.HexColor("#10534f")),("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),14),("ALIGN",(1,0),(1,0),"RIGHT"),("BOX",(0,0),(-1,-1),1,brand),("PADDING",(0,0),(-1,-1),12)]))
    story.extend([earnings_table,Spacer(1,6*mm),deductions_table,Spacer(1,6*mm),net,Spacer(1,8*mm),Paragraph("PAYE, USC and PRSI were entered manually. This payslip does not represent an automated Irish tax calculation or a submission to Revenue.",styles["Italic"])]); document.build(story); return buffer.getvalue()
