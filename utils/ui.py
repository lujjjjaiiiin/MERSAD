"""
ui.py
مكونات واجهة مشتركة بين كل صفحات مرصاد: حقن CSS، الهيدر بالشعار، بطاقات KPI،
بطاقات الرؤى والتوصيات، وشارة الخطورة. يضمن ثبات الهوية البصرية بكل الصفحات.
"""

import base64
from pathlib import Path

import streamlit as st

from utils.data_processing import RISK_LABELS_AR, RISK_EMOJI

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def _logo_base64() -> str:
    logo_path = ASSETS_DIR / "logo.png"
    return base64.b64encode(logo_path.read_bytes()).decode()


def inject_css():
    css_path = ASSETS_DIR / "style.css"
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def page_header(subtitle: str, status_text: str | None = None):
    """يعرض هيدر مرصاد الموحّد (الشعار + الاسم + الشعار النصي + حالة النظام)."""
    logo_b64 = _logo_base64()
    status_html = f'<div class="mersad-status-pill">{status_text}</div>' if status_text else ""
    st.markdown(
        f"""
        <div class="mersad-header">
            <div class="mersad-logo-wrap">
                <img src="data:image/png;base64,{logo_b64}" />
            </div>
            <div class="mersad-title-block">
                <h1>مرصاد <span style="font-weight:400; font-size:18px;">| MERSAD</span></h1>
                <p>{subtitle}</p>
            </div>
            {status_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(icon: str, value: str, label: str):
    st.markdown(
        f"""
        <div class="mersad-kpi">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-value mersad-num">{value}</div>
            <div class="kpi-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(icon: str, text: str):
    st.markdown(
        f"""
        <div class="mersad-insight">
            <div>{icon}</div>
            <div>{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def risk_badge_html(risk_class: str) -> str:
    label = RISK_LABELS_AR.get(risk_class, risk_class)
    emoji = RISK_EMOJI.get(risk_class, "⚪")
    return f'<span class="risk-badge risk-{risk_class}">{emoji} {label}</span>'


def section_title(icon: str, text: str):
    st.markdown(f'<div class="mersad-section-title">{icon} {text}</div>', unsafe_allow_html=True)


def nav_card(icon: str, title: str, desc: str):
    st.markdown(
        f"""
        <div class="mersad-navcard">
            <div class="nav-icon">{icon}</div>
            <div class="nav-title">{title}</div>
            <div class="nav-desc">{desc}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def recommendation_card(rec: dict):
    risk_class = rec["risk_class"]
    st.markdown(
        f"""
        <div class="mersad-rec risk-{risk_class}">
            <div class="rec-priority">{rec['priority']} — منطقة {rec['area']}</div>
            <div class="rec-row"><b>المشكلة:</b> {rec['problem']}</div>
            <div class="rec-row"><b>السبب:</b> {rec['reason']}</div>
            <div class="rec-row"><b>الإجراء المقترح:</b> {rec['action']}</div>
            <div class="rec-row"><b>الاتجاه:</b> <span class="mersad-num">{rec['trend']}</span></div>
            <div class="rec-row" style="font-size:12px; opacity:0.75;">{rec['support']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
