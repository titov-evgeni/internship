import datetime
import random
import time

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

count_posts = 7


def make_request_selenium(url):
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 6.3; Win64; x64)"
                             "AppleWebKit/537.36 (KHTML, like Gecko)"
                             "Chrome/92.0.4515.159 Safari/537.36")
        options.add_argument("--disable-blink-features=AutomationControlled")
        driver = webdriver.Chrome(options=options)
        driver.get(url=url)
        return driver
    except Exception as ex:
        print(ex)


def make_request(url):
    try:
        headers = {
            "User-Agent": ("Mozilla/5.0 (Windows NT 6.3; Win64; x64)"
                           "AppleWebKit/537.36 (KHTML, like Gecko)"
                           "Chrome/92.0.4515.159 Safari/537.36")

        }

        req = requests.get(url, headers=headers)
        src = req.text
        return BeautifulSoup(src, "lxml")
    except Exception as ex:
        print(ex)


def get_data():

    i = 0
    scroll_number = 10
    user_link = ""
    now = datetime.datetime.now().strftime('%Y%m%d%H%M')
    url = "https://www.reddit.com/top/?t=month"

    soup = make_request(url)
    time.sleep(random.randrange(2, 4))
    all_products_hrefs = soup.find_all("a",
                                       class_="SQnoC3ObvgnGjWt90zD9Z _2INHSNB8V5eaWp4P0rY_mE")
    posts_urls = []
    for item in all_products_hrefs:
        post_url = "https://www.reddit.com/" + item.get("href")
        posts_urls.append(post_url)

    posts_urls_done = posts_urls[:]
    while i < count_posts - 1:
        for post_url in posts_urls:
            user_name = post_date = number_of_comments = number_of_votes = post_category = ""

            try:
                soup = make_request(post_url)
            except Exception as ex:
                print(ex)

            try:
                user_data = soup.find("p", class_="tagline").find("a")
                user_name = user_data.text
                user_link = user_data.get("href")
            except Exception as ex:
                print(ex)

            try:
                number_of_votes = soup.find("div", class_="linkinfo").find("span", {"class": "number"}).text
            except Exception as ex:
                print(ex)

            try:
                post_date = soup.find("div", class_="date").find("time").text
            except Exception as ex:
                print(ex)

            try:
                post_category = soup.find("div", class_="titlebox").find("a").text
            except Exception as ex:
                print(ex)

            try:
                number_of_comments = soup.find("a", class_="bylink comments may-blank").text
            except Exception as ex:
                print(ex)

            try:
                driver = make_request_selenium(user_link)
                driver.find_element(By.CLASS_NAME, "_1hNyZSklmcC7R_IfCUcXmZ").click()
                soup = BeautifulSoup(driver.page_source, "lxml")
                user_karma = soup.find("span", id="profile--id-card--highlight-tooltip--karma").text
                user_cake_day = soup.find("span", id="profile--id-card--highlight-tooltip--cakeday").text
                karmas = soup.find("div", class_="_3uK2I0hi3JFTKnMUFHD2Pd").text.split()
                post_karma = karmas[0]
                comment_karma = karmas[3]
            except Exception as ex:
                print(ex)
                driver.close()
                driver.quit()
                continue

            all_data = [str(i), post_url, user_name, user_karma, user_cake_day, post_karma, comment_karma,
                        post_date, number_of_comments, number_of_votes, post_category]

            with open(f"reddit-{now}.txt", "a", encoding="utf-8-sig") as file:
                file.write(';'.join(all_data) + "\n")
                i += 1

            driver.close()
            driver.quit()
            time.sleep(random.randrange(5))
            if i == count_posts:
                return False

        driver = make_request_selenium(url)
        element = driver.find_element(By.TAG_NAME, "body")

        for scroll in range(1, scroll_number):
            element.send_keys(Keys.PAGE_DOWN)
            time.sleep(1)
        scroll_number += 10

        next_posts_urls = []
        soup = BeautifulSoup(driver.page_source, "lxml")
        all_products_hrefs = soup.find_all("a",
                                           class_="SQnoC3ObvgnGjWt90zD9Z _2INHSNB8V5eaWp4P0rY_mE")
        for item in all_products_hrefs:
            post_url = "https://www.reddit.com/" + item.get("href")
            next_posts_urls.append(post_url)
        tre = [x for x in next_posts_urls if x not in posts_urls_done]
        posts_urls_done = posts_urls + next_posts_urls
        posts_urls = tre
        driver.close()
        driver.quit()


get_data()
