import requests
import json
import time
import os


def get_newest_data(output_folder):
    print("开始获取最新数据...")
    # 定义基本的 URL
    base_url = "https://game.gtimg.cn/images/lol/act/jkzlk/js"

    # 获取当前时间戳
    timestamp = int(time.time())

    # 将时间戳作为参数添加到 URL 中
    url_with_timestamp = f"{base_url}/config/versiondataconfig.js?ts={timestamp}"

    # 禁用代理
    proxies = {
        "http": None,
        "https": None,
    }

    try:
        # 下载文件
        response = requests.get(url_with_timestamp, proxies=proxies)
        response.raise_for_status()  # 检查请求是否成功

        # 将文件内容转换为 JSON 格式
        js_data = response.text

        # 解析为 Python 字典
        data = json.loads(js_data)

        latest_version = data[-1]

        # 输出最新版本号
        print(f"最新版本号: {latest_version['version']}")
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        chess_data_url = base_url + latest_version["herourl"]
        class_data_url = base_url + latest_version["joburl"]
        species_data_url = base_url + latest_version["traiturl"]
        chess_data = requests.get(chess_data_url, proxies=proxies).json()
        class_data = requests.get(class_data_url, proxies=proxies).json()
        species_data = requests.get(species_data_url, proxies=proxies).json()
        chess_data_path = os.path.join(output_folder, "chess.json")
        class_data_path = os.path.join(output_folder, "class.json")
        species_data_path = os.path.join(output_folder, "species.json")
        with open(chess_data_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(chess_data, indent=2, ensure_ascii=False))
        with open(class_data_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(class_data, indent=2, ensure_ascii=False))
        with open(species_data_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(species_data, indent=2, ensure_ascii=False))
        print("数据获取成功")
        print('-' * 80)
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
