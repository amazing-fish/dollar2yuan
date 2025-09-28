import os
from pathlib import Path
from tkinter import messagebox, ttk
import tkinter as tk
import json
from datetime import datetime, timedelta
from typing import Dict
import requests
import webview

'''
appkey和sign来自nowapi网站https://www.nowapi.com/api/finance.rate_history
或者联系我
'''
BASE_DATA_PATH = Path(__file__).resolve().parent / "data" / "usd_cny_base.json"
DEFAULT_BASE_DAYS = 30
DEFAULT_BASE_HT_TYPE = 'HT1D'


def fetch_data(appkey, sign, days, ht_type='HT1D'):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=int(days))
    date_start = start_date.strftime('%Y%m%d')
    date_end = end_date.strftime('%Y%m%d')

    url = "https://sapi.k780.com"
    params = {
        'app': 'finance.rate_history.v3',
        'curNoS': 'USDCNY',
        'htType': ht_type,
        'dateYmdS': f"{date_start}-{date_end}",
        'appkey': appkey,
        'sign': sign,
        'format': 'json',
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

    if str(data.get('success')) != '1':
        err_msg = data.get('msgid') or data.get('msg') or data.get('error') or '未知错误'
        raise ValueError(f"API 返回失败：{err_msg}")

    return data


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
            "data": ['开盘价', '收盘价', '最高价', '最低价', '振幅%'],
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

    html_content = f"""
    <!DOCTYPE html>
    <html style="height: 100%">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.bootcdn.net/ajax/libs/echarts/5.0.2/echarts.min.js"></script>
    </head>
    <body style="height: 100%; margin: 0">
        <div id="main" style="height: 100%"></div>
        <script type="text/javascript">
            var myChart = echarts.init(document.getElementById('main'), 'light');
            var option = {echarts_options};
            myChart.setOption(option);
        </script>
    </body>
    </html>
    """
    return html_content



def show_data_with_echarts(data, title='ECharts Visualization'):
    html_content = generate_html_for_echarts(data)
    webview.create_window(title, html=html_content)
    webview.start()


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

    appkey_var = tk.StringVar(value=os.getenv('NOWAPI_APPKEY', env_defaults.get('NOWAPI_APPKEY', '')))
    sign_var = tk.StringVar(value=os.getenv('NOWAPI_SIGN', env_defaults.get('NOWAPI_SIGN', '')))

    base_data = None

    def show_base_data():
        if not base_data:
            messagebox.showinfo("提示", "暂无基础数据，请先刷新。")
            return
        show_data_with_echarts(base_data, title="基础数据走势")

    def refresh_base_data():
        nonlocal base_data
        try:
            data = fetch_data(appkey, sign, DEFAULT_BASE_DAYS, DEFAULT_BASE_HT_TYPE)
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
        appkey = appkey_var.get().strip()
        sign = sign_var.get().strip()
        days = days_entry.get().strip()
        ht_type = ht_type_combo.get().strip()

        # 优先支持“仅查看基础数据”的路径：不需要凭证
        if not days:
            show_base_data()
            return

        # 需要发起请求时，必须提供凭证
        if not appkey or not sign:
            messagebox.showerror("错误", "请先输入 AppKey 和 Sign 凭证！")
            return

        if not days.isdigit():
            messagebox.showerror("错误", "请输入有效的天数！")
            return

        try:
            data = fetch_data(appkey, sign, days, ht_type)
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

    root = tk.Tk()
    root.title("汇率查询工具")

    # 启动即尝试读取本地基础数据（可被 on_submit/show_base_data 使用）
    base_data = load_base_data()

    # 新增凭证输入框
    ttk.Label(root, text="AppKey:").grid(row=0, column=0, padx=10, pady=10, sticky='e')
    appkey_entry = ttk.Entry(root, textvariable=appkey_var)
    appkey_entry.grid(row=0, column=1, padx=10, pady=10, sticky='we')

    ttk.Label(root, text="Sign:").grid(row=1, column=0, padx=10, pady=10, sticky='e')
    sign_entry = ttk.Entry(root, textvariable=sign_var, show='*')
    sign_entry.grid(row=1, column=1, padx=10, pady=10, sticky='we')

    # 近x天
    ttk.Label(root, text="近x天:").grid(row=2, column=0, padx=10, pady=10, sticky='e')
    days_entry = ttk.Entry(root)
    days_entry.grid(row=2, column=1, padx=10, pady=10, sticky='we')

    # 数据类型
    ttk.Label(root, text="数据类型:").grid(row=3, column=0, padx=10, pady=10, sticky='e')
    ht_type_combo = ttk.Combobox(root, values=['HT1D', 'HT1W', 'HT1M', 'HTHY', 'HT1Y'], state="readonly")
    ht_type_combo.grid(row=3, column=1, padx=10, pady=10, sticky='we')
    ht_type_combo.current(0)

    # 按钮：查询/查看基础数据（days 为空 → 查看基础数据；非空 → 执行查询并需要凭证）
    submit_btn = ttk.Button(root, text="查询/查看基础数据", command=on_submit)
    submit_btn.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

    # 刷新本地基础数据
    refresh_btn = ttk.Button(root, text="刷新基础数据", command=refresh_base_data)
    refresh_btn.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

    # 列伸缩
    root.columnconfigure(1, weight=1)

    root.mainloop()



if __name__ == "__main__":
    create_gui()
