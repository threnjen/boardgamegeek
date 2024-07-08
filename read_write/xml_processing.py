from bs4 import BeautifulSoup
from typing import Optional, ClassVar
from pydantic import BaseModel
import re
import pandas as pd


class BGGXMLTag(BaseModel):
    tag: str
    value: Optional[str] = None
    attributes: Optional[dict] = None


class BGGXMLParser(BaseModel):
    MIN_USER_RATINGS: ClassVar[int] = 10

    def parse_xml(
        self, game_page: Optional[BeautifulSoup]=None, filepath: Optional[str]=None
    ) -> BeautifulSoup:
        if game_page is None and filepath is None:
            raise ValueError("No game page or file path provided. Please provide one.")
        if filepath:
            game_page = BeautifulSoup(open(filepath, encoding="utf8"), features="xml")
        game_list = game_page.find_all("item")

        for game in game_list:
            if not self.include_game(game):
                continue
            game_dict = BGGXMLParser._parse_individual_game(game)

    def include_game(self, game: BeautifulSoup) -> bool:
        user_ratings = int(game.find("usersrated")["value"])
        if user_ratings < self.MIN_USER_RATINGS:
            return False
        return True
        
    @staticmethod
    def create_thing_of_type(
        game_page: BeautifulSoup, game_id: str, find_type_str: str
    ) -> pd.DataFrame:
        """Create DataFrame for things for a specific game id

        Inputs:
        game_page: page loaded and read with BeautifulSoup
        game_id: id for this game

        Outputs:
        dataframe"""

        # make dictionary for this item
        this_dict = {
            item["value"]: [1]
            for item in game_page.find_all("link", type=find_type_str)
        }
        this_dict = {"BGGId": [int(game_id)]}
        return pd.DataFrame(this_dict)

    @staticmethod
    def _parse_individual_game(game: BeautifulSoup) -> dict:
        game_dict = {}
        game_dict["BGGId"] = game["id"]
        game_dict["Name"] = game.find("name", type="primary")["value"]
        game_dict["Description"] = game.find("description").text
        game_dict["YearPublished"] = int(game.find("yearpublished")["value"])
        game_dict["MinPlayers"] = int(game.find("minplayers")["value"])
        game_dict["MaxPlayers"] = int(game.find("maxplayers")["value"])
        game_dict["AvgRating"] = float(game.find("average")["value"])
        game_dict["BayesAvgRating"] = float(game.find("bayesaverage")["value"])
        game_dict["StdDev"] = float(game.find("stddev")["value"])
        game_dict["NumOwned"] = int(game.find("owned")["value"])
        game_dict["NumWant"] = int(game.find("wanting")["value"])
        game_dict["NumWish"] = int(game.find("wishing")["value"])
        game_dict["NumWeightVotes"] = int(game.find("numweights")["value"])
        game_dict["GameWeight"] = float(game.find("averageweight")["value"])
        game_dict["ImagePath"] = game.find("image").text
        game_dict["MfgPlaytime"] = int(game.find("playingtime")["value"])
        game_dict["ComMinPlaytime"] = int(game.find("minplaytime")["value"])
        game_dict["ComMaxPlaytime"] = int(game.find("maxplaytime")["value"])
        game_dict["MfgAgeRec"] = int(game.find("minage")["value"])
        game_dict["NumUserRatings"] = int(game.find("usersrated")["value"])
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
        game_dict["ComAgeRec"] = BGGXMLParser.evaulate_poll(game,
            "User Suggested Player Age"
        )  # community age min poll
        game_dict["LanguageEase"] = BGGXMLParser.evaulate_poll(game,
            "Language Dependence"
        )  # Language Ease poll
        game_dict["BestPlayers"] = BGGXMLParser.evaulate_poll(game,
            "User Suggested Number of Players"
        )  # Best Players poll
        game_dict["ComMinPlaytime"] = BGGXMLParser.evaulate_poll(game,
            "User Suggested Play Time"
        )  # Community Min Playtime poll
        game_dict["ComMaxPlaytime"] = BGGXMLParser.evaulate_poll(game,
            "User Suggested Play Time"
        )  # Community Max Playtime poll
        for rank, score in BGGXMLParser.get_rank(game).items():
            game_dict[rank] = score
        game_dict["Family"] = BGGXMLParser.get_family(game)
        game_dict["Setting"] = BGGXMLParser.get_boardgame_family_attribute(game,"Setting:")
        game_dict["Theme"] = BGGXMLParser.get_boardgame_family_attribute(game,"Theme:")
        game_dict["Mechanism"] = BGGXMLParser.get_boardgame_family_attribute(game,
            "Mechanism:"
        )
        game_dict["Category"] = BGGXMLParser.get_boardgame_family_attribute(game,"Category:")
        game_dict["Kickstarted"] = (
            1 if BGGXMLParser.get_boardgame_family_attribute(game,"Crowdfunding") else 0
        )
        for component, value in BGGXMLParser.get_components(game).items():
            game_dict[component] = value
        for player, value in BGGXMLParser.get_player_counts(game).items():
            game_dict[player] = value

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
            f"Rank:{ item['name'] }": float(item["value"])
            for item in game.find_all("rank")
        }

    @staticmethod
    def get_game_data_from_page(
        game_page: BeautifulSoup, game_id: int, find_type_str: str
    ) -> pd.DataFrame:
        """
        Creates a dataframe to store attributes from a specified game id.

        Parameters:
        game_page: BeautifulSoup object
            The BeautifulSoup object containing the game page.
        game_id: int
            The id of the game.
        find_type_str: str
            The type of attribute to find.

        Returns:
        pd.DataFrame
            A dataframe containing the attributes of the specified type
        """

        # find all of the things on page
        all_this_type = game_page.find_all("link", type=find_type_str)

        # make dictionary for this item
        this_dict = {"BGGId": [game_id]}

        # add this item's things to dictionary
        for item in all_this_type:
            this_dict[item["value"]] = [1]

        # return dataframe
        return pd.DataFrame(this_dict)

    @staticmethod
    def get_game_mechanics(game_page: BeautifulSoup, game_id: int) -> pd.DataFrame:
        """
        Creates a dataframe to store the mechanics of a specified game id.  We create customer indicators for the
        specified mechanices.

        Parameters:
        game_page: BeautifulSoup object
            The BeautifulSoup object containing the game page.
        game_id: int
            The id of the game.

        Returns:
        pd.DataFrame
            A dataframe containing the mechanics of the specified game id
        """

        specific_mechanics = {
            "Mechanism: Legacy": "Legacy",
            "Mechanism: Tableau Building": "TableauBuilding",
        }

        # find all mechanics on page
        all_mechanics = game_page.find_all("link", type="boardgamemechanic")

        # make dictionary for this item
        mechanic = {"BGGId": [int(game_id)]}

        # add this item's mechanics to dictionary
        for item in all_mechanics:
            mechanic[item["value"]] = [1]

        # Try Tableau
        for search_name, indicator in specific_mechanics.items():
            try:
                game_page.find("link", type="boardgamefamily", value=(search_name))[
                    "value"
                ]
                mechanic[indicator] = [1]
            except:
                continue

        return pd.DataFrame(mechanic)

    @staticmethod
    def create_awards(awards_level: BeautifulSoup, game_id: int) -> pd.DataFrame:
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

        return pd.DataFrame(award)

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
    def get_family(game: BeautifulSoup) -> str:
        try:
            return (
                game.find("link", type="boardgamefamily", value=re.compile("Game:"))[
                    "value"
                ]
                .strip("Game:")
                .strip(" ")
            )
        except:
            try:
                return (
                    game.find(
                        "link", type="boardgamefamily", value=re.compile("Series:")
                    )["value"]
                    .strip("Series:")
                    .strip(" ")
                )
            except:
                return None


    @staticmethod
    def get_subcategories(game: BeautifulSoup, game_id: str) -> dict[str, int]:
        all_subcategories = game.find_all("link", type="boardgamecategory")

        # Create a dictionary for the new row
        subcategory = {"BGGId": [int(game_id)]}
        for item in all_subcategories:
            subcategory[item["value"]] = [1]
        return subcategory

    @staticmethod
    def get_player_counts(game: BeautifulSoup) -> dict:
        try:
            # Best and Good Players
            players = game.find(
                "poll", title="User Suggested Number of Players"
            ).find_all(
                "results"
            )  # get user players poll
            player_num_votes = int(
                game.find("poll", title="User Suggested Number of Players")[
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
        return {"BestPlayers": best_players, "GoodPlayers": good_players}

    @staticmethod
    def get_components(game: BeautifulSoup) -> dict:
        try:
            families = game.find_all(
                "link", type="boardgamefamily", value=re.compile("Component")
            )
            return {item["name"]: item["value"] for item in families}
        except:
            return {}

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

    # if games_dfs == []:
    #     continue
    # games = pd.concat(games_dfs)
    # designers = pd.concat(designers_dfs)
    # categories = pd.concat(categories_dfs)
    # mechanics = pd.concat(mechanics_dfs)
    # artists = pd.concat(artists_dfs)
    # publishers = pd.concat(publishers_dfs)
    # subcategories = pd.concat(subcategories_dfs)

    # games.to_pickle(f"data_dirty/pulled_games_processed/games{str(file_suffix)}.pkl")
    # designers.to_pickle(
    #     f"data_dirty/pulled_games_processed/designers{str(file_suffix)}.pkl"
    # )
    # categories.to_pickle(
    #     f"data_dirty/pulled_games_processed/categories{str(file_suffix)}.pkl"
    # )
    # mechanics.to_pickle(
    #     f"data_dirty/pulled_games_processed/mechanics{str(file_suffix)}.pkl"
    # )
    # artists.to_pickle(
    #     f"data_dirty/pulled_games_processed/artists{str(file_suffix)}.pkl"
    # )
    # publishers.to_pickle(
    #     f"data_dirty/pulled_games_processed/publishers{str(file_suffix)}.pkl"
    # )
    # subcategories.to_pickle(
    #     f"data_dirty/pulled_games_processed/subcategories{str(file_suffix)}.pkl"
    # )

if __name__ == "__main__":
    BGGXMLParser().parse_xml(filepath="data_dirty/pulled_games/raw_bgg_xml_0_20240707214127.xml")