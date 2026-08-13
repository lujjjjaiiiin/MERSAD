"""
insights.py
توليد رؤى نصية ديناميكية (Insights) من البيانات الفعلية — لا نصوص ثابتة.
تُستخدم بالصفحة الرئيسية وصفحة التوصيات.
"""

import pandas as pd

from utils.data_processing import compute_area_risk_table


def generate_home_insights(df: pd.DataFrame) -> list[dict]:
    insights = []

    # 1) المنطقة الأعلى ارتفاعًا في الحوادث (مقارنة نصف الفترة الثاني بالأول)
    monthly = df.groupby(["Community Area", "month"]).size().reset_index(name="n")
    mid = df["month"].median()
    first = monthly[monthly["month"] <= mid].groupby("Community Area")["n"].sum()
    second = monthly[monthly["month"] > mid].groupby("Community Area")["n"].sum()
    common_idx = first.index.intersection(second.index)
    if len(common_idx) > 0:
        change = ((second[common_idx] - first[common_idx]) / first[common_idx].replace(0, 1)) * 100
        top_change_area = change.idxmax()
        top_change_pct = change.max()
        insights.append(
            {
                "icon": "📈",
                "text": f"المنطقة رقم {int(top_change_area)} شهدت أعلى ارتفاع نسبي في عدد الحوادث بين فترتي البيانات (+{top_change_pct:.0f}%).",
            }
        )

    # 2) أكثر الأوقات نشاطًا
    top_period = df["time_period"].value_counts().idxmax()
    top_period_pct = df["time_period"].value_counts(normalize=True).max() * 100
    insights.append(
        {
            "icon": "⏰",
            "text": f"فترة {top_period} هي الأكثر نشاطًا بنسبة {top_period_pct:.0f}% من إجمالي الحوادث المسجّلة.",
        }
    )

    # 3) أكثر أنواع الجرائم انتشارًا
    top_crime = df["Primary Type"].value_counts().idxmax()
    top_crime_pct = df["Primary Type"].value_counts(normalize=True).max() * 100
    insights.append(
        {
            "icon": "🚨",
            "text": f"«{top_crime}» يمثل النوع الأكثر تكرارًا بنسبة {top_crime_pct:.0f}% من إجمالي الحوادث.",
        }
    )

    # 4) المناطق التي تحتاج اهتمام أكبر (Critical + High)
    area_table = compute_area_risk_table(df)
    needs_attention = area_table[area_table["risk_class"].isin(["Critical", "High"])]
    insights.append(
        {
            "icon": "⚠️",
            "text": f"{len(needs_attention)} منطقة من أصل {len(area_table)} تحتاج اهتمامًا أكبر (مصنّفة مرتفعة أو حرجة الخطورة).",
        }
    )

    return insights


def generate_recommendations(df: pd.DataFrame, top_n: int = 6) -> list[dict]:
    """يولّد قائمة توصيات مرتبة حسب الأولوية بناءً على جدول خطورة المناطق."""
    from utils.risk_engine import area_reasoning, area_recommendation, trend_arrow

    area_table = compute_area_risk_table(df)
    recs = []
    for _, row in area_table.head(top_n).iterrows():
        area_id = int(row["Community Area"])
        arrow, change_pct = trend_arrow(df, area_id)
        priority = {
            "Critical": "🔴 أولوية عالية",
            "High": "🟠 أولوية متوسطة",
            "Medium": "🟡 مراقبة",
            "Low": "🟢 روتيني",
        }[row["risk_class"]]

        recs.append(
            {
                "area": area_id,
                "priority": priority,
                "risk_class": row["risk_class"],
                "problem": f"المنطقة رقم {area_id} تُظهر نمط خطورة {row['risk_class']} بمؤشر {row['risk_score']:.0f}/100.",
                "reason": area_reasoning(df, row),
                "action": area_recommendation(df, row),
                "trend": f"{arrow} {abs(change_pct):.0f}%" if change_pct else "→ مستقر",
                "support": f"مبني على {int(row['incidents']):,} حادثة مسجّلة في هذه المنطقة ضمن العينة المحلّلة.",
            }
        )
    return recs
