import os
from pathlib import Path
from tkinter import messagebox, ttk
import tkinter as tk
import json
from datetime import datetime
from typing import Dict
import requests
import webview


_webview_window_open = False

BASE_DATA_PATH = Path(__file__).resolve().parent / "data" / "usd_cny_base.json"
DEFAULT_BASE_DAYS = 30

def fetch_data(api_key, days, outputsize='compact'):
    if not api_key:
        raise ValueError("请提供有效的 API Key。")

    try:
        days_int = max(int(days), 1)
    except (TypeError, ValueError) as exc:
        raise ValueError("天数需为正整数。") from exc

    size = (outputsize or 'compact').strip().lower()
    if size not in {'compact', 'full'}:
        size = 'compact'

    url = "https://www.alphavantage.co/query"
    params = {
        "function": "FX_DAILY",
        "from_symbol": "USD",
        "to_symbol": "CNY",
        "apikey": api_key,
        "outputsize": size,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ConnectionError("无法连接到汇率服务，请检查网络或稍后再试。") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise ValueError("API 返回的内容不是有效的 JSON。") from exc

    if 'Error Message' in data:
        raise ValueError(data['Error Message'])

    if 'Note' in data:
        raise ValueError(data['Note'])

    time_series = data.get('Time Series FX (Daily)')
    if not time_series:
        raise ValueError("API 未返回有效的日度汇率数据。")

    sorted_dates = sorted(time_series.keys())
    dt_list = []
    for date_str in sorted_dates:
        values = time_series[date_str]
        try:
            open_price = float(values['1. open'])
            high_price = float(values['2. high'])
            low_price = float(values['3. low'])
            close_price = float(values['4. close'])
        except (KeyError, ValueError) as exc:
            raise ValueError("API 返回的数据结构异常。") from exc

        amplitude = 0.0
        if low_price:
            amplitude = ((high_price - low_price) / low_price) * 100

        dt_list.append({
            'd': date_str.replace('-', ''),
            'o': f"{open_price:.4f}",
            'c': f"{close_price:.4f}",
            'h': f"{high_price:.4f}",
            'l': f"{low_price:.4f}",
            'am': f"{amplitude:.2f}",
        })

    dt_list = dt_list[-days_int:]

    return {
        'success': '1',
        'result': {
            'source': 'alpha_vantage.FX_DAILY',
            'fetched_at': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'dtList': dt_list,
        }
    }


def load_base_data():
    if not BASE_DATA_PATH.exists():
        return None
    try:
        with BASE_DATA_PATH.open('r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        messagebox.showwarning("警告", f"基础数据读取失败：{exc}")
        return None


def save_base_data(data):
    BASE_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with BASE_DATA_PATH.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_html_for_echarts(data):
    if not data or 'result' not in data or 'dtList' not in data['result']:
        return "<p>No data available</p>"

    dates = [item['d'] for item in data['result']['dtList']]
    opening_prices = [float(item['o']) for item in data['result']['dtList']]
    closing_prices = [float(item['c']) for item in data['result']['dtList']]
    highest_prices = [float(item['h']) for item in data['result']['dtList']]
    lowest_prices = [float(item['l']) for item in data['result']['dtList']]
    amplitude_percentages = [float(item['am']) for item in data['result']['dtList']]

    echarts_options = {
        "tooltip": {
            "trigger": 'axis',
            "axisPointer": {
                "type": 'cross',
                "crossStyle": {
                    "color": '#999'
                }
            },
            "formatter": "Date: {b0}<br/>{a0}: {c0} CNY<br/>{a1}: {c1} CNY<br/>{a2}: {c2} CNY<br/>{a3}: {c3} CNY<br/>{a4}: {c4}%"
        },
        "legend": {
            "data": ['开盘价', '收盘价', '最高价', '最低价', '振幅（%）'],
            "orient": 'horizontal',
            "top": 'top',
            "left": 'center'
        },
        "grid": {
            "left": '3%',
            "right": '4%',
            "bottom": '3%',
            "containLabel": 'true'
        },
        "toolbox": {
            "feature": {
                "dataZoom": {
                    "yAxisIndex": 'none',
                    "title": {
                        "zoom": "Zoom region",
                        "back": "Restore zoom"
                    }
                },
                "restore": {},
                "saveAsImage": {},
                "magicType": {
                    "type": ['line', 'bar'],
                    "title": {
                        "line": "Line Chart",
                        "bar": "Bar Chart"
                    }
                }
            },
            "right": 10
        },
        "xAxis": {
            "type": 'category',
            "data": dates,
            "axisPointer": {
                "type": 'shadow'
            }
        },
        "yAxis": [{
            "type": 'value',
            "name": '价格',
            "min": 'dataMin',
            "max": 'dataMax',
            "position": 'right',
            "axisLine": {
                "lineStyle": {
                    "color": '#5793f3'
                }
            },
            "axisLabel": {
                "formatter": '{value} CNY'
            }
        }, {
            "type": 'value',
            "name": '振幅（%）',
            "min": 0,
            "max": 'dataMax',
            "position": 'left',
            "axisLine": {
                "lineStyle": {
                    "color": '#d14a61'
                }
            },
            "axisLabel": {
                "formatter": '{value}%'
            }
        }],
        "series": [{
            "name": '开盘价',
            "type": 'line',
            "data": opening_prices
        }, {
            "name": '收盘价',
            "type": 'line',
            "data": closing_prices
        }, {
            "name": '最高价',
            "type": 'line',
            "data": highest_prices
        }, {
            "name": '最低价',
            "type": 'line',
            "data": lowest_prices
        }, {
            "name": '振幅（%）',
            "type": 'line',
            "yAxisIndex": 1,
            "data": amplitude_percentages
        }]
    }

    option_json = json.dumps(echarts_options, ensure_ascii=False)

    html_content = f"""
    <!DOCTYPE html>
    <html style="height: 100%">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.bootcdn.net/ajax/libs/echarts/5.0.2/echarts.min.js"></script>
        <style>
            body {{
                height: 100%;
                margin: 0;
                display: flex;
                flex-direction: column;
            }}

            #main {{
                flex: 1 1 auto;
            }}
        </style>
    </head>
    <body>
        <div id="main"></div>
        <script type="text/javascript">
            var myChart = echarts.init(document.getElementById('main'), 'light');
            var option = {option_json};

            if (!option.legend) {{
                option.legend = {{}};
            }}
            if (!option.legend.selected) {{
                option.legend.selected = {{}};
            }}

            myChart.setOption(option);

            var amplitudeSeriesName = '振幅（%）';
            var amplitudeAxisIndex = 1;
            var amplitudeIndex = option.series.findIndex(function (item) {{
                return item.name === amplitudeSeriesName;
            }});

            function syncAmplitudeAxis(selectedMap) {{
                if (!selectedMap) {{
                    return;
                }}

                var isSelected = selectedMap[amplitudeSeriesName];
                if (typeof isSelected === 'undefined') {{
                    isSelected = true;
                }}

                var currentOption = myChart.getOption();
                if (!currentOption) {{
                    return;
                }}

                var axisConfig = (currentOption.yAxis || []).map(function (axis, index) {{
                    if (index !== amplitudeAxisIndex) {{
                        return axis;
                    }}

                    var updatedAxis = Object.assign({{}}, axis);
                    updatedAxis.show = !!isSelected;

                    var splitLine = Object.assign({{}}, axis.splitLine || {{}});
                    splitLine.show = !!isSelected;
                    updatedAxis.splitLine = splitLine;

                    return updatedAxis;
                }});

                var optionUpdate = {{
                    yAxis: axisConfig
                }};

                if (amplitudeIndex !== -1) {{
                    var currentSeries = (currentOption.series || [])[amplitudeIndex] || {{}};
                    var tooltipConfig = Object.assign({{}}, currentSeries.tooltip || {{}});
                    tooltipConfig.show = !!isSelected;

                    optionUpdate.series = [{{
                        name: amplitudeSeriesName,
                        showSymbol: !!isSelected,
                        tooltip: tooltipConfig
                    }}];
                }}

                myChart.setOption(optionUpdate, false);
            }}

            myChart.on('legendselectchanged', function (params) {{
                if (params.name === amplitudeSeriesName) {{
                    syncAmplitudeAxis(params.selected);
                }}
            }});

            var initialOption = myChart.getOption();
            var initialLegendSelected = (initialOption.legend && initialOption.legend[0] && initialOption.legend[0].selected) || {{}};
            syncAmplitudeAxis(initialLegendSelected);

            window.addEventListener('resize', function () {{
                if (myChart) {{
                    myChart.resize();
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html_content



def show_data_with_echarts(data, title='ECharts Visualization'):
    global _webview_window_open

    if _webview_window_open:
        messagebox.showinfo("提示", "图表窗口已打开，请先关闭后再试。")
        return

    html_content = generate_html_for_echarts(data)
    window = webview.create_window(title, html=html_content)

    def on_closed():
        global _webview_window_open
        _webview_window_open = False

    window.events.closed += on_closed
    _webview_window_open = True
    try:
        webview.start()
    finally:
        _webview_window_open = False


# GUI界面
def create_gui():
    def load_local_env() -> Dict[str, str]:
        env_defaults: Dict[str, str] = {}
        env_file = Path(__file__).resolve().parent / '.env'
        if env_file.exists():
            for line in env_file.read_text(encoding='utf-8').splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith('#') or '=' not in stripped:
                    continue
                key, value = stripped.split('=', 1)
                env_defaults[key.strip()] = value.strip().strip('"').strip("'")
        return env_defaults

    env_defaults = load_local_env()

    root = tk.Tk()
    root.title("汇率查询工具")

    api_key_var = tk.StringVar(value=os.getenv('ALPHAVANTAGE_API_KEY', env_defaults.get('ALPHAVANTAGE_API_KEY', '')))
    outputsize_var = tk.StringVar(value=os.getenv('ALPHAVANTAGE_OUTPUTSIZE', env_defaults.get('ALPHAVANTAGE_OUTPUTSIZE', 'compact')) or 'compact')

    base_data = None

    def show_base_data():
        if not base_data:
            messagebox.showinfo("提示", "暂无基础数据，请先刷新。")
            return
        show_data_with_echarts(base_data, title="基础数据走势")

    def refresh_base_data():
        nonlocal base_data
        api_key = api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("错误", "请先输入 API Key！")
            return

        try:
            data = fetch_data(api_key, DEFAULT_BASE_DAYS, outputsize_var.get())
        except ValueError as e:
            messagebox.showerror("错误", f"API错误：{e}")
            return
        except ConnectionError as e:
            messagebox.showerror("连接错误", f"网络或API连接问题：{e}")
            return
        except Exception as e:
            messagebox.showerror("未知错误", f"出现未知错误：{e}")
            return

        save_base_data(data)
        base_data = data
        messagebox.showinfo("成功", f"基础数据已更新\n最新更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def on_submit():
        api_key = api_key_var.get().strip()
        days = days_entry.get().strip()
        outputsize = outputsize_var.get().strip()

        # 优先支持“仅查看基础数据”的路径：不需要凭证
        if not days:
            show_base_data()
            return

        # 需要发起请求时，必须提供凭证
        if not api_key:
            messagebox.showerror("错误", "请先输入 API Key！")
            return

        if not days.isdigit():
            messagebox.showerror("错误", "请输入有效的天数！")
            return

        try:
            data = fetch_data(api_key, days, outputsize)
        except ValueError as e:
            messagebox.showerror("错误", f"API 错误：{e}")
            return
        except ConnectionError as e:
            messagebox.showerror("连接错误", f"网络或 API 连接问题：{e}")
            return
        except Exception as e:
            messagebox.showerror("未知错误", f"出现未知错误：{e}")
            return

        show_data_with_echarts(data, title="自定义数据走势")

    # 启动即尝试读取本地基础数据（可被 on_submit/show_base_data 使用）
    base_data = load_base_data()

    # 新增凭证输入框
    ttk.Label(root, text="API Key:").grid(row=0, column=0, padx=10, pady=10, sticky='e')
    api_key_entry = ttk.Entry(root, textvariable=api_key_var)
    api_key_entry.grid(row=0, column=1, padx=10, pady=10, sticky='we')

    ttk.Label(root, text="Output Size:").grid(row=1, column=0, padx=10, pady=10, sticky='e')
    outputsize_combo = ttk.Combobox(root, values=['compact', 'full'], textvariable=outputsize_var, state="readonly")
    outputsize_combo.grid(row=1, column=1, padx=10, pady=10, sticky='we')
    if outputsize_var.get() not in {'compact', 'full'}:
        outputsize_var.set('compact')

    # 近x天
    ttk.Label(root, text="近x天:").grid(row=2, column=0, padx=10, pady=10, sticky='e')
    days_entry = ttk.Entry(root)
    days_entry.grid(row=2, column=1, padx=10, pady=10, sticky='we')

    # 按钮：查询/查看基础数据（days 为空 → 查看基础数据；非空 → 执行查询并需要凭证）
    submit_btn = ttk.Button(root, text="查询/查看基础数据", command=on_submit)
    submit_btn.grid(row=3, column=0, columnspan=2, padx=10, pady=10)

    # 刷新本地基础数据
    refresh_btn = ttk.Button(root, text="刷新基础数据", command=refresh_base_data)
    refresh_btn.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

    # 列伸缩
    root.columnconfigure(1, weight=1)

    root.mainloop()



if __name__ == "__main__":
    create_gui()
