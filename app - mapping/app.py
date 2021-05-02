import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import os
import psycopg2
import datetime
import settings2
import re
from io import BytesIO
import base64
from wordcloud import WordCloud
from nltk.stem import WordNetLemmatizer
import numpy as np
from collections import Counter
import gc


# create app and layout
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'Predicting and Mapping Protests'

server = app.server


app.layout = html.Div(children=[
    html.H2('Predicting and Mapping Protests', style={
            'textAlign': 'center'
        }),
    html.H4('CS Capstone Project by Lindsay Hardy and Samantha Rothman', style={
        'textAlign': 'center'
    }),
        
    html.Div(id='live-update-graph'),
    html.Div(id='live-update-hashtags'),
    
    html.Div(
        className='row',
        children=[
            dcc.Markdown("Most Common Words in Tweets Classified as Protests:"),
        ],style={'width': '35%', 'marginLeft': 70}
    ),
    html.Br(),
    
    html.Br(),
    html.Div(html.Img(id="us-cloud")),
    
    html.Br(),
        
    dcc.Interval(
        id='interval-component-slow',
        interval=1*120000, # 2 min in milliseconds
        max_intervals = 1,
        #n_intervals=0
        )
    ], style={'padding': '20px'})



def preprocess(tweet):
    """function to clean text for word cloud"""
    # remove links
    tweet = re.sub(r'http\S+', '', tweet)
    # remove mentions
    tweet = re.sub("@\w+","",tweet)
    # alphanumeric and hashtags
    tweet = re.sub("[^a-zA-Z#]"," ",tweet)
    # remove multiple spaces
    tweet = re.sub("\s+"," ",tweet)
    tweet = tweet.lower()
    # Lemmatize
    lemmatizer = WordNetLemmatizer()
    sent = ' '.join([lemmatizer.lemmatize(w) for w in tweet.split() if len(lemmatizer.lemmatize(w))>3])

    return sent
 
    
@app.callback(Output('live-update-graph', 'children'),
              [Input('interval-component-slow', 'n_intervals')])
def update_graph_live(n):
    """ updates graph with city counts and displays calculations every 2 mins"""
    gc.collect()
    
    # Loading data from Heroku PostgreSQL
    DATABASE_URL= 'postgres://ondoitzgzsialv:77775a500c6f7d4db808d3709ccf1c275893ea9b3f631e1ab50687c3638be2ac@ec2-52-1-115-6.compute-1.amazonaws.com:5432/dee64c87blrg0l'
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    
    # delete the tweets over a day ago
    query2 = "DELETE FROM {} WHERE date < now() - interval '1 day'".format(settings2.TABLE_NAME)
    cur = conn.cursor()
    cur.execute(query2)
    conn.commit()
    cur.close()
     
    # now that we have a clean table
    query3 = "SELECT latitude, longitude, city, state, user_followers_count, user_screen_name FROM {}".format(settings2.TABLE_NAME)
    df_loc2 = pd.read_sql(query3, con=conn)
    conn.close()
    
    # let's do some analysis of these tweets
    
    # total count of classifier
    total_tweets = len(df_loc2)

    # total number of followers
    follow = df_loc2.drop_duplicates(subset=['user_screen_name'])  # dont want to count one user multiple times
    total_followers = follow['user_followers_count'].sum()
    total_users = len(follow)

    # use garbage collector for efficient memory allocation
    del follow
    gc.collect()
    
    # get city data with lat and long to merge with our data
    cities_df = pd.read_csv("uscities.csv")
    locations = df_loc2.merge(cities_df[["city", "state_id", "state_name", "lat", "lng"]], how = "left", left_on = ["city","state"], right_on = ["city", "state_name"])
    df = locations.groupby(["city", "state", "lat", "lng"])["city"].size().reset_index(name='counts')

    del df_loc2, cities_df, locations
    gc.collect()
    
    # total number of tweets in graph
    total_graph = df["counts"].sum()
    
    # plot the counts on a scatter map
    limits = [(0,50),(50,200),(200,400),(400,800),(800,3000)]
    colors = [ "magenta", "blue", "green", "goldenrod", "red"]
    
    fig = go.Figure()

    for i in range(len(limits)):
        lim = limits[i]
        df_sub = df.loc[(df['counts'] >= lim[0]) & (df['counts'] <= lim[1])]
        fig.add_trace(go.Scattergeo(
                locationmode = 'USA-states',
                lon = df_sub['lng'],
                lat = df_sub['lat'],
                text = df_sub[['city', 'counts']],
                marker = dict(
                    size = df_sub['counts'],
                    color = colors[i],
                    line_color='rgb(40,40,40)',
                    line_width=0.5,
                    sizemode = 'area'
                ),
                name = '{0} - {1}'.format(lim[0],lim[1])))

        fig.update_layout(
            title_text = 'Number of Tweets Classified as Protests by City <br>(Hover to see city and count, Click legend to toggle traces)',
            showlegend = True,
            geo = dict(
                scope = 'usa',
                landcolor = 'rgb(217, 217, 217)',
            )
        )
    
    del df
    gc.collect()
    
    # return the results from above in a nice layout
    children = [
                html.Div(html.Div(dcc.Graph(id='live-map', figure= fig))),
                html.Div(
                    className='row',
                    children=[
                        html.Div(
                            children=[
                                html.P('Total Number of Tweets Classified as Protests',
                                    style={
                                        'fontSize': 20,
                                        'textAlign': 'center'
                                    }
                                ),
                                html.P(total_tweets,
                                    style={
                                        'fontSize': 40
                                    }
                                )
                            ],
                            style={
                                'width': '25%',
                                'display': 'inline-block',
                                'textAlign': 'center'
                            }
                        ),
                        html.Div(
                            children=[
                                html.P('Total Number of Tweets in America',
                                    style={
                                        'fontSize': 20,
                                        'textAlign': 'center'
                                    }
                                ),
                                html.P(total_graph,
                                    style={
                                        'fontSize': 40
                                    }
                                )
                            ],
                            style={
                                'width': '25%',
                                'display': 'inline-block',
                                'textAlign': 'center'
                            }
                        ),
                        html.Div(
                            children=[
                                html.P('Total Number of Users',
                                    style={
                                        'fontSize': 20,
                                        'textAlign': 'center'
                                    }
                                ),
                                html.P(total_users,
                                    style={
                                        'fontSize': 40
                                    }
                                )
                            ],
                            style={
                                'width': '25%',
                                'display': 'inline-block',
                                'textAlign': 'center'
                            }
                        ),

                        html.Div(
                            children=[
                                html.P('Total Number of Followers Reached',
                                    style={
                                        'fontSize': 20,
                                        'textAlign': 'center'
                                    }
                                ),
                                html.P(total_followers,
                                    style={
                                        'fontSize': 40
                                    }
                                )
                            ],
                            style={
                                'width': '25%',
                                'display': 'inline-block',
                                'textAlign': 'center'
                            }
                        ),
                    ],
                    style={'marginLeft': 70}
                    
                ),
                html.Br()
            ]
                

    return children

@app.callback(Output('live-update-hashtags', 'children'),
              [Input('interval-component-slow', 'n_intervals')])
def update_hash_live(n):
    """ updates state map and hashtags every 2 mins """
    gc.collect()
    
    # Loading data from Heroku PostgreSQL
    DATABASE_URL= 'postgres://ondoitzgzsialv:77775a500c6f7d4db808d3709ccf1c275893ea9b3f631e1ab50687c3638be2ac@ec2-52-1-115-6.compute-1.amazonaws.com:5432/dee64c87blrg0l'
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    
    # now that we have a clean table
    query_1 = "SELECT latitude, longitude, city, state, hashtags FROM {}".format(settings2.TABLE_NAME)
    new_df = pd.read_sql(query_1, con=conn)
    conn.close()
    
    # get city data to merge with our data
    cities_df1 = pd.read_csv("uscities.csv")
    locations1 = new_df.merge(cities_df1[["city", "state_id", "state_name", "lat", "lng", "population"]], how = "left", left_on = ["city","state"], right_on = ["city", "state_name"])
    
    del cities_df1, new_df
    gc.collect()
    
    # this groups hashtags by location
    locations1["hashtags"] = locations1["hashtags"].apply(eval)
    na2 = locations1.dropna(subset=["hashtags"])
    df2 = na2.groupby(["city", "state", "lat", "lng"])["hashtags"].apply(list).reset_index(name="hashtags")  # this is by city
    df2["hashtags"] = df2["hashtags"].apply(lambda x : list(np.concatenate(x).flat))
    
    # top hashtags in states overall
    us_tags = pd.Series([x for _list in df2["hashtags"] for x in _list]).value_counts()
    top_ustags = us_tags[0:10]
    
    # further group hashtag by state and find top for each state
    state_hash = df2.groupby(["state"])["hashtags"].apply(list).reset_index(name='hashtags')
    state_hash["hashtags"] = state_hash["hashtags"].apply(lambda x : list(np.concatenate(x).flat))
    state_hash["top"] = state_hash["hashtags"].apply(lambda x : str(Counter(x).most_common(3)))
    state_hash["text"] =  "Top Hashtags: " + state_hash["top"] + "<br>"
    
    del df2, na2, us_tags
    gc.collect()

    state_codes = {
    'District of Columbia' : 'dc','Mississippi': 'MS', 'Oklahoma': 'OK',
    'Delaware': 'DE', 'Minnesota': 'MN', 'Illinois': 'IL', 'Arkansas': 'AR',
    'New Mexico': 'NM', 'Indiana': 'IN', 'Maryland': 'MD', 'Louisiana': 'LA',
    'Idaho': 'ID', 'Wyoming': 'WY', 'Tennessee': 'TN', 'Arizona': 'AZ',
    'Iowa': 'IA', 'Michigan': 'MI', 'Kansas': 'KS', 'Utah': 'UT',
    'Virginia': 'VA', 'Oregon': 'OR', 'Connecticut': 'CT', 'Montana': 'MT',
    'California': 'CA', 'Massachusetts': 'MA', 'West Virginia': 'WV',
    'South Carolina': 'SC', 'New Hampshire': 'NH', 'Wisconsin': 'WI',
    'Vermont': 'VT', 'Georgia': 'GA', 'North Dakota': 'ND',
    'Pennsylvania': 'PA', 'Florida': 'FL', 'Alaska': 'AK', 'Kentucky': 'KY',
    'Hawaii': 'HI', 'Nebraska': 'NE', 'Missouri': 'MO', 'Ohio': 'OH',
    'Alabama': 'AL', 'Rhode Island': 'RI', 'South Dakota': 'SD',
    'Colorado': 'CO', 'New Jersey': 'NJ', 'Washington': 'WA',
    'North Carolina': 'NC', 'New York': 'NY', 'Texas': 'TX',
    'Nevada': 'NV', 'Maine': 'ME', 'Puerto Rico': ''}
   
    # find top city
    df_old = locations1.groupby(["city", "state", "lat", "lng"])["city"].size().reset_index(name="counts")
    top_count = df_old["counts"].max()
    top_row = df_old[df_old["counts"]==df_old["counts"].max()]
    top_city = top_row["city"]

    # calculate total amount of tweets per state and get max
    statesdf = df_old.groupby(["state"])["counts"].sum().reset_index(name = "st_counts")
    
    del df_old, locations1
    
    # find top state
    statesdf = statesdf.drop(statesdf[statesdf["state"]=="Puerto Rico"].index)
    top_stcount = statesdf["st_counts"].max()
    top_strow = statesdf[statesdf["st_counts"]==statesdf["st_counts"].max()]
    top_state = top_strow["state"]
    statesdf["code"] = statesdf["state"].apply(lambda x : state_codes[x])
    
    # display state and hashtags on choropleth map
    state_fig = go.Figure(data=go.Choropleth(
        locations= statesdf['code'], # Spatial coordinates
        z = statesdf['st_counts'], # Data to be color-coded
        locationmode = 'USA-states', # set of locations match entries in `locations`
        colorscale = 'Reds',
        text = state_hash['text'],
        colorbar_title = 'Number of Tweets'
        ))

    
    state_fig.update_layout(
        title_text = 'Number of Tweets Classified as Protests by State <br>(Hover to See Top Hashtags per State)',
        geo_scope='usa', # limite map scope to USA
        )
    
    # bar graph for hashtags
    tag_fig = go.Figure([go.Bar(x=top_ustags.index, y=top_ustags)])
    
    # return graphs and calculations in nice layout
    children = [
            html.Div(
                    className='row',
                    children=[
                        html.Div(
                            children=[
                                html.P('State with the Most Tweets about Protests',
                                    style={
                                        'fontSize': 20,
                                        'textAlign': 'center'
                                    }
                                ),
                                html.P(top_state,
                                    style={
                                        'fontSize': 40
                                    }
                                )
                            ],
                            style={
                                'width': '50%',
                                'display': 'inline-block',
                                'textAlign': 'center'
                            }
                        ),
                        html.Div(
                            children=[
                                html.P('City with the Most Tweets about Protests',
                                    style={
                                        'fontSize': 20,
                                        'textAlign': 'center'
                                    }
                                ),
                                html.P(top_city,
                                    style={
                                        'fontSize': 40
                                    }
                                )
                            ],
                            style={
                                'width': '50%',
                                'display': 'inline-block',
                                'textAlign': 'center'
                            }
                        ),
                    ],
                    style={'marginLeft': 70}
                ),
            html.Br(),
            html.Br(),
            html.Div(html.Div(dcc.Graph(id='state-map', figure= state_fig))),
            html.Br(),
            html.Div(
                    className='row',
                    children=[
                        html.P('Top Hashtags in the United States',
                                style={
                                    'fontSize': 20,
                                    'textAlign': 'left'
                                }
                            )
                    ],style={'width': '35%', 'marginLeft': 70}
                ),
                html.Div(html.Div(dcc.Graph(id='tags', figure= tag_fig)))
                ]
                
    del state_hash, statesdf
    gc.collect()
    return children


def make_image(b):
    """ formats the wordcloud to be displayed """
    img = BytesIO()
    b.to_image().save(img, format='PNG')
    return 'data:image/png;base64,{}'.format(base64.b64encode(img.getvalue()).decode())


@app.callback(Output('us-cloud', 'src'),
              [Input('interval-component-slow', 'n_intervals')])
def update_us_word_cloud(n):
    """ creates a wordcloud with text from tweets in the US """
    gc.collect()
    
    # Loading data from Heroku PostgreSQL
    DATABASE_URL= 'postgres://ondoitzgzsialv:77775a500c6f7d4db808d3709ccf1c275893ea9b3f631e1ab50687c3638be2ac@ec2-52-1-115-6.compute-1.amazonaws.com:5432/dee64c87blrg0l'
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    query = "SELECT latitude, longitude, city, state, text FROM  {}".format(settings2.TABLE_NAME)
    df_tweet = pd.read_sql(query, con=conn)
    conn.close()
    
    # merge our data with us city data
    us_df = pd.read_csv("uscities.csv")
    locations2 = df_tweet.merge(us_df[["city", "state_name", "lat", "lng"]], how = "left", left_on = ['city','state'], right_on = ['city', 'state_name'])
    
    del df_tweet, us_df
    gc.collect()
    
    # find tweets in america
    df_tweet2 =  locations2.dropna(subset=['lat', 'lng'])
    
    del locations2
    
    # preprocess text and make the word cloud
    us_words = ' '.join([preprocess(text) for text in df_tweet2["text"]])
    wordcloud2 = WordCloud(width=800, height=500, random_state=21, max_font_size=110).generate(us_words)
    us = make_image(wordcloud2)
    
    del df_tweet2
    gc.collect()
    return us
    
# run the app
if __name__ == '__main__':
        
    app.run_server(debug=True)


