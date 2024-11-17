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

print([[{"mark": char} for char in option] for option in options])
