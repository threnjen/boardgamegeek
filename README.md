# BoardGameGeek Games Recommender System

By: Jen Wadkins

## Introduction

> This notebook series takes us through the entire process of sourcing, cleaning, exploring, and modeling user and game data from BoardGameGeek. The end product is a hybrid recommender system which leverages content-based similarities to support and strengthen a collaborative filtering system. The end system can be presented in one of two ways: For the new user, a cold-start protocol and memory-based collaborative filter are applied in a few seconds, and ratings are produced. For the returning user, model-based collaborative filtering in conjunction with the memory-based filter provide deeper recommendations.

> Content recommenders only work if the data are kept relevant and updated. To that end, I've developed a plan which will allow maintenance of the system at the lowest computational cost, while allowing the system to be available to make recommendations at all times to new users.


## Skills Presented

* Web Scraping
* API usage
* Data Cleaning
* Exploratory Data Analyis
* Data Visualization
* Feature Selection and Engineering
* Content-Based Filtering
* Collaborative Filtering with Statistical Methods and Surprise

## Business Objective and Questions

#### Business Objective

Build a content recommender for BoardGameGeek with a goal of addressing problems that are both common to recommenders in general, and specific to BGG: 
    
    * Establish content recommender - cost of acquiring and maintaining data
    * Cold Start problems where new users and items are not a part of the system
    * Sparse matrix issue where in a system with lots of items, not many are rated by a subset of users, making neighbors difficult to identify
    * BGG specific problem: Reimplementatons/reskins of games result in separated user profiles when they should be similar
    * Deal with computational cost/time limitations when issuing recommendations


#### Questions/Intentions

We will address and solve these problems in building a content recommender for this system:

    * Plan for fast data acquisition and cleaning to allowing frequent system updates
    * Address Cold Start problem with a specific new user plan
    * Overcome the sparse matrix problem with synthetic content-based data
    * Overcome the BGG-specific problem with synthetic content-based data
    * Deal with computational cost by offering on-the-fly recommendations in addition to daily model update

## Methodology

We use the OSEMN for Data Science to organize the project.
* Obtain Data: Source data from BoardGameGeek
* Scrubbing/Cleaning Data: Clean and prepare data for model processing
* Exploring/Visualizing the Data: Perform EDA on data
* Model: Iteratively explore different models
* Analysis: Analyze and explain results


# Table of Contents


#### [BGG01_Obtaining_Primary.ipynb](https://github.com/threnjen/boardgamegeek/blob/main/BGG01_Obtaining_Primary.ipynb)

* **Project Overview**

* **Obtaining Our Data**

* **Cleaning Our Data**

* **Visualizing Our Data**

* **Standard Models**

* **Neural Networks**

* **Ensembling**
    
* **Analysis**

* **APPENDIX**

#### [BGG02_Obtaining_UserID.ipynb](https://github.com/threnjen/boardgamegeek/blob/main/BGG02_Obtaining_UserID.ipynb)

#### [BGG03_Scrubbing-Cleaning.ipynb](https://github.com/threnjen/boardgamegeek/blob/main/BGG03_Scrubbing-Cleaning.ipynb)

#### [BGG04_EDA.ipynb](https://github.com/threnjen/boardgamegeek/blob/main/BGG04_EDA.ipynb)

#### [BGG05_Content_Based.ipynb](https://github.com/threnjen/boardgamegeek/blob/main/BGG05_Content_Based.ipynb)

#### [BGG06_Synthetic_Ratings.ipynb](https://github.com/threnjen/boardgamegeek/blob/main/BGG06_Synthetic_Ratings.ipynb)

#### [BGG07_Build_Datasets.ipynb](https://github.com/threnjen/boardgamegeek/blob/main/BGG07_Build_Datasets.ipynb)

#### [BGG08_Collaborative_Filtering.ipynb](https://github.com/threnjen/boardgamegeek/blob/main/BGG08_Collaborative_Filtering.ipynb)





## Analysis

> xxx

![map of model ensembling](images/stack_map.png)

##### xxx?

> xxx

![price per square foot](images/price_sf.png)


##### xxx?

> xxx

![important words](images/listing_words.png)


##### xxx?

> xxx

##### xxx?

> xxx

##### xxx?

> xxx



## Future Work

* xxx


* xxx


* xxx


* xxx


## Presentation
[Video - Data Science Module 4 Project](https://www.youtube.com/watch?v=y9XZ5QLS2dU&ab_channel=JennyWadkins)

[PDF of Presentation](https://github.com/threnjen/austin_housing_prices/blob/main/mod_4_pdf/Austin_Housing_Study.pdf)
