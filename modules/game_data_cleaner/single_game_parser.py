import json
import os
import re

import awswrangler as wr
import pandas as pd
from bs4 import BeautifulSoup

ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")
GAME_ATTRIBUTES = json.load(open(f"./modules/game_data_cleaner/find_config.json"))[
    "GAME_ATTRIBUTES"
]
MIN_USER_RATINGS = 30


class GameEntryParser:
    def __init__(self, game_entry: BeautifulSoup = None) -> None:
        self.game_entry = game_entry
        self.game_base_attributes = {}
        self.subcategories = {}
        self.designers = {}
        self.categories = {}
        self.mechanics = {}
        self.artists = {}
        self.publishers = {}
        self.expansions = {}

    def check_rating_count_threshold(
        self,
    ) -> bool:
        """Check if the game has enough ratings ratings to be considered"""
        user_ratings = int(self.find_thing_in_soup("usersrated"))

        if user_ratings < MIN_USER_RATINGS:
            return False
        return True

    def parse_individual_game(self) -> dict:
        """Parse the individual game data"""
        self._parse_unique_elements()
        self._parse_config_elements()
        self._parse_poll_items()
        self._parse_family_attributes()
        self._create_game_data()

    def get_single_game_attributes(self) -> tuple[dict]:
        """Return the game data and ancillary data"""
        return (
            self.game_base_attributes,
            self.subcategories,
            self.designers,
            self.categories,
            self.mechanics,
            self.artists,
            self.publishers,
            self.expansions,
        )

    def _parse_unique_elements(self) -> dict:
        """Parse the unique elements of the game
        This includes the BGGId, name, description, image path, number of alternates, expansions, implementations,
        """
        self.game_base_attributes["BGGId"] = self.game_entry["id"]
        self.game_base_attributes["Name"] = self.game_entry.find(
            "name", type="primary"
        )["value"]
        self.game_base_attributes["Description"] = self.game_entry.find(
            "description"
        ).text

        # evaluate self.game_entry.find("image").text if it exists, otherwise set to "None"
        if self.game_entry.find("image") is None:
            self.game_base_attributes["ImagePath"] = "None"
        else:
            self.game_base_attributes["ImagePath"] = self.game_entry.find("image").text

        self.game_base_attributes["NumAlternates"] = len(
            self.game_entry.find_all("name", type="alternate")
        )
        self.game_base_attributes["NumExpansions"] = len(
            self.game_entry.find_all("link", type="boardgameexpansion")
        )
        self.game_base_attributes["NumImplementations"] = len(
            self.game_entry.find_all("link", type="boardgameimplementation")
        )
        self.game_base_attributes["IsReimplementation"] = (
            1
            if self.game_entry.find(
                "link", type="boardgameimplementation", inbound="true"
            )
            else 0
        )
        for rank, score in self._get_rank().items():
            if rank not in [
                "rpgitem",
                "boardgameaccessory",
                "videogame",
                "amiga",
                "commodore64",
                "arcade",
                "atarist",
            ]:
                self.game_base_attributes[rank] = score
        for component, value in self._get_components().items():
            self.game_base_attributes[component] = value
        for player, value in self._get_player_counts().items():
            self.game_base_attributes[player] = value

    def _parse_config_elements(self) -> dict:
        """Parse the configuration elements of the game
        This includes the year published, min and max players, min and max playtime, and min and max age.
        """
        for key, attributes in GAME_ATTRIBUTES.items():
            self.game_base_attributes[key] = self.find_thing_in_soup(
                attributes["find_item"]
            )

    def find_thing_in_soup(self, find_type_str: str) -> str:
        """Find a specific item in the soup"""
        return self.game_entry.find(find_type_str)["value"]

    def _parse_poll_items(self) -> dict:
        """Parse the poll items of the game
        This includes the ratings suggested player age, language dependence, best players, and play time.
        """
        self.game_base_attributes["ComAgeRec"] = self.evaulate_poll(
            "User Suggested Player Age"
        )  # community age min poll
        self.game_base_attributes["LanguageEase"] = self.evaulate_poll(
            "Language Dependence"
        )  # Language Ease poll
        self.game_base_attributes["BestPlayers"] = self.evaulate_poll(
            "User Suggested Number of Players"
        )  # Best Players poll
        # self.game_base_attributes["ComMinPlaytime"] = self.evaulate_poll(
        #     "User Suggested Play Time"
        # )  # Community Min Playtime poll
        # self.game_base_attributes["ComMaxPlaytime"] = self.evaulate_poll(
        #     "User Suggested Play Time"
        # )  # Community Max Playtime poll

    def _parse_family_attributes(self) -> dict:
        """Parse the family attributes of the game
        This includes the family, setting, theme, mechanism, category, and kickstarted attributes.
        """
        self.game_base_attributes["Family"] = self.get_family()
        self.game_base_attributes["Setting"] = self.get_boardgame_family_attribute(
            "Setting:"
        )
        self.game_base_attributes["Theme"] = self.get_boardgame_family_attribute(
            "Theme:"
        )
        self.game_base_attributes["Mechanism"] = self.get_boardgame_family_attribute(
            "Mechanism:"
        )
        self.game_base_attributes["Category"] = self.get_boardgame_family_attribute(
            "Category:"
        )
        self.game_base_attributes["Kickstarted"] = (
            1 if self.get_boardgame_family_attribute("Crowdfunding") else 0
        )

    def _get_rank(self) -> dict:
        """Returns all possible rank types of a game.
        Possible types may include family (e.g. thematic, strategygames),
        overall (coded as 'boardgame'), etc.
        """
        return {
            f"Rank:{item['name']}": item.get("value", 999999.0)
            for item in self.game_entry.find_all("rank")
        }

    def evaulate_poll(self, poll_title: str):
        """Attempts to evaluate a poll item from the game entry."""

        NUMVOTES_TAG = "numvotes"
        # poll_result = None

        poll = self.game_entry.find("poll", title=poll_title)

        if not poll:
            return None

        poll_results = poll.find_all("results")

        if not poll_results:
            return None

        if len(poll_results) == 1:
            results = {
                item["value"]: int(item[NUMVOTES_TAG])
                for item in poll.find_all("result")
            }
            if not len(results):
                return None

            # give the value from results with the most number of item[NUMVOTES_TAG]
            poll_result = max(results, key=results.get)

        elif len(poll_results) > 1:
            # Define the scoring values
            scoring = {"Best": 1, "Recommended": 0.5, "Not Recommended": 0}

            # Initialize variables to track the best numplayers and its score
            poll_result = None
            highest_score = -1

            # Iterate through all <results> tags
            for result in poll_results:
                numplayers = result.get("numplayers")

                # Calculate the score for this numplayers option
                score = sum(
                    int(r["numvotes"]) * scoring[r["value"]]
                    for r in result.find_all("result")
                )

                # Update if this score is the highest
                if score > highest_score:
                    highest_score = score
                    poll_result = numplayers

        return poll_result

    def get_family(self) -> str:
        """Returns the family of a game."""
        family = self.game_entry.find(
            "link", type="boardgamefamily", value=re.compile("Game:")
        )
        if family is not None:
            return (
                self.game_entry.find(
                    "link", type="boardgamefamily", value=re.compile("Game:")
                )["value"]
                .strip("Game:")
                .strip(" ")
            )
        family_series = self.game_entry.find(
            "link", type="boardgamefamily", value=re.compile("Series:")
        )
        if family_series is not None:
            return (
                self.game_entry.find(
                    "link", type="boardgamefamily", value=re.compile("Series:")
                )["value"]
                .strip("Series:")
                .strip(" ")
            )
        return None

    def get_boardgame_family_attribute(self, attribute: str) -> str:
        """Returns a specific attribute of a game family."""

        found_attribute = self.game_entry.find(
            "link", type="boardgamefamily", value=re.compile(attribute)
        )
        if found_attribute is None:
            return None
        return found_attribute["value"].strip(attribute).strip(" ")

    def _get_player_counts(self) -> dict:
        """Returns the best and good player counts for a game.
        Best players are defined as the number of players that have the most votes for best and recommended.
        """
        # Best and Good Players
        players = self.game_entry.find(
            "poll", title="User Suggested Number of Players"
        ).find_all(
            "results"
        )  # get ratings players poll
        player_num_votes = int(
            self.game_entry.find("poll", title="User Suggested Number of Players")[
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
        return {"BestPlayers": best_players, "GoodPlayers": good_players}

    def _get_components(self) -> dict:
        """Returns the components of a game.
        Components may include dice, cards, and board.

        Returns:
            dict"""
        families = self.game_entry.find_all(
            "link", type="boardgamefamily", value=re.compile("Component")
        )
        if families is None:
            return {}

        return {item.get("name", None): item.get("value") for item in families}

    def _create_game_data(self):
        """
        Creates a dataframe to store the game data of a specified game id.
        Also creates ancillary datasets (as dictionaries) for the non-core game data.
        """

        game_id = self.game_entry["id"]

        self.subcategories = self.get_subcategories(game_id)

        # create specialty dataframes
        self.designers = self.create_thing_of_type(
            game_id, find_type_str="boardgamedesigner"
        )
        self.categories = self.create_thing_of_type(
            game_id, find_type_str="boardgamecategory"
        )
        self.mechanics = self.get_game_mechanics(game_id)
        self.artists = self.create_thing_of_type(
            game_id, find_type_str="boardgameartist"
        )
        self.publishers = self.create_thing_of_type(
            game_id, find_type_str="boardgamepublisher"
        )

        self.expansions = self.create_thing_of_type(
            game_id, find_type_str="boardgameexpansion"
        )

    def create_thing_of_type(self, game_id: str, find_type_str: str) -> dict[str, list]:
        """Create DataFrame for things for a specific game id.
        The ratings can pass a find_type_str to get the specific type of thing they want.
        The function will search for that as a link type in the game_entry.

        Parameters:
        game_id: str
            The id of the game.
        find_type_str: str
            The type of thing to search for in the game_entry.

        Returns:
        dict[str, list]
            A dictionary containing the things of the specified game id.  The id is repeated for each thing.
        """
        items = self.game_entry.find_all("link", type=find_type_str)
        return {
            "BGGId": [int(game_id) for _ in range(len(items))],
            find_type_str: [item["value"] for item in items],
        }

    def get_game_mechanics(self, game_id: int) -> dict[str, list]:
        """
        Creates a dataframe to store the mechanics of a specified game id.  We create customer indicators for the
        specified mechanices.

        Parameters:
        self.game_entry: BeautifulSoup object
            The BeautifulSoup object containing the game page.
        game_id: int
            The id of the game.

        Returns:
        dict[str, list]
            A dictionary containing the mechanics of the specified game id.  The id is repeated for each mechanic.
        """

        # find all mechanics on page
        all_mechanics = self.game_entry.find_all("link", type="boardgamemechanic")
        specific_mechanics = {
            "Mechanism: Legacy": "Legacy",
            "Mechanism: Tableau Building": "TableauBuilding",
        }

        all_mechanics = [item["value"] for item in all_mechanics]

        # Try Specifc Mechanics
        for search_name, indicator in specific_mechanics.items():
            element = self.game_entry.find(
                "link", type="boardgamefamily", value=(search_name)
            )
            if element:
                all_mechanics.append(indicator)

        return {
            "BGGId": [int(game_id) for _ in range(len(all_mechanics))],
            "mechanic": all_mechanics,
        }

    def create_awards(
        self, awards_level: BeautifulSoup, game_id: int
    ) -> dict[str, list]:
        """
        Creates a dataframe to store the awards of a specified game id.

        Parameters:
        awards_level: BeautifulSoup object
            The BeautifulSoup object containing the awards page.
        game_id: int
            The id of the game.

        Returns:
        dict[str, list]
            A dictionary containing the awards of the specified game id.  The id is repeated for each award.
        """

        # find all awards on page
        all_awards = awards_level.find_all("a", class_="ng-binding")

        return {
            "BGGId": [game_id for _ in range(len(all_awards))],
            "award": [re.sub("[0-9]", "", item.text).strip(" ") for item in all_awards],
        }

    def get_subcategories(self, game_id: str) -> dict[str, list]:
        """Get the subcategories of a game.

        Parameters:
        game_id: str
            The id of the game.

        Returns:
        dict[str, list]
            A dictionary containing the subcategories of the specified game id.  The id is repeated for each subcategory.
        """
        all_subcategories = self.game_entry.find_all("link", type="boardgamecategory")

        return {
            "BGGId": [game_id for _ in range(len(all_subcategories))],
            "subcategory": [item["value"] for item in all_subcategories],
        }
