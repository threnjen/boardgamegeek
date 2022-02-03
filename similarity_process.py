import pandas as pd
import numpy as np
import numba as nb
import time
import gc
import copy
import json
from statistics import mean

from numba import jit, cuda, prange, typeof, typed, types
from numpy.linalg import norm

from multiprocessing import Pool, Manager

# ignore warnings (gets rid of Pandas copy warnings)
import warnings
warnings.filterwarnings('ignore')
pd.options.display.max_columns = None

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)

from sklearn.preprocessing import MinMaxScaler, normalize

import tensorflow as tf
from tensorflow.compat.v1.losses import cosine_distance
from tensorflow.keras.losses import CosineSimilarity

    
@jit(nopython=True, parallel=True, fastmath=True)
def math_function(game):
    
    results = []
    
    # make the single user matrix for the one user
    single_item = matrix_array[:, game].copy()
    # get the indices where the user is nonzero
    indices = np.nonzero(single_item)[0]
    
    for game2 in all_games:
    
        next_item = matrix_array[:, game2].copy()
        indices2 = np.nonzero(next_item)[0]
            
        common_indices = np.intersect1d(indices, indices2)
        
        if len(common_indices)<4:
            results.append(0)
            continue      
        
        else:
            a = single_item[common_indices].astype(np.float32)
            b = next_item[common_indices].astype(np.float32)
        
            try:
                item_similarity = a @ b.T / (norm(a)*norm(b))
                results.append(item_similarity)
            except:
                results.append(0)
        
    return results
    
def process_block(x):
    
    print("starting block"+str(x))
    start = x
    end = x+3667
    
    if end > len(gameids_columnorder):
      end = len(gameids_columnorder)
    
    #block_start = time.time()
    
    this_block_storage = {}
       
    for game in np.arange(start, end, 1):
    
        print("\nStarting game: "+str(game))
        start = time.time()
    
        gameid_1 = gameids_columnorder[game]
                     
        results = math_function(game)
    
        this_block_storage[gameid_1] = results
    
        end=time.time()
    
        print(end-start)

    #print(time.time()-block_start)
    return this_block_storage

def run_pool():

  values = np.arange(0,22000,3667)
  pool = Pool(6)
  results = pool.map(process_block, values)
  
  # save dictionary
  with open('item_similarities_raw/synthetic_2000_user_ratings_similarities.json', 'w') as convert_file:
      convert_file.write(json.dumps(results))
  
  pool.close()
  

global_start = time.time()

# the basic file required for this work - the full matrix

larger_matrix = pd.read_pickle('synthetic_ratings/users_synthetic_2000_fullmatrix.pkl')


gameids_columnorder = list(larger_matrix.columns)


# convert full matrix to numpy and delete matrix

matrix_array = larger_matrix.to_numpy()


del larger_matrix
gc.collect()

all_games = np.arange(0, matrix_array.shape[1], 1)

#games_range = len(all_games[:100])
 

if __name__ == '__main__':
  run_pool()
  print("\n\n"+str(time.time()-global_start))






