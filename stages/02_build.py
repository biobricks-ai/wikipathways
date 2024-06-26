import os, shutil, tqdm, zipfile
from rdflib import Graph
import subprocess
from hdt import HDTDocument

# SETUP ===========================================================
base_path = os.getcwd()
download_path = os.path.join(base_path, "download", "01_download")
rdf_files_path = os.path.join(download_path, "rdf")
unzipped_files_path = os.path.join(rdf_files_path, "unzipped")
ttl_files_path = os.path.join(rdf_files_path, "ttl_files")
nt_files_path = os.path.join(rdf_files_path, "nt_files")

# BUILD BRICK ======================================================
for path in [unzipped_files_path, ttl_files_path, nt_files_path]:
    os.makedirs(path, exist_ok=True)

# Step 1: Unzip files and collect all TTL files
rdf_zip_files = [f for f in os.listdir(rdf_files_path) if f.endswith('.zip')]

for rdf_file in rdf_zip_files:
    with zipfile.ZipFile(os.path.join(rdf_files_path, rdf_file), 'r') as zip_ref:
        zip_ref.extractall(unzipped_files_path)

# Move all TTL files to ttl_files directory
for root, _, files in os.walk(unzipped_files_path):
    for file in files:
        if file.endswith('.ttl'):
            _ = shutil.move(os.path.join(root, file), os.path.join(ttl_files_path, file))

# Step 2: Convert TTL to NT
for ttl_file in tqdm.tqdm(os.listdir(ttl_files_path), desc="Converting TTL to NT"):
    if ttl_file.endswith('.ttl'):
        g = Graph()
        _ = g.parse(os.path.join(ttl_files_path, ttl_file), format='turtle')
        nt_file = ttl_file.rsplit('.', 1)[0] + '.nt'
        _ = g.serialize(os.path.join(nt_files_path, nt_file), format='nt')

# Step 3: Concatenate all NT files
big_nt_file = os.path.join(rdf_files_path, "combined.nt")
with open(big_nt_file, 'wb') as outfile:
    for nt_file in tqdm.tqdm(os.listdir(nt_files_path), desc="Concatenating NT files"):
        if nt_file.endswith('.nt'):
            with open(os.path.join(nt_files_path, nt_file), 'rb') as infile:
                _ = shutil.copyfileobj(infile, outfile)

# Step 4: Convert NT to HDT
base_uri = "http://rdf.wikipathways.org/"
hdt_file = os.path.join("./brick", "wikipathways.hdt")
os.makedirs("./brick", exist_ok=True)

# Use subprocess to run rdf2hdt command
cmd = f"rdf2hdt -i -p -B {base_uri} {big_nt_file} {hdt_file}"
subprocess.run(cmd, shell=True, check=True)

print(f"HDT file created at: {hdt_file}")

# TESTING ===========================================================

print("Testing the HDT file...")

# Load the HDT file
document = HDTDocument(hdt_file)

# Test 1: Check if the file is not empty
total_triples = document.total_triples
assert total_triples > 0, "HDT file is empty"
print(f"Total triples: {total_triples}")

# Test 2: Check if we can perform a basic search
triples, cardinality = document.search_triples("", "", "")
assert cardinality > 0, "No triples found in basic search"
print(f"Cardinality of basic search: {cardinality}")

# Test 3: Check for a specific WikiPathways predicate
wp_predicate = "http://vocabularies.wikipathways.org/wp#organism"
triples, cardinality = document.search_triples("", wp_predicate, "")
assert cardinality > 0, f"No triples found with predicate {wp_predicate}"
print(f"Triples with WikiPathways organism predicate: {cardinality}")

print("All tests passed successfully!")

# CLEAN UP ===========================================================
shutil.rmtree(unzipped_files_path)
shutil.rmtree(ttl_files_path)
shutil.rmtree(nt_files_path)
os.remove(big_nt_file)
