import pandas as pd  # 导入pandas库，用于数据处理
import itertools  # 导入itertools库，用于生成组合
from concurrent.futures import (
    ThreadPoolExecutor,
)  # 导入ThreadPoolExecutor，用于并行处理
from threading import Lock  # 导入Lock，用于线程安全
import os  # 导入os库，用于文件操作

# 文件路径
chess_data_path = "src/processed/chess_data.csv"  # 棋子数据的CSV文件路径
class_data_path = "src/processed/class_data.csv"  # 职业数据的CSV文件路径
species_data_path = "src/processed/species_data.csv"  # 种族数据的CSV文件路径

# 读取数据
chess_data = pd.read_csv(
    chess_data_path, usecols=["id", "name", "class", "species", "price"]
)  # 只读取必要的列
class_data = pd.read_csv(
    class_data_path, usecols=["id", "numList", "name"]
)  # 只读取必要的列
species_data = pd.read_csv(
    species_data_path, usecols=["id", "numList", "name"]
)  # 只读取必要的列

# 转换 class 和 species 的 numList 为字典
class_dict = {
    row["id"]: eval(row["numList"]) for index, row in class_data.iterrows()
}  # 将职业数据中的numList列转换为字典
species_dict = {
    row["id"]: eval(row["numList"]) for index, row in species_data.iterrows()
}  # 将种族数据中的numList列转换为字典


# 计算羁绊数
def calculate_synergy(combo):
    class_count = {}  # 初始化职业计数字典
    species_count = {}  # 初始化种族计数字典

    # 计算当前组合中的职业和种族数量
    for _, row in combo.iterrows():
        for c in eval(row["class"]):  # 遍历当前棋子组合的职业
            class_count[c] = class_count.get(c, 0) + 1  # 增加职业计数
        for s in eval(row["species"]):  # 遍历当前棋子组合的种族
            species_count[s] = species_count.get(s, 0) + 1  # 增加种族计数

    # 计算激活的羁绊数
    synergy_count = 0  # 初始化激活羁绊计数
    synergy_list = []  # 初始化激活的羁绊列表

    for cid, count in class_count.items():
        if cid in class_dict:  # 如果职业存在于职业字典中
            for num in class_dict[cid]:
                if count >= num:  # 如果当前组合的职业数量大于或等于所需数量
                    synergy_count += 1  # 增加羁绊计数
                    synergy_list.append(
                        class_data[class_data["id"] == cid]["name"].values[0]
                    )  # 添加激活的羁绊名称

    for sid, count in species_count.items():
        if sid in species_dict:  # 如果种族存在于种族字典中
            for num in species_dict[sid]:
                if count >= num:  # 如果当前组合的种族数量大于或等于所需数量
                    synergy_count += 1  # 增加羁绊计数
                    synergy_list.append(
                        species_data[species_data["id"] == sid]["name"].values[0]
                    )  # 添加激活的羁绊名称

    return synergy_count, synergy_list  # 返回激活的羁绊数和羁绊列表


# 找到最大羁绊数
def find_max_synergy(budget_limit, people_limit, max_worker, monovalent):
    max_synergy = 0  # 初始化最大羁绊数
    best_combo = []  # 初始化最佳组合
    best_synergy_list = []  # 初始化最佳羁绊列表
    best_total_cost = 0  # 初始化最佳组合的总费用
    lock = Lock()  # 创建锁对象以确保线程安全

    # 过滤棋子数据，只保留价格小于等于 最高单价 的棋子
    affordable_chess_data = chess_data[
        chess_data["price"] <= monovalent
    ]  # 过滤价格小于等于 最大单价 的棋子

    # 生成所有可能的棋子组合
    possible_combinations = itertools.combinations(
        affordable_chess_data.index, people_limit
    )  # 生成指定人数限制的所有棋子组合

    def process_combo(indexes):
        nonlocal max_synergy, best_combo, best_synergy_list, best_total_cost  # 声明使用外部作用域的变量
        combo = affordable_chess_data.loc[list(indexes)]  # 获取组合对应的棋子数据
        total_cost = combo["price"].sum()  # 计算组合的总费用

        if total_cost <= budget_limit:  # 如果组合的总费用在预算范围内
            synergy, synergy_list = calculate_synergy(
                combo
            )  # 计算组合的羁绊数和激活的羁绊列表

            with lock:  # 使用锁来保证对共享变量的安全访问
                if synergy > max_synergy:  # 如果当前组合的羁绊数大于最大羁绊数
                    max_synergy = synergy  # 更新最大羁绊数
                    best_combo = combo["name"].tolist()  # 更新最佳组合
                    best_synergy_list = synergy_list  # 更新最佳羁绊列表
                    best_total_cost = total_cost  # 更新最佳组合的总费用
                    print(
                        f"当前最大羁绊数: {max_synergy}, 当前最佳组合: {best_combo}, 当前总费用: {best_total_cost}"
                    )  # 打印当前最大羁绊数和最佳组合

    # 使用线程池处理组合
    with ThreadPoolExecutor(
        max_workers=max_worker, thread_name_prefix="synergy"
    ) as executor:  # 减少线程池大小
        # 使用迭代器分批处理组合
        while True:
            batch = list(itertools.islice(possible_combinations, 1000))
            if not batch:
                break
            executor.map(process_combo, batch)  # 并行处理批次组合

    return (
        max_synergy,
        best_combo,
        best_synergy_list,
        best_total_cost,
    )  # 返回最大羁绊数和最佳组合


# 主函数
def main():
    # 输入金币上限和人数上限
    budget_limit = int(input("请输入金币上限: ")) or 45  # 从用户输入获取金币上限
    people_limit = int(input("请输入人数上限: ")) or 9  # 从用户输入获取人数上限
    max_monovalent = int(input("请输入最大单价: ")) or 5  # 从用户输入获取最大单价

    max_threadings = 14 - people_limit  # 动态设置最大线程数

    print(
        f"本次策略：金币上限为{budget_limit}，人数上限为{people_limit}，最大单价为{max_monovalent}，最大线程数为{max_threadings}"
    )

    # 找到最佳组合
    find_max_synergy(
        budget_limit, people_limit, max_threadings, max_monovalent
    )  # 调用函数找出最大羁绊数和最佳组合

if __name__ == "__main__":
    main()  # 调用主函数
