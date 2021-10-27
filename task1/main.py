"""
Get data from the site www.reddit.com on posts
in the 'Top' -> 'This Month' category.
Add data into text file named reddit-YYYYMMDDHHMM.txt
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

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')

COUNT_POSTS = 100
MAX_WAIT = 15
USER_AGENT = ("Mozilla/5.0 (Windows NT 6.3; Win64; x64)"
              "AppleWebKit/537.36 (KHTML, like Gecko)"
              "Chrome/92.0.4515.159 Safari/537.36")


def search_and_del_file(search_mask: str):
    """Find file by mask and delete it"""
    file_list = glob.glob(search_mask)
    if file_list:
        for file_name in file_list:
            os.remove(file_name)


def make_request_selenium(url: str):
    """Make GET request and return object: WebDriver

    Make GET request by reference using 'Сhrome'.
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
            raise Exception
    except Exception as ex:
        logging.error(ex)
        sys.exit()


def make_scroll(driver: WebDriver, scroll_number: int):
    """Make scroll on page

    Find element 'body' on page and make scroll.
    Script stops if element is not found
    """
    try:
        element = driver.find_element(By.TAG_NAME, "body")

        for scroll in range(1, scroll_number):
            element.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.5)
    except Exception as ex:
        logging.error(ex)
        sys.exit()


def make_request_beautifulsoup(url: str):
    """Make GET request and return processed HTML

    Make GET request by reference using 'BeautifulSoup'.
    Write page HTML in file, read file.
    Return page HTML processed with library "lxml"
    """
    try:
        headers = {
            "User-Agent": f"{USER_AGENT}"
        }
        req = requests.get(url, headers=headers, timeout=MAX_WAIT)
        src = req.text

        with open("current_page.html", "w", encoding="utf-8-sig") as file:
            file.write(src)
        with open("current_page.html", encoding="utf-8-sig") as file:
            src = file.read()

        soup = BeautifulSoup(src, "lxml")
        return soup
    except Exception as ex:
        logging.error(ex)


def search_post_href(driver: WebDriver):
    """Find references on posts and return list of them

    Process HTML from 'selenium' with library 'lxml'
    Find all elements 'a' by 'class name' and get attribute 'href' from them.
    Add post_url in list.
    Return page HTML processed with library "lxml"
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
        sys.exit()


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


def get_data(url: str):
    """Get data from page and return file with data"""
    count_records = 0
    scroll_number = round(COUNT_POSTS * 1.5)
    now = datetime.datetime.now().strftime('%Y%m%d%H%M')
    posts_urls_done = []

    search_and_del_file('reddit*')

    driver = make_request_selenium(url)
    make_scroll(driver, scroll_number)

    posts_urls = search_post_href(driver)
    driver.close()
    driver.quit()

    while count_records < COUNT_POSTS:
        for post_url in posts_urls:

            # Create unique id with library "uuid"
            unique_id = uuid.uuid1().hex

            try:
                soup = make_request_beautifulsoup(post_url)
            except Exception as ex:
                logging.error(ex)
                continue

            posts_urls_done.append(post_url)

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
            except Exception as ex:
                logging.error(ex)
                continue

            soup = make_request_beautifulsoup(user_link)

            try:
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
            except Exception as ex:
                logging.error(ex)
                continue

            all_data = [unique_id, post_url, user_name, user_karma,
                        user_cake_day, post_karma, comment_karma, post_date,
                        number_of_comments, number_of_votes, post_category]

            with open(f"reddit-{now}.txt", "a", encoding="utf-8-sig") as file:
                file.write(';'.join(all_data) + "\n")
                count_records += 1

            if count_records == COUNT_POSTS:
                search_and_del_file("*.html")
                return False

        driver = make_request_selenium(url)
        scroll_number += COUNT_POSTS
        make_scroll(driver, scroll_number)

        next_posts_urls = search_post_href(driver)
        driver.close()
        driver.quit()

        # Select urls for which there was no request
        new_posts_urls = [x for x in next_posts_urls
                          if x not in posts_urls_done]
        posts_urls = new_posts_urls


get_data("https://www.reddit.com/top/?t=month")
