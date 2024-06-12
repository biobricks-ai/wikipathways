import os, shutil
import zipfile
from rdflib import Graph
from rdflib_hdt import HDTDocument

# Define the path to the RDF files
rdf_files_path = os.path.join(os.getcwd(), "download", "01_download", "rdf")
unzipped_files_path = os.path.join(rdf_files_path, "unzipped")
os.makedirs(unzipped_files_path, exist_ok=True)

# Get the list of .zip files in the rdf directory
rdf_zip_files = [f for f in os.listdir(rdf_files_path) if f.endswith('.zip')]
rdf_zip_files = [os.path.join(rdf_files_path, f) for f in rdf_zip_files]

# Unzip RDF files
for rdf_file in rdf_zip_files:
  with zipfile.ZipFile(rdf_file, 'r') as zip_ref:
        zip_ref.extractall(unzipped_files_path)

# Initialize a combined graph for HDT
combined_graph = Graph()

root, dirs, files = next(os.walk(unzipped_files_path))
for root, dirs, files in os.walk(unzipped_files_path):
    file = 'download/01_download/rdf/wikipathways-rdf-void.ttl'
    for file in files:
        if file.endswith('.ttl') or file.endswith('.rdf'):
            file_path = os.path.join(root, file)
            g = Graph()
            g.parse(file_path, format='ttl' if file.endswith('.ttl') else 'xml')
            combined_graph += g

# Serialize combined graph to a temporary Turtle file
tmp_ttl_file = os.path.join(unzipped_files_path, "combined_graph.ttl")
combined_graph.serialize(destination=tmp_ttl_file, format='turtle')

# Create HDT file
hdt_file_path = os.path.join(unzipped_files_path, "wikipathways.hdt")
HDTDocument.generate_from_rdf(tmp_ttl_file, hdt_file_path, base_uri="http://example.org/base#")

print(f"HDT file created at: {hdt_file_path}")

# Clean up temporary Turtle file
os.remove(tmp_ttl_file)

# Create HDT file
hdt_file_path = os.path.join(rdf_files_path, "wikipathways.hdt")
combined_graph.serialize(destination=hdt_file_path, format='hdt')

print(f"HDT file created at: {hdt_file_path}")