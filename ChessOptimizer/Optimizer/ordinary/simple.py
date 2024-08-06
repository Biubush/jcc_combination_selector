import pandas as pd
import itertools

# 文件路径
chess_data_path = "src/processed/chess_data.csv"
class_data_path = "src/processed/class_data.csv"
species_data_path = "src/processed/species_data.csv"

# 读取数据
chess_data = pd.read_csv(chess_data_path, usecols=["id", "name", "class", "species", "price"])
class_data = pd.read_csv(class_data_path, usecols=["id", "numList", "name"])
species_data = pd.read_csv(species_data_path, usecols=["id", "numList", "name"])

# 转换 class 和 species 的 numList 为字典
class_dict = {row["id"]: eval(row["numList"]) for index, row in class_data.iterrows()}
species_dict = {row["id"]: eval(row["numList"]) for index, row in species_data.iterrows()}

# 计算羁绊数
def calculate_synergy(combo):
    class_count = {}
    species_count = {}
    for _, row in combo.iterrows():
        for c in eval(row["class"]):
            class_count[c] = class_count.get(c, 0) + 1
        for s in eval(row["species"]):
            species_count[s] = species_count.get(s, 0) + 1

    synergy_count = 0
    synergy_list = []
    for cid, count in class_count.items():
        if cid in class_dict:
            for num in class_dict[cid]:
                if count >= num:
                    synergy_count += 1
                    synergy_list.append(class_data[class_data["id"] == cid]["name"].values[0])

    for sid, count in species_count.items():
        if sid in species_dict:
            for num in species_dict[sid]:
                if count >= num:
                    synergy_count += 1
                    synergy_list.append(species_data[species_data["id"] == sid]["name"].values[0])

    return synergy_count, synergy_list

# 找到最大羁绊数
def find_max_synergy(budget_limit, people_limit, monovalent):
    max_synergy = 0
    best_combo = []
    best_synergy_list = []
    best_total_cost = 0

    affordable_chess_data = chess_data[chess_data["price"] <= monovalent]

    for combo_indexes in itertools.combinations(affordable_chess_data.index, people_limit):
        combo = affordable_chess_data.loc[list(combo_indexes)]
        total_cost = combo["price"].sum()
        if total_cost <= budget_limit:
            synergy, synergy_list = calculate_synergy(combo)
            if synergy > max_synergy:
                max_synergy = synergy
                best_combo = combo["name"].tolist()
                best_synergy_list = synergy_list
                best_total_cost = total_cost

    return max_synergy, best_combo, best_synergy_list, best_total_cost

# 主函数
def main():
    budget_limit = int(input("请输入金币上限: ")) or 45
    people_limit = int(input("请输入人数上限: ")) or 9
    max_monovalent = int(input("请输入最大单价: ")) or 5

    max_synergy, best_combo, best_synergy_list, best_total_cost = find_max_synergy(budget_limit, people_limit, max_monovalent)
    print(f"最大羁绊数: {max_synergy}, 最佳组合: {best_combo}, 总费用: {best_total_cost}")

if __name__ == "__main__":
    main()