import pandas as pd
import json
import os


def load_json(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        return json.load(f)


def process_chess_data(chess_data):
    chess_df = pd.DataFrame(chess_data["data"]).T.reset_index(drop=True)

    # 只保留需要的列
    chess_df = chess_df[["id", "name", "price", "class", "species"]]

    # 将class和species转换为列表
    for col in ["class", "species"]:
        chess_df[col] = chess_df[col].apply(
            lambda x: [int(i) for i in str(x).split("|") if i]
        )

    # 按name去重，保留第一次出现的数据
    chess_df = chess_df.drop_duplicates(subset="name", keep="first")

    # 剔除class或species为[-1]或[]的行
    chess_df = chess_df[chess_df["class"].apply(lambda x: x != [-1] and x != [])]
    chess_df = chess_df[chess_df["species"].apply(lambda x: x != [-1] and x != [])]

    return chess_df


def process_class_species_data(data):
    df = pd.DataFrame(data["data"]).T.reset_index(drop=True)

    # 只保留需要的列
    df = df[["id", "name", "numList"]]

    # 只保留numList长度不为1的行
    df = df[df["numList"].apply(lambda x: len(str(x).split("|")) > 1)]

    # 将numList转换为列表
    df["numList"] = df["numList"].apply(lambda x: [int(i) for i in str(x).split("|")])

    return df


def process_species_data(species_data):
    species_df = pd.DataFrame(species_data["data"]).T.reset_index(drop=True)

    # 只保留level为1的行（每个特质的基本信息）
    species_df = species_df[species_df["level"] == 1]

    # 只保留需要的列并重命名
    species_df = species_df[["checkId", "name", "numList"]]
    species_df = species_df.rename(columns={"checkId": "id"})

    # 删除重复name的行，保留第一次出现的数据
    species_df = species_df.drop_duplicates(subset="name", keep="first")

    # 将numList转换为列表
    species_df["numList"] = species_df["numList"].apply(
        lambda x: [int(i) for i in str(x).split("|")]
    )
    # 只保留numList长度不为1的行
    species_df = species_df[species_df["numList"].apply(lambda x: len(x) > 1)]

    return species_df


def processAndCleanData(original_src_folder="src/original", processed_folder="src/processed"):
    print("开始处理数据...")

    # 加载数据
    original_src_folder = original_src_folder

    if not os.path.exists(original_src_folder):
        print(f"错误: 数据源文件夹 '{original_src_folder}' 不存在")
        return

    chess_data_file = os.path.join(original_src_folder, "chess.json")
    class_data_file = os.path.join(original_src_folder, "class.json")
    species_data_file = os.path.join(original_src_folder, "species.json")
    chess_data = load_json(chess_data_file)
    class_data = load_json(class_data_file)
    species_data = load_json(species_data_file)

    # 处理数据
    chess_df = process_chess_data(chess_data)
    class_df = process_class_species_data(class_data)
    species_df = process_species_data(species_data)

    # species_df中去除class_df中相同name的行
    species_df = species_df[~species_df["name"].isin(class_df["name"])]

    # 打印处理后的数据框
    print(f"\n棋子数: {len(chess_df)}\n职业数: {len(class_df)}\n种族数: {len(species_df)}")

    # 保存处理后的数据为CSV文件
    if not os.path.exists(processed_folder):
        os.makedirs(processed_folder)

    chess_processed_file = os.path.join(processed_folder, "chess_data.csv")
    chess_df.to_csv(chess_processed_file, index=False)
    class_processed_file = os.path.join(processed_folder, "class_data.csv")
    class_df.to_csv(class_processed_file, index=False)
    species_processed_file = os.path.join(processed_folder, "species_data.csv")
    species_df.to_csv(species_processed_file, index=False)

    print(f"\n数据处理成功，已保存为CSV文件，文件路径为: {processed_folder}")
    print('-' * 80)
