import datetime
import time
import os.path
import glob
import uuid
import logging
import requests
import json

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

count_posts = 100
logging.basicConfig(level=logging.INFO, filename='app.log', filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')

user_agent = ("Mozilla/5.0 (Windows NT 6.3; Win64; x64)"
              "AppleWebKit/537.36 (KHTML, like Gecko)"
              "Chrome/92.0.4515.159 Safari/537.36")


def search_and_del_file(search_mask: str):
    file_list = glob.glob(search_mask)
    if file_list:
        for file_name in file_list:
            os.remove(file_name)


def make_request_selenium(url: str):
    try:
        options = webdriver.ChromeOptions()
        options.add_argument(f"user-agent={user_agent}")

        # disable webdriver mode
        # for ChromeDriver version 79.0.3945.16 or over
        options.add_argument("--disable-blink-features=AutomationControlled")

        # headless mode
        options.add_argument("--headless")

        driver = webdriver.Chrome(options=options)
        driver.get(url=url)
        return driver
    except Exception as ex:
        logging.error(ex)


def make_request_beautifulsoup(url: str):
    try:
        headers = {
            "User-Agent": f"{user_agent}"
        }
        req = requests.get(url, headers=headers)
        src = req.text

        with open("current page.html", "w", encoding="utf-8-sig") as file:
            file.write(src)
        with open("current page.html", encoding="utf-8-sig") as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")

        return soup
    except Exception as ex:
        logging.error(ex)


def make_scroll(driver, scroll_number: int):
    try:
        element = driver.find_element(By.TAG_NAME, "body")

        for scroll in range(1, scroll_number):
            element.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.5)
    except Exception as ex:
        logging.error(ex)


def search_post_href(driver):
    try:
        soup = BeautifulSoup(driver.page_source, "lxml")
        all_post_href = soup.find_all("a",
                                      class_=("SQnoC3ObvgnGjWt90zD9Z "
                                              "_2INHSNB8V5eaWp4P0rY_mE"))
        posts_urls = []
        for item in all_post_href:
            post_url = "https://www.reddit.com/" + item.get("href")
            posts_urls.append(post_url)

        return posts_urls
    except Exception as ex:
        logging.error(ex)


def get_data(url: str):
    i = 1
    scroll_number = count_posts * 2
    user_link = ""
    now = datetime.datetime.now().strftime('%Y%m%d%H%M')

    search_and_del_file('reddit*')
    driver = make_request_selenium(url)
    make_scroll(driver, scroll_number)

    posts_urls = search_post_href(driver)
    posts_urls_done = posts_urls[:]
    driver.close()
    driver.quit()

    while i < count_posts - 1:
        for post_url in posts_urls:

            user_name = post_date = number_of_comments = ""
            number_of_votes = post_category = ""

            unique_id = uuid.uuid1().hex

            try:
                soup = make_request_beautifulsoup(post_url)
            except Exception as ex:
                logging.error(ex)
                continue

            try:
                user_data = soup.find("p", class_="tagline").find("a")
                user_name = user_data.text
                user_link = user_data.get("href")
            except Exception as ex:
                logging.error(ex)

            try:
                number_of_votes = ''.join(soup.find("div",
                                                    class_="linkinfo").find(
                    "span", {"class": "number"}).text.split(","))
            except Exception as ex:
                logging.error(ex)

            try:
                post_date = soup.find("div", class_="date").find("time").text
            except Exception as ex:
                logging.error(ex)

            try:
                post_category = soup.find("div", class_="titlebox").find(
                    "a").text
            except Exception as ex:
                logging.error(ex)

            try:
                number_of_comments = soup.find(
                    "a", class_="bylink comments may-blank").text.split()[0]
            except Exception as ex:
                logging.error(ex)

            soup = make_request_beautifulsoup(user_link)

            try:
                get_json_from_response = soup.find(
                    "script", id="data").text[:-1].split('= ', maxsplit=1)[1]
                data_from_json = json.loads(get_json_from_response)
                user = list(data_from_json["profiles"]["about"].keys())[0]
                user_karma = str(data_from_json["profiles"]["about"]
                                 [f'{user}']['karma']['total'])
                post_karma = str(data_from_json["profiles"]["about"]
                                 [f'{user}']['karma']['fromPosts'])
                comment_karma = str(data_from_json["profiles"]["about"]
                                    [f'{user}']['karma']['fromComments'])
                user_cake_day = soup.find("span",
                                          id=("profile--id-card--highlight-"
                                              "tooltip--cakeday")).text
            except Exception as ex:
                logging.error(ex)
                continue

            all_data = [unique_id, post_url, user_name, user_karma,
                        user_cake_day, post_karma, comment_karma, post_date,
                        number_of_comments, number_of_votes, post_category]

            with open(f"reddit-{now}.txt", "a", encoding="utf-8-sig") as file:
                file.write(';'.join(all_data) + "\n")
                print(f"запись{i}")
                i += 1

            if i == count_posts + 1:
                return False

        driver = make_request_selenium(url)
        scroll_number += count_posts
        make_scroll(driver, scroll_number)

        next_posts_urls = search_post_href(driver)
        new_posts_urls = [x for x in next_posts_urls
                          if x not in posts_urls_done]
        posts_urls_done = next_posts_urls
        posts_urls = new_posts_urls
        driver.close()
        driver.quit()


get_data("https://www.reddit.com/top/?t=month")
