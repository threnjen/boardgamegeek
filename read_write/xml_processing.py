from bs4 import BeautifulSoup
from typing import Optional, ClassVar
from pydantic import BaseModel
import re


class BGGXMLTag(BaseModel):
    tag: str
    value: Optional[str] = None
    attributes: Optional[dict] = None


class BGGXMLParser(BaseModel):
    MIN_USER_RATINGS: ClassVar[int] = 10

    def parse_xml(
        self, game_page: Optional[BeautifulSoup], filepath: Optional[str]
    ) -> BeautifulSoup:
        if game_page is None and filepath is None:
            raise ValueError("No game page or file path provided. Please provide one.")
        if filepath:
            game_page = BeautifulSoup(open(filepath, encoding="utf8"), "lxml")
        game_list = game_page.find_all("item")
        if type(game_list) != list:
            game_list = [game_list]

        for game in game_list:
            if self.include_game(game):
                game_dict = self._parse_individual_game(game)

    def include_game(self, game: BeautifulSoup) -> bool:
        try:
            user_ratings = int(game.find("usersrated")["value"])
            if user_ratings < self.MIN_USER_RATINGS:
                return False
        except:
            return False
        return True

    def _parse_individual_game(self, game: BeautifulSoup) -> dict:
        game_dict = {}
        game_dict["game_id"] = game["id"]
        game_dict["game_name"] = game.find("name", type="primary")["value"]
        game_dict["description"] = game.find("description").text
        game_dict["year_published"] = int(game.find("yearpublished")["value"])
        game_dict["min_players"] = int(game.find("minplayers")["value"])
        game_dict["max_players"] = int(game.find("maxplayers")["value"])
        game_dict["avg_rating"] = float(game.find("average")["value"])
        game_dict["bayes_avg"] = float(game.find("bayesaverage")["value"])
        game_dict["std_dev"] = float(game.find("stddev")["value"])
        game_dict["NumOwned"] = int(game.find("owned")["value"])
        game_dict["NumWant"] = int(game.find("wanting")["value"])
        game_dict["NumWish"] = int(game.find("wishing")["value"])
        game_dict["NumWeightVotes"] = int(game.find("numweights")["value"])
        game_dict["game_weight"] = float(game.find("averageweight")["value"])
        game_dict["ImagePath"] = game.find("image").text
        game_dict["MfgPlaytime"] = int(game.find("playingtime")["value"])
        game_dict["comm_min_play"] = int(game.find("minplaytime")["value"])
        game_dict["comm_max_play"] = int(game.find("maxplaytime")["value"])
        game_dict["MfgAgeRec"] = int(game.find("minage")["value"])
        game_dict["NumUserRatings"] = int(game.find("usersrated")["value"])
        game_dict["num_comments"] = int(game.find("comments")["totalitems"])
        game_dict["NumAlternates"] = len(game.find_all("name", type="alternate"))
        game_dict["NumExpansions"] = len(
            game.find_all("link", type="boardgameexpansion")
        )
        game_dict["NumImplementations"] = len(
            game.find_all("link", type="boardgameimplementation")
        )
        game_dict["IsReimplementation"] = (
            1
            if game.find("link", type="boardgameimplementation", inbound="true")
            else 0
        )
        game_dict["ComAgeRec"] = BGGXMLParser.evaulate_poll(
            "User Suggested Player Age"
        )  # community age min poll
        game_dict["LanguageEase"] = BGGXMLParser.evaulate_poll(
            "Language Dependence"
        )  # Language Ease poll
        game_dict["BestPlayers"] = BGGXMLParser.evaulate_poll(
            "User Suggested Number of Players"
        )  # Best Players poll
        game_dict["ComMinPlaytime"] = BGGXMLParser.evaulate_poll(
            "User Suggested Play Time"
        )  # Community Min Playtime poll
        game_dict["ComMaxPlaytime"] = BGGXMLParser.evaulate_poll(
            "User Suggested Play Time"
        )  # Community Max Playtime poll
        for rank, score in BGGXMLParser.get_rank(game).items():
            game_dict[rank] = score
        game_dict["Family"] = BGGXMLParser.get_boardgame_family_attribute("Game:")
        game_dict["Setting"] = BGGXMLParser.get_boardgame_family_attribute("Setting:")
        game_dict["Theme"] = BGGXMLParser.get_boardgame_family_attribute("Theme:")
        game_dict["Mechanism"] = BGGXMLParser.get_boardgame_family_attribute(
            "Mechanism:"
        )
        game_dict["Category"] = BGGXMLParser.get_boardgame_family_attribute("Category:")
        game_dict["Kickstarted"] = (
            1 if BGGXMLParser.get_boardgame_family_attribute("Crowdfunding") else 0
        )
        for component, value in BGGXMLParser.get_components(game).items():
            game_dict[component] = value


        return game_dict

    @staticmethod
    def create_game_entries_from_page(game_page: BeautifulSoup) -> list:
        return game_page.find_all("item")

    @staticmethod
    def evaulate_poll(game: BeautifulSoup, poll_title: str):
        NUMVOTES_TAG = "numvotes"
        poll_result = None
        try:
            poll = game.find("poll", title=poll_title).find_all("result")
            vote_total = sum(
                [int(item[NUMVOTES_TAG]) * int(item["value"][:2]) for item in poll]
            )
            items = sum([int(item[NUMVOTES_TAG]) for item in poll])
            if items > 0:
                poll_result = vote_total / items
            else:
                poll_result = None
        except:
            poll_result = None
        return poll_result

    @staticmethod
    def get_rank(game: BeautifulSoup) -> dict:
        """Returns all possible rank types of a game.
        Possible types may include family (e.g. thematic, strategygames),
        overall (coded as 'boardgame'), etc.
        """
        return {
            f"Rank:{ item['name'] }": float(
                item["value"]) for item in game.find_all("rank")
            
        }

    @staticmethod
    def get_boardgame_family_attribute(game: BeautifulSoup, attribute: str) -> str:
        try:
            return (
                game.find("link", type="boardgamefamily", value=re.compile(attribute))[
                    "value"
                ]
                .strip("Series:")
                .strip(" ")
            )
        except:
            return None

    @staticmethod
    def get_components(game: BeautifulSoup) -> dict:
        try:
            families = game.find_all(
                "link", type="boardgamefamily", value=re.compile("Component")
            )
            return {item["name"]: item["value"] for item in families}
        except:
            return {}
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

            if player_num_votes > 30:  # evaluate if more than 30 votes for num players
                for player in players:
                    best = int(player.find("result", value="Best")["numvotes"])
                    rec = int(player.find("result", value="Recommended")["numvotes"])
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

        # Try to add game series/family
        try:
            family = (
                entry.find("link", type="boardgamefamily", value=re.compile("Game:"))[
                    "value"
                ]
                .strip("Game:")
                .strip(" ")
            )
            this_game["Family"] = family
        except:
            pass

        try:
            family = (
                entry.find("link", type="boardgamefamily", value=re.compile("Series:"))[
                    "value"
                ]
                .strip("Series:")
                .strip(" ")
            )
            this_game["Family"] = family
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
        mechanic = create_mechanics(entry, game_id)
        artist = create_thing_of_type(entry, game_id, find_type_str="boardgameartist")
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

    games.to_pickle(f"data_dirty/pulled_games_processed/games{str(file_suffix)}.pkl")
    designers.to_pickle(
        f"data_dirty/pulled_games_processed/designers{str(file_suffix)}.pkl"
    )
    categories.to_pickle(
        f"data_dirty/pulled_games_processed/categories{str(file_suffix)}.pkl"
    )
    mechanics.to_pickle(
        f"data_dirty/pulled_games_processed/mechanics{str(file_suffix)}.pkl"
    )
    artists.to_pickle(
        f"data_dirty/pulled_games_processed/artists{str(file_suffix)}.pkl"
    )
    publishers.to_pickle(
        f"data_dirty/pulled_games_processed/publishers{str(file_suffix)}.pkl"
    )
    subcategories.to_pickle(
        f"data_dirty/pulled_games_processed/subcategories{str(file_suffix)}.pkl"
    )

    print("Finished items in this group")


print(f"Time: {time.time() - start}\n\n")
