"""
resource_optimizer.py
منطق توزيع الموارد المقترح (Prototype) بناءً على Risk Score لكل منطقة.
التوزيع تناسبي (Proportional Allocation) مع حد أدنى لكل منطقة نشطة — أسلوب شائع
وواقعي لنماذج دعم القرار الأولية، وواضح أنه Prototype وليس قرارًا تشغيليًا حقيقيًا.
"""

import numpy as np
import pandas as pd


def allocate_resources(
    area_table: pd.DataFrame,
    total_resources: int,
    min_per_area: int = 0,
    top_n: int = 10,
) -> pd.DataFrame:
    """
    يوزّع total_resources على أعلى top_n منطقة خطورة بشكل تناسبي مع risk_score،
    مع ضمان حد أدنى (min_per_area) لكل منطقة مُدرجة إن سمحت الموارد.
    """
    table = area_table.head(top_n).copy()
    if table.empty or total_resources <= 0:
        table["allocated_resources"] = 0
        return table

    weights = table["risk_score"] / table["risk_score"].sum()
    raw_alloc = weights * total_resources

    # تقريب مع الحفاظ على المجموع الكلي = total_resources
    floor_alloc = np.floor(raw_alloc).astype(int)
    remainder = int(total_resources - floor_alloc.sum())
    if remainder > 0:
        fractional = (raw_alloc - floor_alloc).sort_values(ascending=False)
        bump_idx = fractional.index[:remainder]
        floor_alloc.loc[bump_idx] += 1

    table["allocated_resources"] = floor_alloc.values

    if min_per_area > 0:
        table["allocated_resources"] = table["allocated_resources"].clip(lower=min_per_area)
        # إعادة ضبط بسيطة لو تجاوز المجموع الموارد المتاحة بسبب الحد الأدنى
        excess = int(table["allocated_resources"].sum() - total_resources)
        if excess > 0:
            order = table.sort_values("risk_score").index
            for idx in order:
                if excess <= 0:
                    break
                reducible = table.loc[idx, "allocated_resources"] - min_per_area
                cut = min(reducible, excess)
                if cut > 0:
                    table.loc[idx, "allocated_resources"] -= cut
                    excess -= cut

    return table


def coverage_period_for_area(top_time_period: str) -> str:
    """يحوّل الفترة الزمنية الأبرز للمنطقة إلى نطاق ساعات تغطية مقترح (تقريبي وواضح أنه إرشادي)."""
    mapping = {
        "الصباح": "٦ص – ١٢ظ",
        "الظهيرة": "١٢ظ – ٥م",
        "المساء": "٥م – ٩م",
        "الليل": "٩م – ٦ص",
    }
    return mapping.get(top_time_period, "على مدار اليوم")
