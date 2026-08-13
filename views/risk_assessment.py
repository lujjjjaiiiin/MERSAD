"""
3_🎯_تقييم_الخطورة.py — أداة Risk Assessment تفاعلية مبنية على موديل XGBoost المدرّب فعليًا
بمشروع مرصاد (لا ادّعاء بالتنبؤ بجريمة فردية — تقدير مستوى خطورة إحصائي بناءً على الأنماط التاريخية).
"""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils.data_processing import (
    load_data,
    load_model,
    load_feature_cols,
    predict_risk,
    DAY_NAMES_AR,
    MONTH_NAMES_AR,
    RISK_LABELS_AR,
    RISK_COLORS,
)
from utils.ui import inject_css, page_header, section_title, risk_badge_html

inject_css()

df = load_data()
model = load_model()
feature_cols = load_feature_cols()

page_header(subtitle="تقييم الخطورة — Risk Assessment بالذكاء الاصطناعي")

st.markdown(
    """
    <div class="mersad-insight" style="border-color: var(--mersad-forest);">
        <div>ℹ️</div>
        <div>هذه الأداة لا "تتنبأ بجريمة" بعينها؛ هي تقدير إحصائي لمستوى الخطورة بناءً على الأنماط
        التاريخية في بيانات شيكاغو، باستخدام موديل XGBoost المدرّب بمشروع مرصاد
        (دقة تقريبية ٨٧٪ على بيانات الاختبار). النتيجة أداة دعم قرار، وليست حكمًا نهائيًا.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

section_title("🧾", "أدخلي سيناريو لتقييمه")

col1, col2, col3 = st.columns(3)

with col1:
    district = st.selectbox("District (الحي الشرطي)", sorted(df["District"].unique().tolist()))
    beats_in_district = sorted(df[df["District"] == district]["Beat"].unique().tolist())
    beat = st.selectbox("Beat (القطاع)", beats_in_district)
    crime_type = st.selectbox("نوع الجريمة", sorted(df["Primary Type"].unique().tolist()))

with col2:
    location_desc = st.selectbox("نوع الموقع", sorted(df["Location Description"].unique().tolist()))
    day_ar = st.selectbox("يوم الأسبوع", DAY_NAMES_AR)
    month_ar = st.selectbox("الشهر", MONTH_NAMES_AR)

with col3:
    hour = st.slider("الساعة", 0, 23, 20)
    arrest = st.toggle("تم القبض؟", value=False)
    domestic = st.toggle("حادثة أسرية (Domestic)؟", value=False)

day_idx = DAY_NAMES_AR.index(day_ar)
month_idx = MONTH_NAMES_AR.index(month_ar) + 1
is_weekend = day_idx in [5, 6]

# إحداثيات القطاع (Beat) المختار — من متوسط بيانات فعلية، بدون أي اختلاق
beat_geo = df[df["Beat"] == beat][["Latitude", "Longitude"]].mean()

# استخدام نفس أكواد الترميز الأصلية المحفوظة بالعمود (بدل إعادة استنتاجها)
pt_code = df[df["Primary Type"] == crime_type]["Primary Type Code"].iloc[0]
loc_code = df[df["Location Description"] == location_desc]["Location Code"].iloc[0]

input_row = {
    "District": district,
    "Beat": beat,
    "day_of_week": day_idx,
    "month": month_idx,
    "is_weekend": is_weekend,
    "Primary Type": pt_code,
    "Location Description": loc_code,
    "Arrest": arrest,
    "Domestic": domestic,
    "Latitude": beat_geo["Latitude"],
    "Longitude": beat_geo["Longitude"],
}

st.markdown('<hr class="mersad-divider">', unsafe_allow_html=True)

if st.button("🎯 قيّمي مستوى الخطورة", type="primary", width='stretch'):
    label, proba = predict_risk(model, feature_cols, input_row)

    res_col1, res_col2 = st.columns([1, 1.4])

    with res_col1:
        section_title("📌", "النتيجة")
        st.markdown(
            f"""
            <div class="mersad-kpi" style="text-align:center; padding: 26px;">
                <div style="font-size:14px; color: var(--mersad-muted);">مستوى الخطورة المتوقع</div>
                <div style="margin: 10px 0;">{risk_badge_html(label)}</div>
                <div class="mersad-num" style="font-size: 30px; font-weight:700; color: var(--mersad-forest);">
                    {proba[label]*100:.0f}%
                </div>
                <div style="font-size:12.5px; color: var(--mersad-muted);">درجة الثقة بالتصنيف</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with res_col2:
        section_title("📊", "توزيع الاحتمالات على المستويات الثلاث")
        proba_df = pd.DataFrame(
            {"المستوى": [RISK_LABELS_AR[k] for k in proba.keys()], "الاحتمال": [v * 100 for v in proba.values()]}
        )
        color_map_ar = {"منخفض": "#3FA66B", "متوسط": "#E8B84B", "مرتفع": "#E0793A"}
        fig = px.bar(
            proba_df, x="الاحتمال", y="المستوى", orientation="h", color="المستوى",
            color_discrete_map=color_map_ar, text="الاحتمال",
        )
        fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
        fig.update_layout(
            showlegend=False, height=260, xaxis_range=[0, 100],
            font_family="IBM Plex Sans Arabic", margin=dict(t=10, l=10, r=10, b=10),
        )
        st.plotly_chart(fig, width='stretch')

    st.markdown('<hr class="mersad-divider">', unsafe_allow_html=True)
    section_title("🔍", "أهم العوامل المؤثرة على الموديل عمومًا")
    st.caption("أهمية الميزات هذه عامة على مستوى الموديل ككل (Global Feature Importance)، وليست تفسيرًا خاصًا بهذه الحالة تحديدًا.")

    importances = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=True)
    fig_imp = px.bar(x=importances.values, y=importances.index, orientation="h")
    fig_imp.update_traces(marker_color="#178A70")
    fig_imp.update_layout(height=380, font_family="IBM Plex Sans Arabic", margin=dict(t=10, l=10, r=10, b=10))
    st.plotly_chart(fig_imp, width='stretch')
else:
    st.info("عبّي السيناريو أعلاه واضغطي «قيّمي مستوى الخطورة» لعرض التقدير.")
