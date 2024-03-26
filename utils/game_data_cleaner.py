import os
import time
from datetime import datetime
from io import BytesIO

import awswrangler as wr
import boto3
import pandas as pd
import regex as re
from bs4 import BeautifulSoup
from lxml import etree

s3_resource = boto3.resource("s3")

# ignore warnings (gets rid of Pandas copy warnings)
import warnings

warnings.filterwarnings("ignore")

import os

IS_LOCAL = os.environ.get("IS_LOCAL", False)


def create_thing_of_type(game_page, game_id, find_type_str):
    """Create DataFrame for things for a specific game id

    Inputs:
    game_page: page loaded and read with BeautifulSoup
    game_id: id for this game

    Outputs:
    dataframe"""

    # find all of the things on page
    all_this_type = game_page.find_all("link", type=find_type_str)

    # make dictionary for this item
    this_dict = {"BGGId": [int(game_id)]}

    # add this item's things to dictionary
    for item in all_this_type:
        this_dict[item["value"]] = [1]

    if find_type_str == "boardgamemechanic":
        # Try Tableau
        try:
            game_page.find(
                "link", type="boardgamefamily", value=("Mechanism: Tableau Building")
            )["value"]
            this_dict["TableauBuilding"] = [1]
        except:
            pass

        # Try is Legacy
        try:
            game_page.find("link", type="boardgamefamily", value=("Mechanism: Legacy"))[
                "value"
            ]
            this_dict["Legacy"] = [1]
        except:
            pass

    # create the dataframe
    df = pd.DataFrame(this_dict)

    # return dataframe
    return df


def create_awards(awards_level, game_id):
    """Create DataFrame for Awards for a specific game id

    Inputs:
    game_page: page loaded and read with BeautifulSoup
    game_id: id for this game

    Outputs:
    dataframe"""

    # find all awards on page
    all_awards = awards_level.find_all("a", class_="ng-binding")

    # make dictionary for this item
    award = {"BGGId": [int(game_id)]}

    # add this item's awards to dictionary
    for item in all_awards:
        item = re.sub("[0-9]", "", item.text).strip(" ")
        award[item] = [1]

    # append to dataframe
    awards = pd.DataFrame(award)

    # return dataframe
    return awards


def make_all_dataframes_per_file():
    files = []

    IS_LOCAL = True
    if IS_LOCAL:
        for item in os.listdir("data_dirty/pulled_games/"):
            if ".xml" in item:
                files.append(f"data_dirty/pulled_games/{item}")
    else:
        all_files = wr.s3.list_objects(
            f"s3://boardgamegeek-scraper/data_dirty/pulled_games/"
        )
        for item in all_files:
            files.append(item)

    file_suffix = 0

    start = time.time()

    for file in files:

        games_dfs = []
        designers_dfs = []
        categories_dfs = []
        mechanics_dfs = []
        artists_dfs = []
        publishers_dfs = []
        subcategories_dfs = []
        comments_dfs = []

        ##### File Setup Section #####

        # increment file suffix
        file_suffix += 1

        if IS_LOCAL:
            game_page = BeautifulSoup(
                open(file, encoding="utf8"), "lxml"
            )  # parse page with beautifulsoup
        else:
            # get file from s3
            s3_client = boto3.client("s3")
            bucket = "boardgamegeek-scraper"
            response = s3_client.get_object(
                Bucket=bucket, Key=file.replace(f"s3://{bucket}/", "")
            )
            response = response["Body"].read().decode("utf-8")
            game_page = BeautifulSoup(response, "lxml")  # parse page with beautifulsoup

        # make entry for each game item on page
        game_entries = game_page.find_all("item")
        print(f"Number of game entries in this file: {len(game_entries)}")

        print("Items loaded. Processing.")
        ##### Process Each Game #####

        for entry in game_entries:

            # check that this game has sufficient user ratings to incluide
            try:
                user_ratings = int(
                    entry.find("usersrated")["value"]
                )  # get the number of user ratings

                if user_ratings < 10:  # check if user ratings are under 10
                    continue
            except:
                continue

            # get game name and BGG ID
            game_name = entry.find("name", type="primary")["value"]
            game_id = entry["id"]
            print(f"Name: {game_name} BGG ID: {str(game_id)}")

            ##### Get Basic Stats #####

            # print("Getting basic stats")
            description = entry.find("description").text  # description text of the game

            try:
                year_pub = int(entry.find("yearpublished")["value"])  # year published
                if year_pub > datetime.now().year:
                    continue
            except:
                pass

            try:
                minplayers = int(entry.find("minplayers")["value"])  # minimum players
            except:
                minplayers = None

            try:
                maxplayers = int(entry.find("maxplayers")["value"])  # maximum players
            except:
                maxplayers = None

            avg_rating = float(entry.find("average")["value"])  # average rating
            bayes_avg = float(
                entry.find("bayesaverage")["value"]
            )  # bayes average rating
            std_dev = float(
                entry.find("stddev")["value"]
            )  # standard deviation of rating
            num_owned = int(entry.find("owned")["value"])  # num of people own this game
            num_want = int(
                entry.find("wanting")["value"]
            )  # num of people want this game
            num_wish = int(
                entry.find("wishing")["value"]
            )  # num of people with game on wishlist
            num_weight_votes = int(
                entry.find("numweights")["value"]
            )  # num of votes for game weight
            game_weight = float(
                entry.find("averageweight")["value"]
            )  # voted game weight

            try:
                image_path = entry.find("image").text  # path to image
            except:
                image_path = None

            try:
                mfg_play_time = int(
                    entry.find("playingtime")["value"]
                )  # mfg stated playtime
            except:
                mfg_play_time = None
            try:
                comm_min_play = int(
                    entry.find("minplaytime")["value"]
                )  # community min playtime
            except:
                comm_min_play = None

            try:
                comm_max_play = int(
                    entry.find("maxplaytime")["value"]
                )  # community max playtime
            except:
                comm_max_play = None

            try:
                mfg_age = int(entry.find("minage")["value"])  # mfg min age
            except:
                mfg_age = None

            # num_comments = int(entry.find('comments')['totalitems']) # num of ratings comments
            num_alts = len(
                entry.find_all("name", type="alternate")
            )  # number alternate versions
            num_expansions = len(
                entry.find_all("link", type="boardgameexpansion")
            )  # number of expansions
            num_implementations = len(
                entry.find_all("link", type="boardgameimplementation")
            )  # number of implementations

            ##### Get reimplementation flag #####
            reimplementation = entry.find(
                "link", type="boardgameimplementation", inbound="true"
            )  # check if game is a reimplementation
            if reimplementation:
                reimplements = 1  # if it's a reimplementation, flag it 1
            else:
                reimplements = 0

            ##### Basic stats requiring some compaction/refinement #####

            def evaluate_poll(poll_title):
                poll_result = None
                try:
                    poll = entry.find("poll", title=poll_title).find_all("result")

                    total = 0
                    items = 0

                    for item in poll:
                        vote = int(item["numvotes"]) * int(item["value"][:2])
                        total += vote
                        items += int(item["numvotes"])

                    if items > 0:
                        poll_result = (
                            total / items
                        )  # make sure not dividing by 0, get community recommended age
                    else:
                        poll_result = None  # if no votes, record none
                except:
                    poll_result = None
                return poll_result

            comm_age = evaluate_poll(
                "User Suggested Player Age"
            )  # community age min poll
            lang_ease = evaluate_poll("Language Dependence")  # Language Ease poll

            try:
                # Best and Good Players
                players = entry.find(
                    "poll", title="User Suggested Number of Players"
                ).find_all(
                    "results"
                )  # get user players poll
                player_num_votes = int(
                    entry.find("poll", title="User Suggested Number of Players")[
                        "totalvotes"
                    ]
                )  # get total votes

                best_players, best_score, good_players = (
                    0,
                    0,
                    [],
                )  # set up for best players loop

                if (
                    player_num_votes > 30
                ):  # evaluate if more than 30 votes for num players
                    for player in players:
                        best = int(player.find("result", value="Best")["numvotes"])
                        rec = int(
                            player.find("result", value="Recommended")["numvotes"]
                        )
                        score = best * 2 + rec * 1
                        positives = best + rec
                        ratio = positives / player_num_votes
                        if score > best_score:
                            best_players, best_score = (
                                player["numplayers"],
                                score,
                            )  # put in # players for best score
                        if ratio > 0.5:
                            good_players.append(
                                player["numplayers"]
                            )  # put in good players if over 50% ratio
                else:
                    best_players = None
            except:
                best_players = None

            # make dataframe for this game
            this_game = pd.DataFrame()
            this_game["BGGId"] = (int(game_id),)
            this_game["Name"] = (game_name,)
            this_game["Description"] = (description,)
            this_game["YearPublished"] = (int(year_pub),)
            this_game["GameWeight"] = (float(game_weight),)
            this_game["AvgRating"] = (float(avg_rating),)
            this_game["BayesAvgRating"] = (float(bayes_avg),)
            this_game["StdDev"] = (float(std_dev),)
            this_game["MinPlayers"] = (minplayers,)
            this_game["MaxPlayers"] = (maxplayers,)
            this_game["ComAgeRec"] = (comm_age,)
            this_game["LanguageEase"] = (lang_ease,)
            this_game["BestPlayers"] = (best_players,)
            this_game["GoodPlayers"] = (good_players,)
            this_game["NumOwned"] = (int(num_owned),)
            this_game["NumWant"] = (int(num_want),)
            this_game["NumWish"] = (int(num_wish),)
            this_game["NumWeightVotes"] = (int(num_weight_votes),)
            this_game["MfgPlaytime"] = (mfg_play_time,)
            this_game["ComMinPlaytime"] = (comm_min_play,)
            this_game["ComMaxPlaytime"] = (comm_max_play,)
            this_game["MfgAgeRec"] = (mfg_age,)
            this_game["NumUserRatings"] = (int(user_ratings),)
            # this_game['NumComments']=int(num_comments),
            this_game["NumAlternates"] = (int(num_alts),)
            this_game["NumExpansions"] = (int(num_expansions),)
            this_game["NumImplementations"] = (int(num_implementations),)
            this_game["IsReimplementation"] = (int(reimplements),)
            this_game["ImagePath"] = image_path

            # add unique information to end of df

            # Add game ranks
            ranks = entry.find_all("rank")
            try:
                for item in ranks:
                    this_game["Rank:" + item["name"]] = float(item["value"])
            except:
                pass

            # Try to add components
            try:
                families = entry.find_all(
                    "link", type="boardgamefamily", value=re.compile("Component")
                )
                for item in families:
                    this_game["Components:" + item["name"]] = item["value"]
            except:
                pass

            # Try to add game series/family
            try:
                family = (
                    entry.find(
                        "link", type="boardgamefamily", value=re.compile("Game:")
                    )["value"]
                    .strip("Game:")
                    .strip(" ")
                )
                this_game["Family"] = family
            except:
                pass

            try:
                family = (
                    entry.find(
                        "link", type="boardgamefamily", value=re.compile("Series:")
                    )["value"]
                    .strip("Series:")
                    .strip(" ")
                )
                this_game["Family"] = family
            except:
                pass

            try:
                setting = (
                    entry.find(
                        "link", type="boardgamefamily", value=re.compile("Setting:")
                    )["value"]
                    .strip("Setting:")
                    .strip(" ")
                )
                this_game["Setting"] = setting
            except:
                pass

            # Try to add theme
            try:
                theme = (
                    entry.find(
                        "link", type="boardgamefamily", value=re.compile("Theme:")
                    )["value"]
                    .strip("Theme:")
                    .strip(" ")
                )
                this_game["Theme"] = theme
            except:
                pass

            try:
                mechanism = (
                    entry.find(
                        "link", type="boardgamefamily", value=re.compile("Mechanism:")
                    )["value"]
                    .strip("Mechanism:")
                    .strip(" ")
                )
                this_game["Mechanism"] = mechanism
            except:
                pass

            # Try to add game category
            try:
                category = (
                    entry.find(
                        "link", type="boardgamefamily", value=re.compile("Category:")
                    )["value"]
                    .strip("Category:")
                    .strip(" ")
                )
                this_game["Category"] = category
            except:
                pass

            # Try is Kickstarted
            try:
                entry.find(
                    "link", type="boardgamefamily", value=re.compile("Crowdfunding")
                )["value"]
                this_game["Kickstarted"] = int(1)
            except:
                pass

            ##### Get subcategories #####

            all_subcategories = entry.find_all("link", type="boardgamecategory")

            # Create an empty DataFrame with columns
            categories_hold = pd.DataFrame(
                columns=["BGGId"] + [item["value"] for item in all_subcategories]
            )

            # Create a dictionary for the new row
            subcategory = {"BGGId": [int(game_id)]}
            for item in all_subcategories:
                subcategory[item["value"]] = [1]

            # Append the dictionary as a new row to the DataFrame
            categories_hold = pd.DataFrame(subcategory)

            # create specialty dataframes
            designer = create_thing_of_type(
                entry, game_id, find_type_str="boardgamedesigner"
            )
            category = create_thing_of_type(
                entry, game_id, find_type_str="boardgamecategory"
            )
            mechanic = create_thing_of_type(
                entry, game_id, find_type_str="boardgamemechanic"
            )
            artist = create_thing_of_type(
                entry, game_id, find_type_str="boardgameartist"
            )
            publisher = create_thing_of_type(
                entry, game_id, find_type_str="boardgamepublisher"
            )

            games_dfs.append(this_game)
            designers_dfs.append(designer)
            categories_dfs.append(category)
            mechanics_dfs.append(mechanic)
            artists_dfs.append(artist)
            publishers_dfs.append(publisher)
            subcategories_dfs.append(categories_hold)

        if games_dfs == []:
            continue
        games = pd.concat(games_dfs)
        designers = pd.concat(designers_dfs)
        categories = pd.concat(categories_dfs)
        mechanics = pd.concat(mechanics_dfs)
        artists = pd.concat(artists_dfs)
        publishers = pd.concat(publishers_dfs)
        subcategories = pd.concat(subcategories_dfs)

        dfs_to_save = {
            "games": games,
            "designers": designers,
            "categories": categories,
            "mechanics": mechanics,
            "artists": artists,
            "publishers": publishers,
            "subcategories": subcategories,
        }

        for item in dfs_to_save:
            dfs_to_save[item].to_pickle(
                f"data_dirty/pulled_games_processed/{item}{str(file_suffix)}.pkl"
            )

            if not IS_LOCAL:
                bucket = "boardgamegeek-scraper"
                key = f"cleaned_data/{item}{str(file_suffix)}.pkl"
                pickle_buffer = BytesIO()
                dfs_to_save[item].to_pickle(pickle_buffer)
                s3_resource.Object(bucket, key).put(Body=pickle_buffer.getvalue())

        print("Finished items in this group")

    print(f"Time: {time.time() - start}\n\n")


def make_master_dfs():
    games_dfs = []
    designers_dfs = []
    categories_dfs = []
    mechanics_dfs = []
    artists_dfs = []
    publishers_dfs = []
    subcategories_dfs = []

    for number in range(1, 500):

        try:
            this_games = pd.read_pickle(
                "data_dirty/pulled_games_processed/games" + str(number) + ".pkl"
            )
            this_designers = pd.read_pickle(
                "data_dirty/pulled_games_processed/designers" + str(number) + ".pkl"
            )
            this_categories = pd.read_pickle(
                "data_dirty/pulled_games_processed/categories" + str(number) + ".pkl"
            )
            this_mechanics = pd.read_pickle(
                "data_dirty/pulled_games_processed/mechanics" + str(number) + ".pkl"
            )
            this_artists = pd.read_pickle(
                "data_dirty/pulled_games_processed/artists" + str(number) + ".pkl"
            )
            this_publishers = pd.read_pickle(
                "data_dirty/pulled_games_processed/publishers" + str(number) + ".pkl"
            )
            this_subcategories = pd.read_pickle(
                "data_dirty/pulled_games_processed/subcategories" + str(number) + ".pkl"
            )

            games_dfs.append(this_games)
            designers_dfs.append(this_designers)
            categories_dfs.append(this_categories)
            mechanics_dfs.append(this_mechanics)
            artists_dfs.append(this_artists)
            publishers_dfs.append(this_publishers)
            subcategories_dfs.append(this_subcategories)
        except:
            print(f"No entry for position {number}")
            continue

        games = pd.concat(games_dfs).reset_index(drop=True)
        designers = pd.concat(designers_dfs).reset_index(drop=True)
        categories = pd.concat(categories_dfs).reset_index(drop=True)
        mechanics = pd.concat(mechanics_dfs).reset_index(drop=True)
        artists = pd.concat(artists_dfs).reset_index(drop=True)
        publishers = pd.concat(publishers_dfs).reset_index(drop=True)
        subcategories = pd.concat(subcategories_dfs).reset_index(drop=True)

        dfs_to_save = {
            "games": games,
            "designers": designers,
            "categories": categories,
            "mechanics": mechanics,
            "artists": artists,
            "publishers": publishers,
            "subcategories": subcategories,
        }

        for item in dfs_to_save:
            dfs_to_save[item].to_pickle(f"data_dirty/pulled_games_processed/{item}.pkl")

            if not IS_LOCAL:
                bucket = "boardgamegeek-scraper"
                key = f"cleaned_data/{item}.pkl"
                pickle_buffer = BytesIO()
                dfs_to_save[item].to_pickle(pickle_buffer)
                s3_resource.Object(bucket, key).put(Body=pickle_buffer.getvalue())


if __name__ == "__main__":
    make_all_dataframes_per_file()
    # make_master_dfs()
