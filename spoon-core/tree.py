import os

def generate_tree(path, prefix="", file=None):
    files = os.listdir(path)
    files.sort()
    for i, name in enumerate(files):
        connector = "└── " if i == len(files)-1 else "├── "
        line = prefix + connector + name + "\n"
        file.write(line)
        if os.path.isdir(os.path.join(path, name)):
            extension = "    " if i == len(files)-1 else "│   "
            generate_tree(os.path.join(path, name), prefix + extension, file)

with open("structure.txt", "w", encoding="utf-8") as f:
    generate_tree(r"C:\Users\doug\Trae Projects\NeoX\spoon-core\spoon-env\Lib\site-packages\spoon_toolkits", file=f)
