import dash
import dash_daq as daq
from dash import Dash, html, dcc, dash_table
from dash.dash_table.Format import Format, Sign
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
from book_recom import recommend_books

# Sample DataFrame

df = pd.DataFrame({
    "Column1":[" "],
    "Column2":[" "],
})

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Button('Find Matches and Update Table Style', id='find-matches-button'),
    dash_table.DataTable(
        id='table',
        columns=[{"name": i, "id": i} for i in df.columns],
        data=[],
        style_data_conditional=[],  # Initialize with empty list
    ),
])


# Callback to find matches and update the DataTable style
@app.callback(
    Output('table', 'data'),
    Output('table', 'style_data_conditional'),
    Input('find-matches-button', 'n_clicks')
)
def update_table_style(n_clicks):
    if n_clicks is None:
        # Default empty style when the app starts
        return []
    
    data = {'Column1': ['apple', 'banana', 'cherry', 'apple', 'orange', 'grape'],
        'Column2': [1, 2, 3, 4, 5, 6]}
    df = pd.DataFrame(data)
    
    # The two lists of strings defined before the callback
    list1 = ['apple', 'cherry', 'banana', 'kiwi']
    list2 = ['banana', 'grape', 'kiwi', 'apple']

    # Find the matches between the two lists
    matches = list(set(list1) & set(list2))

    # Define the style for each match
    style_data_conditional = [
        {
            'if': {'filter_query': f'{{Column1}} contains "{match}"'},
            'backgroundColor': 'blue',
            'color': 'white'
        }
        for match in matches
    ]

    rec =df.to_dict('records')

    return rec, style_data_conditional

if __name__ == '__main__':
    app.run_server(debug=True)
