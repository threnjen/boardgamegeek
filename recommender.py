import easygui as eg
import pandas as pd
import numpy as np
import regex as re

sims_byname = pd.read_pickle('data_cleaned_new_scraper/game_cosine_similarity_byname.pkl')

while True:
  game = eg.enterbox("Enter game name here\nCaps and punctuation don't matter.", 'Enter Game Here')
  
  if game:
    
    game = game.lower()
    game = re.sub('[^A-Za-z0-9\s]+', '', game)
    print(game)
  
    try:
    # test specific games here
      results =  pd.DataFrame(data={'Similarity': sims_byname[game].sort_values(ascending=False)[0:31]})
      results.index = results.index.str.title()
      eg.msgbox(results,'Press OK to enter another game')
    except:
      eg.msgbox("No game found...\n"+
        "There may be more than one game with this name (I didn't account for that)"+
        '\nPress OK to try another game, another spelling, etc.',
        'Try again!')
  
  else: pass