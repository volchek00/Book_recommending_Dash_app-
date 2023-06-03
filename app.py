import dash
from dash import html, dcc, dash_table
from dash.dash_table.Format import Format, Sign
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
from book_recom import recommend_books
import requests
import json

empty_first_table = pd.DataFrame({
    "RECOMMENDED BOOKS":[" "],
})

empty_second_table = pd.DataFrame({
    "BOOK DESCRIPTION":[" "],
})

style_data_conditional = []

first_table = dash_table.DataTable(
    id='dash_first_table',
    data=[],
    columns = [{"id": col, "name": col} for col in empty_first_table.columns],
    style_table={
        'width': '100%',
        'margin': '0 auto',
        'fontFamily': 'Open Sans',
    },
    
    style_cell={
        'textAlign': 'center',
        'fontFamily': 'Open Sans',
        'fontSize': '20px',
        'color': "#2c3e50",
        'whiteSpace': 'normal',
        'overflow': 'hidden',
        'textOverflow': 'ellipsis'
    },
    style_data_conditional=[],
    style_header={
        'backgroundColor': '#4CAF50',
        'fontWeight': 'bold',
        'color': 'white',
    },
    selected_rows=[],
    row_selectable='single',
)

second_table = dash_table.DataTable(
    id='dash_second_table',
    data=[],
    columns = [{"id": col, "name": col} for col in empty_second_table.columns],
    style_table={
        'width': '100%',
        'margin': '0 auto',
        'fontFamily': 'Open Sans',
    },
    style_cell={
        'textAlign': 'center',
        'fontFamily': 'Open Sans',
        'fontSize': '20px',
        'color': "#2c3e50",
        'whiteSpace': 'normal',
        'overflow': 'hidden',
        'textOverflow': 'ellipsis'
    },   
        style_header={
        'backgroundColor': '#4CAF50',
        'fontWeight': 'bold',
        'color': 'white',
    }, 
),

external_stylesheets = ['assets/style.css']
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = dbc.Container([
    # div for header and div_2
    html.Div([
        html.H1("The SHELFIE", className='h1'),
        html.H2("what you should read next", className='h2'),
        # html.Br(),
        # html.H4("Please, fill in the following information:", className='h4'),
    ],
    className='div_1'),

    # div_2 for inputs, button and input boxes
    html.Div([
        html.Div([
            html.Label('A book You like: ', className='label'),
            dcc.Input(id='input-book', type='text', value='', className='input-box'),
        ],
        className = "input_1"),
        html.Div([
            html.Label('Your home country: ', className='label'),
            dcc.Input(id='input-country', type='text', value='', className='input-box'),
        ],
        className = "input_2"),
        html.Div([
            html.Label('Your age: ', className='label'),
            dcc.Input(id='input-age', type='number', value='', className='input-box'),
        ],
        className = "input_3"),
        html.Div([
            html.Button('Submit', id='submit-button', n_clicks=0, className='submit-button'),
        ],
        className = "input_4"),
        html.Br(),
    ],
    className='div_2'),
    html.Div(id = "div_users_amount", className='h3'),


    html.Div([
        html.Div(
            second_table,
            className="table2",
            id = "hidden_div",
            style={'display': 'none'},
        ),
        html.Div(
            html.Div(
                first_table,
                className="table1",
            ),
        ),
    ],
    className='div_3', 
    id = "div_3", 
    style = {'display': 'none'}),
],
className='container')

# Define the callback function
@app.callback(
    Output('dash_first_table', 'data'),
    Output('dash_first_table', 'style_data_conditional'),
    Output('div_users_amount', 'children'),
    Output('div_3', 'style'),
    Input('submit-button', 'n_clicks'),
    State('input-book', 'value'),
    State('input-country', 'value'),
    State('input-age', 'value'),
    prevent_initial_call=True,
)
def update_output_table(n_clicks, input_book, input_country, input_age):
    """
    Updates rows of the first table with the recommended books, 
    highlights the rows where the recommended book is also in the similar users' books
    and displays the amount of similar users.
    """
    style_data_conditional = []
    users_amount_text = ''
    
    if (n_clicks > 0) and input_book:
        # Call the recommendation system with the user input parameters
        top_books, similar_users_books, similar_users_amount = recommend_books(input_book, input_country, input_age)
        print(f"callback similar users are: {similar_users_books}")
        # Create a new DataFrame with a single column called "Recommended Books"
        df = pd.DataFrame({
            "RECOMMENDED BOOKS": top_books,
        })

        # Highlight rows where the recommended book is also in the similar users' books
        matches = list(set(top_books) & set(similar_users_books))

        if len(matches) > 0:
            # Define the style for each match
            style_data_conditional = [
                {
                    'if': {'filter_query': f'{{RECOMMENDED BOOKS}} contains "{match}"'},
                    'backgroundColor': '#4CAF50',
                    'color': 'white'
                }
                for match in matches
            ]
            print(f"matches are: {matches}")
        else:
            print("No matches")

        recommended_books_list = df.to_dict('records')

        # if input_country is not None or input_age is not None:
        if similar_users_amount > 0:
            users_amount_text  = 'Another "{}" user(s) from my database read the book you put in. The user(s) enjoyed other books that are in green cells bellow'.format(similar_users_amount)
        else:
            users_amount_text = "I have noticed you did not fill in your country or age. Fill them in to get more accurate recommendations."

    return recommended_books_list, style_data_conditional, users_amount_text, {'display': 'block'}


# Define the callback function
@app.callback(
    Output('dash_second_table', 'data'),
    Input('dash_first_table', 'selected_rows'),
    State('dash_first_table', 'data'),
    # State('input-book', 'value'),
    # State('input-country', 'value'),
    # State('input-age', 'value'),
    prevent_initial_call=True,
)
def update_description(chosen_rows, data):
    """
    selects the row of the first table and displays the description of the book in the second table
    """
    table_data = []
    if chosen_rows is not None:
        print(f"Chosen rows are: {chosen_rows}")
        # Retrieve the data of the selected row
        selected_row_data = data[chosen_rows[0]]
        print(f"Selected row data is: {selected_row_data}")

        with open("C:/Users/vaclp/Desktop/Projects/books/data_temporary/book_isbns.json", "r") as f:
            book_isbns = json.load(f)

        # Search for the ISBN value of the selected book title
        selected_book_isbn = None
        for book_title, isbn in book_isbns.items():
            if selected_row_data['RECOMMENDED BOOKS'] == book_title:
                selected_book_isbn = isbn
                print(f"selected_book_isbn is: {selected_book_isbn}")
                break

        description = 'Unfortunately, no book description for this book is  available!'
        try:
            # scrape the book description from the Google Books API
            url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{selected_book_isbn}&key=AIzaSyCcWHzAiivlklQRoxUuw-5XTvp6QxSG6TM'
            # url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{selected_book_isbn}&key=AIzaSyCUkW3cWIVr4oEBzp78iSaxtYxZpqsbSdI'
            print(f"url is {url}")
            response = requests.get(url)
            data = response.json()
            if 'items' in data and data['items']:
                book = data['items'][0]['volumeInfo']
                description = book.get('description', 'N/A')
                print(f"description is: {description}")
        except:
            pass

        # Create a new DataFrame with a single column called "Book Description"
        df = pd.DataFrame({
            "BOOK DESCRIPTION": [description],
        })
        
        table_data = df.to_dict('records')

    # Return the Dash table component
    return table_data


@app.callback(
    Output('hidden_div', 'style'),
    Input('dash_first_table', 'selected_rows'),
    prevent_initial_call=True,
)
def reveal_table(chosen_rows):
    """
    reveals the second table when a row of the first table is selected
    """
    if chosen_rows is not None:
        return  {'display': 'block'}
    else:
        return  {'display': 'none'}


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
