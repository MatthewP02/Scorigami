import plotly.graph_objects as go
import numpy as np
import json

file = "Scorigami.json"

with open(f"{file}", 'r') as f:
    data = json.load(f)

grid = np.array(data['grid'])
grid = grid[:, :163]
hover_text = np.array(data['hover_text'], dtype=object)

fig = go.Figure()
hover_text = np.empty(grid.shape, dtype=object)
hover_text.fill('')

#tells total number of games with score
for i in range(73):
    for j in range(i,163):
        if grid[i][j] == 1:
            hover_text[i][j] = f"Score is impossible."
        else:
            games = round(grid[i][j]*10000)
            if games == 0:
                hover_text[i][j] = f"No games here yet!"
            elif games == 1:
                hover_text[i][j] = f"There has been 1 game with this score.<br>"
                hover_text[i][j] += f"To view all scores, go to Score Researcher tab"
            else:
                hover_text[i][j] = f"There have been {games} games with this score<br>"
                hover_text[i][j] += f"To view all scores, go to Score Researcher tab"
        
        if i == j and grid[i][j] == 0:
            hover_text[i][j] = "Score is no longer possible"
            grid[i][j] = 1

# Load the board
#counts total amount of unique scores
unique_scores = np.count_nonzero((grid >= 0.0001) & (grid <= 0.9999))

# Find the maximum value in the grid where the value is <= 0.5
max_value = np.max(grid[grid <= 0.9999])

fig = go.Figure(data=go.Heatmap(
                    z=grid,
                    text=hover_text,
                    colorscale=[[0, 'rgb(255,255,255)'], [0.0001, 'rgb(211, 255, 194)'], [max_value, 'rgb(68, 235, 2)'], [max_value+0.01, 'rgb(0,0,0)'], [1, 'rgb(0,0,0)']],
                    hoverinfo='z+text',
                    hovertemplate='%{x}:%{y}<br>%{text}<extra></extra><extra></extra>',
                    showscale=False
                ))

# Set axis labels and title
fig.update_layout(
    title=f'College Football Scorigami, {unique_scores} unique scores',
    xaxis=dict(
        tickvals=list(range(163)),
        ticktext=list(range(163)),
        tickfont=dict(size=8),
        title="Winning Team Score",  # Move x-axis title to top
        side="top",
        title_standoff=15,
        fixedrange=True
    ),
    yaxis=dict(
        tickvals=list(range(73)),
        ticktext=list(range(73)),
        tickfont=dict(size=8),
        autorange="reversed",  # Reverse the y-axis
        title='Losing Team Score',
        fixedrange=True
    ),
    autosize=True,  # Disable automatic sizing
    margin=dict(l=50, r=50, b=100, t=100, pad=4)  # Adjust margins
)

# Show the plot
fig.show()
print(unique_scores)

# Save the plot as an HTML file
fig.write_html("games/templates/Scorigami.html")

#print(f'{len(uniquescores)} unique scores')
#np.save('NoTieclemsonigami.npy', grid)

# Convert the figure to a JSON string
