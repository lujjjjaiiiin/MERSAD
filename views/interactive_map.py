"""
1_🗺️_الخريطة_التفاعلية.py — Command Center الخاص بمرصاد.
خريطة تفاعلية (Heatmap + Risk Zones) مع فلاتر مترابطة وسلايدر زمني ولوحة ذكاء جانبية.
"""

import folium
import pandas as pd
import streamlit as st
from folium.plugins import HeatMap
from streamlit_folium import st_folium

from utils.data_processing import (
    load_data,
    compute_area_risk_table,
    RISK_LABELS_AR,
    RISK_COLORS,
)
from utils.risk_engine import area_reasoning, area_recommendation, trend_arrow, risk_badge
from utils.resource_optimizer import coverage_period_for_area
from utils.ui import inject_css, page_header, section_title, risk_badge_html

inject_css()

df = load_data()

page_header(subtitle="MERSAD Command Center — الخريطة التفاعلية")

# ===================== الفلاتر =====================
with st.sidebar:
    st.markdown("### 🔎 فلاتر الخريطة")

    crime_types = ["الكل"] + sorted(df["Primary Type"].unique().tolist())
    selected_type = st.selectbox("نوع الجريمة", crime_types)

    risk_levels = ["الكل"] + list(RISK_LABELS_AR.values())
    selected_risk_ar = st.selectbox("مستوى الخطورة (تاريخيًا)", risk_levels)

    hour_range = st.slider("النطاق الزمني (الساعة)", 0, 23, (0, 23))

    st.markdown("---")
    st.markdown("### 🧩 طبقات الخريطة")
    show_heatmap = st.checkbox("🔥 خريطة الكثافة الحرارية", value=True)
    show_zones = st.checkbox("⚠️ مناطق الخطورة", value=True)
    show_markers = st.checkbox("📍 عيّنة من نقاط الحوادث", value=False)

# تطبيق الفلاتر
filtered = df[(df["hour"] >= hour_range[0]) & (df["hour"] <= hour_range[1])]
if selected_type != "الكل":
    filtered = filtered[filtered["Primary Type"] == selected_type]
if selected_risk_ar != "الكل":
    ar_to_en = {v: k for k, v in RISK_LABELS_AR.items()}
    target = ar_to_en[selected_risk_ar]
    if target in ["Low", "Medium", "High"]:
        filtered = filtered[filtered["risk_level"] == target]

if filtered.empty:
    st.warning("لا توجد حوادث مطابقة لهذا الفلتر ضمن العينة المتاحة. جرّبي تغيير المعايير.")
    st.stop()

area_table = compute_area_risk_table(filtered) if len(filtered) > 200 else compute_area_risk_table(df)

# ===================== لوحة ملخص مرصاد =====================
left, right = st.columns([2.4, 1])

with right:
    section_title("🧠", "ملخص مرصاد")
    top_area = area_table.iloc[0]
    top_period = filtered["time_period"].value_counts().idxmax() if not filtered.empty else "—"
    top_crime = filtered["Primary Type"].value_counts().idxmax() if not filtered.empty else "—"

    monthly = filtered.groupby(["Community Area", "month"]).size().reset_index(name="n")
    mid = filtered["month"].median() if not filtered.empty else 6
    first = monthly[monthly["month"] <= mid].groupby("Community Area")["n"].sum()
    second = monthly[monthly["month"] > mid].groupby("Community Area")["n"].sum()
    common_idx = first.index.intersection(second.index)
    if len(common_idx) > 0:
        chg = ((second[common_idx] - first[common_idx]) / first[common_idx].replace(0, 1)) * 100
        top_rise_area = int(chg.idxmax())
        top_rise_pct = chg.max()
    else:
        top_rise_area, top_rise_pct = "—", 0

    st.markdown(
        f"""
        <div class="mersad-kpi" style="margin-bottom:10px;">
            🔴 <b>أعلى منطقة خطورة</b><br>
            <span class="kpi-value mersad-num" style="font-size:22px;">منطقة {int(top_area['Community Area'])}</span>
        </div>
        <div class="mersad-kpi" style="margin-bottom:10px;">
            ⏰ <b>أخطر فترة ضمن الفلتر</b><br>
            <span class="kpi-value" style="font-size:20px;">{top_period}</span>
        </div>
        <div class="mersad-kpi" style="margin-bottom:10px;">
            🚨 <b>أكثر نوع جريمة ضمن الفلتر</b><br>
            <span class="kpi-value" style="font-size:18px;">{top_crime}</span>
        </div>
        <div class="mersad-kpi" style="margin-bottom:10px;">
            📈 <b>أعلى ارتفاع</b><br>
            <span class="kpi-value mersad-num" style="font-size:18px;">منطقة {top_rise_area} {"(+%.0f%%)" % top_rise_pct if top_rise_pct else ""}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("##### 🗂️ Legend")
    for cls in ["Critical", "High", "Medium", "Low"]:
        st.markdown(
            f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">'
            f'<div style="width:14px;height:14px;border-radius:50%;background:{RISK_COLORS[cls]};"></div>'
            f'<span>{RISK_LABELS_AR[cls]}</span></div>',
            unsafe_allow_html=True,
        )

with left:
    section_title("🗺️", f"عرض {len(filtered):,} حادثة ضمن الفلتر الحالي".replace(",", "٬"))

    center_lat = filtered["Latitude"].mean()
    center_lon = filtered["Longitude"].mean()

    fmap = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles="cartodbpositron")

    if show_heatmap:
        heat_sample = filtered.sample(min(6000, len(filtered)), random_state=42)
        HeatMap(
            heat_sample[["Latitude", "Longitude"]].values.tolist(),
            radius=11,
            blur=16,
            min_opacity=0.35,
        ).add_to(fmap)

    if show_zones:
        for _, row in area_table.iterrows():
            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=6 + (row["incidents"] / area_table["incidents"].max()) * 18,
                color=RISK_COLORS[row["risk_class"]],
                fill=True,
                fill_color=RISK_COLORS[row["risk_class"]],
                fill_opacity=0.55,
                weight=1.5,
                tooltip=(
                    f"منطقة {int(row['Community Area'])} — "
                    f"{RISK_LABELS_AR[row['risk_class']]} ({row['risk_score']:.0f}/100)"
                ),
                popup=folium.Popup(f"area_{int(row['Community Area'])}", max_width=50),
            ).add_to(fmap)

    if show_markers:
        marker_sample = filtered.sample(min(400, len(filtered)), random_state=42)
        for _, r in marker_sample.iterrows():
            folium.CircleMarker(
                location=[r["Latitude"], r["Longitude"]],
                radius=2.5,
                color="#16332D",
                fill=True,
                fill_opacity=0.5,
                weight=0,
            ).add_to(fmap)

    map_state = st_folium(fmap, height=560, width=None, returned_objects=["last_object_clicked_tooltip"])

st.markdown('<hr class="mersad-divider">', unsafe_allow_html=True)

# ===================== تفاصيل المنطقة المختارة =====================
section_title("📍", "تفاصيل المنطقة")

clicked_tooltip = map_state.get("last_object_clicked_tooltip") if map_state else None
selected_area_id = None
if clicked_tooltip and "منطقة" in clicked_tooltip:
    try:
        selected_area_id = int(clicked_tooltip.split("منطقة")[1].strip().split(" ")[0])
    except (ValueError, IndexError):
        selected_area_id = None

if selected_area_id is None:
    st.info("👆 اضغطي على أي دائرة بالخريطة (طبقة مناطق الخطورة) لعرض تفاصيلها هنا، أو اختاري منطقة يدويًا:")
    selected_area_id = st.selectbox(
        "اختيار يدوي للمنطقة",
        area_table["Community Area"].astype(int).tolist(),
        label_visibility="collapsed",
    )

area_row = area_table[area_table["Community Area"] == selected_area_id]
if area_row.empty:
    st.warning("لا تتوفر بيانات كافية لهذه المنطقة ضمن الفلتر الحالي.")
else:
    area_row = area_row.iloc[0]
    area_df = df[df["Community Area"] == selected_area_id]
    arrow, chg = trend_arrow(df, selected_area_id)

    d1, d2, d3, d4, d5 = st.columns(5)
    d1.metric("عدد الحوادث", f"{int(area_row['incidents']):,}".replace(",", "٬"))
    d2.metric("أكثر جريمة", area_row["top_crime_type"])
    d3.metric("أخطر فترة", area_row["top_time_period"])
    d4.markdown(f"**مستوى الخطورة**<br>{risk_badge_html(area_row['risk_class'])}", unsafe_allow_html=True)
    d5.metric("الاتجاه", f"{arrow} {abs(chg):.0f}%" if chg else "→ مستقر")

    st.markdown(
        f"""
        <div class="mersad-insight" style="border-color: {RISK_COLORS[area_row['risk_class']]};">
            <div>💡</div>
            <div>
                <b>لماذا هذه المنطقة {RISK_LABELS_AR[area_row['risk_class']]}؟</b><br>
                {area_reasoning(df, area_row)}
            </div>
        </div>
        <div class="mersad-insight" style="border-color: var(--mersad-forest);">
            <div>🧭</div>
            <div><b>توصية مرصاد:</b> {area_recommendation(df, area_row)}
            <br><span class="mersad-caption">فترة التغطية المقترحة: {coverage_period_for_area(area_row['top_time_period'])}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
