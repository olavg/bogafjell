from waybackpy import WaybackMachineAvailabilityAPI
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse
import re

def is_valid_url(url, base_domain, snapshot_timestamp):
    return base_domain in url and snapshot_timestamp in url

def adjust_links(soup, base_domain):
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        parsed_href = urlparse(href)
        if parsed_href.netloc and base_domain not in parsed_href.netloc:
            continue
        a_tag['href'] = re.sub(r'^/web/\d+/', '/', href)

    for tag in soup.find_all(['img', 'script', 'link'], src=True):
        src = tag['src']
        parsed_src = urlparse(src)
        if parsed_src.netloc and base_domain not in parsed_src.netloc:
            continue
        tag['src'] = re.sub(r'^/web/\d+/', '/', src)

    return soup

def download_file(url, base_folder):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            original_url = url.split('/http:/')[-1].split('/https:/')[-1]
            path = urlparse('http://' + original_url).path
            path_parts = path.split('/')
            filename = path_parts.pop() if path_parts[-1] else 'index.html'

            filename = re.sub(r'\.php$', '.html', filename)
            if '.' not in filename:
                filename += '.html'

            subfolder_path = os.path.join(base_folder, *path_parts)
            os.makedirs(subfolder_path, exist_ok=True)
            file_path = os.path.join(subfolder_path, filename)

            encoding = response.apparent_encoding if response.apparent_encoding else 'utf-8'
            content = response.content.decode(encoding, 'ignore')
            with open(file_path, 'w', encoding=encoding) as file:
                file.write(content)
            return file_path
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return None

def crawl_page(url, base_domain, folder, visited, snapshot_timestamp):
    if url in visited:
        return

    print(f"Crawling: {url}")
    visited.add(url)
    page_content = download_file(url, folder)

    if not page_content:
        return

    try:
        with open(page_content, 'rb') as file:
            content = file.read()
            soup = BeautifulSoup(content, 'html.parser', from_encoding='utf-8')
            soup = adjust_links(soup, base_domain)

            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                joined_url = urljoin(url, href)
                if is_valid_url(joined_url, base_domain, snapshot_timestamp) and joined_url not in visited:
                    crawl_page(joined_url, base_domain, folder, visited, snapshot_timestamp)
    except Exception as e:
        print(f"Error processing {page_content}: {e}")

def download_site(archive_url, folder):
    visited_urls = set()
    snapshot_timestamp = archive_url.split('/')[4]  # Extract timestamp from the archive URL
    crawl_page(archive_url, "bogafjell.net", folder, visited_urls, snapshot_timestamp)

archive_url = "https://web.archive.org/web/20040128221425/http://www.bogafjell.net/"
download_folder = "bogafjell_net_archive"

download_site(archive_url, download_folder)
