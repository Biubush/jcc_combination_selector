import pandas as pd
from deap import base, creator, tools, algorithms
import random
import multiprocessing
import os
from tqdm import tqdm  # 引入 tqdm 库

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
    combo = chess_data.iloc[individual]  # 获取个体对应的棋子组合
    total_cost = combo["price"].sum()  # 计算组合的总费用
    # 如果不满足限制条件，返回-1
    if total_cost > BUDGET_LIMIT or len(individual) > PEOPLE_LIMIT:
        return (-1,)
    synergy_count, _ = calculate_synergy(
        combo, class_dict, species_dict, class_data, species_data
    )  # 计算组合的羁绊数
    return (synergy_count,)  # 返回羁绊数作为适应度值

# 定义生成个体函数
def generate_individual(chess_data, MAX_MONOVALENT, MIN_MONOVALENT, BUDGET_LIMIT, PEOPLE_LIMIT):
    individual = []  # 初始化个体列表
    total_cost = 0  # 初始化总费用
    available_indices = list(range(len(chess_data)))  # 获取可用索引列表
    random.shuffle(available_indices)  # 随机打乱索引列表

    for idx in available_indices:
        price = chess_data.iloc[idx]["price"]  # 获取当前棋子的价格
        # 检查单价限制、总费用限制和人数限制
        if (
            MIN_MONOVALENT <= price <= MAX_MONOVALENT
            and total_cost + price <= BUDGET_LIMIT
            and len(individual) < PEOPLE_LIMIT
        ):
            individual.append(idx)  # 添加当前索引到个体列表
            total_cost += price  # 更新总费用
        # 如果达到预算或人数限制，则停止生成
        if total_cost == BUDGET_LIMIT or len(individual) == PEOPLE_LIMIT:
            break

    individual.sort()  # 按索引排序，避免重复组合
    return individual  # 返回生成的个体

# 定义交叉操作
def cxSet(ind1, ind2, chess_data, BUDGET_LIMIT, PEOPLE_LIMIT, MIN_MONOVALENT):
    temp1 = set(ind1)  # 将个体1转换为集合
    temp2 = set(ind2)  # 将个体2转换为集合
    all_indices = list(temp1.union(temp2))  # 合并两个集合并转换为列表
    random.shuffle(all_indices)  # 随机打乱合并后的列表

    new_ind1 = []  # 初始化新个体1
    new_ind2 = []  # 初始化新个体2
    total_cost1 = 0  # 初始化新个体1的总费用
    total_cost2 = 0  # 初始化新个体2的总费用

    for idx in all_indices:
        price = chess_data.iloc[idx]["price"]  # 获取当前棋子的价格
        # 将索引添加到新个体1，满足人数和预算限制
        if len(new_ind1) < PEOPLE_LIMIT and total_cost1 + price <= BUDGET_LIMIT and price >= MIN_MONOVALENT:
            new_ind1.append(idx)
            total_cost1 += price  # 更新新个体1的总费用
        # 将索引添加到新个体2，满足人数和预算限制
        elif len(new_ind2) < PEOPLE_LIMIT and total_cost2 + price <= BUDGET_LIMIT and price >= MIN_MONOVALENT:
            new_ind2.append(idx)
            total_cost2 += price  # 更新新个体2的总费用

    new_ind1.sort()  # 按索引排序
    new_ind2.sort()  # 按索引排序
    ind1[:] = new_ind1  # 更新个体1
    ind2[:] = new_ind2  # 更新个体2
    return ind1, ind2  # 返回更新后的个体

# 定义变异操作
def mutSet(individual, indpb, chess_data, MAX_MONOVALENT, MIN_MONOVALENT, BUDGET_LIMIT):
    for i in range(len(individual)):
        # 以概率indpb进行变异
        if random.random() < indpb:
            current_cost = sum(
                chess_data.iloc[individual]["price"]
            )  # 计算当前个体的总费用
            current_price = chess_data.iloc[individual[i]][
                "price"
            ]  # 获取当前索引的价格
            available_indices = list(
                set(range(len(chess_data))) - set(individual)
            )  # 获取可用索引列表
            random.shuffle(available_indices)  # 随机打乱可用索引列表

            for new_idx in available_indices:
                new_price = chess_data.iloc[new_idx]["price"]  # 获取新索引的价格
                # 检查新价格是否满足单价限制和预算限制
                if (
                    MIN_MONOVALENT <= new_price <= MAX_MONOVALENT
                    and current_cost - current_price + new_price <= BUDGET_LIMIT
                ):
                    individual[i] = new_idx  # 替换当前索引
                    break
    individual.sort()  # 按索引排序
    return (individual,)  # 返回变异后的个体

# 计算羁绊函数（用于最终结果展示和评估）
def calculate_synergy(combo, class_dict, species_dict, class_data, species_data):
    class_count = {}  # 初始化职业计数字典
    species_count = {}  # 初始化种族计数字典

    for _, row in combo.iterrows():
        # 解析职业信息并计数
        for c in eval(row["class"]):
            class_count[c] = class_count.get(c, 0) + 1
        # 解析种族信息并计数
        for s in eval(row["species"]):
            species_count[s] = species_count.get(s, 0) + 1

    synergy_count = 0  # 初始化羁绊计数
    synergy_list = []  # 初始化羁绊列表

    # 计算职业羁绊
    for cid, count in class_count.items():
        if cid in class_dict:
            max_activated = 0  # 初始化激活数
            for num in class_dict[cid]:
                if count >= num:
                    max_activated = num  # 更新最大激活数
                else:
                    break
            if max_activated > 0:
                synergy_count += 1  # 增加羁绊计数
                synergy_list.append(
                    f"{class_data[class_data['id'] == cid]['name'].values[0]}({max_activated})"
                )  # 将激活的羁绊名称添加到列表

    # 计算种族羁绊
    for sid, count in species_count.items():
        if sid in species_dict:
            max_activated = 0  # 初始化激活数
            for num in species_dict[sid]:
                if count >= num:
                    max_activated = num  # 更新最大激活数
                else:
                    break
            if max_activated > 0:
                synergy_count += 1  # 增加羁绊计数
                synergy_list.append(
                    f"{species_data[species_data['id'] == sid]['name'].values[0]}({max_activated})"
                )  # 将激活的羁绊名称添加到列表

    return synergy_count, synergy_list  # 返回羁绊计数和列表

def genetic_algorithm_optimizer(processed_data_folder):
    print("开始羁绊优化...")
    # 文件路径
    chess_data_path = os.path.join(processed_data_folder, "chess_data.csv")
    class_data_path = os.path.join(processed_data_folder, "class_data.csv")
    species_data_path = os.path.join(processed_data_folder, "species_data.csv")
    # 读取棋子数据，包括id、名称、职业、种族、价格
    chess_data = pd.read_csv(
        chess_data_path,
        usecols=["id", "name", "class", "species", "price"],
    )
    # 读取职业数据，包括id、数量列表、名称
    class_data = pd.read_csv(class_data_path, usecols=["id", "numList", "name"])
    # 读取种族数据，包括id、数量列表、名称
    species_data = pd.read_csv(species_data_path, usecols=["id", "numList", "name"])

    # 将职业数据和种族数据中的数量列表字符串转换为列表对象
    class_data["numList"] = class_data["numList"].apply(eval)
    species_data["numList"] = species_data["numList"].apply(eval)

    # 将职业数据和种族数据转换为字典形式，便于后续处理
    class_dict = dict(zip(class_data["id"], class_data["numList"]))
    species_dict = dict(zip(species_data["id"], species_data["numList"]))

    # 获取用户输入
    BUDGET_LIMIT = int(input("请输入预算限制(默认50): ") or 50)
    PEOPLE_LIMIT = int(input("请输入人数上限(默认10): ") or 10)
    MIN_MONOVALENT = int(input("请输入单价下限(默认1): ") or 1)
    MAX_MONOVALENT = int(input("请输入单价上限(默认5): ") or 5)

    # 定义遗传算法的目标函数
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    toolbox.register("attr_int", random.randint, 0, len(chess_data) - 1)
    toolbox.register(
        "individual",
        tools.initRepeat,
        creator.Individual,
        toolbox.attr_int,
        n=PEOPLE_LIMIT,
    )
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register(
        "evaluate",
        evaluate,
        chess_data=chess_data,
        BUDGET_LIMIT=BUDGET_LIMIT,
        PEOPLE_LIMIT=PEOPLE_LIMIT,
        class_dict=class_dict,
        species_dict=species_dict,
        class_data=class_data,
        species_data=species_data,
    )
    toolbox.register(
        "mate",
        cxSet,
        chess_data=chess_data,
        BUDGET_LIMIT=BUDGET_LIMIT,
        PEOPLE_LIMIT=PEOPLE_LIMIT,
        MIN_MONOVALENT=MIN_MONOVALENT
    )
    toolbox.register(
        "mutate",
        mutSet,
        indpb=0.2,
        chess_data=chess_data,
        MAX_MONOVALENT=MAX_MONOVALENT,
        MIN_MONOVALENT=MIN_MONOVALENT,
        BUDGET_LIMIT=BUDGET_LIMIT,
    )
    toolbox.register("select", tools.selTournament, tournsize=3)

    # 种群数量,100~500之间的随机整数
    n_population = random.randint(100, 500)
    population = toolbox.population(n=n_population)  # 初始化种群

    # 设置遗传算法参数
    NGEN = random.randint(50, 300)  # 迭代次数,50~300之间的随机整数
    CXPB = round(random.uniform(0.50, 0.90), 2)  # 交叉概率,0.50~0.90之间的随机浮点数，保留2位小数
    MUTPB = round(random.uniform(0.10, 0.50), 2)  # 变异概率,0.10~0.50之间的随机浮点数，保留2位小数

    print(f"本次遗传算法随机参数:\n种群数量\t{n_population}\n迭代次数\t{NGEN}\n交叉概率\t{CXPB}\n变异概率\t{MUTPB}")

    # 使用 multiprocessing.Pool 来加速计算
    with multiprocessing.Pool() as pool:
        toolbox.register("map", pool.map)

        # 添加进度条
        for _ in tqdm(range(NGEN), desc="遗传算法进度"):
            algorithms.eaSimple(
                population,
                toolbox,
                cxpb=CXPB,
                mutpb=MUTPB,
                ngen=1,  # 每次运行一代，以便更新进度条
                verbose=False,
            )

    # 输出结果
    best_individual = tools.selBest(population, 1)[0]
    best_combo = chess_data.iloc[best_individual]  # 获取最佳个体对应的棋子组合
    max_synergy = calculate_synergy(
        best_combo, class_dict, species_dict, class_data, species_data
    )[
        0
    ]  # 计算最佳组合的最大羁绊数

    print("-" * 80)
    print(f"最大羁绊数: {max_synergy}")  # 打印最大羁绊数
    print("-" * 80)

    best_combinations = []  # 初始化最大羁绊数组合列表
    seen_combinations = set()  # 初始化已见组合集合

    for ind in population:
        synergy, synergy_list = calculate_synergy(
            chess_data.iloc[ind], class_dict, species_dict, class_data, species_data
        )  # 计算当前个体的羁绊数
        if synergy == max_synergy:
            combination = tuple(
                sorted(chess_data.iloc[ind]["name"])
            )  # 将组合的名称排序并转化为元组
            if combination not in seen_combinations:  # 如果组合不在已见集合中
                best_combinations.append(
                    (ind, synergy_list, chess_data.iloc[ind]["price"].sum())
                )  # 添加到最佳组合列表
                seen_combinations.add(combination)  # 添加到已见组合集合

    print("所有最大羁绊数的组合:")
    print("-" * 80)
    for ind, synergy_list, cost in best_combinations:
        combo = chess_data.iloc[ind]  # 获取组合信息
        combo_str = ', '.join(
            f"{row['name']}({row['price']})" for _, row in combo.iterrows()
        )  # 生成棋子名称和价格字符串
        print(f"组合: {combo_str}")  # 打印组合名称和价格
        print(f"激活的羁绊: {', '.join(synergy_list)}")  # 打印激活的羁绊
        print(f"总费用: {cost}")  # 打印组合总费用
        print(f"棋子数量: {len(ind)}")  # 打印组合棋子数量
        print("-" * 80)

