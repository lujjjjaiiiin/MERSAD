"""
5_💡_التوصيات.py — توصيات ديناميكية مبنية على مؤشر الخطورة الفعلي لكل منطقة.
"""

import streamlit as st

from utils.data_processing import load_data
from utils.insights import generate_recommendations
from utils.ui import inject_css, page_header, section_title, recommendation_card

inject_css()

df = load_data()

page_header(subtitle="توصيات مرصاد — مبنية على البيانات وليست عامة")

with st.sidebar:
    st.markdown("### 🔎 عدد التوصيات")
    top_n = st.slider("عدد المناطق المشمولة", 3, 15, 6)

recs = generate_recommendations(df, top_n=top_n)

section_title("💡", f"أعلى {len(recs)} مناطق أولوية")
st.caption("كل توصية مبنية على: المشكلة، السبب المستخرج من البيانات، الإجراء المقترح، والبيانات الداعمة.")

for rec in recs:
    recommendation_card(rec)
