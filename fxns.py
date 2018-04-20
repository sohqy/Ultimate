#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  4 18:23:06 2018

@author: sohqiaoyan

"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as pco
import seaborn as sns
import networkx as nx
import copy
from plotly.offline import download_plotlyjs, init_notebook_mode,  plot
import plotly.graph_objs as go
init_notebook_mode()


#%% Color Options
UTcmap = {'T':(0.73,0.56,0.81), 'U':(0.67, 0.70, 0.73), 'UT':(0.85,0.53,0.5)}
FMcmap = {'M':(0.33,0.60,0.78),'F':(0.27, 0.70, 0.62)}
sns.set_style('whitegrid')
sns.set_context('paper')

#%%


def readdata(filename):
    """
    Function : Returns lists of csv files to read
    Each game has two dataframes:
        1. Overviews: 
            overall stats that include Score, O/D, Gender ratio 
            and timeout information per point. 
        2. Pitchtimes: 
            Player based statistics including Goals, Assists, and 
            whether they were on the pitch for each point.
    
    Inputs: 
        filename - This should be a string for the csv file in which the 
        tournament games are stored in. 
    
    Outputs: 
        overviews, pitchtimes, roster
        
        overviews - Dictionary of dataframes containing game events 
        pitchtimes - Dictionary of dataframes containing player stats
        roster - Dataframe containing player names and gender for the entire tournament.
    """
    tournament = pd.read_csv(filename)
    tournament = tournament.dropna(how = 'all')
    tournament = tournament.dropna(axis = 1, how = 'all')

    overviews = {}
    pitchtimes = {}

    tournament['Overview'] = tournament['Opponent']+'-'+'Overview.csv'
    tournament['Pitchtime'] = tournament['Opponent']+'-'+'Pitchtime.csv'

    # Import game overviews
    for i in range(len(tournament)):
        overviews[tournament['Opponent'][i]]=pd.read_csv(tournament['Overview'][i])
        pitchtimes[tournament['Opponent'][i]]=pd.read_csv(tournament['Pitchtime'][i])
    
    for game in pitchtimes:
        pitchtimes[game] = pitchtimes[game].rename(index = str, columns = {"Unnamed: 0":'Gender', "Unnamed: 1":"Name"})
        pitchtimes[game].drop(pitchtimes[game].tail(3).index, inplace = True)
        
    roster = pitchtimes[game][['Name','Gender']]
    
    return overviews, pitchtimes, roster

#%%

def vis_events(game, overviews):
    """
    Function : Overview of specified game, displaying: 
                    - Score evolution within the game
                    - Gender ratio of each point
                    - Which team called the gender ratio
                    - When timeouts happen
        
    Inputs: 
        game - String, name of opponent of interest. 
        overviews - dictionary containing dataframes of game events
    
    Outputs:
        Plotly Scatter and Line graph.
    """
    fm2 = dict((k, pco.to_hex(v)) for k,v in FMcmap.items())
    ut2 = dict((k, pco.to_hex(v)) for k,v in UTcmap.items())
    
    gameinfo = overviews[game]
    
     # Extract all timeout information
    mto = gameinfo[['Midpoint Timeouts', 'Point number']].dropna()
    bto = gameinfo[['Timeouts between points', 'Events between points']].dropna()
    
    # Rename columns for concatenating the two sets
    mto = mto.rename(index = str, columns={'Point number':'x', 'Midpoint Timeouts':'Timeout'})
    bto = bto.rename(index = str, columns={'Events between points':'x','Timeouts between points':'Timeout'})
    
    # Store timeout information in one place
    timeouts = mto.append(bto)
    timeouts.reset_index(inplace = True, drop = True)
    
    # Plot Trace
    trace1 = go.Scatter(
        x = gameinfo['Point number'],
        y = gameinfo['Deep Space'],
        mode = 'lines+markers',
        marker = dict(
                size = '10', 
                color = gameinfo['Gender ratio'].map(fm2),
                ),
        line = dict(
                color = '#ABB2B9',
                ),
        text = gameinfo['Gender ratio']+gameinfo['Gender Called by'],
        name = 'Deep Space'
    )
    
    trace2 = go.Scatter(
        x = gameinfo['Point number'],
        y = gameinfo['Opponent'],
        mode = 'lines+markers',
        marker = dict(
                color = '#BB8FCE'),
        name = str(game)
        )
    
    shapes = list()
    for xc in timeouts.x:
        index = timeouts[timeouts['x']==xc].index[0]
        colors = timeouts['Timeout'].map(ut2)
        shapes.append({'type': 'line',
                       'xref': 'x',
                       'yref': 'y',
                       'x0': xc,
                       'y0': 0,
                       'x1': xc,
                       'y1': len(gameinfo),
                       'line': {
                                'color': colors[index],
                                'width': 2,
                                'dash':'dash'
                                },
                       })
    
    layout = go.Layout(
            title = "Events vs "+str(game),
            shapes = shapes,
            yaxis = dict(
                    title = "Score"),
            xaxis = dict(
                    title = "Point Number"),
            legend = dict(
                    orientation = 'h',
                    y = 1.1,
                    x = 0.5,
                    ),
            )
            
    fig = go.Figure(data = [trace2,trace1], layout = layout)
    plot(fig)
    return plot(fig, include_plotlyjs=False, output_type='div')

def vis_possessions(game, overviews):
    """
    Function : Visualises number of possessions the team has had in each point of the game.
    
    Inputs:
        game - name of opponent in question
        overviews - dictionary containing dataframes of game events
        
    Outputs:
        Plotly scatter graph. 
        
    """
    yn = {0 : '#BB8FCE', 1 : '#ABB2B9'}
    yn1 ={0:'Conceded', 1:'Converted'}
    gameinfo = overviews[game]
    trace_1 = [go.Scatter(
            x = gameinfo['Point number'],
            y = gameinfo['Number of posessions'],
            mode = 'markers',
            marker = dict(
                size = '10', 
                color = gameinfo['Did we score'].map(yn),
                ),
            text = gameinfo['Did we score'].map(yn1),
            )]
    
    layout = go.Layout(
            title = "Number of Possessions per Point - "+str(game),
            yaxis = dict(
                    title = "Number of Possessions"),
            xaxis = dict(
                    title = "Point Number"),
            )
        
    fig = go.Figure(data=trace_1, layout = layout)
    plot(fig)
    
    return plot(fig, include_plotlyjs=False, output_type='div')

#%%

def totalgoalassist_list(pitchtimes, overviews):
    """
    Function :   Goals, Assists for all games
    
    Inputs: 
        pitchtimes - Dictionary containing all dataframes of player stats
        overviews  - Dictionary containing all dataframes of game stats
        
    Outputs: 
        Dataframe containing Goal and Assist pairs. 
    """
    GAtotal = []

    for game in pitchtimes:
        points = len(overviews[game])
        scored = pitchtimes[game].select_dtypes(include=['object'])
        GA = pd.DataFrame(index = range(points), columns = ['Goals', 'Assists'])
    
        for i in range(points):
            if str(i+1) in scored:
                GA['Goals'][i] = pitchtimes[game].loc[pitchtimes[game][str(i+1)]=="G"]['Name'].item()
                GA['Assists'][i] =  pitchtimes[game].loc[pitchtimes[game][str(i+1)]=="A"]['Name'].item()
        GA = GA.dropna()
        GAtotal.append(GA)

    GAtotal = pd.concat(GAtotal)
    
    return GAtotal

def vis_GAflow(GAtotal,pitchtimes,roster, title='Visualising GA flow'):
    """
    Function : Creates a Plotly Alluvial flow graph.
    
    Inputs: 
        GAtotal - Dataframe of Goal/Assist pairs
        pitchtimes - Dictionary of dataframes containing player stats
        roster - Dataframe containing roster for the entire tournament
        title - Title of the generated plot. (String)
        
    Outputs:  
        Plotly Alluvial Flow Diagram.
    """
    # Generate a color palette with enough variations to cover the whole team
    sns.set_palette('husl',len(roster))
    # Map colors to each player.
    playercmap = dict(zip(roster.Name, sns.color_palette()))
    # Calculate weight of each link, and save to new DataFrame.
    sankey = GAtotal.groupby(['Assists','Goals']).size().to_frame('Counts').reset_index()
    
    # Convert Names (Categoricals) into integers
    sankey['Assists']=sankey['Assists'].astype('category')
    # Generate a list of unique instances, defines nodes and assigns each with an index integer. 
    labels = np.append(pd.unique(sankey.Assists),pd.unique(sankey.Goals))
    # Put list into sankeyinfo dataframe to keep node information 
    sankeyinfo = pd.DataFrame({"Labels":labels})
    # Map colors to player nodes, and convert each into hex representation for Plotly.
    sankeyinfo['Colors'] = sankeyinfo.Labels.map(playercmap)
    sankeyinfo['hexcolor']=sankeyinfo.Colors.apply(pco.to_hex)
    
    # Assign integer representation to sources
    sankey['Source'] = sankey.Assists.cat.codes
    
    # Extract target and respective node indices to new dataframe,
    # Invert dictionary to map Name to index, instead of index to name
    gls = dict(sankeyinfo['Labels'][max(sankey.Source)+1:])
    gls = {v:k for k,v in gls.items()}
    # Map/Assign integer to targets
    sankey['Target'] = sankey.Goals.map(gls)
    
    genderdict = dict(zip(roster.Name, roster.Gender))
    rmap = {'FF':'#45B39D', 'FM': '#7DCEA0', 'MF':'#85C1E9','MM':'#5499C7'}
    sankey['GA pair']=sankey.Assists.map(genderdict)+sankey.Goals.map(genderdict)
    sankey['Linkcolor']=sankey['GA pair'].map(rmap)
    
    # Plot Sankey/Alluvial Diagram
    data_trace = dict(type = 'sankey', 
                      domain = dict(x=[0,1], y=[0,1]), 
                      orientation = "h", 
                      valueformat = ".0f", 
                      
                      node = dict(pad = 10, thickness = 30, line = dict(color = "black", width = 0),
                      label = sankeyinfo.Labels,
                      #color = sankeyinfo.hexcolor
                      color = '#ABB2B9',
                      ),
                      
                      link = dict(
                              source = sankey['Source'],
                              target = sankey['Target'],
                              value = sankey['Counts'],
                              color = sankey['Linkcolor']
                              )
                      )
                      
    layout = dict(
            title = title,
            height = 800,
            width = 800,
            font = dict(size = 10)
            )
    
    fig = dict(data = [data_trace], layout=layout)
    plot(fig)
    return plot(fig, include_plotlyjs=False, output_type='div')

#%%

def calc_indstats(overviews, pitchtimes, roster):
    """
    Function : Calculates individual performances and responsibilities.
    
    Inputs: 
        overviews - dictionary containing dataframes of game events
        pitchtimes - Dictionary of dataframes containing player stats
        roster - Dataframe containing roster for the entire tournament
        
    Outputs:  
        Dataframe containing individual player statistics.
    """
    indstats = roster.copy()
    s = ['Points Played', 'Goals','Assists']
    for column in s:
        p=np.zeros(len(roster))
        for game in pitchtimes: 
            p1 = pitchtimes[game][column] 
            p = p+p1
        indstats[column]=p
    
    o1 = []
    o0 = []
    d1 = []
    d0 = []
    for game in overviews:
        for i in range(len(overviews[game])):
            r = pitchtimes[game][['Name',str(i+1)]].dropna()
            r = r.reset_index(drop=True)
            r.drop(str(i+1), inplace = True, axis = 1)
            
            if overviews[game]['Did we score'][i]==1:
                if overviews[game]['Starting on O/D'][i]=='O':
                    o1.append(r)                    
                else:
                    d1.append(r)
            else:
                if overviews[game]['Starting on O/D'][i]=='O':
                    o0.append(r)
                else:
                    d0.append(r)

    o1 = pd.concat(o1)
    o0 = pd.concat(o0)
    d1 = pd.concat(d1)
    d0 = pd.concat(d0)
   
    a = o1.Name.value_counts().reindex(indstats.Name).fillna(0)
    indstats['O Converted']=a.tolist()
    
    a = o0.Name.value_counts().reindex(indstats.Name).fillna(0)
    indstats['O Conceded']=a.tolist()
    
    a = d1.Name.value_counts().reindex(indstats.Name).fillna(0)
    indstats['D Converted']=a.tolist()
    
    a = d0.Name.value_counts().reindex(indstats.Name).fillna(0)
    indstats['D Conceded']=a.tolist()
    
    indstats['O Points'] = indstats['O Converted']+indstats['O Conceded']
    indstats['D Points'] = indstats['D Converted']+indstats['D Conceded']
    indstats['Conceded'] = indstats['O Conceded']+indstats['D Conceded']
    indstats['Converted, not GA']= indstats['Points Played']-(indstats['Goals']+indstats['Assists']+indstats['Conceded'])
    indstats.sort_values('Points Played', ascending = False, inplace = True)
    
    return indstats

def vis_player_pointresults(indstats, title='Breakdown of points played by player'):
    """
    Function : Visualises outcomes of points played by each player.
    
    Inputs: 
        indstats - Dataframe containing individual player statistics.
        
    Outputs:  
        Plotly stacked bar chart with percentages normalised to each individual.
    """
    trace_1 = go.Bar(
        x = indstats.Name,
        y = indstats.Conceded/indstats['Points Played'],
        marker =dict(color = '#45B39D'
                ),
        name = 'Conceded'
        )
    
    trace_2 = go.Bar(
            x = indstats.Name,
            y = indstats['Converted, not GA']/indstats['Points Played'],
            marker =dict(color = '#7DCEA0'
                ),
            name = 'Converted'
            )
    
    trace_3 = go.Bar(
            x = indstats.Name,
            y = indstats.Assists/indstats['Points Played'],
            marker =dict(color = '#5499C7'
                ),
            name = 'Assists'
            )
    
    trace_4 = go.Bar(
            x = indstats.Name,
            y = indstats.Goals/indstats['Points Played'],
            marker =dict(color = '#85C1E9'
                ),
            name = 'Goals'
            )
    
    
    data = [trace_1, trace_2, trace_3, trace_4]
    layout = go.Layout(
        barmode='stack',
        title = title,
        yaxis = dict(
                title = 'Percentage of Points Played'
                ),
        legend = dict(
                orientation = 'h',
                x=0.35,
                y=1.1
                )
    )
    
    fig = go.Figure(data=data, layout=layout)
    plot(fig)
    return plot(fig, include_plotlyjs=False, output_type='div')

def vis_player_odpoints(indstats):
    """
    Function : Visualises number of points played by each player, along with team average.
    
    Inputs: 
        indstats - Dataframe containing individual player statistics.
        
    Outputs:  
        Plotly stacked bar chart using absolute numbers.
    """
    trace_1 = go.Bar(
        x = indstats.Name,
        y = indstats['O Points'],
         marker = dict(
                    color = "#7DCEA0"
                    ),
        name = 'O Points')

    trace_2 = go.Bar(
            x = indstats.Name,
            y = indstats['D Points'],
            marker = dict(
                    color = "#5499C7"
                    ),
            name = 'D Points')
    
    layout = go.Layout(
            barmode = 'stack',
            title = 'O and D point breakdowns',
            shapes=[{'type': 'line',
                     'xref': 'x',
                     'yref': 'y',
                     'x0': -0.5,
                     'y0': np.mean(indstats['Points Played']),
                     'x1': 23.5,
                     'y1': np.mean(indstats['Points Played']),
                    'line': {
                            'color': '#ABB2B9',
                            'width': 2,
                            'dash':'dash',
                            },  
                            },
                    ])
    
    fig = go.Figure(data =[trace_1, trace_2], layout =layout)
    plot(fig)
    return plot(fig, include_plotlyjs=False, output_type='div')

def vis_player_efficiency(indstats,pointtype='O'):
    """
    Function : Visualises the conversion efficiency for O and D points by individual player.
    
    Inputs: 
        indstats - Dataframe containing individual player statistics.
        pointtype - Determine to view offensive 'O' points or defensive 'D' points. default = 'O', 
        
    Outputs:  
        Plotly stacked bar chart with conversion rates normalised to points played by each individual.
    """
    trace_1 = go.Bar(
        x = indstats.Name,
        y = indstats['O Converted']/indstats['O Points'],
        marker = dict(
                color = "#7DCEA0"
                ),
        name = 'Converting on O')
    
    trace_2 = go.Bar(
            x = indstats.Name,
            y = indstats['O Conceded']/indstats['O Points'],
            marker = dict(
                    color = "#45B39D"
                    ),
            name = 'Conceding on O')
    
    trace_3 = go.Bar(
            x = indstats.Name,
            y = indstats['D Converted']/indstats['D Points'],
            marker = dict(
                    color = "#85C1E9"
                    ),
            name = 'Converting on D')
    
    trace_4 = go.Bar(
            x = indstats.Name,
            y = indstats['D Conceded']/indstats['D Points'],
            marker = dict(
                    color = "#5499C7"
                    ),
            name = 'Conceding on D')
            
    if pointtype == 'O':
        data = [trace_1, trace_2]
        t1 = 'Offensive'
    else:
        data = [trace_3, trace_4]
        t1 = 'Defensive'
        
    layout = go.Layout(
            barmode='stack',
            title = t1 + ' Conversion Efficiency',
            yaxis = dict(
                    title = 'Proportion of points played',),
            legend = dict(
                    orientation = 'h',
                    x=0.25,
                    y=1.1,
                    ),
            )
    
    fig = go.Figure(data=data, layout = layout)
    plot(fig)
    return plot(fig, include_plotlyjs=False, output_type='div')

#%% Pie Charts
    
    
def pie_gender_GApair(indstats,GAtotal, title = 'Assist/Goal Pair Type by Gender'):
    """
    Function : Visualises the gender pair proportions for all scored points
    
    Inputs: 
        indstats - Dataframe containing individual player statistics.
        GAtotal - two columned list containing all goal and assist pairs 
        
    Outputs:  
        Plotly Pie Chart
    """
    genderdict = dict(zip(indstats.Name, indstats.Gender))
    rmap = {'FF':'#45B39D', 'FM': '#7DCEA0', 'MF':'#5499C7','MM':'#85C1E9'}
    a = pd.DataFrame()
    a['Goals'] = GAtotal.Goals.map(genderdict)
    a['Assists'] = GAtotal.Assists.map(genderdict)
    a['GA pair'] = a.Assists + a.Goals
    
    b = a['GA pair'].value_counts()
    b.index.name = 'Pair Type'
    b=b.reset_index()
    
    values = b['GA pair']
    labels = b['Pair Type']
    colors = b['Pair Type'].map(rmap)
    trace = go.Pie(labels = labels, values = values, marker = dict(colors=colors))
    layout = go.Layout(title = title, legend = dict(orientation = 'h', x=0.5, y = -0.2))
    fig=go.Figure(data=[trace], layout=layout)
    
    plot(fig)
    return plot(fig, include_plotlyjs=False, output_type='div')
    

def calc_gender_r(GAtotal, overviews, indstats):
    """
    Function : Calculates gender ratio based stats 
    
    Inputs: 
        GAtotal - two columned list containing all goal and assist pairs 
        overviews - dictionary containing dataframes of game events
        indstats - Dataframe containing individual player statistics.
        
    Outputs:  
        Dataframe consisting of Goals, Assists, and Conversion rates for points sorted by gender ratio.
    """
    allgames = []
    for game in overviews:
        allgames.append(overviews[game][['Gender ratio','Did we score']])
    allgames = pd.concat(allgames)
    allgames.reset_index(drop=True)
    
    genderstats=pd.DataFrame(allgames['Gender ratio'].value_counts())
    genderstats['Converted']=allgames[allgames['Did we score']==1]['Gender ratio'].value_counts()
    genderstats['Conceded']=genderstats['Gender ratio'] - genderstats['Converted']
    
    genderdict = dict(zip(indstats.Name, indstats.Gender))
    a = pd.DataFrame()
    a['Goals'] = GAtotal.Goals.map(genderdict)
    a['Assists'] = GAtotal.Assists.map(genderdict)
    a['Gender ratio'] = allgames['Gender ratio'][allgames['Did we score']==1]
    genderstats['F Goals']=a[a.Goals=='F']['Gender ratio'].value_counts()
    genderstats['M Goals']=a[a.Goals=='M']['Gender ratio'].value_counts()
    genderstats['F Assists']=a[a.Assists=='F']['Gender ratio'].value_counts()
    genderstats['M Assists']=a[a.Assists=='M']['Gender ratio'].value_counts()
    
    genderstats.index.name = 'Ratio'
    genderstats.reset_index(inplace = True)
    
    return genderstats

def pie_gender_con(genderstats, title = 'Gender: Point Conversion'):
    """
    Function : Visualises the conversion rates for each gender ratio
    
    Inputs: 
        genderstats - Dataframe containing gender ratio based statistics.
        title - Title for Pie Chart. default: 'Gender: Point Conversion'
        
    Outputs:  
        Plotly Pie Chart
    """
    a = genderstats.melt(id_vars = 'Ratio', value_vars=['Converted','Conceded'])
    values = a.value
    labels = a.Ratio+' Point, ' + a.variable
    layout = go.Layout(title = title, legend = dict(orientation = 'h', x=0.25) )
    colors = ['#5499C7','#45B39D','#85C1E9','#7DCEA0']
    
    trace = go.Pie(labels = labels, values = values, marker = dict(colors=colors))
    fig = go.Figure(data=[trace], layout=layout)
    plot(fig)
    return plot(fig, include_plotlyjs=False, output_type='div')

def pie_gender_g(genderstats, title = 'Gender: Breakdown of Goals'):
    """
    Function : Visualises the proportion of goals by each gender for each gender ratio
    
    Inputs: 
        genderstats - Dataframe containing gender ratio based statistics.
        title - Title for Pie Chart. default: 'Gender: Breakdown of Goals'
        
    Outputs:  
        Plotly Pie Chart
    """
    a = genderstats.melt(id_vars = 'Ratio', value_vars=['F Goals', 'M Goals'])
    values = a.value
    labels = a.Ratio + ' Point, ' + a.variable
    layout = go.Layout(title = title, legend = dict(orientation = 'h', x=0.25) )
    colors = ['#5499C7','#45B39D','#85C1E9','#7DCEA0']
    
    trace = go.Pie(labels = labels, values = values, marker = dict(colors=colors))
    fig = go.Figure(data=[trace], layout=layout)
    plot(fig)
    return plot(fig, include_plotlyjs=False, output_type='div')
    
def pie_gender_a(genderstats, title = 'Gender: Breakdown of Assists'):
    """
    Function : Visualises the proportion of assists by each gender for each gender ratio
    
    Inputs: 
        genderstats - Dataframe containing gender ratio based statistics.
        title - Title for Pie Chart. default: 'Gender: Breakdown of Assists'
        
    Outputs:  
        Plotly Pie Chart
    """
    a = genderstats.melt(id_vars = 'Ratio', value_vars=['F Assists', 'M Assists'])
    values = a.value
    labels = a.Ratio + ' Point, ' + a.variable
    layout = go.Layout(title = title, legend = dict(orientation = 'h', x=0.25) )
    colors = ['#5499C7','#45B39D','#85C1E9','#7DCEA0']
    
    trace = go.Pie(labels = labels, values = values, marker = dict(colors=colors))
    fig = go.Figure(data=[trace], layout=layout)
    plot(fig)
    return plot(fig, include_plotlyjs=False, output_type='div')

#%%
    
def vis_disparity(genderstats, indstats, GAtotal):
    """
    Function : Displays the difference in expected and actual number of points scored by each gender pair type.
    
    Inputs: 
        genderstats - Dataframe containing gender ratio based statistics.
        indstats - Dataframe containing individual player statistics.
        GAtotal - two columned list containing all goal and assist pairs 
        
    Outputs:  
        Plotly Bar Chart
    """
    a = {'AG Type':['FF','FM','MF','MM']}
    a = pd.DataFrame(a)
    
    a['F Point %'] = [2/7, 2/7, 2/7, 1/7]
    a['M Point %'] = [1/7, 2/7, 2/7, 2/7]
    
    a['F Numbers'] = a['F Point %'].apply(lambda x: x*genderstats.Converted[genderstats.Ratio=='F'])
    a['M Numbers'] = a['M Point %'].apply(lambda x: x*genderstats.Converted[genderstats.Ratio=='M'])
    a['Theoretical'] = a['F Numbers'] + a['M Numbers']
    
    genderdict = dict(zip(indstats.Name, indstats.Gender))
    b = pd.DataFrame()
    b['Goals'] = GAtotal.Goals.map(genderdict)
    b['Assists'] = GAtotal.Assists.map(genderdict)
    b['GA pair'] = b.Assists + b.Goals
    b = b['GA pair'].value_counts()
    b=b.reindex(a['AG Type'])
    a['Actual']=b.tolist()
    
    a['Difference']=a['Actual']-a['Theoretical']
    #a['text'] = 'Theoretical: ' + a['Theoretical']+', Actual: '+a['Actual']
    trace = go.Bar(
            x=a['AG Type'],
            y = a.Difference,
            marker = dict(
                    color = ['#7DCEA0','#45B39D','#85C1E9','#5499C7']
                             ),
            text = 'Theoretical: ' + a['Theoretical'].round(2).astype(str)+', Actual: '+a['Actual'].astype(str),
    )
    layout = go.Layout(
            title = 'Disparity between Theoretical and Actual Assist/Goal Pair Numbers',
            xaxis=dict(
                    title='Assist/Goal Pair Type'),
            yaxis = dict(
                    title ='Difference')
                    )
    fig = go.Figure(data=[trace], layout = layout)
    plot(fig)
    
    b = a[['Theoretical','Actual','Difference']].copy()
        
    return b, plot(fig, include_plotlyjs= False, output_type='div')

#%% 
    
def vis_GArank(indstats, option='A'):
    """
    Function : Visualises the red zone leaderboard according to gender. Anonymised x-axis for emphasis on gender.
    
    Inputs: 
        indstats - Dataframe containing individual player statistics.
        option - to visualise goals, 'G' or assists 'A'. Default = 'A'.
        
    Outputs:  
        Plotly Bar Chart.
    """
    
    fm2 = dict((k, pco.to_hex(v)) for k,v in FMcmap.items())
    GArank = indstats[['Name','Gender','Goals','Assists']].copy()
    Grank = GArank.sort_values(by=['Goals'], ascending=False)
    Arank = GArank.sort_values(by=['Assists'], ascending=False)
    Grank['Rank']=range(1,len(Grank)+1)
    Arank['Rank']=range(1,len(Arank)+1)

    traceG = go.Bar(
                x = Grank.Rank,
                y = Grank.Goals,
                marker = dict(
                        color = Grank.Gender.map(fm2),
                        )
                    )
    traceA = go.Bar(
                x = Arank.Rank,
                y = Arank.Assists,
                marker = dict(
                        color = Arank.Gender.map(fm2),
                        )
                    )
    layout = go.Layout(
            title = 'Ranking Goals on Gender')
    
    if option == 'A':
        layout = go.Layout(
                title = 'Ranking Assists on Gender',
                xaxis = dict(
                        title = 'Rank',
                        autotick = False,),
                )
        fig = go.Figure(data=[traceA], layout=layout)
        
    elif option=='G':
        layout = go.Layout(
                title = 'Ranking Goals on Gender',
                xaxis = dict(
                        title = 'Rank',
                        autotick = False,),
                )
        fig = go.Figure(data=[traceG], layout=layout)
    
    plot(fig)
    return plot(fig, include_plotlyjs=False, output_type='div')

#%%
    
def vis_odlean(indstats):
    """
    Function : Visualises whether each individual performs better on O or D points. 
    
    Inputs: 
        indstats - Dataframe containing individual player statistics.
        
    Outputs:  
        Plotly Scatter Graph
    """
    a = {'Name':indstats['Name'],'Gender':indstats.Gender,'O Conv':indstats['O Converted']/indstats['O Points'], 'D Conv':indstats['D Converted']/indstats['D Points']}
    a = pd.DataFrame(a)
    a['O Score']=a['O Conv']-np.mean(a['O Conv'])
    a['D Score']=a['D Conv']-np.mean(a['D Conv'])
    
    fm2 = dict((k, pco.to_hex(v)) for k,v in FMcmap.items())
    
    trace2 = go.Scatter(
                x = a['D Score'],
                y = a['O Score'],
                mode = 'markers',
                text = a.Name,
                marker = dict(
                        size = '10',
                        color=a.Gender.map(fm2),
                ))
            
    layout = go.Layout(
            title = 'O/D Lean of Players',
            xaxis = dict(
                    title = 'D Score'),
            yaxis = dict(
                    title = 'O Score'),
            shapes = [{
                    'type':'rect',
                    'x0':-np.std(a['D Score']),
                    'x1':np.std(a['D Score']),
                    'y0':-np.std(a['O Score']),
                    'y1':np.std(a['O Score']),
                    'line':{
                            'color': '#ABB2B9'},
                    }],
            )
    
    fig=go.Figure(data=[trace2], layout = layout)
    plot(fig)

#%% 
def calc_player_turns(pitchtimes, overviews):
    """
    Function : Calculates individual performances based on number of possession on points played.
    
    Inputs: 
        overviews - dictionary containing dataframes of game events
        pitchtimes - Dictionary of dataframes containing player stats
                
    Outputs:  
        B0, B1 - Dataframes containing number of possessions in each conceded or converted point played by each individual.
    """
    A = copy.deepcopy(pitchtimes)
    B0 = copy.deepcopy(A)
    B1 = copy.deepcopy(A)
    for game in A:
        A[game].replace(to_replace=['G','A'], value=1.0, inplace=True)
        A[game].drop(['Points Played', 'Goals', 'Assists'], axis=1, inplace = True)
        
        B0[game]=A[game].copy()
        B1[game]=A[game].copy()        
        
        for i in range(len(overviews[game])):
            if A[game][str(i+1)].dtype == 'object':
                A[game][str(i+1)]=A[game][str(i+1)].astype(float)
        
            if overviews[game]['Did we score'][i]==1:
                B1[game][str(i+1)]=A[game][str(i+1)]*overviews[game]['Number of posessions'][i]
                B0[game][str(i+1)]= np.nan
            else:
                B0[game][str(i+1)]=A[game][str(i+1)]*overviews[game]['Number of posessions'][i]
                B1[game][str(i+1)]= np.nan
   
        B0[game] = B0[game].transpose()
        B1[game] = B1[game].transpose()
    
        B1[game].columns=B1[game].loc['Name']
        B1[game].drop(['Name', 'Gender'], inplace=True)
   
        B0[game].columns=B0[game].loc['Name']
        B0[game].drop(['Name', 'Gender'], inplace=True)
    B0 = pd.concat(B0)
    B1 = pd.concat(B1)
    
    return B0, B1
    
def vis_player_odposviolin(B0, B1, roster):
    """
    Function : Visualises individual performances based on number of possessions per point.
    
    Inputs: 
        B0 - Dataframe containing number of possessions per conceded point played by each individual
        B1 - Dataframe containing number of possessions per converted point played by each individual
        roster - Dataframe containing roster for the entire tournament
        
    Outputs:  
        Plotly Violin Plot.
    """
    data = []
    for name in roster.Name:
        trace1 = go.Violin(
                y=B1[name].dropna(),
                name=str(name),
                spanmode='hard',
                scalemode='count',
                showlegend=True,
                hoveron='violins',
                #points = 'all',
                #pointpos = 0.5,
                #jitter = 0.5,
                bandwidth = 0.25,
                side = 'positive',
                meanline = dict(
                        visible = True,),
                line = dict(
                        color = '#45B39D')
                    )
        data.append(trace1)
    
        trace2 = go.Violin(
                y=B0[name].dropna(),
                name=str(name),
                spanmode='hard',
                side = 'negative',
                scalemode='count',
                hoveron='violins',
                bandwidth=0.25,
                #points ='all',
                #pointpos = -0.5,
                #jitter = 0.5,
                showlegend=True,
                meanline = dict(
                        visible = True,
                    ),
                line = dict(color = '#85C1E9'),
                ) 
        data.append(trace2)
    
    layout = go.Layout(
        title = 'Number of Possessions in Points by Player',
        yaxis = dict(
                title='Number of Possessions',)
        )
    
    fig = go.Figure(data=data, layout=layout)
    plot(fig)