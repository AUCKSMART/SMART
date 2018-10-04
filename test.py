import plotly.plotly as py
import plotly
import plotly.graph_objs as go
from data_test import Articles
import pandas as pd
plotly.tools.set_credentials_file(username='Lionheart', api_key='2G2YOx4ToYo0aNG0p0yt')
Articles = Articles()

df = pd.DataFrame([[ij for ij in i] for i in Articles])
df.rename(columns = {0:'id',1:'title',2:'body',3:'author',4:'create_date',5:'sold'},inplace=True);

trace1 = go.Scatter(
    x=df['title'],
    y=df['sold'],
    mode = 'markers'
)
layout = go.Layout(
    title='Movies Box-Office Sales',
    xaxis=dict( type='log',title='Movies'),
    yaxis=dict( title=" Copies in Millions")
)
data = [trace1]
fig = go.Figure(data=data, layout=layout)
py.plot(fig, filename='Hollywood Movies')