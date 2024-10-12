import pandas as pd
from deap import base, creator, tools, algorithms
import random
import multiprocessing
import os
from tqdm import tqdm
import torch

# 检查是否有可用的 GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 定义评估函数
def evaluate(
    individual,
    chess_data,
    BUDGET_LIMIT,
    PEOPLE_LIMIT,
    class_dict,
    species_dict,
    class_data,
    species_data,
):
    # 将个体转化为 Tensor 放到 GPU 上
    individual_tensor = torch.tensor(individual, device=device)
    combo = chess_data.iloc[individual_tensor.cpu().numpy()]  # 获取个体对应的棋子组合
    total_cost = torch.sum(torch.tensor(combo["price"].values, device=device))  # 计算组合的总费用

    if total_cost > BUDGET_LIMIT or len(individual) > PEOPLE_LIMIT:
        return (-1,)

    synergy_count, _ = calculate_synergy(
        combo, class_dict, species_dict, class_data, species_data
    )
    return (synergy_count,)

# 定义生成个体函数
def generate_individual(chess_data, MAX_MONOVALENT, MIN_MONOVALENT, BUDGET_LIMIT, PEOPLE_LIMIT):
    individual = []  
    total_cost = 0  
    available_indices = list(range(len(chess_data)))
    random.shuffle(available_indices)  

    for idx in available_indices:
        price = chess_data.iloc[idx]["price"]
        if (
            MIN_MONOVALENT <= price <= MAX_MONOVALENT
            and total_cost + price <= BUDGET_LIMIT
            and len(individual) < PEOPLE_LIMIT
        ):
            individual.append(idx)
            total_cost += price
        if total_cost == BUDGET_LIMIT or len(individual) == PEOPLE_LIMIT:
            break

    individual.sort() 
    return individual

# 定义交叉操作
def cxSet(ind1, ind2, chess_data, BUDGET_LIMIT, PEOPLE_LIMIT, MIN_MONOVALENT):
    temp1 = set(ind1)
    temp2 = set(ind2)
    all_indices = list(temp1.union(temp2))
    random.shuffle(all_indices)

    new_ind1 = []
    new_ind2 = []
    total_cost1 = 0
    total_cost2 = 0

    for idx in all_indices:
        price = chess_data.iloc[idx]["price"]
        if len(new_ind1) < PEOPLE_LIMIT and total_cost1 + price <= BUDGET_LIMIT and price >= MIN_MONOVALENT:
            new_ind1.append(idx)
            total_cost1 += price
        elif len(new_ind2) < PEOPLE_LIMIT and total_cost2 + price <= BUDGET_LIMIT and price >= MIN_MONOVALENT:
            new_ind2.append(idx)
            total_cost2 += price

    new_ind1.sort()
    new_ind2.sort()
    ind1[:] = new_ind1
    ind2[:] = new_ind2
    return ind1, ind2

# 定义变异操作
def mutSet(individual, indpb, chess_data, MAX_MONOVALENT, MIN_MONOVALENT, BUDGET_LIMIT):
    for i in range(len(individual)):
        if random.random() < indpb:
            current_cost = sum(chess_data.iloc[individual]["price"])
            current_price = chess_data.iloc[individual[i]]["price"]
            available_indices = list(set(range(len(chess_data))) - set(individual))
            random.shuffle(available_indices)

            for new_idx in available_indices:
                new_price = chess_data.iloc[new_idx]["price"]
                if (
                    MIN_MONOVALENT <= new_price <= MAX_MONOVALENT
                    and current_cost - current_price + new_price <= BUDGET_LIMIT
                ):
                    individual[i] = new_idx
                    break
    individual.sort()
    return (individual,)

# 计算羁绊函数
def calculate_synergy(combo, class_dict, species_dict, class_data, species_data):
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
            max_activated = 0
            for num in class_dict[cid]:
                if count >= num:
                    max_activated = num
                else:
                    break
            if max_activated > 0:
                synergy_count += 1
                synergy_list.append(f"{class_data[class_data['id'] == cid]['name'].values[0]}({max_activated})")

    for sid, count in species_count.items():
        if sid in species_dict:
            max_activated = 0
            for num in species_dict[sid]:
                if count >= num:
                    max_activated = num
                else:
                    break
            if max_activated > 0:
                synergy_count += 1
                synergy_list.append(f"{species_data[species_data['id'] == sid]['name'].values[0]}({max_activated})")

    return synergy_count, synergy_list

def genetic_algorithm_optimizer(processed_data_folder):
    print("开始羁绊优化...")
    chess_data_path = os.path.join(processed_data_folder, "chess_data.csv")
    class_data_path = os.path.join(processed_data_folder, "class_data.csv")
    species_data_path = os.path.join(processed_data_folder, "species_data.csv")
    chess_data = pd.read_csv(chess_data_path, usecols=["id", "name", "class", "species", "price"])
    class_data = pd.read_csv(class_data_path, usecols=["id", "numList", "name"])
    species_data = pd.read_csv(species_data_path, usecols=["id", "numList", "name"])

    class_data["numList"] = class_data["numList"].apply(eval)
    species_data["numList"] = species_data["numList"].apply(eval)

    class_dict = dict(zip(class_data["id"], class_data["numList"]))
    species_dict = dict(zip(species_data["id"], species_data["numList"]))

    BUDGET_LIMIT = int(input("请输入预算限制(默认50): ") or 50)
    PEOPLE_LIMIT = int(input("请输入人数上限(默认10): ") or 10)
    MIN_MONOVALENT = int(input("请输入单价下限(默认1): ") or 1)
    MAX_MONOVALENT = int(input("请输入单价上限(默认5): ") or 5)

    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    toolbox.register("attr_int", random.randint, 0, len(chess_data) - 1)
    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_int, n=PEOPLE_LIMIT)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", evaluate, chess_data=chess_data, BUDGET_LIMIT=BUDGET_LIMIT,
                     PEOPLE_LIMIT=PEOPLE_LIMIT, class_dict=class_dict, species_dict=species_dict,
                     class_data=class_data, species_data=species_data)
    toolbox.register("mate", cxSet, chess_data=chess_data, BUDGET_LIMIT=BUDGET_LIMIT,
                     PEOPLE_LIMIT=PEOPLE_LIMIT, MIN_MONOVALENT=MIN_MONOVALENT)
    toolbox.register("mutate", mutSet, indpb=0.2, chess_data=chess_data,
                     MAX_MONOVALENT=MAX_MONOVALENT, MIN_MONOVALENT=MIN_MONOVALENT, BUDGET_LIMIT=BUDGET_LIMIT)
    toolbox.register("select", tools.selTournament, tournsize=3)

    n_population = random.randint(100, 500) if device.type == "cpu" else random.randint(500, 1500)
    population = toolbox.population(n=n_population)

    for ind in population:
        ind.fitness.values = toolbox.evaluate(ind)

    NGEN = random.randint(50, 300) if device.type == "cpu" else random.randint(300, 1500)
    CXPB = round(random.uniform(0.50, 0.90), 2)
    MUTPB = round(random.uniform(0.10, 0.50), 2)

    print(f"本次算法使用设备：{device}")

    print(f"本次遗传算法随机参数:\n种群数量\t{n_population}\n迭代次数\t{NGEN}\n交叉概率\t{CXPB}\n变异概率\t{MUTPB}")

    with multiprocessing.Pool() as pool:
        toolbox.register("map", pool.map)

        for _ in tqdm(range(NGEN), desc="优化中"):
            offspring = algorithms.varAnd(population, toolbox, CXPB, MUTPB)
            fits = toolbox.map(toolbox.evaluate, offspring)

            for fit, ind in zip(fits, offspring):
                ind.fitness.values = fit

            population[:] = tools.selBest(offspring + population, k=len(population))

    best_ind = tools.selBest(population, 1)[0]
    synergy_count, synergy_list = calculate_synergy(
        chess_data.iloc[best_ind], class_dict, species_dict, class_data, species_data
    )
    print(f"最佳个体：{chess_data.iloc[best_ind]['name'].tolist()}")
    print(f"羁绊总数：{synergy_count}")
    print(f"羁绊列表：{synergy_list}")

if __name__ == "__main__":
    processed_src_folder = "your/processed/data/folder"  # 修改为你的数据文件夹路径
    genetic_algorithm_optimizer(processed_src_folder)
