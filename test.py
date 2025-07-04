with open("dataset.txt", "r") as f:
    lines = f.readlines()

with open("dataset.txt", "w") as f:
    for line in lines:
        if line.strip():
            f.write(line)