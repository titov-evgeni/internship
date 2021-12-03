"""
Get data from the site www.reddit.com on posts
in the 'Top' -> 'This Month' category.
Add data into data base
"""
import sys
import os.path
import glob
import uuid
import logging
import requests
import bs4
import json
import time
import datetime
import multiprocessing
import argparse

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from db_connectors.mongo import MongodbService

logging.basicConfig(handlers=[logging.FileHandler(filename='app.log',
                                                  mode='w', encoding='utf-8')],
                    level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

parser = argparse.ArgumentParser(description='Posts data from reddit '
                                             'to txt file')
parser.add_argument('--posts_number', type=int,
                    default=10,
                    help='Required number of posts')
parser.add_argument('--file_name', type=str,
                    default=datetime.datetime.now().strftime('%Y%m%d%H%M'),
                    help='Name of the output file')
args = parser.parse_args()

COUNT_POSTS = args.posts_number
MAX_WAIT = 15
GOOD_SCROLL_COUNT = 20
USER_AGENT = ("Mozilla/5.0 (Windows NT 6.3; Win64; x64)"
              "AppleWebKit/537.36 (KHTML, like Gecko)"
              "Chrome/92.0.4515.159 Safari/537.36")


def search_and_del_file_in_current_directory(search_mask: str):
    """Find file by mask and delete it"""
    file_list = glob.glob(search_mask)
    if file_list:
        for file_name in file_list:
            os.remove(file_name)


def get_data_from_post_and_user_page(url: str):
    """Get data from page and return file with data"""
    post_url = url
    unique_id = uuid.uuid1().hex

    soup = make_request_beautifulsoup(url)

    try:
        data_from_json = get_data_from_response(soup)
        user_id = list(data_from_json["posts"]["models"].keys())[0]
        user_name = str(data_from_json["posts"]["models"]
                        [f'{user_id}']['author'])
        number_of_votes = str(data_from_json["posts"]["models"]
                              [f'{user_id}']['score'])
        number_of_comments = str(data_from_json["posts"]["models"]
                                 [f'{user_id}']['numComments'])

        # post creation date from json comes as 1634227843000
        unix_post_date = str(data_from_json["posts"]["models"]
                             [f'{user_id}']['created'])[:-3]
        post_date = convert_unix_time(int(unix_post_date))

        user_link = "https://www.reddit.com/user/" + f"{user_name}"

        post_category = soup.find("span",
                                  class_="_19bCWnxeTjqzBElWZfIlJb"
                                  ).text.split("/")[1]

        soup = make_request_beautifulsoup(user_link)

        data_from_json = get_data_from_response(soup)
        user_id = list(data_from_json["profiles"]["about"].keys())[0]
        user_karma = str(data_from_json["profiles"]["about"]
                         [f'{user_id}']['karma']['total'])
        post_karma = str(data_from_json["profiles"]["about"]
                         [f'{user_id}']['karma']['fromPosts'])
        comment_karma = str(data_from_json["profiles"]["about"]
                            [f'{user_id}']['karma']['fromComments'])
        unix_user_cake_day = str(data_from_json["subreddits"]["about"]
                                 [f'{user_id}']['created'])
        user_cake_day = convert_unix_time(int(unix_user_cake_day))

        all_data = {"_id": unique_id,
                    "post_url": post_url,
                    "user_name": user_name,
                    "user_karma": user_karma,
                    "user_cake_day": user_cake_day,
                    "post_karma": post_karma,
                    "comment_karma": comment_karma,
                    "post_date": post_date,
                    "number_of_comments": number_of_comments,
                    "number_of_votes": number_of_votes,
                    "post_category": post_category
                    }
        return all_data
    except Exception as ex:
        logging.error(ex)
        all_data = []
        return all_data


def make_request_selenium(url: str):
    """Make GET request and return object: WebDriver

    Make GET request by link using 'Сhrome'.
    Return object: 'selenium.webdriver.chrome.webdriver.WebDriver'
    """
    try:
        options = webdriver.ChromeOptions()
        options.add_argument(f"user-agent={USER_AGENT}")

        # Disable webdriver mode
        # for ChromeDriver version 79.0.3945.16 or over
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Headless mode
        options.add_argument("--headless")

        # Output only fatal error in console
        options.add_argument("--log-level=3")
        driver = webdriver.Chrome(options=options)
        driver.get(url=url)
        try:
            # Waits for element "body" for MAX_WAIT
            # script stops if element is not found
            WebDriverWait(driver, MAX_WAIT).until(
                ec.presence_of_element_located((By.TAG_NAME, "body")))
            return driver
        except (AssertionError, WebDriverException):
            driver.close()
            driver.quit()
            raise Exception
    except Exception as ex:
        logging.error(ex)
        sys.exit()


def make_scroll_on_page(driver: WebDriver, scrolls: int):
    """Make scroll on page

    Find element 'body' on page and make scroll.
    Script stops if element is not found
    """
    try:
        element = driver.find_element(By.TAG_NAME, "body")

        for scroll in range(1, scrolls):
            element.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.5)
    except Exception as ex:
        logging.error(ex)
        driver.close()
        driver.quit()
        sys.exit()


def make_request_beautifulsoup(url: str):
    """Make GET request and return processed HTML

    Make GET request by link using 'BeautifulSoup'.
    Write page HTML in file, read file.
    Return page HTML processed with library "lxml"
    """
    try:
        headers = {"User-Agent": f"{USER_AGENT}"}
        req = requests.get(url, headers=headers, timeout=MAX_WAIT)
        src = req.text
        soup = BeautifulSoup(src, "lxml")
        return soup
    except Exception as ex:
        logging.error(ex)


def search_post_href_in_page_html(driver: WebDriver):
    """Find posts links and return list of them

    Process HTML from 'selenium' with library 'lxml'
    Find all elements 'a' by 'class name' and get attribute 'href' from them.
    Add post_url in list.
    Return posts urls list
    Script stops if list is empty
    """
    try:
        soup = BeautifulSoup(driver.page_source, "lxml")
        all_post_href = soup.find_all("a",
                                      class_=("SQnoC3ObvgnGjWt90zD9Z "
                                              "_2INHSNB8V5eaWp4P0rY_mE"))
        posts_urls = []
        for item in all_post_href:
            post_url = "https://www.reddit.com" + item.get("href")
            posts_urls.append(post_url)

        if posts_urls:
            return posts_urls
        else:
            raise Exception
    except Exception as ex:
        logging.error(ex)
        driver.close()
        driver.quit()
        sys.exit()


def get_post_urls_from_main_page(driver: WebDriver, scroll_number: int):
    """Get data from page and return posts links"""
    make_scroll_on_page(driver, scroll_number)
    posts_urls = search_post_href_in_page_html(driver)
    return posts_urls


def get_data_from_response(soup: bs4.BeautifulSoup):
    """Get 'JSON' from HTML and return 'dict' data"""
    get_json_from_response = soup.find(
        "script", id="data").text[:-1].split('= ', maxsplit=1)[1]
    data_from_json = json.loads(get_json_from_response)
    return data_from_json


def convert_unix_time(unix_post_date: int):
    """Convert unix time and return readable date"""
    post_date = datetime.datetime.utcfromtimestamp(
        unix_post_date).strftime('%Y-%m-%d')
    return post_date


if __name__ == '__main__':
    try:
        db_name = 'posts_data'
        connector = MongodbService("localhost", 27017)
        connector.drop_db(db_name)
    except Exception as server_ex:
        logging.error(server_ex)
        sys.exit()
    site_url = "https://www.reddit.com/top/?t=month"
    count_records = 0
    posts_urls_done = []
    scroll_count = COUNT_POSTS if COUNT_POSTS <= 25 else GOOD_SCROLL_COUNT

    search_and_del_file_in_current_directory('reddit*')
    selenium_driver = make_request_selenium(site_url)
    all_posts_urls = get_post_urls_from_main_page(selenium_driver,
                                                  scroll_count)

    while count_records < COUNT_POSTS:
        with multiprocessing.Pool(multiprocessing.cpu_count()) as process:
            all_posts_data = process.map(get_data_from_post_and_user_page,
                                         all_posts_urls)

            for post_data in all_posts_data:
                if post_data:
                    posts_urls_done.append(post_data["post_url"])
                    json_data = json.dumps(post_data, indent=4,
                                           ensure_ascii=False).encode('utf8')
                    try:
                        re = requests.post("http://localhost:8087/posts/",
                                           data=json_data)
                        count_records += 1
                    except Exception as server_ex:
                        logging.error(server_ex)
                        selenium_driver.close()
                        selenium_driver.quit()
                        sys.exit()

                if count_records == COUNT_POSTS:
                    selenium_driver.close()
                    selenium_driver.quit()
                    sys.exit()

            next_posts_urls = get_post_urls_from_main_page(selenium_driver,
                                                           scroll_count)

            # Select urls for which there was no request
            new_posts_urls = [x for x in next_posts_urls
                              if x not in posts_urls_done]

            all_posts_urls = new_posts_urls
