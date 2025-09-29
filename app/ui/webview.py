from __future__ import annotations

import json
from importlib import resources
from string import Template
from threading import Lock
from typing import Optional

import webview

from app.models.rate import RatesSnapshot

_TEMPLATE_CACHE: Optional[Template] = None
_TEMPLATE_LOCK = Lock()
_WINDOW_OPEN = False


def _load_template() -> Template:
    global _TEMPLATE_CACHE
    if _TEMPLATE_CACHE is not None:
        return _TEMPLATE_CACHE

    with _TEMPLATE_LOCK:
        if _TEMPLATE_CACHE is None:
            template_text = resources.files("app.ui.templates").joinpath("echarts.html").read_text("utf-8")
            _TEMPLATE_CACHE = Template(template_text)
    return _TEMPLATE_CACHE


def _build_option(snapshot: RatesSnapshot) -> dict:
    data = snapshot.to_chart_payload()
    color_palette = ["#2563eb", "#0ea5e9", "#f97316", "#a855f7", "#ef4444"]
    base_text_style = {"fontFamily": "'Inter', 'Helvetica Neue', 'PingFang SC', sans-serif"}
    return {
        "backgroundColor": "transparent",
        "color": color_palette,
        "textStyle": base_text_style,
        "animationDuration": 900,
        "tooltip": {
            "trigger": "axis",
            "backgroundColor": "rgba(15,23,42,0.92)",
            "borderWidth": 0,
            "textStyle": {"color": "#f8fafc", **base_text_style},
            "axisPointer": {
                "type": "cross",
                "crossStyle": {"color": "#475569", "width": 1.2},
            },
            "formatter": (
                "{b0}<br/>"
                "开盘价：{c0} CNY<br/>"
                "收盘价：{c1} CNY<br/>"
                "最高价：{c2} CNY<br/>"
                "最低价：{c3} CNY<br/>"
                "振幅：{c4}%"
            ),
        },
        "legend": {
            "data": ["开盘价", "收盘价", "最高价", "最低价", "振幅（%）"],
            "icon": "roundRect",
            "itemWidth": 18,
            "itemHeight": 10,
            "top": 16,
            "textStyle": {"color": "#1e293b", **base_text_style},
        },
        "grid": {
            "left": "6%",
            "right": "6%",
            "bottom": "15%",
            "top": "20%",
            "containLabel": True,
        },
        "toolbox": {
            "show": True,
            "right": 24,
            "feature": {
                "dataZoom": {
                    "yAxisIndex": "none",
                    "title": {"zoom": "区域缩放", "back": "还原"},
                },
                "saveAsImage": {"title": "导出图片"},
                "restore": {"title": "还原"},
            },
            "iconStyle": {"borderColor": "#1e293b"},
        },
        "dataZoom": [
            {"type": "slider", "height": 18, "bottom": 24, "borderColor": "#cbd5f5"},
            {"type": "inside"},
        ],
        "xAxis": {
            "type": "category",
            "data": data["dates"],
            "axisLine": {"lineStyle": {"color": "#cbd5f5"}},
            "axisLabel": {"color": "#475569"},
            "axisPointer": {"type": "shadow"},
            "boundaryGap": False,
        },
        "yAxis": [
            {
                "type": "value",
                "name": "价格 (CNY)",
                "axisLine": {"lineStyle": {"color": "#2563eb"}},
                "axisLabel": {"color": "#475569"},
                "splitLine": {"lineStyle": {"color": "#e2e8f0"}},
            },
            {
                "type": "value",
                "name": "振幅 (%)",
                "axisLine": {"lineStyle": {"color": "#ef4444"}},
                "axisLabel": {"color": "#475569"},
                "splitLine": {"lineStyle": {"color": "#f1f5f9", "type": "dashed"}},
            },
        ],
        "series": [
            {
                "name": "开盘价",
                "type": "line",
                "smooth": True,
                "lineStyle": {"width": 2},
                "areaStyle": {
                    "opacity": 0.1,
                    "color": "rgba(37, 99, 235, 0.15)",
                },
                "data": data["open"],
            },
            {
                "name": "收盘价",
                "type": "line",
                "smooth": True,
                "lineStyle": {"width": 2},
                "areaStyle": {
                    "opacity": 0.08,
                    "color": "rgba(14, 165, 233, 0.2)",
                },
                "data": data["close"],
            },
            {
                "name": "最高价",
                "type": "line",
                "smooth": True,
                "lineStyle": {"width": 2, "type": "dashed"},
                "data": data["high"],
            },
            {
                "name": "最低价",
                "type": "line",
                "smooth": True,
                "lineStyle": {"width": 2, "type": "dashed"},
                "data": data["low"],
            },
            {
                "name": "振幅（%）",
                "type": "line",
                "yAxisIndex": 1,
                "smooth": True,
                "lineStyle": {"width": 2},
                "symbol": "circle",
                "symbolSize": 6,
                "data": data["amplitude"],
            },
        ],
    }


def render_rates(snapshot: RatesSnapshot, title: str = "汇率走势", theme: str = "light") -> None:
    global _WINDOW_OPEN

    if snapshot.is_empty():
        raise ValueError("没有可视化的数据。")

    if _WINDOW_OPEN:
        raise RuntimeError("图表窗口已打开，请先关闭后再试。")

    option = _build_option(snapshot)
    template = _load_template()
    html_content = template.substitute(
        title=title,
        theme=theme,
        option_json=json.dumps(option, ensure_ascii=False),
    )

    window = webview.create_window(title, html=html_content)

    def on_closed() -> None:
        global _WINDOW_OPEN
        _WINDOW_OPEN = False

    window.events.closed += on_closed
    _WINDOW_OPEN = True
    try:
        webview.start()
    finally:
        _WINDOW_OPEN = False
