import dash
from dash import dcc as dcc
from dash import html as html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np


path = r"E:\Projects\Plex\20240123_120813_plexHistory.csv"

plexDF = pd.read_csv(path,index_col=False,)

# Convert the date columns from object to datetime
plexDF['Originally Available'] = pd.to_datetime(plexDF['Originally Available'], errors='coerce')

plexDF['Viewed At'] = pd.to_datetime(plexDF['Viewed At'], errors='coerce')


# Assign distinct colors to usernames for graphics
userNames = plexDF['User Alias'].unique()

colorPalette = px.colors.qualitative.Set1

userColorMap = {user: colorPalette[i % len(colorPalette)] for i, user in enumerate(userNames)}

# Assign unique colors for devices

uniqueDevices = plexDF['Device'].unique()

deviceColors = px.colors.qualitative.Pastel

deviceColorMap = {device: deviceColors[i % len(deviceColors)] for i, device in enumerate(uniqueDevices)}


#Unique Years
plexDF['Year'] = plexDF['Viewed At'].dt.year
years = plexDF['Year'].unique()


######-----------GRAPHS

#---------------------------------WATCH HOURS MONTHLY PER USER CHART GENERATION


plexDF['Month'] = plexDF['Viewed At'].dt.month_name()

userMonth = plexDF.groupby(['User Alias', 'Month'])['Duration_Hrs'].sum().reset_index()

userMonth = userMonth.pivot(index='Month', columns='User Alias', values='Duration_Hrs').fillna(0)

months_order = ['January', 'February', 'March', 'April', 'May', 'June','July', 'August', 'September', 'October', 'November', 'December']

userMonth = userMonth.reindex(months_order)

watchBarMonths = go.Figure()

for user in userMonth.columns:
    watchBarMonths.add_trace(go.Bar(
        x=userMonth.index,
        y=userMonth[user],
        name=user,
        marker_color=userColorMap.get(user, 'grey') 
    ))



watchBarMonths.update_layout(
    title_text='Monthly Breakdown per User',
    title_font_size=20,
    title_x=0.5,
    xaxis_title = "Month",
    yaxis_title = "Duration in Hours",
    legend_title = "User",
    barmode='stack'
                )

watchBarMonths.update_xaxes(tickangle=-45)


#---------------------------------WATCH HOURS PER USER CHART GENERATION
userDuration = plexDF.groupby('User Alias')['Duration_Hrs'].sum().reset_index().sort_values('Duration_Hrs',ascending=False)


watchHours = go.Figure()

# Loop through each user and add a bar to the chart
for user in userDuration['User Alias']:
    user_data = userDuration[userDuration['User Alias'] == user]
    watchHours.add_trace(go.Bar(
        x=user_data['User Alias'],
        y=user_data['Duration_Hrs'],
        name=user,
        marker_color=userColorMap.get(user, 'grey') 
    ))


watchHours.update_layout(
    title_text='Screen Time: User Watch Hour Statistics',
    title_font_size=20,
    title_x=0.5,
    xaxis=dict(title='User'),
    yaxis=dict(title='Duration in Hours'),
    bargap=0.2)    


#---------------------------------MEDIA TYPE PER USER CHART GENERATION


mediaType = plexDF.groupby(['User Alias', 'Type'])['Duration_Hrs'].sum().reset_index()

mediaType = mediaType.pivot(index='User Alias', columns='Type', values = 'Duration_Hrs').fillna(0)

watchMediaType = px.bar(
    mediaType
    ,barmode = 'stack'
    ,title = 'User Preferences in Content Type and Movie Genres'
                )

watchMediaType.update_layout(
    title_font_size=20,
    title_x=0.5,
    xaxis_title = 'Users',
    yaxis_title = 'Duration in Hours',
    legend_title = "Media Type"
                    )

#---------------------------------DEVICES USED CHART GENERATION

devices = plexDF.groupby(['Device'])['Duration_Hrs'].sum().reset_index()

watchDevices = go.Figure(data=[go.Pie(
    labels=devices['Device'],
    values=devices['Duration_Hrs'],
    marker=dict(colors=[deviceColorMap[device] for device in devices['Device']])
    )])

watchDevices.update_layout(
    title_text='Hours Spent Across Viewing Platforms',
    title_font_size=20,
    title_x=0.5           )

# Customize the pie chart layout
watchDevices.update_traces(textinfo='percent+label'
                           , pull=[0.1]*len(devices['Device'])
                           )



# Initialize app
app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],
                )
app.title = "Plex Review"

app.layout = html.Div([
    html.H1('Plex Review', style ={'textAlign': 'center','font-weight': 'bold'} ),
    
    html.Div([
    html.Label('Year:', style={'font-weight': 'bold'}),
    dcc.Dropdown(
        id='year-selector',
        options=[{'label': 'ALL', 'value': 'ALL'}] + [{'label': year, 'value': year} for year in years],
        value= 'ALL',
        clearable=False,
        placeholder="Select Year",
        style={'width': '100%'}
        ),
    ], style={'padding': '10px'}),

    html.Div([
    html.Label('User:', style={'font-weight': 'bold'}),
    dcc.Dropdown(
        id='user-selector',
        options=[{'label': user, 'value': user} for user in userNames],
        value= userNames,
        multi=True,
        placeholder="Select User",
        style={'width': '100%'}
        ),
    ], style={'padding': '10px'}),
    html.Div([
        dcc.Graph(id='watchHours-chart', figure = watchHours),
        dcc.Graph(id='watchMonths-chart', figure = watchBarMonths)
    ] , style={'display':'flex','flex-wrap':'wrap'}),    



    html.Div([
        dcc.Graph(id='watchMediaType-chart', figure = watchMediaType),
        dcc.Graph(id='watchDevices-chart', figure = watchDevices)
    ] , style={'display':'flex','flex-wrap':'wrap'})    
])

#Callbacks to update graphs

@app.callback(
    [
       Output('watchHours-chart','figure'), 
       Output('watchMonths-chart','figure'), 
       Output('watchMediaType-chart','figure'), 
       Output('watchDevices-chart','figure') 
    ],
    [
         Input('year-selector','value'),
         Input('user-selector','value')
     
     ]

)

def updateCharts(selectedYear,selectedUser):

    plexFiltered = plexDF.copy()


    if selectedYear != 'ALL':
        plexFiltered = plexFiltered[plexFiltered['Year'] == selectedYear]
    
    if selectedUser:
        plexFiltered = plexFiltered[plexFiltered['User Alias'].isin(selectedUser)]

#---------------------------------WATCH HOURS MONTHLY PER USER CHART GENERATION


    plexFiltered['Month'] = plexFiltered['Viewed At'].dt.month_name()

    updatedUserMonth = plexFiltered.groupby(['User Alias', 'Month'])['Duration_Hrs'].sum().reset_index()

    updatedUserMonth = updatedUserMonth.pivot(index='Month', columns='User Alias', values='Duration_Hrs').fillna(0)

    months_order = ['January', 'February', 'March', 'April', 'May', 'June','July', 'August', 'September', 'October', 'November', 'December']

    updatedUserMonth = updatedUserMonth.reindex(months_order)


    updatedWatchBarMonths = go.Figure()

    for user in updatedUserMonth.columns:
        updatedWatchBarMonths.add_trace(go.Bar(
            x=updatedUserMonth.index,
            y=updatedUserMonth[user],
            name=user,
            marker_color=userColorMap.get(user, 'grey') 
        ))



    updatedWatchBarMonths.update_layout(
        title_text='Monthly Breakdown per User',
        title_font_size=20,
        title_x=0.5,
        xaxis_title = "Month",
        yaxis_title = "Duration in Hours",
        legend_title = "User",
        barmode='stack'
                    )

    updatedWatchBarMonths.update_xaxes(tickangle=-45)

#---------------------------------WATCH HOURS PER USER CHART GENERATION
    userDurationFiltered = plexFiltered.groupby('User Alias')['Duration_Hrs'].sum().reset_index().sort_values('Duration_Hrs',ascending=False)

    updatedWatchHours = go.Figure()

    for user in userDurationFiltered['User Alias']:
        user_data = userDurationFiltered[userDurationFiltered['User Alias'] == user]
        updatedWatchHours.add_trace(go.Bar(
            x=user_data['User Alias'],
            y=user_data['Duration_Hrs'],
            name=user,
            marker_color=userColorMap.get(user, 'grey')
        ))



    updatedWatchHours.update_layout(
        title_text='Screen Time: User Watch Hour Statistics',
        title_font_size=20,
        title_x=0.5,
        xaxis=dict( title='User'),
        yaxis=dict(title='Duration in Hours'),
        bargap=0.2)    


    #---------------------------------MEDIA TYPE PER USER CHART GENERATION


    updatedMediaType = plexFiltered.groupby(['User Alias', 'Type'])['Duration_Hrs'].sum().reset_index()

    updatedMediaType = updatedMediaType.pivot(index='User Alias', columns='Type', values = 'Duration_Hrs').fillna(0)

    updatedWatchMediaType = px.bar(
        updatedMediaType
        ,barmode = 'stack'
        ,title = 'User Preferences in Content Type and Movie Genres'
                    )

    updatedWatchMediaType.update_layout(
        title_font_size=20,
        title_x=0.5,
        xaxis_title = 'Users',
        yaxis_title = 'Duration in Hours',
        legend_title = "Media Type"
                        )

    #---------------------------------updatedDevices USED CHART GENERATION

    updatedDevices = plexFiltered.groupby(['Device'])['Duration_Hrs'].sum().reset_index()

    updatedWatchDevices = go.Figure(data=[go.Pie(
        labels=updatedDevices['Device'],
        values=updatedDevices['Duration_Hrs'],
        marker=dict(colors=[deviceColorMap.get(device, 'grey') for device in devices['Device']])
        )])

    updatedWatchDevices.update_layout(
        title_text='Hours Spent Across Viewing Platforms',
        title_font_size=20,
        title_x=0.5           )

    updatedWatchDevices.update_traces(textinfo='percent+label'
                               , pull=[0.1]*len(updatedDevices['Device'])
                               )
    return updatedWatchHours, updatedWatchBarMonths, updatedWatchMediaType, updatedWatchDevices



# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)