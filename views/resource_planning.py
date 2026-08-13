"""
4_🧭_تخطيط_الموارد.py — خطة توزيع موارد مقترحة (Prototype) + محاكي تفاعلي.
التوزيع تناسبي بناءً على Risk Score الفعلي لكل منطقة، وليس أرقامًا ثابتة.
"""

import plotly.express as px
import streamlit as st

from utils.data_processing import load_data, compute_area_risk_table, RISK_LABELS_AR, RISK_COLORS
from utils.resource_optimizer import allocate_resources, coverage_period_for_area
from utils.ui import inject_css, page_header, section_title, risk_badge_html

inject_css()

df = load_data()
area_table = compute_area_risk_table(df)

page_header(subtitle="تخطيط الموارد — نموذج أولي لدعم القرار")

st.markdown(
    """
    <div class="mersad-insight" style="border-color: var(--mersad-forest);">
        <div>⚠️</div>
        <div>هذه خطة <b>نموذجية (Prototype)</b> لتوضيح فكرة التوزيع الذكي للموارد بناءً على مؤشر الخطورة
        المحسوب من البيانات. الأرقام هنا وحدات افتراضية وليست قرارات تشغيلية حقيقية.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

section_title("🎛️", "محاكي توزيع الموارد")

sim1, sim2, sim3 = st.columns(3)
with sim1:
    total_resources = st.slider("إجمالي الوحدات المتاحة", 5, 40, 18)
with sim2:
    resource_type = st.selectbox("نوع المورد", ["دوريات ميدانية", "فرق استجابة", "وحدات دعم", "كاميرات مراقبة متنقلة"])
with sim3:
    min_per_area = st.slider("الحد الأدنى لكل منطقة مُدرجة", 0, 3, 0)

top_n = st.slider("عدد المناطق المشمولة بالخطة (الأعلى خطورة)", 3, min(20, len(area_table)), 8)

plan = allocate_resources(area_table, total_resources, min_per_area=min_per_area, top_n=top_n)
plan["فترة التغطية"] = plan["top_time_period"].map(coverage_period_for_area)

st.markdown('<hr class="mersad-divider">', unsafe_allow_html=True)

col_chart, col_table = st.columns([1, 1.4])

with col_chart:
    section_title("📊", f"توزيع {resource_type} المقترح")
    plot_plan = plan.sort_values("allocated_resources").copy()
    plot_plan["منطقة"] = "منطقة " + plot_plan["Community Area"].astype(int).astype(str)
    fig = px.bar(
        plot_plan,
        x="allocated_resources",
        y="منطقة",
        orientation="h",
        color="risk_class",
        color_discrete_map=RISK_COLORS,
        text="allocated_resources",
        labels={"allocated_resources": "عدد الوحدات المخصّصة", "منطقة": ""},
    )
    fig.update_traces(textposition="outside")
    max_alloc = max(int(plot_plan["allocated_resources"].max()), 1)
    fig.update_layout(
        height=max(320, 32 * len(plan)), showlegend=False,
        xaxis_range=[0, max_alloc + 1],
        font_family="IBM Plex Sans Arabic", margin=dict(t=10, l=10, r=30, b=10),
    )
    st.plotly_chart(fig, width='stretch')
    st.markdown(
        f'<p class="mersad-caption">إجمالي الوحدات الموزّعة: '
        f'<span class="mersad-num">{int(plan["allocated_resources"].sum())}</span> من '
        f'<span class="mersad-num">{total_resources}</span></p>',
        unsafe_allow_html=True,
    )

with col_table:
    section_title("📋", "خطة توزيع الموارد التفصيلية")
    display_table = plan[
        ["Community Area", "risk_class", "allocated_resources", "فترة التغطية", "top_crime_type"]
    ].rename(
        columns={
            "Community Area": "المنطقة",
            "risk_class": "مستوى الخطورة",
            "allocated_resources": f"عدد {resource_type}",
            "top_crime_type": "أكثر جريمة",
        }
    )
    display_table["المنطقة"] = display_table["المنطقة"].astype(int)
    display_table["مستوى الخطورة"] = display_table["مستوى الخطورة"].map(RISK_LABELS_AR)
    st.dataframe(display_table, width='stretch', hide_index=True, height=max(320, 35 * len(plan)))

st.markdown('<hr class="mersad-divider">', unsafe_allow_html=True)

section_title("⚖️", "التوزيع الحالي (الوزن المتساوي) مقابل التوزيع المقترح (حسب الخطورة)")

equal_alloc = total_resources / len(plan) if len(plan) else 0
compare_df = plan[["Community Area", "allocated_resources"]].copy()
compare_df["توزيع متساوٍ افتراضي"] = equal_alloc
compare_df = compare_df.rename(columns={"Community Area": "المنطقة", "allocated_resources": "توزيع مرصاد المقترح"})
compare_df["المنطقة"] = compare_df["المنطقة"].astype(int).astype(str)

fig_cmp = px.bar(
    compare_df.melt(id_vars="المنطقة", var_name="النوع", value_name="عدد الوحدات"),
    x="المنطقة", y="عدد الوحدات", color="النوع", barmode="group",
    color_discrete_map={"توزيع متساوٍ افتراضي": "#C9D9D2", "توزيع مرصاد المقترح": "#0F5C4D"},
)
fig_cmp.update_layout(height=380, font_family="IBM Plex Sans Arabic", margin=dict(t=10, l=10, r=10, b=10))
st.plotly_chart(fig_cmp, width='stretch')

st.markdown(
    """
    <p class="mersad-caption">
    التوزيع المتساوي الافتراضي هنا للمقارنة فقط (توزيع الموارد بالتساوي على كل المناطق المشمولة بغض النظر عن الخطورة) —
    بينما توزيع مرصاد يخصّص وحدات أكثر للمناطق الأعلى خطورة بناءً على البيانات الفعلية.
    </p>
    """,
    unsafe_allow_html=True,
)
