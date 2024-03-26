import sys
from utils.game_data_scraper import scrape_urls_file

if __name__ == "__main__":
    task = sys.argv[1]
    group = sys.argv[2]
    print(group)
    print("Task Successfully launched!")

    if task == "scrape_games":
        scrape_urls_file()
