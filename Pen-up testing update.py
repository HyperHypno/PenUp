import requests
from bs4 import BeautifulSoup
import time
import csv
import os
from transformers import pipeline

import requests

def get_latest_version():
    url = 'https://api.github.com/repos/yourusername/yourrepo/releases/latest'
    response = requests.get(url)
    latest_release = response.json()
    return latest_release['tag_name']

def download_update(download_url, filename):
    response = requests.get(download_url)
    with open(filename, 'wb') as file:
        file.write(response.content)
    return filename

def check_for_update(current_version):
    latest_version = get_latest_version()
    if latest_version != current_version:
        return latest_version
    return None


def download_update_asset(asset_url):
    response = requests.get(asset_url)
    with open('new_version.exe', 'wb') as file:
        file.write(response.content)
    return 'new_version.exe'

def update_application():
    latest_version = check_for_update('v1.0.0')  # Current version
    if latest_version:
        download_url = f'https://github.com/yourusername/yourrepo/releases/download/{latest_version}/your_application.exe'
        download_update_asset(download_url)
        # Optionally, replace the current executable


# Function to search DuckDuckGo
def search_duckduckgo(query, count=10):
    search_url = f"https://duckduckgo.com/html/?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    for a in soup.find_all('a', class_='result__a', href=True)[:count]:
        results.append(a['href'])
    return results

# Function to fetch the content of a page
def fetch_page_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    response = requests.get(url, headers=headers)
    return response.text

# Function to extract information from the HTML content
def extract_information(html_content):
    soup = BeautifulSoup(html_content, "html.parser")

    # Try to focus on the main content, avoiding sidebars and ads
    main_content = soup.find('article')  # Adjust based on the website structure
    if not main_content:
        main_content = soup.find('main')
    if not main_content:
        main_content = soup.find('body')  # Fallback to the entire body

    paragraphs = [p.get_text() for p in main_content.find_all('p')]
    return ' '.join(paragraphs)


# Function to save or update the feedback in the CSV
def update_feedback_csv(url, feedback):
    csv_file = 'feedback.csv'
    exists = os.path.isfile(csv_file)
    with open(csv_file, mode='a' if exists else 'w', newline='') as file:
        writer = csv.writer(file)
        if not exists:
            writer.writerow(['url', 'score'])  # Write header
        rows = []
        if exists:
            with open(csv_file, mode='r', newline='') as read_file:
                reader = csv.reader(read_file)
                rows = list(reader)
                for row in rows:
                    if row[0] == url:
                        row[1] = int(row[1]) + feedback
                        break
                else:
                    writer.writerow([url, feedback])
        else:
            writer.writerow([url, feedback])
        if rows:
            with open(csv_file, mode='w', newline='') as write_file:
                writer = csv.writer(write_file)
                writer.writerows(rows)

# Function to retrieve feedback from the CSV
def get_feedback():
    feedback = {}
    csv_file = 'feedback.csv'
    if os.path.exists(csv_file):
        with open(csv_file, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                feedback[row['url']] = int(row['score'])
    return feedback

# Main function to manage the search and feedback loop
def main():
    keywords = input("Enter the topic: ")
    search_time = int(input("Enter the duration for search in minutes: "))
    search_time *= 60
    feedback = get_feedback()

    start_time = time.time()

    while time.time() - start_time < search_time:
        urls = search_duckduckgo(keywords)
        for url in urls:
            if time.time() - start_time >= search_time:
                break

            score = feedback.get(url, 0)
            html_content = fetch_page_content(url)
            text = extract_information(html_content)

            
            summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
            summary = summarizer(text, max_length=150, min_length=30, do_sample=False)[0]['summary_text']
            
            

            print(f"Source: {url}")
            print("Summary:", summary)

            user_input = input("Do you like this source? (y/n): ").strip().lower()
            if user_input == 'y':
                update_feedback_csv(url, 1)
            elif user_input == 'n':
                update_feedback_csv(url, -1)

if __name__ == "__main__":
    main()
