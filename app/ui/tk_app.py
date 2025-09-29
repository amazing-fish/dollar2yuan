from __future__ import annotations

import os
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from app.config import DEFAULT_BASE_DAYS, load_env_defaults
from app.models.rate import RatesSnapshot
from app.services.alpha_vantage import AlphaVantageClient, AlphaVantageError
from app.services.base_rates_service import BaseRatesRefreshError, BaseRatesService
from app.ui.webview import render_rates


class RatesApp(tk.Tk):
    def __init__(self, base_rates_service: BaseRatesService) -> None:
        super().__init__()
        self.title("USD ⇌ CNY 现代行情面板")
        self.geometry("920x600")
        self.minsize(900, 560)
        self.configure(bg="#e9eef6")

        self.base_rates_service = base_rates_service
        self._base_snapshot: Optional[RatesSnapshot] = None

        self.env_defaults = load_env_defaults()
        self.api_key_var = tk.StringVar(value=os.getenv("ALPHAVANTAGE_API_KEY", self.env_defaults.get("ALPHAVANTAGE_API_KEY", "")))
        self.outputsize_var = tk.StringVar(value=os.getenv("ALPHAVANTAGE_OUTPUTSIZE", self.env_defaults.get("ALPHAVANTAGE_OUTPUTSIZE", "compact")))
        self.days_var = tk.StringVar()
        self.status_var = tk.StringVar(value="欢迎体验现代化的汇率洞察面板")
        self.base_title_var = tk.StringVar()
        self.base_desc_var = tk.StringVar()
        self.base_update_var = tk.StringVar()
        self.metric_price_var = tk.StringVar()
        self.metric_range_var = tk.StringVar()
        self.metric_amplitude_var = tk.StringVar()
        self.coverage_var = tk.StringVar()

        self._configure_style()
        self._build_layout()
        self._load_local_snapshot()

    # region UI
    def _configure_style(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TLabel", font=("Microsoft YaHei", 10), background="#ffffff", foreground="#1f2937")
        style.configure("App.TFrame", background="#e9eef6")
        style.configure("Card.TFrame", background="#ffffff", relief="flat", borderwidth=0)
        style.configure("CardInner.TFrame", background="#ffffff")
        style.configure("Section.TLabel", font=("Microsoft YaHei", 12, "bold"), background="#ffffff", foreground="#1e293b")
        style.configure("Hero.TLabel", font=("Microsoft YaHei", 18, "bold"), background="#e9eef6", foreground="#0f172a")
        style.configure("Subtitle.TLabel", font=("Microsoft YaHei", 10), background="#e9eef6", foreground="#475569")
        style.configure("Badge.TLabel", font=("Microsoft YaHei", 9), background="#dbeafe", foreground="#1d4ed8")
        style.configure("Status.TLabel", font=("Microsoft YaHei", 10), background="#e9eef6", foreground="#1f2937")
        style.configure("MetricTitle.TLabel", font=("Microsoft YaHei", 10), background="#ffffff", foreground="#64748b")
        style.configure("MetricValue.TLabel", font=("Microsoft YaHei", 14, "bold"), background="#ffffff", foreground="#0f172a")
        style.configure("Input.TEntry", padding=6, fieldbackground="#f8fafc")
        style.configure("TCombobox", padding=6)
        style.configure("Accent.TButton", padding=10, font=("Microsoft YaHei", 10, "bold"), background="#2563eb", foreground="#ffffff")
        style.map(
            "Accent.TButton",
            background=[("active", "#1d4ed8"), ("disabled", "#94a3b8")],
            foreground=[("disabled", "#ffffff")],
        )
        style.configure("Primary.TButton", padding=10, font=("Microsoft YaHei", 10, "bold"), background="#0ea5e9", foreground="#ffffff")
        style.map(
            "Primary.TButton",
            background=[("active", "#0284c7"), ("disabled", "#94a3b8")],
            foreground=[("disabled", "#ffffff")],
        )
        style.configure("Ghost.TButton", padding=8, font=("Microsoft YaHei", 10), background="#ffffff", foreground="#2563eb")
        style.map(
            "Ghost.TButton",
            background=[("active", "#f1f5f9"), ("disabled", "#ffffff")],
            foreground=[("disabled", "#94a3b8")],
        )

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        container = ttk.Frame(self, padding=(32, 28, 32, 24), style="App.TFrame")
        container.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        header = ttk.Frame(container, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)

        title = ttk.Label(header, text="美元兑人民币 · 全景洞察", style="Hero.TLabel")
        title.grid(row=0, column=0, sticky="w")

        subtitle = ttk.Label(
            header,
            text="对接 Alpha Vantage 与本地缓存，打造现代桌面级体验。",
            style="Subtitle.TLabel",
        )
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

        content = ttk.Frame(container, style="App.TFrame")
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        form_card = ttk.Frame(content, padding=24, style="Card.TFrame")
        form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        form_card.columnconfigure(0, weight=1)

        ttk.Label(form_card, text="数据源配置", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            form_card,
            text="输入 Alpha Vantage 凭证或直接查看基础数据，支持一键刷新最新行情。",
            wraplength=360,
            style="TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 14))

        ttk.Label(form_card, text="API Key", style="TLabel").grid(row=2, column=0, sticky="w", pady=(0, 6))
        api_entry = ttk.Entry(form_card, textvariable=self.api_key_var, style="Input.TEntry")
        api_entry.grid(row=3, column=0, sticky="ew")

        ttk.Label(form_card, text="Output Size", style="TLabel").grid(row=4, column=0, sticky="w", pady=(18, 6))
        output_combo = ttk.Combobox(
            form_card,
            values=["compact", "full"],
            textvariable=self.outputsize_var,
            state="readonly",
        )
        output_combo.grid(row=5, column=0, sticky="ew")
        if self.outputsize_var.get() not in {"compact", "full"}:
            self.outputsize_var.set("compact")

        ttk.Label(form_card, text="自定义天数", style="TLabel").grid(row=6, column=0, sticky="w", pady=(18, 6))
        days_entry = ttk.Entry(form_card, textvariable=self.days_var, style="Input.TEntry")
        days_entry.grid(row=7, column=0, sticky="ew")

        ttk.Separator(form_card).grid(row=8, column=0, sticky="ew", pady=18)

        actions = ttk.Frame(form_card, style="CardInner.TFrame")
        actions.grid(row=9, column=0, sticky="ew")
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)

        ttk.Button(actions, text="打开走势 / 查询", style="Primary.TButton", command=self._on_submit).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 8),
        )

        ttk.Button(actions, text="刷新基础数据", style="Accent.TButton", command=self._refresh_base_data).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(8, 0),
        )

        insight_card = ttk.Frame(content, padding=24, style="Card.TFrame")
        insight_card.grid(row=0, column=1, sticky="nsew")
        insight_card.columnconfigure(0, weight=1)

        ttk.Label(insight_card, textvariable=self.base_title_var, style="Section.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Label(
            insight_card,
            textvariable=self.base_desc_var,
            style="TLabel",
            wraplength=280,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(6, 12))

        badge = ttk.Label(insight_card, textvariable=self.base_update_var, style="Badge.TLabel")
        badge.grid(row=2, column=0, sticky="w")

        ttk.Separator(insight_card).grid(row=3, column=0, sticky="ew", pady=18)

        metrics = ttk.Frame(insight_card, style="CardInner.TFrame")
        metrics.grid(row=4, column=0, sticky="ew")
        metrics.columnconfigure(0, weight=1)
        metrics.columnconfigure(1, weight=1)

        ttk.Label(metrics, text="最新收盘价", style="MetricTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(metrics, text="当日区间", style="MetricTitle.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(metrics, textvariable=self.metric_price_var, style="MetricValue.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Label(metrics, textvariable=self.metric_range_var, style="MetricValue.TLabel").grid(row=1, column=1, sticky="w", pady=(4, 0))

        ttk.Label(metrics, text="振幅", style="MetricTitle.TLabel").grid(row=2, column=0, sticky="w", pady=(12, 0))
        ttk.Label(metrics, text="覆盖天数", style="MetricTitle.TLabel").grid(row=2, column=1, sticky="w", pady=(12, 0))
        ttk.Label(metrics, textvariable=self.metric_amplitude_var, style="MetricValue.TLabel").grid(row=3, column=0, sticky="w", pady=(4, 0))
        ttk.Label(metrics, textvariable=self.coverage_var, style="MetricValue.TLabel").grid(row=3, column=1, sticky="w", pady=(4, 0))

        self.view_base_btn = ttk.Button(
            insight_card,
            text="查看基础走势",
            style="Ghost.TButton",
            command=self._show_base_snapshot,
        )
        self.view_base_btn.grid(row=5, column=0, sticky="ew", pady=(20, 0))

        status_frame = ttk.Frame(container, style="App.TFrame")
        status_frame.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        status_frame.columnconfigure(1, weight=1)

        ttk.Separator(status_frame).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        ttk.Label(status_frame, text="状态", style="MetricTitle.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8))
        ttk.Label(status_frame, textvariable=self.status_var, style="Status.TLabel").grid(row=1, column=1, sticky="w")

        self._reset_base_summary()
    # endregion

    # region Data
    def _load_local_snapshot(self) -> None:
        try:
            snapshot = self.base_rates_service.load_snapshot()
        except BaseRatesRefreshError as exc:
            self._reset_base_summary()
            self.status_var.set(str(exc))
            return

        if snapshot:
            self._sync_base_snapshot(snapshot)
        else:
            self._reset_base_summary()
            self.status_var.set("未找到本地基础数据，请尝试刷新。")

    def _refresh_base_data(self) -> None:
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("错误", "请先输入 API Key！")
            return

        client = AlphaVantageClient(api_key)
        try:
            snapshot = self.base_rates_service.refresh_snapshot(
                client=client,
                outputsize=self.outputsize_var.get().strip() or "compact",
                days=DEFAULT_BASE_DAYS,
            )
        except BaseRatesRefreshError as exc:
            messagebox.showerror("刷新失败", str(exc))
            return

        self._sync_base_snapshot(snapshot, status_message=self._snapshot_status_text(snapshot, prefix="基础数据已更新"))
        messagebox.showinfo("完成", "基础数据刷新完成，快去探索最新走势吧！")

    def _on_submit(self) -> None:
        days_value = self.days_var.get().strip()
        if not days_value:
            self._show_base_snapshot()
            return

        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("错误", "请先输入 API Key！")
            return

        try:
            client = AlphaVantageClient(api_key)
            snapshot = client.fetch_rates(days=days_value, outputsize=self.outputsize_var.get())
        except (AlphaVantageError, ValueError) as exc:
            messagebox.showerror("查询失败", str(exc))
            return

        try:
            render_rates(snapshot, title="自定义数据走势")
        except RuntimeError as exc:
            messagebox.showinfo("提示", str(exc))
        except ValueError as exc:
            messagebox.showwarning("提示", str(exc))
        else:
            self.status_var.set(f"已展示近 {snapshot.trading_days()} 天的自定义走势。")

    def _show_base_snapshot(self) -> None:
        if not self._base_snapshot:
            messagebox.showinfo("提示", "暂无基础数据，请先刷新。")
            return

        try:
            render_rates(self._base_snapshot, title="基础数据走势")
        except RuntimeError as exc:
            messagebox.showinfo("提示", str(exc))
        except ValueError as exc:
            messagebox.showwarning("提示", str(exc))
        else:
            self.status_var.set(
                f"已打开基础数据走势（覆盖 {self._base_snapshot.trading_days()} 天）。"
            )

    def _reset_base_summary(self) -> None:
        self._base_snapshot = None
        self.base_title_var.set("基础数据未就绪")
        self.base_desc_var.set("刷新基础数据以解锁图表能力，或直接查询自定义区间。")
        self.base_update_var.set("尚未更新")
        self.metric_price_var.set("--")
        self.metric_range_var.set("--")
        self.metric_amplitude_var.set("--")
        self.coverage_var.set("--")
        if hasattr(self, "view_base_btn"):
            self.view_base_btn.state(["disabled"])

    def _sync_base_snapshot(self, snapshot: RatesSnapshot, status_message: Optional[str] = None) -> None:
        self._base_snapshot = snapshot
        span = snapshot.date_span()
        if snapshot.trading_days():
            coverage_text = f"覆盖 {snapshot.trading_days()} 个交易日"
            if span:
                coverage_text = f"{coverage_text}（{span}）"
        else:
            coverage_text = "暂无交易日信息"

        self.base_title_var.set("基础行情缓存已就绪")
        self.base_desc_var.set(coverage_text)
        self.base_update_var.set(snapshot.fetched_at.strftime("更新于 %Y-%m-%d %H:%M"))

        latest = snapshot.latest_bar()
        if latest:
            self.metric_price_var.set(f"{latest.close_price:.4f} CNY")
            self.metric_range_var.set(f"{latest.low_price:.4f} ~ {latest.high_price:.4f} CNY")
            self.metric_amplitude_var.set(f"{latest.amplitude:.2f}%")
        else:
            self.metric_price_var.set("--")
            self.metric_range_var.set("--")
            self.metric_amplitude_var.set("--")

        self.coverage_var.set(f"{snapshot.trading_days()} 天" if snapshot.trading_days() else "--")
        if hasattr(self, "view_base_btn"):
            self.view_base_btn.state(["!disabled"])

        status_text = status_message or self._snapshot_status_text(snapshot)
        self.status_var.set(status_text)

    # endregion

    # region Helpers
    @staticmethod
    def _snapshot_status_text(snapshot: RatesSnapshot, prefix: str = "本地基础数据") -> str:
        formatted = snapshot.fetched_at.strftime("%Y-%m-%d %H:%M:%S")
        return f"{prefix}更新时间：{formatted}"

    def run(self) -> None:
        self.mainloop()
    # endregion
