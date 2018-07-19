class Const:
    CSV_ENCODING = "utf-8"
    DEFAULT_FIELDS = [
        "Name",
        "Link",
        "Description",
        "Following",
        "Followers",
        "Twitter",
        "Facebook"
    ]

    RESERVE_URLS_PATH = "../text_and_data/reserve_urls.txt"
    USED_URLS_PATH = "../text_and_data/used_urls.txt"
    OUT_PATH = "../text_and_data/out.csv"
    JSON_UA_PATH = "../text_and_data/user_agents.json"

    THREADS_NUMBER = 50
    ITERATION_TIMEOUT = 3

    P_DESCRIPTION_CLASS = "bx by w b x bz ca ab ac"
    A_FOLLOW_CLASS = "avatar"

    DIV_TAG = "div"
    A_TAG = "a"
    H1_TAG = "h1"

    DATA_ACTION_FOLLOWING = "following"
    DATA_ACTION_FOLLOWERS = "followers"

    TITLE_TWITTER = "Twitter"
    TITLE_FACEBOOK = "Facebook"


