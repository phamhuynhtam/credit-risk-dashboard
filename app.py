# app.py - Credit Risk Dashboard (Hoàn chỉnh, chạy được)
import os
import pandas as pd
import numpy as np
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, dash_table
from dash.dash_table.Format import Format, Scheme
import dash_bootstrap_components as dbc
from datetime import datetime

# Tạo dữ liệu mẫu nếu chưa có
def create_sample_data(filename='credit_risk_data.csv', n=1000):
    if os.path.exists(filename):
        return pd.read_csv(filename)
    np.random.seed(42)
    data = {
        'Customer_ID': np.arange(1, n+1),
        'Age': np.random.randint(18, 71, size=n),
        'Income': np.random.uniform(20000, 100000, size=n).round(2),
        'Debt': np.random.uniform(5000, 50000, size=n).round(2),
        'Credit_Score': np.random.randint(300, 851, size=n),
        'Loan_Amount': np.random.uniform(5000, 100000, size=n).round(2),
        'Interest_Rate': np.random.uniform(3.0, 18.0, size=n).round(2),
    }
    prob_default = np.where(data['Credit_Score'] < 600, 0.6,
                   np.where(data['Credit_Score'] < 700, 0.3, 0.1))
    data['Default_Status'] = np.random.binomial(1, prob_default)
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    return df

df = create_sample_data()

# Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("Credit Risk Dashboard", className="text-center text-light mt-4"), width=12)),

    dbc.Row([
        dbc.Col([
            html.H4("Bộ lọc", className="text-light"),
            html.Label("Nhóm tuổi", className="text-light mt-3"),
            dcc.Dropdown(id='age-filter', options=[
                {'label': 'Tất cả', 'value': 'all'},
                {'label': '18-30', 'value': '18-30'},
                {'label': '31-50', 'value': '31-50'},
                {'label': '51+', 'value': '51+'}
            ], value='all', clearable=False),
            html.Label("Thu nhập (USD)", className="text-light mt-3"),
            dcc.RangeSlider(id='income-slider', min=20000, max=100000, step=5000,
                            value=[20000, 100000], marks={i: f'${i//1000}k' for i in range(20000, 100001, 20000)}),
            html.Div(id='update-time', className="text-muted small mt-3")
        ], width=3, className="bg-dark p-3 rounded"),

        dbc.Col([
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([html.H5(id='total-customers'), html.P("Tổng KH")])), width=3),
                dbc.Col(dbc.Card(dbc.CardBody([html.H5(id='default-rate'), html.P("Tỷ lệ vỡ nợ")])), width=3),
                dbc.Col(dbc.Card(dbc.CardBody([html.H5(id='avg-score'), html.P("TB Credit Score")])), width=3),
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(dcc.Graph(id='histogram-credit-score'), width=6),
                dbc.Col(dcc.Graph(id='scatter-age-income'), width=6),
            ], className="mb-4"),

            dbc.Row([
                dbc.Col(dcc.Graph(id='pie-default'), width=4),
                dbc.Col(dash_table.DataTable(
                    id='high-risk-table',
                    columns=[
                        {"name": "ID", "id": "Customer_ID"},
                        {"name": "Tuổi", "id": "Age"},
                        {"name": "Thu nhập", "id": "Income", "type": "numeric", "format": Format(precision=0, scheme=Scheme.fixed).group(True)},
                        {"name": "Credit Score", "id": "Credit_Score"},
                        {"name": "Nợ", "id": "Debt", "type": "numeric", "format": Format(precision=0, scheme=Scheme.fixed).group(True)},
                    ],
                    style_cell={'textAlign': 'center', 'backgroundColor': '#333', 'color': 'white'},
                    style_header={'backgroundColor': '#222', 'color': 'white', 'fontWeight': 'bold'},
                    page_size=10
                ), width=8),
            ])
        ], width=9)
    ]),

    dcc.Interval(id='interval-component', interval=30*1000, n_intervals=0)
], fluid=True, style={'backgroundColor': '#1a1a1a'})

@app.callback(
    [Output('histogram-credit-score', 'figure'), Output('scatter-age-income', 'figure'),
     Output('pie-default', 'figure'), Output('high-risk-table', 'data'),
     Output('total-customers', 'children'), Output('default-rate', 'children'),
     Output('avg-score', 'children'), Output('update-time', 'children')],
    [Input('interval-component', 'n_intervals'), Input('age-filter', 'value'), Input('income-slider', 'value')]
)
def update_dashboard(n, age_group, income_range):
    global df
    try:
        df_new = pd.read_csv('credit_risk_data.csv')
        if not df_new.equals(df): df = df_new
    except: pass

    filtered = df.copy()
    if age_group != 'all':
        if age_group == '18-30': filtered = filtered[(filtered['Age'] >= 18) & (filtered['Age'] <= 30)]
        elif age_group == '31-50': filtered = filtered[(filtered['Age'] >= 31) & (filtered['Age'] <= 50)]
        elif age_group == '51+': filtered = filtered[filtered['Age'] > 50]
    filtered = filtered[(filtered['Income'] >= income_range[0]) & (filtered['Income'] <= income_range[1])]

    total = len(filtered)
    default_rate = filtered['Default_Status'].mean() * 100
    avg_score = filtered['Credit_Score'].mean()

    fig1 = px.histogram(filtered, x='Credit_Score', color='Default_Status', nbins=30, barmode='overlay',
                        color_discrete_map={0: '#00cc96', 1: '#ef553b'}, title='Credit Score theo Vỡ nợ')
    fig1.update_layout(plot_bgcolor='#2d2d2d', paper_bgcolor='#2d2d2d', font_color='white')

    fig2 = px.scatter(filtered, x='Age', y='Income', color='Default_Status', size='Loan_Amount',
                      hover_data=['Customer_ID'], color_discrete_map={0: '#00cc96', 1: '#ef553b'},
                      title='Tuổi vs Thu nhập')
    fig2.update_layout(plot_bgcolor='#2d2d2d', paper_bgcolor='#2d2d2d', font_color='white')

    pie_data = filtered['Default_Status'].value_counts()
    fig3 = px.pie(values=pie_data.values, names=['Không vỡ nợ', 'Vỡ nợ'],
                  color_discrete_sequence=['#00cc96', '#ef553b'], title='Tỷ lệ vỡ nợ')
    fig3.update_layout(plot_bgcolor='#2d2d2d', paper_bgcolor='#2d2d2d', font_color='white')

    high_risk = filtered[filtered['Credit_Score'] < 600].sort_values('Credit_Score').head(10)
    table_data = high_risk[['Customer_ID', 'Age', 'Income', 'Credit_Score', 'Debt']].to_dict('records')

    update_time = f"Cập nhật: {datetime.now().strftime('%H:%M:%S')}"

    return fig1, fig2, fig3, table_data, f"{total:,}", f"{default_rate:.1f}%", f"{avg_score:.0f}", update_time

if __name__ == '__main__':
    app.run_server(debug=False)
