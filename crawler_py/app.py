import functools
from bs4 import BeautifulSoup
import os
import logging
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from datetime import date, datetime, timedelta
from flask import Flask
from flask import jsonify
import pickle5 as pickle
import asyncio
import progressbar
import requests
import re
import time
import ssl
import pandas as pd
import sys
from dotenv import load_dotenv
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import multiprocessing as mp
import concurrent.futures as ft
load_dotenv(verbose=True)
ssl._create_default_https_context = ssl._create_unverified_context
logging.basicConfig(
        level=logging.INFO,
        format='%(threadName)10s %(name)18s: %(message)s',
        stream=sys.stderr,
    )


app = Flask(__name__, instance_relative_config=True)
app.debug = True
#app.logger.info(os.environ)
app.logger.info(os.environ.get("SEARCH_WORDS"))
class ProgressBar_:
    def __init__(self, max_value):
        self.bar = progressbar.ProgressBar(max_value=max_value)
        self.bar.start()
        self.count = 0
    def update_bar(self):
        self.count += 1
        self.bar.update(self.count)
        time.sleep(0.01)
    def finish_bar(self):
        self.bar.finish()

class Crawler :
    def __init__(self):
        self.login_glassdoor = {
            "login" : os.environ.get("LOGIN_GLASSDOOR"),
            "password": os.environ.get("PASSWORD_GLASSDOOR")
        }
        self.chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
        self.search_words = [word.lstrip() for word in os.environ.get("SEARCH_WORDS").split(",")]
        self.main_word = os.environ.get("MAIN_WORDS")
        self.offers = []
        self.links = []
        self.connexion = MongoClient(os.environ.get("MONGO_ALIAS"), int(os.environ.get("MONGO_PORT")))
        self.db = self.connexion[os.environ.get("MONGO_DB")]
        self.offers_db = self.db[os.environ.get("MONGO_COLECTION")]
        self.project_path = os.environ.get("PROJECT_PATH")
        self.options = Options()
        self.options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2866.71 Safari/537.36')
        self.options.add_argument("--disable-infobars")
        self.options.add_argument('--headless')
        self.options.add_argument("--disable-notifications")
        self.options.add_argument("--disable-infobars")
        self.options.add_argument('--window-size=1920,1080')
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--verbose")
        self.options.add_argument('--disable-gpu')
        self.options.add_argument("--whitelisted-ips=''")
        self.browser = ''
        self.options.add_experimental_option("prefs", { \
            "profile.default_content_setting_values.media_stream_mic": 1, 
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.geolocation": 1, 
            "profile.default_content_setting_values.notifications": 1 
        })
        PROJECT_ROOT = os.path.abspath(os.path.dirname(self.project_path))
        self.DRIVER_BIN = os.path.join(PROJECT_ROOT, self.chromedriver_path)
        self.delay = 2
        app.logger.info("- SETUP -")
        self.keyword = ""
    def is_alive(self):
        try:
            self.browser.execute(Command.STATUS)
            return True
        except:
            #TO FIX
            return True
    def save_cookie(self):
        with open(self.project_path+"chrome_profile/cookies", 'wb') as filehandler:
            pickle.dump(self.browser.get_cookies(), filehandler)

    def load_cookie(self):
        with open(self.project_path+"chrome_profile/cookies", 'rb') as cookiesfile:
            cookies = pickle.load(cookiesfile)
            for cookie in cookies:
                self.browser.add_cookie(cookie)    
    
    def waiter(self, selectorType, selector, isAllElements, isInFunc=None):
        attempt = 1
        max_attempts = 3
        self.browser.implicitly_wait(self.delay/2)
        while True:
            try:
                if isAllElements is True:
                    return WebDriverWait(self.browser, self.delay).until(EC.visibility_of_all_elements_located((selectorType, selector)))
                else:
                    elements = [
                         WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((selectorType, selector))),
                         WebDriverWait(self.browser, self.delay).until(EC.visibility_of_element_located((selectorType, selector)))
                    ]
                    return elements[1]
            except :
                if attempt == max_attempts:
                    if self.is_alive():
                        self.browser.quit()
                    raise
                    if isInFunc is not None:
                        self.browser.refresh()
                        isInFunc()
                    else:
                        app.logger.info("error", selector)
                        raise
                attempt += 1

    def generate_links(self):
        glass_link = []
        for keyword in self.search_words :
            keyword_glass = keyword.replace(" ", "-")
            keyword = keyword.replace(" ", "+")
            #last 24 hours
            self.links.append(f"https://fr.indeed.com/emplois?q={keyword}&l=Paris+(75)&rbl=Paris+(75)&jlid=38ec804400892bb8&jt=permanent&sort=date&fromage=1")
            #last 3 days
            self.links.append(f"https://fr.indeed.com/emplois?q={keyword}&l=Paris+(75)&rbl=Paris+(75)&jlid=38ec804400892bb8&jt=permanent&sort=date&fromage=3")
            self.links.append(f"https://www.welcometothejungle.com/fr/jobs?refinementList%5Bcontract_type_names.fr%5D%5B0%5D=CDI&page=1&query={keyword}&aroundQuery=Paris%2C%20France&aroundLatLng=48.85718%2C2.34141&aroundRadius=20000&sortBy=mostRecent")
            self.links.append(f"https://www.linkedin.com/jobs/search/?currentJobId=3239533589&f_E=2&f_PP=101240143&geoId=105015875&keywords={keyword}&location=France&sortBy=DD")
            glass_link.append(f"https://www.glassdoor.fr/ {keyword}")
        self.links.sort()
        self.links = self.links + glass_link
        
    def add_offers(self, date, title, link, company):
        offer = {
            "date": date,
            "title": title,
            "link": link,
            "company": company,
            "read": False,
            "is_fav": False
        }
        app.logger.info(title)
        self.update_or_insert_mongo(offer)
        if offer not in self.offers:
            self.offers.append(offer)
            
    def log_glassdoor(self):
        self.waiter(By.XPATH, '/html/body/div[7]/div[3]/div/div/div[2]/div/button[2]', False, self.log_glassdoor).click()
        self.waiter(By.XPATH, '//div[@class="locked-home-sign-in"]', False, self.log_glassdoor).click()
        
        self.waiter(By.XPATH, '//input[@id="userEmail"]', False, self.log_glassdoor).clear()
        self.waiter(By.XPATH, '//input[@id="userEmail"]', False, self.log_glassdoor).send_keys(self.login_glassdoor["login"])
        self.waiter(By.XPATH, '//input[@id="userPassword"]', False, self.log_glassdoor).clear()
        self.waiter(By.XPATH, '//input[@id="userPassword"]', False, self.log_glassdoor).send_keys(self.login_glassdoor["password"])
        self.waiter(By.XPATH, '//button[@name="submit"]', False, self.log_glassdoor).click()
        self.save_cookie()
    
    def search_glassdoor(self):
        self.waiter(By.XPATH, '//*[@id="sc.keyword"]', False, self.search_glassdoor).clear()
        self.waiter(By.XPATH, '//*[@id="sc.keyword"]', False, self.search_glassdoor).send_keys(self.keyword)
        webdriver.ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()
        self.waiter(By.XPATH, '//*[@id="sc.location"]', False, self.search_glassdoor).clear()
        self.waiter(By.XPATH, '//*[@id="sc.location"]', False, self.search_glassdoor).send_keys("Paris, 75 (France)")
        webdriver.ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()
        self.waiter(By.XPATH, '//button[@data-test="search-bar-submit"]', False, self.search_glassdoor).click()
        self.browser.implicitly_wait(self.delay)
    
    def filter_glassdoor(self):
        webdriver.ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()
        self.waiter(By.XPATH, '//*[@id="filter_jobType"]', False, self.filter_glassdoor).click()
        self.browser.implicitly_wait(self.delay)
        self.waiter(By.XPATH, '//li[@value="internship"]', False, self.filter_glassdoor).click()
        webdriver.ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()
        self.waiter(By.XPATH, '//*[@id="filter_fromAge"]', False, self.filter_glassdoor).click()
        self.browser.implicitly_wait(self.delay)
        self.waiter(By.XPATH, '//li[@value="3"]', False, self.filter_glassdoor).click()
        webdriver.ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()
    
    def update_or_insert_mongo(self, offer):
        app.logger.info("- UPDATE MONGO DB -")
        if "_id" in offer:
            del offer["_id"]
        if self.offers_db.count_documents({'title': offer["title"], "company": offer["company"]}) > 0:
            if "read" in offer:
                del offer["read"]
            if "is_fav" in offer:
                del offer["is_fav"]
            update = self.offers_db.update_one({"title": offer["title"], "company": offer["company"]}, {"$set": offer})
            app.logger.info(update)
        else:
            insert = self.offers_db.insert_one(offer)
            app.logger.info(insert)
    async def start(self, loop):
        app.logger.info('starting')
        self.generate_links()
        app.logger.info(__name__)
        if __name__ == 'app':
            app.logger.info('creating executor tasks')
            with ft.ThreadPoolExecutor(max_workers=5) as pool:
                result_futures = list(map(lambda x: pool.submit(self.start_crawling, x), self.links))
                app.logger.info(str(len(result_futures)))
                for future in ft.as_completed(result_futures):
                    try:
                        return future.result() 
                    except Exception as e:
                        app.logger.error('e is', e, type(e))
            app.logger.info('waiting for executor tasks')
            app.logger.info('exiting')
        
    def start_crawling(self, link_or):
        app.logger.info(link_or)
        app.logger.info(f"http://{os.environ.get('NODE_IP')}:4444/wd/hub")
        app.logger.info(link_or)
        try:
            self.browser = webdriver.Remote(
                command_executor=f"http://{os.environ.get('SELENIUM_ALIAS')}:4444/wd/hub",
                desired_capabilities=DesiredCapabilities.CHROME,
                options=self.options,
            )
            self.browser.maximize_window()
            app.logger.info(str(self.links.index(link_or)+1) + " / " + str(len(self.links)))
            link = link_or.split(" ")[0]
            if "glassdoor" not in link:
                self.browser.get(link)
            else :
                self.browser.get(link.split(" ")[0])
                self.log_glassdoor()
            webdriver.ActionChains(self.browser).send_keys(Keys.ESCAPE).perform()
            htmlSource = self.browser.page_source
            
            if "indeed" in link:
                soup = BeautifulSoup(htmlSource, 'html.parser')
                app.logger.info("--- INDEED ---")
                cards = soup.find_all("div", class_="jobsearch-SerpJobCard")
                for card in cards :
                    date = card.find("span", class_="date").get_text().strip()
                    if "plus de" not in date:
                        if "aujourd'hui" in date.lower() or "publiée à l'instant" in date.lower():
                            date_dt = datetime.now()
                        else :
                            number = int(re.findall(r'\d+', date)[0])
                            if "jours" in date.lower():
                                date_dt = datetime.today() - timedelta(days=number)

                        head = card.find("h2", class_="title")
                        title = head.find("a").get_text().strip()
                        if self.main_word in title.lower():
                            date = date_dt.strftime("%d/%m/%Y")
                            link = f"https://fr.indeed.com{head.find('a').get('href')}"
                            company = card.find("span", class_="company").get_text().strip()
                            self.add_offers(date, title, link, company)

            if "welcometothejungle" in link:
                soup = BeautifulSoup(htmlSource, 'html.parser')
                app.logger.info("--- WELCOME TO THE JUNGLE ---")
                cards = soup.find_all("article", {"data-role": "jobs:thumb"})
                for card in cards:
                    head = card.find("header")
                    a_el = head.find("a")
                    title = a_el.find("h3").get_text().strip()
                    if self.main_word in title.lower():
                        date = pd.to_datetime(head.find("time")["datetime"]).strftime("%d/%m/%Y")
                        link = f"https://www.welcometothejungle.com{a_el.get('href')}"
                        company = head.find("h4").get_text().strip()
                        self.add_offers(date, title, link, company)

            if "linkedin" in link:
                self.browser.implicitly_wait(self.delay/2)
                self.browser.execute_script("document.querySelector('.jobs-search__results-list').scrollTo(0, document.querySelector('.jobs-search__results-list').scrollHeight)")
                htmlSource = self.browser.page_source
                soup = BeautifulSoup(htmlSource, 'html.parser')
                app.logger.info("--- LINKEDIN ---")
                cards = soup.find_all("li", class_="job-result-card")
                for i, card in enumerate(cards):
                    title = card.find("h3", class_="job-result-card__title").get_text().strip()
                    if self.main_word in title.lower():               
                        date = pd.to_datetime(card.find("time")["datetime"]).strftime("%d/%m/%Y")
                        link = card.find("a", class_= "result-card__full-card-link").get('href')
                        company = card.find("a", href=lambda href: href and "company" in href).get_text().strip()
                        self.add_offers(date, title, link, company)
            if "glassdoor" in link:
                keyword = link_or.split(" ")[1]
                keyword = keyword.replace("+", " ")
                app.logger.info("--- GLASSDOOR ---", keyword)
                self.keyword = keyword
                
                self.search_glassdoor()
                blank_item = self.waiter(By.XPATH, '//*[@id="MainCol"]/div[1]/div[1]/div/div/h1', False)
                blank_item.click()
                self.search_glassdoor()
                self.filter_glassdoor()

                htmlSource = self.browser.page_source
                soup = BeautifulSoup(htmlSource, 'html.parser')
                cards = soup.find_all("li", class_="react-job-listing")
                for i, card in enumerate(cards):
                    if card.find("a"):
                        header = card.find_all("span", attrs={'class': None})
                        title = header[1].get_text().strip()
                        if self.main_word in title.lower():
                            raw_date = card.find('div', attrs={'data-test': "job-age"}).get_text().strip().split(" ")
                            if len(raw_date) > 1:
                                date_dt = datetime.today() - timedelta(days=int(raw_date[0]))
                            else :
                                hour = re.compile("(\d+)").match(raw_date[0]).group(1)
                                if int(hour) == 24:
                                    date_dt = datetime.today() - timedelta(days=1)
                                else:
                                    date_dt = datetime.now()
                            date = date_dt.strftime("%d/%m/%Y")
                            link = f"https://www.glassdoor.fr{card.find('a').get('href')}"
                            company = header[0].get_text().strip()
                            self.add_offers(date, title, link, company)
        except Exception as e:
            app.logger.error(e)
            app.logger.error(self.browser)
            if self.is_alive():
                self.browser.quit()
        finally:
            app.logger.info("--END--")
            self.offers.sort(key=lambda x: datetime.strptime(x["date"], '%d/%m/%Y'), reverse=True)
            app.logger.info("--QUIT--")
            if self.is_alive():
                self.browser.quit()
            
            return self.offers


async def crawler(loop):
    crawler = Crawler()
    offers = await crawler.start(loop)
    return offers


@app.route('/', methods=['GET'])
def index():
    crawler = Crawler()
    loop = asyncio.new_event_loop()

    offers = loop.run_until_complete(crawler.start(loop))
    if offers:
        if len(offers) > 0:
            offers = [offer["title"] for offer in offers]
    return jsonify({"response": "DONE !", "offers": offers})


if __name__ == '__main__':
    app.run(debug=True)
