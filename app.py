#https://python.plainenglish.io/a-simple-guide-to-plotly-for-plotting-financial-chart-54986c996682
#https://www.datapine.com/blog/financial-graphs-and-charts-examples/
import streamlit as st
from datetime import date 
import yfinance as yf
from ta.trend import MACD
from ta.momentum import StochasticOscillator
from prophet import Prophet
from prophet.plot import plot_plotly
from plotly import graph_objs as go
from plotly.subplots import make_subplots
from htbuilder import div, big, h2, styles
from htbuilder.units import rem
import pandas as pd
st.set_page_config(layout="wide")

st.title("Nifty 50 Stocks Analysis")

nifty50_stocks = nifty50 = pd.read_html('https://en.wikipedia.org/wiki/NIFTY_50')[1]
symbols = nifty50['Symbol'].to_list()
for count in range(len(symbols)):
    symbols[count] = symbols[count] + ".NS"

st.sidebar.title("Select Stock")
selected_stock = st.sidebar.selectbox("Select Ticker", symbols)
n_years = st.sidebar.slider("Years of prediction:",1,4)
period_options = ['1y','2y','5y','10y','ytd','6mo','3mo','1mo','5d']
sel_period = st.sidebar.selectbox("Select Period", period_options)
period = n_years * 365

sel_ticker = yf.Ticker(selected_stock)

@st.cache
def load_data(ticker):
    data = yf.download(ticker, period = sel_period)
    dt_all = pd.date_range(start=data.index[0],end=data.index[-1])# build complete timeline from start date to end date
    dt_obs = [d.strftime("%Y-%m-%d") for d in pd.to_datetime(data.index)]# retrieve the dates that ARE in the original datset
    dt_breaks = [d for d in dt_all.strftime("%Y-%m-%d").tolist() if not d in dt_obs]# define dates with missing values
    data['MA5'] = data['Close'].rolling(window=5).mean()
    data['MA20'] = data['Close'].rolling(window=20).mean()
    #data.reset_index(inplace = True)
    return (data,dt_breaks)

data_load_state = st.sidebar.text("Loading Data ...")
data,breaks = load_data(selected_stock)
data_load_state.text("Done!")

st.subheader(sel_ticker.info['longName'])#Fullname
col1,col2,col3,col4,col5 = st.columns(5)
col1.metric("Closing Price on " + str(data.reset_index().iloc[-1]['Date'])[0:10], round(data.iloc[-1]['Close'],2), round((data.iloc[-1]['Close']-data.iloc[-1]['Open']),2))
col2.metric("High",round(data['Close'].max()))
col3.metric("Low",round(data['Low'].min()))
lower = data['Close'][0]
upper = data['Close'].iloc[-1]
return_percent = round((upper-lower)/lower * 100,2)
try:
    col4.metric("PE Ratio",sel_ticker.info['trailingPE'])
except:
    col4.metric("PE Ratio","-")

if return_percent>0:
    col5_color = 'GREEN'
if return_percent==0:
    col5_color = 'BLACK'
if return_percent<0:
    col5_color = 'RED'

# for return metric
def display_dial(title, value, color):
        st.markdown(
            div(
                style=styles(
                    text_align="Center",
                    color=color,
                    padding=(rem(0.8), 0, rem(3), 0),
                )
            )(
                h2(style=styles(font_size=rem(0.8), font_weight=600, padding=0))(title),
                big(style=styles(font_size=rem(3), font_weight=800, line_height=1))(
                    value
                ),
            ),
            unsafe_allow_html=True,
        )

with col5:
    display_dial(
        "Returns for selected period", str(return_percent) + "%", col5_color
    )
#col5.metric("Returns", str(return_percent) + "%",delta=str(return_percent) + "%")

# raw data table
def get_date(date):
    return str(date[0:10])

st.subheader('Raw data')
display_data = data.iloc[::-1].reset_index()
display_data['Date'] = display_data['Date'].astype('str').apply(func = get_date)
st.write(display_data)

#graphs
def plot_raw_data():
    #Subplots
    fig = make_subplots(rows=5, cols=1, shared_xaxes=True,row_heights=[2.5,0.1,1,1,1],vertical_spacing=0.03)
    st.subheader("OHLC chart")
    c1,c2 = st.columns(2)
    with c1:
        ma5 = st.checkbox('MA5')
    with c2:    
        ma20 = st.checkbox('MA20')
    fig.add_trace(go.Candlestick(x=data.index,open=data['Open'],high=data['High'],low=data['Low'],close=data['Close'],showlegend=False),row=1,col=1)
    if ma5:   
        fig.add_trace(go.Scatter(x=data.index, y=data['MA5'], opacity=0.7, line=dict(color='blue', width=2), name='MA 5'),row=1,col=1)
    if ma20:
        fig.add_trace(go.Scatter(x=data.index, y=data['MA20'], opacity=0.7, line=dict(color='orange', width=2), name='MA 20'),row=1,col=1)
    # MACD
    macd = MACD(close=data['Close'], window_slow=26,window_fast=12, window_sign=9)
    # stochastic
    stoch = StochasticOscillator(high=data['High'], close=data['Close'],low=data['Low'],window=14, smooth_window=3)

    colors = ['green' if row['Open'] - row['Close'] >= 0 else 'red' for index, row in data.iterrows()]
    # Plot OHLC on 1st subplot (using the codes from before)
    # Plot volume trace on 3nd row 
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'],marker_color = colors), row=3, col=1)
    # Plot MACD trace on 4rd row
    colors = ['green' if val >= 0 else 'red' for val in macd.macd_diff()]
    fig.add_trace(go.Bar(x=data.index, y=macd.macd_diff(),marker_color = colors), row=4, col=1)
    fig.add_trace(go.Scatter(x=data.index,y=macd.macd(),line=dict(color='violet', width=2)), row=4, col=1)
    fig.add_trace(go.Scatter(x=data.index,y=macd.macd_signal(),line=dict(color='blue', width=1)), row=4, col=1)
    # Plot stochastics trace on 5th row
    fig.add_trace(go.Scatter(x=data.index,y=stoch.stoch(),line=dict(color='violet', width=2)), row=5, col=1)
    fig.add_trace(go.Scatter(x=data.index,y=stoch.stoch_signal(),line=dict(color='blue', width=1)), row=5, col=1)
    # update layout by changing the plot size, hiding legends & rangeslider, and removing gaps between dates
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=3, col=1)
    fig.update_yaxes(title_text="MACD", showgrid=False, row=4, col=1)
    fig.update_yaxes(title_text="Stoch", row=5, col=1)

    fig.update_layout(height=1500, showlegend=False, xaxis_rangeslider_visible=True,xaxis_rangeslider_thickness = 0.04,xaxis_rangebreaks=[dict(bounds=["sat", "mon"]),dict(values=breaks)])
    fig.update_layout(margin=go.layout.Margin(
        l=20, #left margin
        r=20, #right margin
        b=20, #bottom margin
        t=20  #top margin
    ))
    st.plotly_chart(fig,use_container_width=True)
plot_raw_data()


# Predict forecast with Prophet.
df_train = data.reset_index()[['Date','Close']]
df_train = df_train.rename(columns={"Date": "ds", "Close": "y"})

m = Prophet()
m.fit(df_train)
future = m.make_future_dataframe(periods=period)
forecast = m.predict(future)

# Show and plot forecast
st.subheader('Forecast data')
st.write(forecast.tail())
    
st.write(f'Forecast plot for {n_years} years')
fig1 = plot_plotly(m, forecast)
st.plotly_chart(fig1,use_container_width=True)

st.subheader("Forecast components")
fig2 = m.plot_components(forecast)
st.write(fig2)

#Company Financials
st.subheader("Company Financials")
financials = sel_ticker.get_financials()
financials = financials.dropna(thresh=3)
financials.columns = list(financials.columns.year)
value = 10000000
financials=(financials/value).round(2)
st.write(financials)
st.write(" *Values reported in crores")

#Balance sheet
st.subheader("Balance Sheet")
balance_sheet = sel_ticker.get_balance_sheet()
balance_sheet = balance_sheet.dropna(thresh=3)
balance_sheet.columns = list(balance_sheet.columns.year)
balance_sheet = (balance_sheet/value).round(2)
st.write(balance_sheet)
st.write(" *Values reported in crores")
