"""
6_⚖️_قارن_المناطق.py — مقارنة تفصيلية بين منطقتين أو أكثر.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_processing import load_data, compute_area_risk_table, RISK_LABELS_AR, DAY_NAMES_AR
from utils.resource_optimizer import allocate_resources, coverage_period_for_area
from utils.ui import inject_css, page_header, section_title, risk_badge_html

inject_css()

df = load_data()
area_table = compute_area_risk_table(df)

page_header(subtitle="قارن المناطق — مقارنة جنبًا إلى جنب")

section_title("🔎", "اختاري مناطق للمقارنة")
areas_sorted = area_table["Community Area"].astype(int).tolist()
selected_areas = st.multiselect(
    "اختاري منطقتين أو أكثر", areas_sorted, default=areas_sorted[:2] if len(areas_sorted) >= 2 else areas_sorted
)

if len(selected_areas) < 2:
    st.info("اختاري منطقتين على الأقل لعرض المقارنة.")
    st.stop()

sub_table = area_table[area_table["Community Area"].isin(selected_areas)].copy()
sub_table["Community Area"] = sub_table["Community Area"].astype(int)

# صف بطاقات سريعة
cols = st.columns(len(selected_areas))
for col, area_id in zip(cols, selected_areas):
    row = sub_table[sub_table["Community Area"] == area_id].iloc[0]
    with col:
        st.markdown(
            f"""
            <div class="mersad-kpi" style="text-align:center;">
                <div style="font-size:15px; font-weight:700;">منطقة {area_id}</div>
                <div style="margin:8px 0;">{risk_badge_html(row['risk_class'])}</div>
                <div class="mersad-num" style="font-size:22px; color: var(--mersad-forest);">{row['risk_score']:.0f}/100</div>
                <div class="mersad-caption">{int(row['incidents']):,} حادثة</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<hr class="mersad-divider">', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    section_title("📊", "عدد الحوادث")
    plot_table = sub_table.copy()
    plot_table["منطقة"] = "منطقة " + plot_table["Community Area"].astype(str)
    fig1 = px.bar(
        plot_table, x="منطقة", y="incidents",
        color="risk_class",
        color_discrete_map={"Low": "#3FA66B", "Medium": "#E8B84B", "High": "#E0793A", "Critical": "#C0392B"},
        labels={"incidents": "عدد الحوادث", "منطقة": ""},
    )
    fig1.update_layout(showlegend=False, height=320, font_family="IBM Plex Sans Arabic", margin=dict(t=10, l=10, r=10, b=10))
    st.plotly_chart(fig1, width='stretch')

with col2:
    section_title("🎯", "مؤشر الخطورة (Risk Score)")
    fig2 = go.Figure()
    for _, row in sub_table.iterrows():
        fig2.add_trace(
            go.Scatterpolar(
                r=[row["risk_score"], row["high_share"] * 100, row["arrest_rate"] * 100],
                theta=["مؤشر الخطورة", "نسبة الحوادث عالية الخطورة", "نسبة القبض"],
                fill="toself",
                name=f"منطقة {int(row['Community Area'])}",
            )
        )
    fig2.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height=320, font_family="IBM Plex Sans Arabic", margin=dict(t=30, l=30, r=30, b=10),
    )
    st.plotly_chart(fig2, width='stretch')

section_title("🚨", "أنواع الجرائم حسب المنطقة")
crime_compare = (
    df[df["Community Area"].isin(selected_areas)]
    .groupby(["Community Area", "Primary Type"])
    .size()
    .reset_index(name="n")
)
top_types_overall = (
    df[df["Community Area"].isin(selected_areas)]["Primary Type"].value_counts().head(6).index.tolist()
)
crime_compare = crime_compare[crime_compare["Primary Type"].isin(top_types_overall)]
crime_compare["Community Area"] = crime_compare["Community Area"].astype(int).astype(str)

fig3 = px.bar(
    crime_compare, x="Primary Type", y="n", color="Community Area", barmode="group",
    labels={"n": "عدد الحوادث", "Primary Type": ""},
    color_discrete_sequence=["#0F5C4D", "#3FA66B", "#E8B84B", "#E0793A", "#C0392B", "#5FA876"],
)
fig3.update_layout(height=380, font_family="IBM Plex Sans Arabic", margin=dict(t=10, l=10, r=10, b=10))
st.plotly_chart(fig3, width='stretch')

section_title("⏰", "الأوقات مقابل مستوى النشاط")
period_compare = (
    df[df["Community Area"].isin(selected_areas)]
    .groupby(["Community Area", "time_period"])
    .size()
    .reset_index(name="n")
)
period_compare["Community Area"] = period_compare["Community Area"].astype(int).astype(str)
period_order = ["الصباح", "الظهيرة", "المساء", "الليل"]
fig4 = px.line_polar(
    period_compare, r="n", theta="time_period", color="Community Area", line_close=True,
    category_orders={"time_period": period_order},
    color_discrete_sequence=["#0F5C4D", "#3FA66B", "#E8B84B", "#E0793A", "#C0392B"],
)
fig4.update_traces(fill="toself", opacity=0.5)
fig4.update_layout(height=380, font_family="IBM Plex Sans Arabic", margin=dict(t=30, l=30, r=30, b=10))
st.plotly_chart(fig4, width='stretch')

section_title("🧭", "الموارد المقترحة لكل منطقة (عند تخصيص ١٠ وحدات على أعلى ١٠ مناطق)")
plan = allocate_resources(area_table, total_resources=10, top_n=10)
plan_display = plan[plan["Community Area"].isin(selected_areas)][
    ["Community Area", "risk_class", "allocated_resources", "top_time_period"]
].copy()
if plan_display.empty:
    st.caption("المناطق المختارة ليست ضمن أعلى ١٠ مناطق خطورة، لذلك لا تظهر بخطة الموارد الحالية (راجعي صفحة تخطيط الموارد لتوسيع النطاق).")
else:
    plan_display["Community Area"] = plan_display["Community Area"].astype(int)
    plan_display["risk_class"] = plan_display["risk_class"].map(RISK_LABELS_AR)
    plan_display["فترة التغطية"] = plan_display["top_time_period"].map(coverage_period_for_area)
    plan_display = plan_display.rename(
        columns={"Community Area": "المنطقة", "risk_class": "مستوى الخطورة", "allocated_resources": "الوحدات المقترحة"}
    )[["المنطقة", "مستوى الخطورة", "الوحدات المقترحة", "فترة التغطية"]]
    st.dataframe(plan_display, width='stretch', hide_index=True)
