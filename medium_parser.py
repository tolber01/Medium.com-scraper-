import requests
import random
import csv
import time
import json
from multiprocessing.dummy import Pool as ThreadPool
from fake_useragent import UserAgent
from bs4 import BeautifulSoup, SoupStrainer


class App:
    def __init__(self):
        START_LINK = check_files_and_start()
        print("start ->", START_LINK)
        parser = Parser(START_LINK)

class Parser:
    def __init__(self, start):
        self.ua = UserAgent()
        print("collecting User-Agents...")
        self.user_agents = self.get_user_agents_list()  # Collecting User-Agents
        print("done")
        
        self.pool = ThreadPool(100)  # Creating Pool object of multiprocessing

        self.current_urls = self.get_followers_or_following(  # Collecting basic list of urls
            start + "/following",
            self.get_html(start + "/following")
        )
        print(self.current_urls)
        self.current_urls.extend(
            self.get_followers_or_following(
                start + "/followers",
                self.get_html(start + "/followers")
            )
        )

        self.new_urls = []  # Extra list is necessary in the code

        with open("used_urls.txt", "r") as f:  # Reading used urls from .txt file
            self.used_urls = f.read().split("\n")
        self.counter = 0

        while True:  # Main loop
            self.main_loop()  # Main function of the loop
    
    def main_loop(self):
        self.pool.map(self.parse, self.current_urls)  # Using multiprocessing for current urls

        self.current_urls = self.new_urls  # Replacing current urls with new urls

        with open("used_urls.txt", "w") as f2:  # Write new used urls to .txt file
            f2.write("\n".join(self.used_urls))
        with open("reserve_urls.txt", "w") as f3:  # Write reserve urls to .txt file
            f3.write("\n".join(self.current_urls))

        print("Current urls ->", len(self.current_urls))  # Print number of available urls

        time.sleep(3)  # 3 second timeout
    
    def parse(self, profile_url):
        if profile_url in self.used_urls:  # Checking url
            return
        html_of_user = self.get_html(profile_url)  # Get html code of user
        if html_of_user is None:
            return
        only_header_tags = SoupStrainer("header")  # Generating tag keys for a beautiful soup
        only_buttonset_class = SoupStrainer(
            "a"
        )
        header_soup = BeautifulSoup(
            html_of_user,
            "lxml",
            parse_only=only_header_tags
        )
        buttonset_soup = BeautifulSoup(
            html_of_user,
            "lxml",
            parse_only=only_buttonset_class
        )
        
        try:  # Scraping user's name
            hero_name = header_soup.find(
                ["h1", "h2", "h3", "h4"],
                {"class": "hero-title"}
            ).text
        except AttributeError:
            return self.parse(profile_url)
        
        hero_description = self.get_user_description(header_soup)

        following_people_quantity = self.get_number_of_following(buttonset_soup)
        followers_quantity = self.get_number_of_followers(buttonset_soup)

        twitter_url = self.get_twitter_url(buttonset_soup)
        facebook_url = self.get_facebook_url(buttonset_soup)

        following_url = profile_url + "/following"
        followers_url = profile_url + "/followers"

        urls_to_return = self.get_followers_or_following(
            following_url,
            self.get_html(following_url)
        )  # Scraping new urls
        urls_to_return.extend(
            self.get_followers_or_following(
                followers_url,
                self.get_html(followers_url)
            )
        )
        self.new_urls.extend(urls_to_return)

        self.counter += 1
        print(self.counter)
        user = {  # Making user dictionary
            "Name": hero_name,
            "Link": profile_url,
            "Description": hero_description,
            "Following": following_people_quantity,
            "Followers": followers_quantity,
            "Twitter": twitter_url,
            "Facebook": facebook_url
        }
        self.used_urls.append(profile_url)  # New used url
        with open("used_urls.txt", "a") as f:
            f.write(profile_url + "\n")
        self.write_to_csv(user)

    def get_user_description(self, soup):
        try:  # Scraping user's description
            hero_description = soup.find(
                "p",
                {"class": "hero-description"}
            ).text
            return hero_description
        except AttributeError:
            return ""

    def get_number_of_following(self, soup):
        try:  # Scraping number of following
            following_people_quantity = int(
                soup.find(
                    "a",
                    {"data-action-value": "following"}
                ).get("title").split()[1].replace(",", "")
            )
            return following_people_quantity
        except AttributeError:
            return None 

    def get_number_of_followers(self, soup):
        try:  # Scraping number of followers
            followers_quantity = int(
                soup.find(
                    "a",
                    {"data-action-value": "followers"}
                ).get("title").split()[1].replace(",", "")  
            )
            return followers_quantity
        except AttributeError:
            return None

    def get_twitter_url(self, soup):
        try:  # Scraping twitter url
            twitter = soup.find(
                "a",
                {"title": "Twitter"}
            ).get("href")
            return twitter
        except AttributeError:
            return None 

    def get_facebook_url(self, soup):
        try:  # Scraping facebook url
            facebook_url = soup.find(
                "a",
                {"title": "Facebook"}
            ).get("href")
            return facebook_url
        except AttributeError:
            return None

    def get_user_agents_list(self):  # Loading User-Agents from .json file
        data = json.load(open("user_agents.json"))
        result = []
        for piece_of_data in data["useragentswitcher"]["folder"]:
            try:
                for user_agent in piece_of_data["useragent"]:
                    result.append(user_agent["-useragent"])
            except KeyError:
                pass
        return result

    def write_to_csv(self, user):  # Write user to .csv table
        with open("out.csv", "a", encoding='utf-8', newline="") as csv_file:
            field_names = [
                "Name",
                "Link",
                "Description",
                "Following",
                "Followers",
                "Twitter",
                "Facebook"
            ]
            writer = csv.DictWriter(csv_file, fieldnames=field_names)
            writer.writerow(user)

    def get_html(self, url_to_html):  # Request -> response -> html
        try:
            result = requests.get(
                url=url_to_html,
                headers={"User-Agent": self.ua.random}
            ).text
        except:
            try:
                result = requests.get(
                    url=url_to_html,
                    headers={"User-Agent": random.choice(self.user_agents)},
                    # timeout=(10, 0.01)
                ).text
                return result
            except:
                return self.get_html(url_to_html)
        else:
            return result

    def get_followers_or_following(self, url_to_followers, html): 
        # Get new urls from following and followers
        only_a_tags = SoupStrainer("a")
        a_soup = BeautifulSoup(
            html, 
            "lxml", 
            parse_only=only_a_tags
        )
        followers_links_list = [
            link.get("href") for link in a_soup.find_all(
                "a",
                {"class": "avatar"}
            )
        ]
        return followers_links_list


def check_files_and_start():
    with open("reserve_urls.txt", "r") as f1: # Working with files
        text = f1.read()
        if text != "":
            return random.choice(text.split("\n"))
        else:
            with open("used_urls.txt", "r") as f:
                data = f.read()
            if data == "":
                with open("out.csv", "w", encoding='utf-8', newline="") as csv_file:
                    field_names = [
                        "Name",
                        "Link",
                        "Description",
                        "Following",
                        "Followers",
                        "Twitter",
                        "Facebook"
                    ]
                    writer = csv.DictWriter(csv_file, fieldnames=field_names)
                    writer.writeheader()
            with open("used_urls.txt", "r") as f:
                result = f.read().split("\n")[-2]
            return result

if __name__ == "__main__":  # Main process
    main = App()
