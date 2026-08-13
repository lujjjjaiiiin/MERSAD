"""
home.py — الصفحة الرئيسية (نظرة عامة) لتطبيق مرصاد.
يُستدعى هذا الملف عبر نظام التنقل بـ app.py (st.navigation).
"""

import streamlit as st
import plotly.express as px

from utils.data_processing import load_data, global_kpis, RISK_LABELS_AR
from utils.insights import generate_home_insights
from utils.ui import inject_css, page_header, kpi_card, insight_card, section_title, nav_card

inject_css()

df = load_data()
kpis = global_kpis(df)

page_header(
    subtitle="نرصد اليوم، نتوقع الغد — منصة ذكية لتحليل أنماط الجرائم وتوجيه القرار",
    status_text=f"🟢 النظام متصل بـ {kpis['total_incidents']:,} حادثة محلّلة".replace(",", "٬"),
)

# ===== نظرة عامة سريعة =====
section_title("📊", "نظرة عامة")

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    kpi_card("📁", f"{kpis['total_incidents']:,}", "إجمالي الحوادث بالعينة")
with c2:
    kpi_card("🗺️", f"{kpis['n_areas']}", "عدد المناطق المغطّاة")
with c3:
    kpi_card("🚨", kpis["top_crime"], f"أكثر الجرائم انتشارًا ({kpis['top_crime_share']:.0f}%)")
with c4:
    kpi_card("📍", f"منطقة {kpis['top_risk_area']}", f"الأعلى خطورة (مؤشر {kpis['top_risk_score']:.0f}/100)")
with c5:
    kpi_card("⏰", kpis["top_period"], "الفترة الزمنية الأعلى نشاطًا")

st.markdown("<br>", unsafe_allow_html=True)

col_a, col_b = st.columns([1.3, 1])

with col_a:
    section_title("💡", "ما الذي يحدث الآن؟")
    for insight in generate_home_insights(df):
        insight_card(insight["icon"], insight["text"])

with col_b:
    section_title("🧭", "توزيع مستوى الخطورة العام")
    risk_counts = df["risk_level"].value_counts().reindex(["Low", "Medium", "High"]).fillna(0)
    risk_counts_ar = [RISK_LABELS_AR[r] for r in risk_counts.index]
    fig = px.pie(
        values=risk_counts.values,
        names=risk_counts_ar,
        hole=0.55,
        color=risk_counts_ar,
        color_discrete_map={"منخفض": "#3FA66B", "متوسط": "#E8B84B", "مرتفع": "#E0793A"},
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),
        height=300,
        font_family="IBM Plex Sans Arabic",
    )
    st.plotly_chart(fig, width='stretch')
    st.markdown(
        f'<p class="mersad-caption">{kpis["overall_high_share"]:.0f}% من إجمالي الحوادث تقع ضمن نطاق الخطورة المرتفعة تاريخيًا.</p>',
        unsafe_allow_html=True,
    )

st.markdown('<hr class="mersad-divider">', unsafe_allow_html=True)

# ===== تنقّل سريع =====
section_title("🚀", "استكشف مرصاد")

n1, n2, n3, n4, n5, n6 = st.columns(6)
nav_items = [
    ("🗺️", "الخريطة التفاعلية", "استكشاف جغرافي للحوادث ومستوى الخطورة"),
    ("📊", "تحليل الجرائم", "أنماط الوقت والنوع والموقع"),
    ("🎯", "تقييم الخطورة", "تقدير الخطورة بالذكاء الاصطناعي"),
    ("🧭", "تخطيط الموارد", "محاكي توزيع الموارد الذكي"),
    ("💡", "التوصيات", "توصيات مبنية على البيانات"),
    ("⚖️", "قارن المناطق", "مقارنة تفصيلية بين المناطق"),
]
for col, (icon, title, desc) in zip([n1, n2, n3, n4, n5, n6], nav_items):
    with col:
        nav_card(icon, title, desc)

st.markdown(
    """
    <p class="mersad-caption" style="text-align:center; margin-top: 24px;">
    مرصاد | MERSAD — نموذج أولي لدعم القرار مبني على بيانات جرائم شيكاغو العامة (عينة تحليلية من الداتاست المنظف).
    الأرقام والتوصيات تعليمية/تحليلية ولا تمثل قرارات تشغيلية حقيقية.
    </p>
    """,
    unsafe_allow_html=True,
)
