# 项目说明

<img src="https://github.com/Biubush/jcc_combination_selector/blob/main/static/pics/preview.png">

## 简介

这是一个应用于金铲铲之战，基于基因算法的python项目

其作用为：在用户限定条件下，计算可以激活最大羁绊数的组合有哪些

## 使用步骤

首先，下载项目，解压到文件夹，进入项目文件夹

### 环境部署

创建一个虚拟环境（推荐但不必要）

```shell
pip install virtualenv #安装virtualenv工具，如果已安装可略过
virtualenv .venv #创建虚拟环境文件夹.venv
```

激活你的虚拟环境

1. windows
```shell
.venv/Scripts/activate
```

2. linux

```bash
source .venv/bin/activate
```

安装依赖

```bash
pip install -r requirements.txt
```

### 运行脚本

```bash
python run.py
```

## 自定义参数

默认用户可输入的参数有：

- 预算限制——组合的总价上限
- 人数上限——组合的棋子数上限
- 单价下限——组合中棋子单价下限
- 单价上限——组合中棋子单价上限

> 注意，计算的结果可能为局部最优解，建议多运行几次验证是否有更好的方案

# 二次开发

此项目仅仅用于学习算法和数据处理用途，没什么实际意义，不必在此项目耗费时间。