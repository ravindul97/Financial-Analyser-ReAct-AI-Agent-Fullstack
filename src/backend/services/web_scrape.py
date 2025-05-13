from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os
import re
import requests
import logging

async def web_scrape(url):
    #Set up headless Chrome inside the function
    chrome_options = Options()
    chrome_options.add_argument("--headless")

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)

    try:
        #Extract company symbol from URL
        match = re.search(r"symbol=([A-Z]+)\.N0000", url)
        if match:
            exact_company = match.group(1)
            logging.info(f"exact_company: {exact_company}")
        else:
            exact_company = "UNKNOWN"

        #Load the web page
        driver.get(url)

        #Wait until Financials tab load
        wait.until(EC.presence_of_element_located((By.ID, "21b")))

        #Wait until at least one report row is present
        wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, '//*[@id="21b"]/div/div/div/table/tbody/tr')
        ))

        #Find the first 12 PDF links from the financials section
        pdf_links = []
        #Check more rows just in case
        for i in range(1, 15):
            try:
                xpath = f'//*[@id="21b"]/div/div/div/table/tbody/tr[{i}]/td[2]/div/div[2]/a[1]'
                link_element = driver.find_element(By.XPATH, xpath)
                href = link_element.get_attribute("href")
                if href and href.endswith(".pdf"):
                    pdf_links.append(href)
                if len(pdf_links) == 12:
                    break
            except:
                continue

        #Create output directory
        if exact_company in ['REXP', 'DIPD']:
            output_dir = os.path.join("data", "unprocess_data", exact_company)
        else:
            output_dir = os.path.join("data", "unprocess_data")

        os.makedirs(output_dir, exist_ok=True)

        #Download and save PDFs
        logging.info("Found PDF links:")
        for i, pdf_url in enumerate(pdf_links, start=1):
            logging.info(f"[{i}] {pdf_url}")
            response = requests.get(pdf_url)
            filename = os.path.join(output_dir, f"financial_report_{exact_company}_{i}.pdf")
            with open(filename, "wb") as f:
                f.write(response.content)
            logging.info(f"Saved: {filename}")

        return f"Web scrape completed for {exact_company}."

    except Exception as e:
        logging.error(f"Error occured in web scraping: {e}")
        return f"Error occured in web scraping: {str(e)}"

    finally:
        #Clean up the browser
        driver.quit()
