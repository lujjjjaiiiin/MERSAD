"""
2_📊_تحليل_الجرائم.py — استكشاف أنماط الجرائم عبر الوقت والنوع والموقع.
"""

import plotly.express as px
import streamlit as st

from utils.data_processing import load_data, DAY_NAMES_AR
from utils.ui import inject_css, page_header, section_title

inject_css()

df = load_data()

page_header(subtitle="تحليل الجرائم — الأنماط الزمنية والمكانية")

with st.sidebar:
    st.markdown("### 🔎 فلاتر التحليل")
    crime_types = ["الكل"] + sorted(df["Primary Type"].unique().tolist())
    selected_types = st.multiselect("أنواع الجرائم", crime_types[1:], default=[])
    community_filter = st.multiselect(
        "المناطق (Community Area)", sorted(df["Community Area"].unique().tolist()), default=[]
    )

filtered = df.copy()
if selected_types:
    filtered = filtered[filtered["Primary Type"].isin(selected_types)]
if community_filter:
    filtered = filtered[filtered["Community Area"].isin(community_filter)]

if filtered.empty:
    st.warning("لا توجد بيانات مطابقة لهذا الفلتر.")
    st.stop()

GREEN_SCALE = ["#DCEFE6", "#9FD3B7", "#5FA876", "#2E8B57", "#0F5C4D"]

# ===== صف المؤشرات =====
c1, c2, c3 = st.columns(3)
c1.metric("عدد الحوادث ضمن الفلتر", f"{len(filtered):,}".replace(",", "٬"))
c2.metric("عدد أنواع الجرائم", filtered["Primary Type"].nunique())
c3.metric("نسبة القبض", f"{filtered['Arrest'].mean()*100:.1f}%")

st.markdown('<hr class="mersad-divider">', unsafe_allow_html=True)

# ===== أكثر أنواع الجرائم =====
section_title("🚨", "أكثر أنواع الجرائم انتشارًا")
top_types = filtered["Primary Type"].value_counts().head(10).sort_values()
fig1 = px.bar(
    x=top_types.values,
    y=top_types.index,
    orientation="h",
    color=top_types.values,
    color_continuous_scale=GREEN_SCALE,
    labels={"x": "عدد الحوادث", "y": ""},
)
fig1.update_layout(
    showlegend=False, coloraxis_showscale=False, height=380,
    font_family="IBM Plex Sans Arabic", margin=dict(t=10, l=10, r=10, b=10),
)
st.plotly_chart(fig1, width='stretch')

col1, col2 = st.columns(2)

with col1:
    section_title("⏰", "التوزيع حسب ساعة اليوم")
    hourly = filtered["hour"].value_counts().sort_index()
    fig2 = px.area(x=hourly.index, y=hourly.values, labels={"x": "الساعة", "y": "عدد الحوادث"})
    fig2.update_traces(line_color="#0F5C4D", fillcolor="rgba(15,92,77,0.18)")
    fig2.update_layout(height=320, font_family="IBM Plex Sans Arabic", margin=dict(t=10, l=10, r=10, b=10))
    st.plotly_chart(fig2, width='stretch')

with col2:
    section_title("📅", "التوزيع حسب يوم الأسبوع")
    daily = filtered["day_name"].value_counts().reindex(DAY_NAMES_AR)
    fig3 = px.bar(x=daily.index, y=daily.values, labels={"x": "", "y": "عدد الحوادث"})
    fig3.update_traces(marker_color="#178A70")
    fig3.update_layout(height=320, font_family="IBM Plex Sans Arabic", margin=dict(t=10, l=10, r=10, b=10))
    st.plotly_chart(fig3, width='stretch')

col3, col4 = st.columns(2)

with col3:
    section_title("🌗", "التوزيع حسب الفترة اليومية")
    period_order = ["الصباح", "الظهيرة", "المساء", "الليل"]
    period_counts = filtered["time_period"].value_counts().reindex(period_order)
    fig4 = px.pie(
        values=period_counts.values, names=period_counts.index, hole=0.5,
        color_discrete_sequence=["#9FD3B7", "#5FA876", "#2E8B57", "#0F5C4D"],
    )
    fig4.update_traces(textinfo="percent+label")
    fig4.update_layout(height=320, showlegend=False, font_family="IBM Plex Sans Arabic", margin=dict(t=10, l=10, r=10, b=10))
    st.plotly_chart(fig4, width='stretch')

with col4:
    section_title("📍", "أكثر مواقع الحوادث")
    top_loc = filtered["Location Description"].value_counts().head(8).sort_values()
    fig5 = px.bar(
        x=top_loc.values, y=top_loc.index, orientation="h",
        labels={"x": "عدد الحوادث", "y": ""},
    )
    fig5.update_traces(marker_color="#3FA66B")
    fig5.update_layout(height=320, font_family="IBM Plex Sans Arabic", margin=dict(t=10, l=10, r=10, b=10))
    st.plotly_chart(fig5, width='stretch')

st.markdown('<hr class="mersad-divider">', unsafe_allow_html=True)

section_title("🔥", "خريطة حرارية: الجريمة × الفترة اليومية")
period_order = ["الصباح", "الظهيرة", "المساء", "الليل"]
pivot = (
    filtered.groupby(["Primary Type", "time_period"]).size().reset_index(name="n")
)
top10_types = filtered["Primary Type"].value_counts().head(10).index.tolist()
pivot = pivot[pivot["Primary Type"].isin(top10_types)]
pivot_table = pivot.pivot(index="Primary Type", columns="time_period", values="n").reindex(
    columns=period_order
).fillna(0)
pivot_table = pivot_table.loc[top10_types]

fig6 = px.imshow(
    pivot_table.values,
    x=pivot_table.columns,
    y=pivot_table.index,
    color_continuous_scale=GREEN_SCALE,
    aspect="auto",
    labels=dict(color="عدد الحوادث"),
)
fig6.update_layout(height=420, font_family="IBM Plex Sans Arabic", margin=dict(t=10, l=10, r=10, b=10))
st.plotly_chart(fig6, width='stretch')
