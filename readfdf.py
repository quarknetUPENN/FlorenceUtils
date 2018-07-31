from l1a import L1a

with open("save.fdf", "r") as fdf:
    exec("data = " + fdf.readline())
print(data)
