"""
app.py — نقطة الدخول ونظام التنقل لتطبيق مرصاد (MERSAD).

أسماء ملفات الصفحات إنجليزية بالكامل (views/*.py) لتفادي مشاكل ترميز
الملفات (عربي/إيموجي) عند الرفع لمنصات مثل GitHub / Streamlit Cloud،
بينما العناوين والأيقونات المعروضة بالشريط الجانبي عربية بالكامل عبر st.Page.
"""

import streamlit as st

from utils.ui import inject_css

st.set_page_config(
    page_title="مرصاد | MERSAD",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

home = st.Page("views/home.py", title="نظرة عامة", icon="🏠", default=True)
interactive_map = st.Page("views/interactive_map.py", title="الخريطة التفاعلية", icon="🗺️")
crime_analysis = st.Page("views/crime_analysis.py", title="تحليل الجرائم", icon="📊")
risk_assessment = st.Page("views/risk_assessment.py", title="تقييم الخطورة", icon="🎯")
resource_planning = st.Page("views/resource_planning.py", title="تخطيط الموارد", icon="🧭")
recommendations = st.Page("views/recommendations.py", title="التوصيات", icon="💡")
compare_areas = st.Page("views/compare_areas.py", title="قارن المناطق", icon="⚖️")
reports = st.Page("views/reports.py", title="التقارير", icon="🧾")

pg = st.navigation(
    {
        "مرصاد": [home],
        "الاستكشاف والتحليل": [interactive_map, crime_analysis, compare_areas],
        "دعم القرار": [risk_assessment, resource_planning, recommendations],
        "التقارير": [reports],
    }
)

pg.run()
