import pandas as pd
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import difflib
import matplotlib as plt
import plotly.io as pio
from fuzzywuzzy import process
pio.renderers
import requests
import json


def recommend_books(book, country, age):
    # DATA PREPROCESSING
    users = pd.read_csv('data_raw/BX-Users.csv', sep=';', on_bad_lines='skip', encoding="latin-1")
    books = pd.read_csv('data_raw/BX-Books.csv', sep=';', on_bad_lines='skip', encoding="latin-1")
    ratings = pd.read_csv('data_raw/BX-Book-Ratings.csv', sep=';', on_bad_lines='skip', encoding="latin-1")

    # filter and rename columns
    users.rename(columns = {'User-ID':'user_id', 'Location':'location', 'Age':'age'}, inplace = True)
    ratings.rename(columns = {'User-ID':'user_id', 'Book-Rating':'rating'}, inplace = True)
    books = books[['ISBN', 'Book-Title', 'Book-Author', 'Year-Of-Publication', 'Publisher']]
    books.rename(columns = {'Book-Title':'title', 'Book-Author':'author', 'Year-Of-Publication':'year', 'Publisher':'publisher'}, inplace = True)
    books.dropna(inplace=True)
    # create title:isbn dict in json 
    book_dict = dict(zip(books['title'], books['ISBN']))
    with open('C:/Users/vaclp/Desktop/Projects/books/data_temporary/book_isbns.json', 'w') as f:
        json.dump(book_dict, f)

    # USERS:
    # replace NaN in users.age with median age:
    median_age = users['age'].median()
    users['age'].fillna(median_age, inplace=True)
    print(f"users before filters: {users.shape}")

    similar_users = []
    countrymen = []

    # USER INPUTS - looking for users who are from the same country and have similar age:
    if age:    
        age = int(age)
        age_min = age - 10
        age_max = age + 10
        age_filtered_users = users[(users['age'] >= age_min) & (users['age'] <= age_max)]
        similar_users = age_filtered_users['user_id'].tolist()
        # print(f"similar users after age: {len(similar_users)}")

    if country:
        country = country.lower()
        country_filtered_users = users[users['location'].str.lower().str.contains(country)]
        countrymen = country_filtered_users['user_id'].tolist()
        # print(f"users from the same country: {len(countrymen)}")

    if similar_users and countrymen:
        similar_users = list(set(similar_users).intersection(set(countrymen)))
    elif countrymen:
        similar_users = countrymen

    if not similar_users:
        print("No users found for given criteria")
        
    # print(f"countrymen with similar age : {len(similar_users)}")

    # RATINGS 
    user_ratings_count = ratings.groupby('user_id')['rating'].count()
    user_ratings_count_sorted = user_ratings_count.sort_values(ascending=True)
    high_ratings_users = user_ratings_count_sorted[user_ratings_count_sorted >= 15]
    ratings_final = ratings[ratings['user_id'].isin(high_ratings_users.index)]

    # BOOKS:
 
    books.dropna(inplace=True)
    book_ratings_count = ratings_final['ISBN'].value_counts()
    isbn_less_than_50 = book_ratings_count[book_ratings_count < 30].index.tolist()
    books = books[~books['ISBN'].isin(isbn_less_than_50)]
    # print(book_ratings_count[book_ratings_count < 30 and book_ratings_count.iloc("050552354X")])
    book_ratings_count.plot.bar()



    # merge ratings and books dfs on ISBN:
    ratings_and_books_merged = pd.concat([ratings_final, books], axis = 1, join='inner')
    ratings_and_books_merged.drop_duplicates(subset=['user_id', 'ISBN'], inplace = True)

    # Create a pivot table with user_id as index, book titles as columns, and rating as values
    books_pivot_table = ratings_and_books_merged.pivot_table(columns='title', index='user_id', values="rating")
    books_pivot_table.fillna(0, inplace=True)
    # ________________________________________________________________________________________________________

    # BOOK RECOMMENDATION:
    # user inputs
    input_book = book.lower()

    # Is user book input spelled correctly? if not, find closest match with fuzzywuzzy
    if input_book in books_pivot_table.columns:
        book_user_read = input_book
        print("FOUND: book you like is in the database")
    else:
        matches = process.extract(input_book, books_pivot_table.columns)
        book_user_read = matches[0][0]

    # print(f"This is the book user likes: {book_user_read}")
    # print(f"pivot table shape (rows:users, columns:titles): {books_pivot_table.shape}")
    # list of the users who read the input book too
    users_who_read_book = books_pivot_table[book_user_read][books_pivot_table[book_user_read]>0].index.tolist()
    # print(f"users who read the input book: {users_who_read_book}")
    similar_users_books = []
    similar_users_amount = 0

    # check if users who read the input book are in similar_users list
    users_who_read_book_in_similar_users = list(set(users_who_read_book).intersection(set(similar_users)))
    if users_who_read_book_in_similar_users:
        similar_users_amount = len(users_who_read_book_in_similar_users)
        # print(f"{similar_users_amount} similar users who read the input book found: {users_who_read_book_in_similar_users}")
        for similar_user_id in users_who_read_book_in_similar_users:
            books_read_by_similar_user = ratings_and_books_merged.loc[ratings_and_books_merged['user_id'] == similar_user_id]['title'].tolist()
            books_ranking_by_similar_user = ratings_and_books_merged.loc[ratings_and_books_merged['user_id'] == similar_user_id][['title', 'rating']].set_index('title')['rating'].to_dict()
            books_ranking_by_similar_user = {book_title: book_ranking for book_title, book_ranking in books_ranking_by_similar_user.items() if book_ranking >= 6}  
            # Remove input book from the dictionary
            del books_ranking_by_similar_user[book_user_read]
            # Add books read by the user to the similar_users_books list
            similar_users_books.extend(books_read_by_similar_user)
    else:
        print("No similar user found")

    # WHAT OTHER BOOKS READ THE USERS WHO READ THE INPUT BOOK?
    # create a subset of the pivot table with the users who read the book
    users_subset = books_pivot_table.loc[users_who_read_book, :]
    # calculate the sum of ratings for each book across all users
    book_rankings = users_subset.sum(axis=0)
    # create a dictionary of book titles and their user rankings
    book_rankings_dict = dict(book_rankings)
    # remove the input book from the dictionary
    del book_rankings_dict[book_user_read]
    # sort the dictionary by values in descending order
    book_rankings_dict = dict(sorted(book_rankings_dict.items(), key=lambda item: item[1], reverse=True))
    # put top 100 books (by ranking) in a list, but just keys

    top_books = []
    isbn_list = []
    count = 0
    # recommending best 200 books with ranking higher than 5
    for book, ranking in book_rankings_dict.items():
        if count == 200:
            break
        if ranking >= 6:
            top_books.append(book)
            isbn = books[books['title'] == book]['ISBN'].iloc[0]
            isbn_list.append(isbn)
            count += 1
    # print(f"top books: {len(top_books)}")

    # save isbn_list to a file
    with open("C:/Users/vaclp/Desktop/Projects/books/data_temporary/isbn_list.json", "w") as f:
        json.dump(isbn_list, f)

    # save book_rankings_dict to a file
    with open("C:/Users/vaclp/Desktop/Projects/books/data_temporary/book_rankings_dict.json", "w") as f:
        json.dump(book_rankings_dict, f)

    # print(f"similar users amount: {similar_users_amount}")
                
    return top_books, similar_users_books, similar_users_amount



