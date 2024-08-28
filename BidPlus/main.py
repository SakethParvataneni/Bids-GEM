import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from bs4 import BeautifulSoup
import schedule
import openai

# Set your OpenAI API key

# Set up Selenium WebDriver for Edge
edge_options = Options()
edge_options.add_argument("--headless")  # Run in headless mode
edge_options.add_argument("--disable-gpu")
edge_options.add_argument("--no-sandbox")
edge_options.add_argument("--disable-dev-shm-usage")

# Provide the correct path to the Edge WebDriver
service = Service(executable_path="C:\\Users\\ADMIN\\Downloads\\edgedriver_win64\\msedgedriver.exe")

driver = webdriver.Edge(service=service, options=edge_options)

# Function to scrape tenders
def scrape_tenders():
    try:
        url = "https://bidplus.gem.gov.in/all-bids"
        print("Navigating to the page...")
        driver.get(url)
        driver.set_page_load_timeout(30)  # Wait for up to 30 seconds for the page to load
        time.sleep(5)  # Give additional time for any dynamic content to load

        print("Page loaded, extracting content...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        tenders = []
        for tender_div in soup.find_all("div", class_="border"):
            tender = {}
            tender['title'] = tender_div.find("p", class_="bidList").text.strip()
            tender['link'] = tender_div.find("a", href=True)['href']
            tenders.append(tender)
        
        print(f"Found {len(tenders)} tenders.")
        download_tenders(tenders)

    except Exception as e:
        print(f"An error occurred during scraping: {e}")

# Function to download tender documents
def download_tenders(tenders):
    download_folder = "tenders/"
    os.makedirs(download_folder, exist_ok=True)
    
    for tender in tenders:
        try:
            tender_url = f"https://bidplus.gem.gov.in{tender['link']}"
            tender_response = requests.get(tender_url)
            
            tender_file_path = os.path.join(download_folder, f"{tender['title']}.html")
            with open(tender_file_path, 'w', encoding='utf-8') as f:
                f.write(tender_response.text)
            
            print(f"Downloaded: {tender['title']}")
            summarize_and_save_tender(tender_file_path)

        except Exception as e:
            print(f"An error occurred while downloading {tender['title']}: {e}")

# Function to summarize the tender using OpenAI
def summarize_tender(tender_text):
    try:
        response = openai.Completion.create(
          engine="text-davinci-003",
          prompt=f"Summarize the following tender:\n\n{tender_text}\n\nInclude the category, qualifications needed, and PBG.",
          max_tokens=150
        )
        return response.choices[0].text.strip()

    except Exception as e:
        print(f"An error occurred during summarization: {e}")
        return "Summary could not be generated."

# Function to summarize and save the tender
def summarize_and_save_tender(tender_file_path):
    try:
        with open(tender_file_path, 'r', encoding='utf-8') as f:
            tender_text = f.read()

        summary = summarize_tender(tender_text)
        
        summary_file_path = tender_file_path.replace(".html", "_summary.txt")
        with open(summary_file_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"Summarized and saved: {summary_file_path}")

    except Exception as e:
        print(f"An error occurred while summarizing {tender_file_path}: {e}")

# Schedule the scraping to run every few hours
schedule.every(4).hours.do(scrape_tenders)

# Run the scheduled tasks
while True:
    schedule.run_pending()
    time.sleep(1)
