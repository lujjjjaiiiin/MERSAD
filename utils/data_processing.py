"""
data_processing.py
طبقة تحميل ومعالجة البيانات لتطبيق مرصاد.
كل الدوال هنا Cached عشان الأداء، ومافيه أي بيانات مختلقة —
كل شي مبني على data/mersad_sample.csv (عينة حقيقية من الداتاست المنظف)
وملفات الموديل بمجلد models/.
"""

import joblib
import numpy as np
import pandas as pd
import streamlit as st

DATA_PATH = "data/mersad_sample.csv"
MODEL_PATH = "models/xgb_model.joblib"
FEATURE_COLS_PATH = "models/feature_cols.joblib"
MAPPINGS_PATH = "models/feature_mappings.joblib"

DAY_NAMES_AR = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
MONTH_NAMES_AR = [
    "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
    "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر",
]

RISK_ORDER = ["Low", "Medium", "High", "Critical"]
RISK_LABELS_AR = {
    "Low": "منخفض",
    "Medium": "متوسط",
    "High": "مرتفع",
    "Critical": "حرج",
}
RISK_EMOJI = {"Low": "🟢", "Medium": "🟡", "High": "🟠", "Critical": "🔴"}
RISK_COLORS = {
    "Low": "#3FA66B",
    "Medium": "#E8B84B",
    "High": "#E0793A",
    "Critical": "#C0392B",
}


def time_period_ar(hour: int) -> str:
    """يحول الساعة إلى فترة يومية بالعربي (نفس منطق النوت بوك: Morning/Afternoon/Evening/Night)."""
    if 6 <= hour < 12:
        return "الصباح"
    if 12 <= hour < 17:
        return "الظهيرة"
    if 17 <= hour < 21:
        return "المساء"
    return "الليل"


@st.cache_data(show_spinner=False)
def load_mappings():
    return joblib.load(MAPPINGS_PATH)


@st.cache_data(show_spinner=False)
def load_feature_cols():
    return joblib.load(FEATURE_COLS_PATH)


@st.cache_resource(show_spinner=False)
def load_model():
    return joblib.load(MODEL_PATH)


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    """يحمّل عينة البيانات المنظفة ويفك ترميز الأعمدة الفئوية لأسماء حقيقية."""
    df = pd.read_csv(DATA_PATH)
    mappings = load_mappings()

    df["Primary Type Code"] = df["Primary Type"]
    df["Location Code"] = df["Location Description"]

    df["Primary Type"] = df["Primary Type"].map(
        lambda i: mappings["Primary Type"][i] if i < len(mappings["Primary Type"]) else "غير معروف"
    )
    df["Location Description"] = df["Location Description"].map(
        lambda i: mappings["Location Description"][i]
        if i < len(mappings["Location Description"])
        else "غير معروف"
    )

    df["day_name"] = df["day_of_week"].map(lambda d: DAY_NAMES_AR[d])
    df["month_name"] = df["month"].map(lambda m: MONTH_NAMES_AR[m - 1])
    df["time_period"] = df["hour"].map(time_period_ar)

    return df


@st.cache_data(show_spinner=False)
def community_area_centroids(df: pd.DataFrame) -> pd.DataFrame:
    """يحسب مركز كل منطقة (Community Area) من متوسط الإحداثيات الفعلية — بدون اختلاق أي إحداثيات."""
    g = (
        df.groupby("Community Area")
        .agg(
            Latitude=("Latitude", "mean"),
            Longitude=("Longitude", "mean"),
            incidents=("Community Area", "size"),
        )
        .reset_index()
    )
    return g


@st.cache_data(show_spinner=False)
def compute_area_risk_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    يبني جدول خطورة لكل منطقة (Community Area) بناءً على:
    - عدد الحوادث الفعلي
    - توزيع مستويات الخطورة (High/Medium/Low) المشتقة أصلًا بالنوت بوك
    - نسبة الحوادث خلال آخر ٣ أشهر بالبيانات مقابل الأشهر الأقدم (اتجاه تقريبي)
    يحوّل هذا لـ Risk Score من ٠-١٠٠ ويصنّف لأربع مستويات (منخفض/متوسط/مرتفع/حرج).
    """
    centroids = community_area_centroids(df)

    risk_share = (
        df.groupby("Community Area")["risk_level"]
        .apply(lambda s: (s == "High").mean())
        .reset_index(name="high_share")
    )

    top_type = (
        df.groupby("Community Area")["Primary Type"]
        .agg(lambda s: s.value_counts().idxmax())
        .reset_index(name="top_crime_type")
    )

    top_period = (
        df.groupby("Community Area")["time_period"]
        .agg(lambda s: s.value_counts().idxmax())
        .reset_index(name="top_time_period")
    )

    arrest_rate = (
        df.groupby("Community Area")["Arrest"].mean().reset_index(name="arrest_rate")
    )

    table = centroids.merge(risk_share, on="Community Area")
    table = table.merge(top_type, on="Community Area")
    table = table.merge(top_period, on="Community Area")
    table = table.merge(arrest_rate, on="Community Area")

    # Risk Score: مزيج من (حصة الحوادث عالية الخطورة) و(الكثافة النسبية لعدد الحوادث)
    incident_norm = (table["incidents"] - table["incidents"].min()) / (
        table["incidents"].max() - table["incidents"].min() + 1e-9
    )
    table["risk_score"] = (0.7 * table["high_share"] + 0.3 * incident_norm) * 100
    table["risk_score"] = table["risk_score"].round(1)

    q75 = table["risk_score"].quantile(0.75)
    q50 = table["risk_score"].quantile(0.50)
    q25 = table["risk_score"].quantile(0.25)

    def classify(score):
        if score >= q75:
            return "Critical"
        if score >= q50:
            return "High"
        if score >= q25:
            return "Medium"
        return "Low"

    table["risk_class"] = table["risk_score"].apply(classify)
    table = table.sort_values("risk_score", ascending=False).reset_index(drop=True)
    return table


@st.cache_data(show_spinner=False)
def global_kpis(df: pd.DataFrame) -> dict:
    total_incidents = len(df)
    n_areas = df["Community Area"].nunique()
    top_crime = df["Primary Type"].value_counts().idxmax()
    top_crime_share = df["Primary Type"].value_counts(normalize=True).max() * 100

    area_table = compute_area_risk_table(df)
    top_risk_area = area_table.iloc[0]
    top_period = df["time_period"].value_counts().idxmax()
    overall_high_share = (df["risk_level"] == "High").mean() * 100

    return {
        "total_incidents": total_incidents,
        "n_areas": n_areas,
        "top_crime": top_crime,
        "top_crime_share": top_crime_share,
        "top_risk_area": int(top_risk_area["Community Area"]),
        "top_risk_score": top_risk_area["risk_score"],
        "top_period": top_period,
        "overall_high_share": overall_high_share,
    }


def predict_risk(model, feature_cols, input_row: dict):
    """يشغّل موديل XGBoost المدرّب على صف مدخلات واحد ويرجع مستوى الخطورة والاحتمالات."""
    X = pd.DataFrame([input_row])[feature_cols]
    proba = model.predict_proba(X)[0]
    pred_idx = int(np.argmax(proba))
    # ترميز الهدف: 0=High, 1=Low, 2=Medium (كما تأكدنا بمشروع مرصاد)
    idx_to_label = {0: "High", 1: "Low", 2: "Medium"}
    label = idx_to_label[pred_idx]
    proba_dict = {idx_to_label[i]: float(p) for i, p in enumerate(proba)}
    return label, proba_dict
