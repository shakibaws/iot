import os
import re

# Funzione per trovare tutte le librerie importate in un file Python
def find_imports(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    # Regex per trovare le dichiarazioni di import
    imports = re.findall(r'^\s*(?:import|from)\s+(\S+)', content, re.MULTILINE)
    print(imports)
    return imports

# Directory principale
base_dir = "./"

# Insieme per mantenere tutte le librerie trovate senza duplicati
all_imports = set()

# Cammina attraverso la directory principale e tutte le sottocartelle
for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.endswith(".py"):
            file_path = os.path.join(root, file)
            imports = find_imports(file_path)
            all_imports.update(imports)

# Scrivi tutte le librerie trovate in un file di output
output_file = "libraries.txt"
with open(output_file, 'w') as file:
    for lib in sorted(all_imports):
        file.write(lib + "\n")

print(f"Librerie trovate salvate in {output_file}")
