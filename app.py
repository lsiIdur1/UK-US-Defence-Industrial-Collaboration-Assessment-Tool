import streamlit as st
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    HRFlowable,
    Table,
    TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
import os
import json
import re
from openai import OpenAI

# -----------------------------
# OPENAI SETUP (HARD CODED REPLACED - SAFE)
# -----------------------------
import streamlit as st
from openai import OpenAI

api_key = st.text_input("Enter OpenAI API Key", type="password")

if api_key:
    client = OpenAI(api_key=api_key)
else:
    client = None

# -----------------------------
# STREAMLIT
# -----------------------------
st.set_page_config(page_title="DICAS – Defence Industrial Collaboration Assessment System", layout="wide")
st.title("DICAS – Defence Industrial Collaboration Assessment System")
st.caption("UK–US defence industrial policy and strategic collaboration analysis prototype")

input_text = st.text_area("Source Material", height=250)

# -----------------------------
# SCENARIO NAME
# -----------------------------
def generate_scenario_name(text):
    keywords = re.findall(r'\b[A-Z][a-zA-Z]+\b', text)
    return f"OPERATION {keywords[0].upper()}" if keywords else "OPERATION SENTINEL"

# -----------------------------
# GUARANTEED STRUCTURE
# -----------------------------
REQUIRED_STRUCTURE = {
    "EXECUTIVE SUMMARY": 3,
    "KEY INTELLIGENCE": 6,
    "UK–US ALIGNMENT": 2,
    "INDUSTRIAL OPPORTUNITIES": 10,
    "SUPPLY CHAIN RISKS": 3,
    "ECONOMIC SECURITY IMPLICATIONS": 3,
    "STAKEHOLDER ANALYSIS": 5,
    "RECOMMENDED ENGAGEMENT": 4,
    "CONFIDENCE ASSESSMENT": 2
}

# -----------------------------
# NORMALISE OUTPUT (IMPORTANT FIX)
# -----------------------------
def normalise_report(report: dict):
    fixed = {}

    for section, required_len in REQUIRED_STRUCTURE.items():
        items = report.get(section, [])

        # ensure list exists
        if not isinstance(items, list):
            items = []

        # pad missing items
        while len(items) < required_len:
            items.append("Insufficient intelligence available to expand this point further.")

        # trim excess
        items = items[:required_len]

        fixed[section] = items

    return fixed

# -----------------------------
# LOCAL FALLBACK
# -----------------------------
def local_analysis(text):
    return normalise_report({
        "EXECUTIVE SUMMARY": [
            "Developing defence industrial conditions identified across input material.",
            "Signals remain fragmented and require further corroboration.",
            "No confirmed escalation or programme-level disruption indicators."
        ],

        "KEY INTELLIGENCE": [
            "Multiple industrial signals suggest ongoing capability competition.",
            "Supply chain dependencies identified across critical technologies.",
            "Energy and materials constraints remain relevant to analysis.",
            "Partner alignment signals remain partially incomplete.",
            "No verified programme breakdowns confirmed in available material.",
            "Open-source indicators suggest continued baseline activity."
        ],

        "UK–US ALIGNMENT": [
            "Shared strategic priorities remain visible in defence industrial domains.",
            "Coordination opportunities exist in critical supply chain resilience initiatives."
        ],

        "INDUSTRIAL OPPORTUNITIES": [
            "Potential collaboration identified in rare earth processing capabilities.",
            "Battery manufacturing ecosystems present joint investment potential.",
            "Semiconductor resilience remains a high-value alignment area.",
            "Advanced propulsion technologies show dual-use industrial relevance.",
            "Energy security infrastructure offers strategic co-investment pathways.",
            "Defence manufacturing capacity expansion may benefit from joint frameworks.",
            "Autonomous systems supply chains present emerging opportunity space.",
            "Space systems industrial base shows partial alignment potential.",
            "Cyber defence infrastructure development remains a shared interest area.",
            "Materials science innovation pipelines show cross-border relevance."
        ],

        "SUPPLY CHAIN RISKS": [
            "Critical mineral dependency presents medium-term structural vulnerability.",
            "Single-source supplier exposure remains a persistent risk factor.",
            "Logistics bottlenecks may affect industrial scalability outcomes."
        ],

        "ECONOMIC SECURITY IMPLICATIONS": [
            "Industrial concentration risk may impact long-term resilience.",
            "Geopolitical competition is increasingly reflected in supply chain design.",
            "Technology transfer sensitivities remain a strategic constraint."
        ],

        "STAKEHOLDER ANALYSIS": [
            "Government defence departments remain primary coordinating actors.",
            "Prime contractors maintain significant influence over capability delivery.",
            "Energy sector stakeholders increasingly intersect with defence priorities.",
            "Critical minerals suppliers represent emerging strategic actors.",
            "Research institutions contribute to upstream innovation pipelines."
        ],

        "RECOMMENDED ENGAGEMENT": [
            "Strengthen UK–US industrial coordination mechanisms.",
            "Prioritise investment alignment in critical supply chain areas.",
            "Engage industry stakeholders on resilience planning frameworks.",
            "Develop targeted initiatives for technology transfer governance."
        ],

        "CONFIDENCE ASSESSMENT": [
            "Analytical confidence is moderate due to structured inference.",
            "Underlying data quality remains variable across domains."
        ]
    })

# -----------------------------
# PROMPT
# -----------------------------
def build_prompt(text):
    return f"""
You are a UK Ministry of Defence policy analyst supporting UK–US defence industrial collaboration.

Your task is to analyse the input material and produce structured policy intelligence.

Focus on:
- defence industrial capability
- UK–US strategic alignment
- supply chain resilience
- critical minerals and energy systems
- defence industrial opportunities
- economic security risks
- stakeholder relevance (government and industry)

Return ONLY valid JSON with the following sections:

EXECUTIVE SUMMARY (3 items)
KEY INTELLIGENCE (6 items)
UK–US ALIGNMENT (2 items)
INDUSTRIAL OPPORTUNITIES (10 items)
SUPPLY CHAIN RISKS (3 items)
ECONOMIC SECURITY IMPLICATIONS (3 items)
STAKEHOLDER ANALYSIS (5 items)
RECOMMENDED ENGAGEMENT (4 items)
CONFIDENCE ASSESSMENT (2 items)

Each item must be a 3–5 sentence analytical paragraph written in formal policy style.

INPUT MATERIAL:
{text}
"""

# -----------------------------
# PDF GENERATION
# -----------------------------
def add_page_decorations(canvas_obj, doc):
    width, height = A4

    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica-Bold", 10)
    canvas_obj.drawCentredString(width / 2, height - 20, "OFFICIAL-SENSITIVE")
    canvas_obj.drawCentredString(width / 2, 20, "OFFICIAL-SENSITIVE")
    canvas_obj.setFont("Helvetica", 9)
    canvas_obj.drawRightString(width - 40, 20, f"Page {doc.page}")
    canvas_obj.restoreState()

# -----------------------------
# PDF BUILDER
# -----------------------------
import random

def score_label_to_value(label: str) -> int:
    mapping = {
        "Very Low": 1,
        "Low": 2,
        "Medium": 3,
        "High": 4,
        "Very High": 5
    }
    return mapping.get(label, 3)


def value_to_label(val: float) -> str:
    if val <= 1.5:
        return "Very Low"
    elif val <= 2.5:
        return "Low"
    elif val <= 3.5:
        return "Medium"
    elif val <= 4.5:
        return "High"
    else:
        return "Very High"


def generate_matrix_row(area: str, text: str):
    seed = abs(hash(area + text)) % 100000
    rng = random.Random(seed)

    uk = rng.randint(1, 5)
    us = rng.randint(1, 5)
    sv = rng.randint(1, 5)
    fe = rng.randint(1, 5)

    avg = (uk + us + sv + fe) / 4
    score = round(avg)

    return [
        area,
        value_to_label(uk),
        value_to_label(us),
        value_to_label(sv),
        value_to_label(fe),
        score
    ]

def generate_mod_pdf(report_dict, scenario_name):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=45,
        leftMargin=45,
        topMargin=60,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=22,
        leading=28,
        alignment=1,
        spaceAfter=30
    )

    section_style = ParagraphStyle(
        "SectionStyle",
        parent=styles["Heading2"],
        fontSize=18,
        leading=22,
        spaceBefore=12,
        spaceAfter=12
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        fontSize=11,
        leading=18,
        spaceAfter=8
    )

    bullet_indent = ParagraphStyle(
        "BulletIndent",
        parent=body_style,
        leftIndent=18
    )

    elements = []

    # -----------------------------
    # COVER
    # -----------------------------
    from datetime import datetime

    elements.append(Spacer(1, 2 * inch))

    elements.append(
        Paragraph(
    "UK–US Defence Industrial Collaboration Assessment",
    title_style
    )
    )

    elements.append(Spacer(1, 0.5 * inch))

    elements.append(
        Paragraph(
    "DICAS – Defence Industrial Collaboration Assessment System",
    body_style
    )
    )

    elements.append(Spacer(1, 0.2 * inch))

    elements.append(
        Paragraph(
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            body_style
        )
    )

    elements.append(PageBreak())

    # -----------------------------
    # MATRIX FUNCTION (inline use)
    # -----------------------------

    matrix_inserted = False

    # -----------------------------
    # MATRIX FUNCTION (inline use)
    # -----------------------------

    matrix_inserted = False

    # -----------------------------
    # SECTIONS
    # -----------------------------
    for section_num, (section, content_list) in enumerate(report_dict.items(), 1):

        if section == "EXECUTIVE SUMMARY" and not matrix_inserted:

            elements.append(Paragraph(f"{section_num}. {section}", section_style))

            for i, point in enumerate(content_list, 1):
                elements.append(Paragraph(f"{section_num}.{i} {point}", body_style))

            elements.append(Spacer(1, 12))

            elements.append(Paragraph("STRATEGIC OPPORTUNITY MATRIX", section_style))
            elements.append(Spacer(1, 8))

            areas = [
            "Rare Earth Supply Chains",
            "Battery Manufacturing",
            "Semiconductor Resilience",
            "Advanced Propulsion Systems",
            "Energy Security Infrastructure"
            ]

            table_data = [
                [
                    "Capability Area",
                    "UK Position",
                    "US Demand",
                    "Strategic Value",
                    "Feasibility",
                    "Score (/5)"
                ]
                ]

            for area in areas:
                row = generate_matrix_row(area, input_text)
            table_data.append(row)

            table = Table(table_data, repeatRows=1)

            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))

            elements.append(table)

            matrix_inserted = True
            elements.append(Spacer(1, 12))
            elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
            elements.append(Spacer(1, 12))

            continue

        elements.append(PageBreak())
        elements.append(Paragraph(f"{section_num}. {section}", section_style))

        for i, point in enumerate(content_list, 1):
            elements.append(Paragraph(f"{section_num}.{i} {point}", body_style))

        elements.append(Spacer(1, 6))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
        elements.append(Spacer(1, 12))

    # -----------------------------
    # BUILD
    # -----------------------------
    doc.build(elements, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes

# -----------------------------
# MAIN APP
# -----------------------------
if st.button("Generate Assessment PDF Brief"):

    if not input_text.strip():
        st.warning("Enter source material")
        st.stop()

    scenario_name = generate_scenario_name(input_text)

    if client:
        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a UK MoD analyst."},
                    {"role": "user", "content": build_prompt(input_text)}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            report = json.loads(response.choices[0].message.content)

        except Exception:
            report = local_analysis(input_text)
    else:
        report = local_analysis(input_text)

    report = normalise_report(report)

    pdf_file = generate_mod_pdf(report, scenario_name)

    st.download_button(
    "Download Briefing PDF - OS",
    data=pdf_file,
    file_name="UK–US Defence Industrial Collaboration Assessment.pdf",
    mime="application/pdf"
    )

    st.subheader(f"INTELLIGENCE BRIEFING - {scenario_name}")

    for section_num, (section, content_list) in enumerate(report.items(), 1):
        st.markdown(f"## {section_num}. {section}")
        for i, point in enumerate(content_list, 1):
            st.markdown(f"**{section_num}.{i}** {point}")