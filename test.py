# 定义选项列表
options = [
    "A",
    "B",
    "C",
    "D",
    "AB",
    "AC",
    "AD",
    "BC",
    "BD",
    "CD",
    "ABC",
    "ABD",
    "ACD",
    "BCD",
    "ABCD",
]

for option in options:
    # 使用列表推导式将当前选项转化为 mark 数组
    stuAnswer = [{"mark": char} for char in option]
    print(stuAnswer)
