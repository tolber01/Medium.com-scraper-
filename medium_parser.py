#!../Scripts/python.exe
import random
import time
import csv
import json
from multiprocessing.dummy import Pool as ThreadPool
import requests
from bs4 import BeautifulSoup, SoupStrainer
from fake_useragent import UserAgent
from constants import Const as const


class App:
    def __init__(self):
        start_url = self.check_files_and_start()
        print("start ->", start_url)
        parser = Parser(start_url)

    def check_files_and_start(self):
        with open(const.RESERVE_URLS_PATH, "r") as reserve_urls_file: # Working with files
            reserve_urls_text = reserve_urls_file.read()

            if reserve_urls_text:
                return random.choice(reserve_urls_text.split("\n"))
            else:
                with open(const.USED_URLS_PATH, "r") as used_urls_file:
                    used_urls_text = used_urls_file.read()

                if not used_urls_text:
                    with open(cosnt.OUT_PATH, "w", encoding=const.CSV_ENCODING, newline="") as csv_file:
                        field_names = const.DEFAULT_FIELDS
                        writer = csv.DictWriter(csv_file, fieldnames=field_names)
                        writer.writeheader()

                with open(const.USED_URLS_PATH, "r") as used_urls_file:
                    last_used_url = used_urls_file.read().split("\n")[-3]

                return last_used_url

class Parser:
    def __init__(self, start):
        print("collecting User-Agents...")
        self.fake_ua = UserAgent()
        self.user_agents = self.get_user_agents_list()  # Collecting User-Agents
        print("done")
        
        self.pool = ThreadPool(const.THREADS_NUMBER)  # Creating Pool object of multiprocessing based on threads

        self.current_urls = self.get_basic_urls(start)  # Collecting basic list of urls
        print(self.current_urls)

        self.new_urls = []  # Extra list is necessary in the code

        with open(const.USED_URLS_PATH, "r") as used_urls_file:  # Reading used urls from .txt file
            self.used_urls = used_urls_file.read().split("\n")
        self.counter = 0

        while True:  # Main loop
            self.main_loop_iteration()  # Main function of the loop

    def get_user_agents_list(self):  # Loading User-Agents from .json file
        json_file_data = json.load(open(const.JSON_UA_PATH))
        user_agents_list = []
        for piece_of_data in json_file_data["useragentswitcher"]["folder"]:
            try:
                for user_agent in piece_of_data["useragent"]:
                    user_agents_list.append(user_agent["-useragent"])
            except KeyError:
                pass
        return user_agents_list

    def get_basic_urls(self, start_url):
        basic_urls = self.get_followers_or_following(
            start_url + "/following",
            self.get_html(start_url + "/following")
        )
        basic_urls.extend(
            self.get_followers_or_following(
                start_url + "/followers",
                self.get_html(start_url + "/followers")
            )
        )
        return basic_urls

    def get_followers_or_following(self, url_to_followers, html): 
        # Get new urls from following and followers
        only_a_tags = SoupStrainer(const.A_TAG)
        a_soup = BeautifulSoup(
            html, 
            "lxml", 
            parse_only=only_a_tags
        )
        followers_links_list = [
            link.get("href") for link in a_soup.find_all(
                const.A_TAG,
                {"class": const.A_FOLLOW_CLASS}
            )
        ]
        return followers_links_list

    def get_html(self, url_to_html):  # Request -> response -> html
        try:
            html_code = requests.get(
                url=url_to_html,
                headers={"User-Agent": self.fake_ua.random}
            ).text
        except:
            try:
                html_code = requests.get(
                    url=url_to_html,
                    headers={"User-Agent": random.choice(self.user_agents)}
                ).text
                return html_code
            except:
                return self.get_html(url_to_html)
        else:
            return html_code
    
    def main_loop_iteration(self):
        self.pool.map(self.parse, self.current_urls)  # Using multiprocessing for current urls

        self.current_urls = self.new_urls  # Replacing current urls with new urls

        with open(const.USED_URLS_PATH, "w") as used_urls_file:  # Write new used urls to .txt file
            used_urls_file.write("\n".join(self.used_urls))
        with open(const.RESERVE_URLS_PATH, "w") as reserve_urls_file:  # Write reserve urls to .txt file
            reserve_urls_file.write("\n".join(self.current_urls))

        print("Current urls ->", len(self.current_urls))  # Print number of available urls

        time.sleep(const.ITERATION_TIMEOUT)  # Iteration timeout (default = 3s)
    
    def parse(self, profile_url):
        if profile_url in self.used_urls:
            print("used")  # Checking url
            return
        else:
            self.used_urls.append(profile_url)  # New used url

        with open(const.USED_URLS_PATH, "a") as used_urls_file:
            used_urls_file.write(profile_url + "\n")

        following_url = profile_url + "/following"
        followers_url = profile_url + "/followers"

        html_of_user = self.get_html(profile_url)  # Get html code of user, following & followers pages
        html_of_following = self.get_html(following_url)
        html_of_followers = self.get_html(followers_url)

        if html_of_user is None:
            return

        only_div_tags = SoupStrainer(const.DIV_TAG)  # Generating tag keys for a beautiful soup
        only_link_tags = SoupStrainer(const.A_TAG)

        header_soup = BeautifulSoup(  # Generating BeautifulSoup object
            html_of_user,
            "lxml",
            parse_only=only_div_tags
        )
        buttonset_soup_following = BeautifulSoup(
            html_of_following,
            "lxml",
            parse_only=only_link_tags
        )
        buttonset_soup_followers = BeautifulSoup(
            html_of_followers,
            "lxml",
            parse_only=only_link_tags
        )
        
        hero_name = self.get_user_name(header_soup, profile_url)
        
        hero_description = self.get_user_description(header_soup)

        following_people_quantity = self.get_number_of_following(buttonset_soup_following)
        followers_quantity = self.get_number_of_followers(buttonset_soup_following)

        twitter_url = self.get_twitter_url(buttonset_soup_following)
        facebook_url = self.get_facebook_url(buttonset_soup_following)

        urls_to_return = self.get_followers_or_following(
            following_url,
            html_of_following
        )  # Scraping new urls
        urls_to_return.extend(
            self.get_followers_or_following(
                followers_url,
                html_of_followers
            )
        )
        self.new_urls.extend(urls_to_return)

        self.counter += 1
        print(self.counter)
        

        user = dict(zip(
                const.DEFAULT_FIELDS, 
                [
                    hero_name,
                    profile_url,
                    hero_description,
                    following_people_quantity,
                    followers_quantity,
                    twitter_url,
                    facebook_url
                ]
        ))
        self.write_to_csv(user)

    def get_user_name(self, soup, current_url):
        try:  # Scraping user's name
            name = soup.find(const.H1_TAG).text
        except AttributeError:
            print("doesn't parse")
            return self.parse(current_url)
        else:
            return name

    def get_user_description(self, soup):
        try:  # Scraping user's description
            hero_description = soup.find(
                "p",
                {"class": const.P_DESCRIPTION_CLASS}
            ).text
        except AttributeError:
            return ""
        else:
            return hero_description

    def get_number_of_following(self, soup):
        try:  # Scraping number of following
            following_people_quantity = int(
                soup.find(
                    "a",
                    {"data-action-value": const.DATA_ACTION_FOLLOWING}
                ).get("title").split()[1].replace(",", "")
            )
        except AttributeError:
            return None
        else:
            return following_people_quantity

    def get_number_of_followers(self, soup):
        try:  # Scraping number of followers
            followers_quantity = int(
                soup.find(
                    "a",
                    {"data-action-value": const.DATA_ACTION_FOLLOWERS}
                ).get("title").split()[1].replace(",", "")  
            )
        except AttributeError:
            return None
        else:
            return followers_quantity

    def get_twitter_url(self, soup):
        try:  # Scraping twitter url
            twitter = soup.find(
                "a",
                {"title": const.TITLE_TWITTER}
            ).get("href")
        except AttributeError:
            return None
        else:
            return twitter

    def get_facebook_url(self, soup):
        try:  # Scraping facebook url
            facebook_url = soup.find(
                "a",
                {"title": const.TITLE_FACEBOOK}
            ).get("href")
        except AttributeError:
            return None
        else:
            return facebook_url

    def write_to_csv(self, user):  # Write user to .csv table
        with open(const.OUT_PATH, "a", encoding=const.CSV_ENCODING, newline="") as csv_file:
            field_names = const.DEFAULT_FIELDS
            writer = csv.DictWriter(csv_file, fieldnames=field_names)
            writer.writerow(user)


if __name__ == "__main__":  # Main process
    main = App()
