"""
7_🧾_التقارير.py — إنشاء تقرير مختصر قابل للتصدير (CSV + تقرير HTML قابل للطباعة كـPDF من المتصفح).
"""

from datetime import datetime

import streamlit as st

from utils.data_processing import load_data, compute_area_risk_table, global_kpis, RISK_LABELS_AR
from utils.insights import generate_home_insights, generate_recommendations
from utils.resource_optimizer import allocate_resources, coverage_period_for_area
from utils.ui import inject_css, page_header, section_title

inject_css()

df = load_data()
kpis = global_kpis(df)
area_table = compute_area_risk_table(df)

page_header(subtitle="التقارير — ملخص جاهز للتصدير والمشاركة")

section_title("⚙️", "إعدادات التقرير")
c1, c2 = st.columns(2)
with c1:
    n_priority_areas = st.slider("عدد المناطق ذات الأولوية بالتقرير", 3, 15, 6)
with c2:
    resources_for_plan = st.slider("إجمالي الموارد المفترضة لخطة التقرير", 5, 30, 10)

recs = generate_recommendations(df, top_n=n_priority_areas)
plan = allocate_resources(area_table, resources_for_plan, top_n=n_priority_areas)
insights = generate_home_insights(df)
now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

st.markdown('<hr class="mersad-divider">', unsafe_allow_html=True)
section_title("👁️", "معاينة التقرير")

with st.container(border=True):
    st.markdown(f"### تقرير مرصاد | MERSAD")
    st.markdown(f"**تاريخ الإنشاء:** {now_str}")
    st.markdown("#### ملخص الوضع")
    st.markdown(
        f"- إجمالي الحوادث المحلّلة: **{kpis['total_incidents']:,}**\n"
        f"- عدد المناطق: **{kpis['n_areas']}**\n"
        f"- أكثر جريمة انتشارًا: **{kpis['top_crime']}** ({kpis['top_crime_share']:.0f}%)\n"
        f"- الفترة الأعلى نشاطًا: **{kpis['top_period']}**\n"
        f"- نسبة الحوادث عالية الخطورة تاريخيًا: **{kpis['overall_high_share']:.0f}%**"
    )

    st.markdown("#### المناطق الأعلى خطورة")
    top_areas_display = area_table.head(n_priority_areas)[
        ["Community Area", "risk_class", "risk_score", "incidents", "top_crime_type", "top_time_period"]
    ].copy()
    top_areas_display["risk_class"] = top_areas_display["risk_class"].map(RISK_LABELS_AR)
    top_areas_display.columns = ["المنطقة", "مستوى الخطورة", "المؤشر", "الحوادث", "أكثر جريمة", "أخطر فترة"]
    st.dataframe(top_areas_display, hide_index=True, width='stretch')

    st.markdown("#### أهم الأنماط المكتشفة")
    for ins in insights:
        st.markdown(f"- {ins['icon']} {ins['text']}")

    st.markdown("#### خطة توزيع الموارد المقترحة")
    plan_display = plan[["Community Area", "risk_class", "allocated_resources", "top_time_period"]].copy()
    plan_display["Community Area"] = plan_display["Community Area"].astype(int)
    plan_display["risk_class"] = plan_display["risk_class"].map(RISK_LABELS_AR)
    plan_display["فترة التغطية"] = plan_display["top_time_period"].map(coverage_period_for_area)
    plan_display.columns = ["المنطقة", "مستوى الخطورة", "الوحدات المقترحة", "top_time_period", "فترة التغطية"]
    st.dataframe(
        plan_display[["المنطقة", "مستوى الخطورة", "الوحدات المقترحة", "فترة التغطية"]],
        hide_index=True, width='stretch',
    )

    st.markdown("#### التوصيات")
    for rec in recs:
        st.markdown(
            f"**{rec['priority']} — منطقة {rec['area']}**  \n"
            f"المشكلة: {rec['problem']}  \n"
            f"السبب: {rec['reason']}  \n"
            f"الإجراء المقترح: {rec['action']}\n"
        )

st.markdown('<hr class="mersad-divider">', unsafe_allow_html=True)
section_title("⬇️", "تصدير التقرير")

exp1, exp2 = st.columns(2)

with exp1:
    csv_bytes = area_table.head(n_priority_areas).to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ تحميل جدول المناطق (CSV)",
        data=csv_bytes,
        file_name=f"mersad_report_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        width='stretch',
    )

with exp2:
    recs_html = "".join(
        f"<div class='rec'><h4>{r['priority']} — منطقة {r['area']}</h4>"
        f"<p><b>المشكلة:</b> {r['problem']}</p>"
        f"<p><b>السبب:</b> {r['reason']}</p>"
        f"<p><b>الإجراء المقترح:</b> {r['action']}</p>"
        f"<p class='muted'>{r['support']}</p></div>"
        for r in recs
    )
    areas_rows = "".join(
        f"<tr><td>{int(row['Community Area'])}</td><td>{RISK_LABELS_AR[row['risk_class']]}</td>"
        f"<td>{row['risk_score']:.0f}</td><td>{int(row['incidents']):,}</td>"
        f"<td>{row['top_crime_type']}</td><td>{row['top_time_period']}</td></tr>"
        for _, row in area_table.head(n_priority_areas).iterrows()
    )
    insights_html = "".join(f"<li>{ins['icon']} {ins['text']}</li>" for ins in insights)

    html_report = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
    <meta charset="UTF-8">
    <title>تقرير مرصاد</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; direction: rtl; color:#16332D; padding: 30px; }}
        h1 {{ color:#0F5C4D; }}
        h2 {{ color:#178A70; border-bottom: 2px solid #E3EEE9; padding-bottom:6px; margin-top:28px;}}
        table {{ width:100%; border-collapse: collapse; margin-top:10px;}}
        th, td {{ border:1px solid #E3EEE9; padding:8px; text-align:right; }}
        th {{ background:#0F5C4D; color:white; }}
        .rec {{ border-right:4px solid #178A70; background:#F4FAF7; padding:10px 14px; margin-bottom:10px; border-radius:6px;}}
        .muted {{ color:#5C766E; font-size:12px; }}
        .kpi {{ display:inline-block; margin-left:18px; }}
    </style>
    </head>
    <body>
        <h1>تقرير مرصاد | MERSAD</h1>
        <p class="muted">تاريخ الإنشاء: {now_str}</p>

        <h2>ملخص الوضع</h2>
        <div class="kpi">إجمالي الحوادث: <b>{kpis['total_incidents']:,}</b></div>
        <div class="kpi">عدد المناطق: <b>{kpis['n_areas']}</b></div>
        <div class="kpi">أكثر جريمة: <b>{kpis['top_crime']}</b></div>
        <div class="kpi">الفترة الأعلى: <b>{kpis['top_period']}</b></div>

        <h2>المناطق الأعلى خطورة</h2>
        <table>
            <tr><th>المنطقة</th><th>مستوى الخطورة</th><th>المؤشر</th><th>الحوادث</th><th>أكثر جريمة</th><th>أخطر فترة</th></tr>
            {areas_rows}
        </table>

        <h2>أهم الأنماط المكتشفة</h2>
        <ul>{insights_html}</ul>

        <h2>التوصيات</h2>
        {recs_html}

        <p class="muted">تقرير مرصاد نموذجي مبني على عينة تحليلية من بيانات جرائم شيكاغو العامة، ولا يمثل قرارات تشغيلية حقيقية.</p>
    </body>
    </html>
    """
    st.download_button(
        "⬇️ تحميل التقرير الكامل (HTML — قابل للطباعة كـ PDF من المتصفح)",
        data=html_report.encode("utf-8"),
        file_name=f"mersad_report_{datetime.now().strftime('%Y%m%d')}.html",
        mime="text/html",
        width='stretch',
    )

st.caption("لتحويل تقرير الـHTML إلى PDF: افتحي الملف بالمتصفح ثم Ctrl+P (أو ⌘+P) واختاري «حفظ كـ PDF».")
