import pandas as pd
import datetime
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from glob import glob
from dateutil.relativedelta import relativedelta, TH

intraday_trade_log = pd.read_csv('banknifty_short_straddle_920_1510_20%.csv')

intraday_trade_log['Entry_Datetime'] = intraday_trade_log['Entry_Datetime'].apply(lambda x: datetime.datetime.strptime(x,'%Y-%m-%d %H:%M:%S'))
intraday_trade_log['Date'] = intraday_trade_log['Entry_Datetime'].apply(lambda x: x.date())

plt.figure(figsize=(20,8))
intraday_trade_log['PnL'].cumsum().plot()

intraday_trade_log.info()

import missingno as msno

msno.bar(intraday_trade_log)

intraday_trade_log = intraday_trade_log[intraday_trade_log['CE_Entry_Price'].notna()]

intraday_trade_log = intraday_trade_log[intraday_trade_log['CE_Exit_Price'].notna()]

intraday_trade_log = intraday_trade_log[intraday_trade_log['PE_Entry_Price'].notna()]

intraday_trade_log = intraday_trade_log[intraday_trade_log['PE_Exit_Price'].notna()]

intraday_trade_log['PnL'] = (intraday_trade_log['CE_Entry_Price'] - intraday_trade_log['CE_Exit_Price']) + (intraday_trade_log['PE_Entry_Price'] - intraday_trade_log['PE_Exit_Price'])

intraday_trade_log['PnL'].cumsum().plot()

insample_trade_log = intraday_trade_log[:int(len(intraday_trade_log)/2)]

outsample_trade_log = intraday_trade_log[int(len(intraday_trade_log)/2):]

initial_capital = 200000
intraday_trade_log['Quantity'] = 25

intraday_trade_log['Entry_Price'] = intraday_trade_log['CE_Entry_Price']+intraday_trade_log['PE_Entry_Price']
intraday_trade_log['Exit_Price'] = intraday_trade_log['CE_Exit_Price']+intraday_trade_log['PE_Exit_Price']

intraday_trade_log['Entry_Including_Slippage'] = intraday_trade_log['Entry_Price'] - (intraday_trade_log['Entry_Price']*0.02) #2% here means 1% for each ce and pe
intraday_trade_log['Exit_Including_Slippage'] = intraday_trade_log['Exit_Price'] + (intraday_trade_log['Exit_Price']*0.02) #2% here means 1% for each ce and pe

intraday_trade_log['PnL_Including_Slippages'] = (intraday_trade_log['Entry_Including_Slippage']-intraday_trade_log['Exit_Including_Slippage'])*intraday_trade_log['Quantity']

intraday_trade_log['PnL_Including_Slippages_Cumulative_Sum'] = intraday_trade_log['PnL_Including_Slippages'].cumsum()

intraday_trade_log['Equity'] = 0
intraday_trade_log['Rate_of_Return'] = 0

intraday_trade_log

for i in range(len(list(intraday_trade_log.index))):

    if i == 0:
        intraday_trade_log['Equity'].iloc[i] = initial_capital + intraday_trade_log['PnL_Including_Slippages'].iloc[i]
        intraday_trade_log['Rate_of_Return'].iloc[i] = (intraday_trade_log['PnL_Including_Slippages'].iloc[i]/initial_capital)*100
    else:
        intraday_trade_log['Equity'].iloc[i] = intraday_trade_log['Equity'].iloc[i-1] + intraday_trade_log['PnL_Including_Slippages'].iloc[i]
        intraday_trade_log['Rate_of_Return'].iloc[i] = (intraday_trade_log['PnL_Including_Slippages'].iloc[i]/intraday_trade_log['Equity'].iloc[i-1])*100

intraday_trade_log

win_rate = round(len(intraday_trade_log[intraday_trade_log['PnL_Including_Slippages']>0])/len(intraday_trade_log),2)
print(f'Win Rate:{win_rate}')

mean_win = intraday_trade_log[intraday_trade_log['PnL_Including_Slippages']>0]['PnL_Including_Slippages'].mean()
mean_loss = intraday_trade_log[intraday_trade_log['PnL_Including_Slippages']<0]['PnL_Including_Slippages'].mean()
risk_reward = abs(mean_win/mean_loss)
expectancy = round((win_rate*risk_reward) - ((1-win_rate)*1),2)

print(f'Expectancy:{expectancy}')

number_of_trading_days_in_a_year = 252
risk_free_interest_rate = 5
mean = intraday_trade_log['Rate_of_Return'].mean() * number_of_trading_days_in_a_year - risk_free_interest_rate
sigma = intraday_trade_log['Rate_of_Return'].std() * np.sqrt(number_of_trading_days_in_a_year)
sharpe_ratio = round(mean/sigma,2)

print(f'Sharpe Ratio:{sharpe_ratio}')

downside_standard_deviation = intraday_trade_log[intraday_trade_log['Rate_of_Return']<0]['Rate_of_Return'].std() * np.sqrt(number_of_trading_days_in_a_year)
sortino_ratio = round(mean/downside_standard_deviation,2)
print(f'Sortino Ratio:{sortino_ratio}')

intraday_trade_log['Drawdown'] = intraday_trade_log['PnL_Including_Slippages_Cumulative_Sum'] - intraday_trade_log['PnL_Including_Slippages_Cumulative_Sum'].cummax()
max_drawdown = round(intraday_trade_log['Drawdown'].min(),2)
print(f'Max Drawdown [Rs.] :{max_drawdown}')

max_drawdown_percent = round(max_drawdown/intraday_trade_log[intraday_trade_log['Drawdown'] == intraday_trade_log['Drawdown'].min()]['Equity'].iloc[0]*100,2)
print(f'Max Drawdown Percent:{max_drawdown_percent}')

intraday_trade_log['Recovery'] = 0
for i in range(len(intraday_trade_log)):
    if (intraday_trade_log['Drawdown'].iloc[i] < 0):
        intraday_trade_log['Recovery'].iloc[i] = intraday_trade_log['Recovery'].iloc[i-1] + 1
recovery_trades = intraday_trade_log['Recovery'].max()

print(f'Number of trades done from Drawdown to achieve a new peak: {recovery_trades}')

intraday_trade_log_equity_high = intraday_trade_log[intraday_trade_log['Recovery'] == 0]
intraday_trade_log_equity_high['number_days_between_equity_highs'] = (intraday_trade_log_equity_high['Entry_Datetime'] - intraday_trade_log_equity_high['Entry_Datetime'].shift())
recovery_days = int(intraday_trade_log_equity_high['number_days_between_equity_highs'].apply(lambda x: x.days).max())
print(f'Number of Days taken from Drawdown to achieve a new peak: {recovery_days}')

number_of_trading_days_for_this_backtest = (intraday_trade_log.iloc[-1]['Entry_Datetime'].date() - intraday_trade_log.iloc[0]['Entry_Datetime'].date()).days
cagr = (((intraday_trade_log.iloc[-1]['Equity']/initial_capital)**(1/(number_of_trading_days_for_this_backtest/365)))-1)*100
cagr = round(cagr,2)

print(f'CAGR:{cagr}')

calmar_ratio = round(abs(cagr/max_drawdown_percent),2)

print(f'Calmar Ratio:{calmar_ratio}')

backtest_start_date = intraday_trade_log.iloc[0]['Entry_Datetime'].date()
backtest_start_date

backtest_end_date = intraday_trade_log.iloc[-1]['Entry_Datetime'].date()
backtest_end_date

number_of_trades = len(intraday_trade_log)
number_of_trades

number_of_wins = len(intraday_trade_log[intraday_trade_log['PnL_Including_Slippages']>0])
print(f'Number of Wins: {number_of_wins}')

number_of_losses = len(intraday_trade_log[intraday_trade_log['PnL_Including_Slippages']<0])
print(f'Number of Losses: {number_of_losses}')

average_profit_per_trade = round(intraday_trade_log[intraday_trade_log['PnL_Including_Slippages'] > 0]['PnL_Including_Slippages'].mean(),2)
print(f'Average Profit Per Trade: {average_profit_per_trade}')

average_loss_per_trade = round(intraday_trade_log[intraday_trade_log['PnL_Including_Slippages'] < 0]['PnL_Including_Slippages'].mean(),2)
print(f'Average Loss Per Trade: {average_loss_per_trade}')

max_pnl = round(intraday_trade_log['PnL_Including_Slippages'].max(),2)
print(f'Max PnL Point:{max_pnl}')

min_pnl = round(intraday_trade_log['PnL_Including_Slippages'].min(),2)
print(f'Min PnL Point:{min_pnl}')

median_of_trade = round(intraday_trade_log['PnL_Including_Slippages'].median(),2)
print(f'Median:{median_of_trade}')

gross_profit = intraday_trade_log[intraday_trade_log['PnL_Including_Slippages']>0]['PnL_Including_Slippages'].sum()
gross_loss = intraday_trade_log[intraday_trade_log['PnL_Including_Slippages']<0]['PnL_Including_Slippages'].sum()

profit_factor = round(abs(gross_profit/gross_loss),2)
print(f'Profit Factor:{profit_factor}')

outlier_adjusted_profit_factor = round(abs((gross_profit-max_pnl)/gross_loss),2)
print(f'Outlier Adjusted Profit Factor:{outlier_adjusted_profit_factor}')

intraday_trade_log['Continuous_Wins'] = 0
intraday_trade_log['Continuous_Losses'] = 0

for i in range(1,len(intraday_trade_log)):
    if intraday_trade_log['PnL_Including_Slippages'].iloc[i-1] > 0:
        intraday_trade_log['Continuous_Wins'].iloc[i] = intraday_trade_log['Continuous_Wins'].iloc[i-1]+1
    if intraday_trade_log['PnL_Including_Slippages'].iloc[i-1] < 0:
        intraday_trade_log['Continuous_Losses'].iloc[i] = intraday_trade_log['Continuous_Losses'].iloc[i-1]+1

consecutive_wins = intraday_trade_log['Continuous_Wins'].max()
consecutive_losses = intraday_trade_log['Continuous_Losses'].max()
print(f'Consecutive Wins:{consecutive_wins}')
print(f'Consecutive Losses:{consecutive_losses}')

metrics = pd.DataFrame(columns=['Backtest Start Date','Backtest End Date','Number of Trades','Number of Wins','Number of Losses','Average Profit','Average Loss','Maximum Profit Points','Maximum Loss Points','Median Trade','Win Rate','Expectancy','Sharpe Ratio','Sortino Ratio','Max Drawdown','Max Drawdown Percent','Days Taken to Recover From Drawdown','Number of Trades to Recover From Drawdown','Calmar','CAGR','Consecutive Wins','Consecutive Losses','Profit Factor (Amount of Profit per unit of Loss)','Outlier Adjusted Profit Factor (Profit Factor except that One Exceptional Biggest Winner)'])

metrics = metrics.append({'Backtest Start Date':backtest_start_date, 
                          'Backtest End Date':backtest_end_date, 
                          'Number of Trades':number_of_trades,
                          'Number of Wins':number_of_wins,
                          'Number of Losses':number_of_losses,
                          'Average Profit':average_profit_per_trade,
                          'Average Loss':average_loss_per_trade,
                          'Maximum Profit Points':max_pnl,
                          'Maximum Loss Points':min_pnl,
                          'Median Trade':median_of_trade,
                          'Win Rate':win_rate,
                          'Expectancy':expectancy,
                          'Sharpe Ratio':sharpe_ratio,
                          'Sortino Ratio':sortino_ratio,
                          'Max Drawdown':max_drawdown,
                          'Max Drawdown Percent':max_drawdown_percent,
                          'Days Taken to Recover From Drawdown':recovery_days,
                          'Number of Trades to Recover From Drawdown':recovery_trades,
                          'Calmar':calmar_ratio,
                          'CAGR':cagr,
                          'Consecutive Wins':consecutive_wins,
                          'Consecutive Losses':consecutive_losses,
                          'Profit Factor (Amount of Profit per unit of Loss)':profit_factor,
                          'Outlier Adjusted Profit Factor (Profit Factor except that One Exceptional Biggest Winner)':outlier_adjusted_profit_factor},ignore_index=True)

metrics.T

returns = intraday_trade_log[['Entry_Datetime','Equity']]

returns.set_index('Entry_Datetime',inplace=True)

returns = returns.resample('M').last()

returns['%Change'] = returns['Equity'].pct_change()*100

returns.reset_index(inplace=True)

returns['Year'] = returns['Entry_Datetime'].apply(lambda x: x.year)
returns['Month'] = returns['Entry_Datetime'].apply(lambda x: x.month)

import calendar

returns['Month'] = returns['Month'].apply(lambda x: calendar.month_abbr[x])

returns = returns[['Entry_Datetime', '%Change', 'Year', 'Month']]

x = returns.groupby(['Year','Month'])['%Change'].mean()

broad_returns = x.unstack()

broad_returns['Total'] = broad_returns[broad_returns.columns].sum(axis=1)

broad_returns = broad_returns[['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Total']]

broad_returns = round(broad_returns,2)

broad_returns

import seaborn as sns
cm = sns.light_palette('green',as_cmap=True)

broad_returns_image = broad_returns.style.background_gradient(cmap=cm).set_precision(2).highlight_min(axis=0,color='lightgreen').highlight_max(axis=0,color='green')

broad_returns_image

drawdown_values = intraday_trade_log['Drawdown'].drop_duplicates().nsmallest(5)
drawdown_df = intraday_trade_log[intraday_trade_log['Drawdown'].isin(list(drawdown_values.values))].copy()

drawdown_figure = plt.figure(figsize=(20,8))
plt.plot(intraday_trade_log['Date'],intraday_trade_log['Equity'])
plt.scatter(drawdown_df['Date'],drawdown_df['Equity'],color='black')

returns['Month-Year'] = returns.apply(lambda x: (str(x['Month']) + ' ' + str(x['Year'])[-2:]).upper(),axis=1)

monthly_returns_barplot = plt.figure(figsize=(20,8))
sns.barplot(x='Month-Year',y='%Change',data=returns,estimator=np.median,ci=0)

metrics.T

drawdown_figure

broad_returns_image

monthly_returns_barplot