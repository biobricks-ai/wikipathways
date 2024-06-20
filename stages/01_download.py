import os, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Define the base URL
base_url = "https://data.wikipathways.org/current/"

# Create the download directory
download_path = os.path.join(os.getcwd(), "download", "01_download")
os.makedirs(download_path, exist_ok=True)

# Step 1: Download the main HTML page
main_page = requests.get(base_url)
main_html_path = os.path.join(download_path, "status.html")
with open(main_html_path, 'w', encoding='utf-8') as file:
    file.write(main_page.text)

# Parse the main HTML page
soup = BeautifulSoup(main_page.content, 'html.parser')

# Step 2: Go to each subdirectory link in the table
table = soup.find('table')
subdirectory_links = [a['href'] for a in table.find_all('a', href=True)]

# Function to download files from a subdirectory
def download_files_from_subdirectory(subdirectory_url, local_subdirectory_path):
    response = requests.get(subdirectory_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table')
    files = [a['href'] for a in table.find_all('a', href=True) if not a['href'].endswith('/')]
    
    os.makedirs(local_subdirectory_path, exist_ok=True)
    for file in files:
        file_url = f"{subdirectory_url}/{file}"
        local_file_path = os.path.join(local_subdirectory_path, file)
        print(f"Downloading {file_url} to {local_file_path}")
        with requests.get(file_url, stream=True) as r:
            r.raise_for_status()
            with open(local_file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    _ = f.write(chunk)

# Step 3: Download each file in the subdirectories
for link in subdirectory_links:
    subdirectory_url = urljoin(base_url, link)
    local_subdirectory_path = os.path.join(download_path, link.strip('/'))
    download_files_from_subdirectory(subdirectory_url, local_subdirectory_path)

print("Download done.")
