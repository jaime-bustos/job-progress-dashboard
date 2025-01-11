import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from datetime import datetime, timedelta
import plotly.express as px
from job_analyzer import JobAnalyzer


# load data
your_file_name = "example.xlsx"
file_path = "/Users/jaimebustosjr/Projects/job-progress-dashboard/src/" + your_file_name
df = pd.read_excel(file_path)

# convert 'Date Applied' to datetime
df['Date Applied'] = pd.to_datetime(df['Date Applied'])

# function to determine application status
# if date applied is less than 4 months ago, set status to pending

def update_status(df):

    four_months_ago = datetime.now() - timedelta(days=120)

    def determine_status(row):
        # check if offered (should be checked first)
        if row['Offered'] == 1:
            return 'Offered'
        
        # check if interviewed
        if row['Interviewed'] == 1:
            return 'Interviewed'
        
        # check if application is old (>4 months) and no interview
        if pd.isna(row['Interviewed']) and row['Date Applied'] < four_months_ago:
            return 'Rejected'
        
        # default case - application is still pending
        return 'Pending'
    
    # apply the status determination function to each row
    df['Status'] = df.apply(determine_status, axis=1)
    return df

# update status
df = update_status(df)

# initialize the Dash app
app = dash.Dash(__name__)

# layout of the dashboard
app.layout = html.Div([
    html.H1("Job Application Progress Dashboard", style={'text-align': 'center', 'font-family': 'Helvetica Neue'}),
    
    # Status filter dropdown
    dcc.Dropdown(
        id='status-filter',
        options=[{'label': status, 'value': status} for status in df['Status'].unique()],
        multi=True,
        placeholder='Filter by Status',
        style={'font-family': 'Helvetica Neue', 'margin-bottom': '20px'}
    ),

    # new horizontal stack layout for status section
    html.Div([
        # left section
        html.Div([
            dcc.Graph(id='status-bar-chart', style={'font-family': 'Helvetica Neue'}),
        ], style={'width': '50%', 'display': 'inline-block', 'vertical-align': 'top'}),
        
        # right section
        html.Div([
            html.Div(id='summary', style={
                'margin': '20px',
                'padding': '20px',
                'text-align': 'center',
                'font-family': 'Helvetica Neue',
                'border': '1px solid #ddd',
                'border-radius': '5px',
                'background-color': '#f9f9f9'
            })
        ], style={'width': '50%', 'display': 'inline-block', 'vertical-align': 'top'}),
    ], style={'display': 'flex', 'margin-bottom': '20px'}),

    # timeline chart (full width)
    dcc.Graph(id='timeline-trend-chart', style={'font-family': 'Helvetica Neue'}),
], style={'padding': '20px'})

# initialize the analyzer
job_analyzer = JobAnalyzer()

# callback to update the bar chart, timeline trend, and summary
@app.callback(
    [Output('status-bar-chart', 'figure'),
     Output('timeline-trend-chart', 'figure'),
     Output('summary', 'children')],
    [Input('status-filter', 'value')]
)
def update_dashboard(selected_status):
    
    filtered_df = df if not selected_status else df[df['Status'].isin(selected_status)]
    
    # bar chart
    status_counts = filtered_df['Status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    fig_bar = px.bar(status_counts, x='Status', y='Count', title='Job Application Status')
    
    # timeline trend
    timeline_counts = filtered_df.groupby('Date Applied').size().reset_index(name='Count')
    timeline_counts = timeline_counts.sort_values(by='Date Applied')
    
    fig_timeline_bar = px.bar(timeline_counts, x='Date Applied', y='Count', title='Timeline of Job Applications')
    fig_timeline_bar.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all", label="All")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date",
            autorange=True
        )
    )

    # enhanced summary statistics
    total_apps = len(filtered_df)
    interviewed = len(filtered_df[filtered_df['Status'] == 'Interviewed'])
    offered = len(filtered_df[filtered_df['Status'] == 'Offered'])
    pending = len(filtered_df[filtered_df['Status'] == 'Pending'])
    rejected = len(filtered_df[filtered_df['Status'] == 'Rejected'])
    
    # get job insights using the analyzer
    job_insights = job_analyzer.analyze_job_trends(filtered_df)
    
    # update summary_text to include job insights
    summary_text = html.Div([
        html.H3("Application Summary", style={'margin-bottom': '20px'}),
        html.Div([
            html.P(f"Total Applications: {total_apps}"),
            html.P(f"Pending: {pending}"),
            html.P(f"Interviewed: {interviewed}"),
            html.P(f"Offered: {offered}"),
            html.P(f"Rejected: {rejected}"),
            html.Hr(),
            html.P(f"Interview Rate: {interviewed/total_apps:.1%}" if total_apps > 0 else "N/A"),
            html.P(f"Offer Rate: {offered/total_apps:.1%}" if total_apps > 0 else "N/A"),
            html.Hr(),
            html.H4("Job Search Insights", style={'margin-top': '20px', 'margin-bottom': '10px'}),
            *[html.P(insight, style={'font-style': 'italic'}) for insight in job_insights],
        ], style={'text-align': 'left'})
    ])
    
    return fig_bar, fig_timeline_bar, summary_text

# run the app
if __name__ == '__main__':
    app.run_server(debug=True)