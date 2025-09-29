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
    return {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross",
                "crossStyle": {"color": "#999"},
            },
            "formatter": "Date: {b0}<br/>{a0}: {c0} CNY<br/>{a1}: {c1} CNY<br/>{a2}: {c2} CNY<br/>{a3}: {c3} CNY<br/>{a4}: {c4}%",
        },
        "legend": {
            "data": ["开盘价", "收盘价", "最高价", "最低价", "振幅（%）"],
            "orient": "horizontal",
            "top": "top",
            "left": "center",
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "3%",
            "containLabel": True,
        },
        "toolbox": {
            "feature": {
                "dataZoom": {
                    "yAxisIndex": "none",
                    "title": {"zoom": "Zoom region", "back": "Restore zoom"},
                },
                "restore": {},
                "saveAsImage": {},
                "magicType": {
                    "type": ["line", "bar"],
                    "title": {"line": "Line Chart", "bar": "Bar Chart"},
                },
            },
            "right": 10,
        },
        "xAxis": {
            "type": "category",
            "data": data["dates"],
            "axisPointer": {"type": "shadow"},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "价格",
                "min": "dataMin",
                "max": "dataMax",
                "position": "right",
                "axisLine": {"lineStyle": {"color": "#5793f3"}},
                "axisLabel": {"formatter": "{value} CNY"},
            },
            {
                "type": "value",
                "name": "振幅（%）",
                "min": 0,
                "max": "dataMax",
                "position": "left",
                "axisLine": {"lineStyle": {"color": "#d14a61"}},
                "axisLabel": {"formatter": "{value}%"},
                "splitLine": {"show": True},
            },
        ],
        "series": [
            {"name": "开盘价", "type": "line", "data": data["open"]},
            {"name": "收盘价", "type": "line", "data": data["close"]},
            {"name": "最高价", "type": "line", "data": data["high"]},
            {"name": "最低价", "type": "line", "data": data["low"]},
            {
                "name": "振幅（%）",
                "type": "line",
                "yAxisIndex": 1,
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
