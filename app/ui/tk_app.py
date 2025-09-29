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
        self.title("汇率查询工具")
        self.geometry("520x360")

        self.base_rates_service = base_rates_service
        self._base_snapshot: Optional[RatesSnapshot] = None

        self.env_defaults = load_env_defaults()
        self.api_key_var = tk.StringVar(value=os.getenv("ALPHAVANTAGE_API_KEY", self.env_defaults.get("ALPHAVANTAGE_API_KEY", "")))
        self.outputsize_var = tk.StringVar(value=os.getenv("ALPHAVANTAGE_OUTPUTSIZE", self.env_defaults.get("ALPHAVANTAGE_OUTPUTSIZE", "compact")))
        self.days_var = tk.StringVar()
        self.status_var = tk.StringVar(value="欢迎使用汇率查询工具")

        self._configure_style()
        self._build_layout()
        self._load_local_snapshot()

    # region UI
    def _configure_style(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TLabel", font=("Microsoft YaHei", 10))
        style.configure("Accent.TButton", padding=8, font=("Microsoft YaHei", 10))
        style.configure("Primary.TButton", padding=8, font=("Microsoft YaHei", 10))

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main_frame = ttk.Frame(self, padding=24)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(1, weight=1)

        header = ttk.Label(main_frame, text="美元兑人民币日度行情", font=("Microsoft YaHei", 14, "bold"))
        header.grid(row=0, column=0, columnspan=2, pady=(0, 16), sticky="w")

        ttk.Label(main_frame, text="API Key").grid(row=1, column=0, padx=(0, 12), pady=6, sticky="e")
        api_entry = ttk.Entry(main_frame, textvariable=self.api_key_var)
        api_entry.grid(row=1, column=1, padx=(0, 12), pady=6, sticky="ew")

        ttk.Label(main_frame, text="Output Size").grid(row=2, column=0, padx=(0, 12), pady=6, sticky="e")
        output_combo = ttk.Combobox(main_frame, values=["compact", "full"], textvariable=self.outputsize_var, state="readonly")
        output_combo.grid(row=2, column=1, padx=(0, 12), pady=6, sticky="ew")
        if self.outputsize_var.get() not in {"compact", "full"}:
            self.outputsize_var.set("compact")

        ttk.Label(main_frame, text="近 X 天").grid(row=3, column=0, padx=(0, 12), pady=6, sticky="e")
        days_entry = ttk.Entry(main_frame, textvariable=self.days_var)
        days_entry.grid(row=3, column=1, padx=(0, 12), pady=6, sticky="ew")

        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=4, column=0, columnspan=2, pady=16, sticky="ew")
        action_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(1, weight=1)

        submit_btn = ttk.Button(action_frame, text="查询 / 查看基础数据", style="Primary.TButton", command=self._on_submit)
        submit_btn.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        refresh_btn = ttk.Button(action_frame, text="刷新基础数据", style="Accent.TButton", command=self._refresh_base_data)
        refresh_btn.grid(row=0, column=1, padx=(8, 0), sticky="ew")

        status_bar = ttk.Label(main_frame, textvariable=self.status_var, foreground="#2c3e50")
        status_bar.grid(row=5, column=0, columnspan=2, pady=(12, 0), sticky="w")
    # endregion

    # region Data
    def _load_local_snapshot(self) -> None:
        try:
            snapshot = self.base_rates_service.load_snapshot()
        except BaseRatesRefreshError as exc:
            self.status_var.set(str(exc))
            return

        if snapshot:
            self._base_snapshot = snapshot
            self.status_var.set(self._snapshot_status_text(snapshot))
        else:
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

        self._base_snapshot = snapshot
        self.status_var.set(self._snapshot_status_text(snapshot, prefix="基础数据已更新"))
        messagebox.showinfo("成功", "基础数据已更新！")

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

    # endregion

    # region Helpers
    @staticmethod
    def _snapshot_status_text(snapshot: RatesSnapshot, prefix: str = "本地基础数据") -> str:
        formatted = snapshot.fetched_at.strftime("%Y-%m-%d %H:%M:%S")
        return f"{prefix}更新时间：{formatted}"

    def run(self) -> None:
        self.mainloop()
    # endregion
