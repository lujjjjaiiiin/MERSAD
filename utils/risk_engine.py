"""
risk_engine.py
منطق حساب مستوى الخطورة وتوليد "السبب" وراء كل تصنيف — بدون أرقام مختلقة،
كل القيم مشتقة من data/mersad_sample.csv مباشرة.
"""

import pandas as pd

from utils.data_processing import RISK_LABELS_AR, RISK_EMOJI


def area_reasoning(df: pd.DataFrame, area_row: pd.Series) -> str:
    """يبني جملة تفسير لماذا حصلت المنطقة على مستوى الخطورة هذا، بالاعتماد على بياناتها الفعلية."""
    area_id = int(area_row["Community Area"])
    area_df = df[df["Community Area"] == area_id]

    period_share = area_df["time_period"].value_counts(normalize=True)
    top_period = period_share.idxmax()
    top_period_pct = period_share.max() * 100

    top_type_share = area_df["Primary Type"].value_counts(normalize=True)
    top_type = top_type_share.idxmax()
    top_type_pct = top_type_share.max() * 100

    high_pct = (area_df["risk_level"] == "High").mean() * 100

    reasons = []
    if high_pct >= 50:
        reasons.append(f"{high_pct:.0f}% من حوادث المنطقة مصنّفة ضمن الفئة عالية الخطورة تاريخيًا")
    if top_period_pct >= 30:
        reasons.append(f"تركّز واضح للحوادث خلال فترة {top_period} ({top_period_pct:.0f}% من الحوادث)")
    if top_type_pct >= 20:
        reasons.append(f"نوع الجريمة الأبرز هو «{top_type}» بنسبة {top_type_pct:.0f}%")

    if not reasons:
        reasons.append("نشاط الحوادث في هذه المنطقة موزّع بشكل متقارب بين الأنواع والأوقات المختلفة")

    return "، ".join(reasons) + "."


def trend_arrow(df: pd.DataFrame, area_id: int) -> tuple[str, float]:
    """
    يقارن عدد حوادث المنطقة بالنصف الثاني من نطاق الأشهر المتاح مقابل النصف الأول
    (تقريب معقول للاتجاه الزمني بدون الحاجة لعمود تاريخ كامل).
    """
    area_df = df[df["Community Area"] == area_id]
    if area_df.empty or area_df["month"].nunique() < 2:
        return "→", 0.0

    mid = area_df["month"].median()
    first_half = (area_df["month"] <= mid).sum()
    second_half = (area_df["month"] > mid).sum()

    if first_half == 0:
        return "→", 0.0

    change_pct = ((second_half - first_half) / first_half) * 100
    if change_pct > 5:
        return "↑", change_pct
    if change_pct < -5:
        return "↓", change_pct
    return "→", change_pct


def risk_badge(risk_class: str) -> str:
    """يرجع شارة نصية جاهزة للعرض: إيموجي + الاسم بالعربي."""
    return f"{RISK_EMOJI.get(risk_class, '⚪')} {RISK_LABELS_AR.get(risk_class, risk_class)}"


def area_recommendation(df: pd.DataFrame, area_row: pd.Series) -> str:
    """يولّد توصية نصية بناءً على بيانات المنطقة الفعلية."""
    area_id = int(area_row["Community Area"])
    area_df = df[df["Community Area"] == area_id]
    period_share = area_df["time_period"].value_counts(normalize=True)
    top_period = period_share.idxmax()
    risk_class = area_row["risk_class"]

    if risk_class == "Critical":
        return f"يقترح مرصاد رفع التغطية الميدانية بشكل عاجل خلال فترة {top_period}، ومتابعة المنطقة بشكل يومي نظرًا لارتفاع مؤشر الخطورة."
    if risk_class == "High":
        return f"يقترح مرصاد زيادة عدد الدوريات خلال فترة {top_period}، مع مراجعة أسبوعية لمؤشرات المنطقة."
    if risk_class == "Medium":
        return f"يقترح مرصاد إبقاء المنطقة تحت المراقبة الدورية، مع التركيز على فترة {top_period} عند تخصيص الموارد."
    return "المنطقة ضمن المستوى الطبيعي حاليًا — تغطية روتينية قياسية تعتبر كافية."
