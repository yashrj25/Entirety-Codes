#import libraries
import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt
from glob import glob
from dateutil.relativedelta import relativedelta, TH

#fetch all the files from the diretory
path = pd.DataFrame(glob('/nfo_2019-20_data/*'),columns=['location'])
path['data_date'] = path['location'].apply(lambda x: x.split('_')[-1].split('.')[0])
path['data_date'] = path['data_date'].apply(lambda x: datetime.datetime.strptime(x,'%Y-%m-%d'))
path = path.sort_values(['data_date'])
path.reset_index(drop=True,inplace=True)

intraday_trade_log = pd.DataFrame(columns=['Entry_Datetime','Future_Traded_Price','ATM','Days_to_Expiry','CE_Symbol','CE_Entry_Price','CE_Exit_Price','CE_Exit_Datetime','PE_Symbol','PE_Entry_Price','PE_Exit_Price','PE_Exit_Datetime','PnL'])

for index, row in path.iterrows():
    
    try:
        print(index)

        data = pd.read_pickle(row['location'])

        entry_datetime = datetime.datetime.combine(row['data_date'].date(),datetime.time(9,20))
        exit_datetime = datetime.datetime.combine(row['data_date'].date(),datetime.time(15,10))


        #I-CurrentMonth
        #II-NextMonth
        #III-NextToNextMonth
        data['expiry_type'] = np.where((data['instrument_type'] == 'FUT'),data['ticker'].apply(lambda x: x.split('-')[-1].split('.')[0]),'')

        future_expiry_offset = 'I'
        instrument = 'BANKNIFTY'
        base = 100

        futures_data = data[(data['instrument_type'] == 'FUT') & (data['instrument_name'] == instrument) & (data['expiry_type'] == future_expiry_offset)]
        futures_data.reset_index(drop=True,inplace=True)

        atm = futures_data[futures_data['datetime'] == entry_datetime]['open'].iloc[0]
        atm = base*round(atm/base)

        nearest_expiry = row['data_date'].date() + relativedelta(weekday=TH(+1))

        ce_data = data[(data['instrument_type'] == 'CE') & (data['instrument_name'] == instrument) & ((data['expiry_date'] == nearest_expiry)|(data['expiry_date'] == nearest_expiry - datetime.timedelta(days=1))|(data['expiry_date'] == nearest_expiry - datetime.timedelta(days=2))) & (data['strike_price'] == atm)]
        ce_data.reset_index(drop=True,inplace=True)

        pe_data = data[(data['instrument_type'] == 'PE') & (data['instrument_name'] == instrument) & ((data['expiry_date'] == nearest_expiry)|(data['expiry_date'] == nearest_expiry - datetime.timedelta(days=1))|(data['expiry_date'] == nearest_expiry - datetime.timedelta(days=2))) & (data['strike_price'] == atm)]
        pe_data.reset_index(drop=True,inplace=True)

        ce_symbol = ce_data['ticker'].iloc[0]
        pe_symbol = pe_data['ticker'].iloc[0]

        futures_data = futures_data[['datetime','close']].set_index('datetime')
        ce_data = ce_data[['datetime','close']].set_index('datetime')
        pe_data = pe_data[['datetime','close']].set_index('datetime')

        intraday_data = pd.concat([futures_data,ce_data,pe_data],axis=1)
        intraday_data.columns = ['futures_close','ce_close','pe_close']
        intraday_data = intraday_data.ffill()

        #pd.set_option('display.max_rows',400)

        intraday_data.reset_index(inplace=True)

        traded_prices = intraday_data[intraday_data['datetime'] == entry_datetime]

        futures_entry_price = traded_prices['futures_close'].iloc[0]
        ce_entry_price = traded_prices['ce_close'].iloc[0]
        pe_entry_price = traded_prices['pe_close'].iloc[0]

        stop_loss_percentage = 20/100

        ce_stop_loss = ce_entry_price + ce_entry_price*stop_loss_percentage

        pe_stop_loss = pe_entry_price + pe_entry_price*stop_loss_percentage

        entry_time_index = intraday_data[intraday_data['datetime'] == entry_datetime].index[0]

        exit_time_index = intraday_data[intraday_data['datetime'] == exit_datetime].index[0]

        intraday_data = intraday_data[entry_time_index:exit_time_index+1]

        intraday_data['ce_pnl'] = 0
        intraday_data['pe_pnl'] = 0

        intraday_data.reset_index(drop=True,inplace=True)

        ce_stop_loss_counter = 0
        pe_stop_loss_counter = 0
        ce_exit_datetime = ''
        pe_exit_datetime = ''
        ce_exit_price = 0
        pe_exit_price = 0
        ce_pnl = 0
        pe_pnl = 0
        pnl = 0

        for index, row in intraday_data.iterrows():
            ce_ltp = row['ce_close']
            pe_ltp = row['pe_close']

            #criterias for exit
            #none of the stoplosses were hit and time limit is reached
            if (ce_stop_loss_counter == 0) & (pe_stop_loss_counter == 0) & (row['datetime'] == exit_datetime):

                ce_pnl = ce_entry_price - ce_ltp
                pe_pnl = pe_entry_price - pe_ltp

                ce_stop_loss_counter = 1
                pe_stop_loss_counter = 1

                ce_exit_datetime = row['datetime']
                pe_exit_datetime = row['datetime']

                ce_exit_price = ce_ltp
                pe_exit_price = pe_ltp

                intraday_data.loc[index,'ce_pnl'] = ce_pnl
                intraday_data.loc[index,'pe_pnl'] = pe_pnl

                print('none of the stoplosses were hit and time limit is reached')

                pnl = ce_pnl + pe_pnl

                break

            #ce stop loss is hit and none were hit till now
            elif (ce_ltp >= ce_stop_loss) & (ce_stop_loss_counter == 0) & (pe_stop_loss_counter == 0):

                ce_pnl = ce_entry_price - ce_stop_loss
                pe_pnl = pe_entry_price - pe_ltp

                ce_stop_loss_counter = 1

                ce_exit_datetime = row['datetime']

                ce_exit_price = ce_stop_loss

                intraday_data.loc[index,'ce_pnl'] = ce_pnl
                intraday_data.loc[index,'pe_pnl'] = pe_pnl

                print('ce stop loss is hit and none were hit till now')

                pnl = ce_pnl + pe_pnl


            #pe stop loss is hit and none were hit till now
            elif (pe_ltp >= pe_stop_loss) & (ce_stop_loss_counter == 0) & (pe_stop_loss_counter == 0):

                ce_pnl = ce_entry_price - ce_ltp
                pe_pnl = pe_entry_price - pe_stop_loss

                pe_stop_loss_counter = 1

                pe_exit_datetime = row['datetime']

                pe_exit_price = pe_stop_loss

                intraday_data.loc[index,'ce_pnl'] = ce_pnl
                intraday_data.loc[index,'pe_pnl'] = pe_pnl

                print('pe stop loss is hit and none were hit till now')

                pnl = ce_pnl + pe_pnl


            #either ce or pe sl was hit and now other one is also hit
            elif (ce_stop_loss_counter == 1) & (pe_stop_loss_counter == 0):

                if (pe_ltp >= pe_stop_loss) & (row['datetime'] < exit_datetime):

                    pe_pnl = pe_entry_price - pe_stop_loss

                    pe_stop_loss_counter = 1

                    pe_exit_price = pe_stop_loss

                    pe_exit_datetime = row['datetime']

                    intraday_data.loc[index,'ce_pnl'] = ce_pnl
                    intraday_data.loc[index,'pe_pnl'] = pe_pnl

                    print('ce sl was hit and now other one is also hit')

                    pnl = ce_pnl + pe_pnl

                    break


                elif (row['datetime'] == exit_datetime):

                    pe_pnl = pe_entry_price - pe_ltp

                    pe_stop_loss_counter = 1

                    pe_exit_price = pe_ltp

                    pe_exit_datetime = row['datetime']

                    intraday_data.loc[index,'ce_pnl'] = ce_pnl
                    intraday_data.loc[index,'pe_pnl'] = pe_pnl

                    print('pe sl was hit and now other exited based on exit time')

                    pnl = ce_pnl + pe_pnl

                    break


            #either ce or pe sl was hit and now other one is also hit
            elif (ce_stop_loss_counter == 0) & (pe_stop_loss_counter == 1):

                if (ce_ltp >= ce_stop_loss) & (row['datetime'] < exit_datetime):

                    ce_pnl = ce_entry_price - ce_stop_loss

                    ce_stop_loss_counter = 1

                    ce_exit_price = ce_stop_loss

                    ce_exit_datetime = row['datetime']

                    intraday_data.loc[index,'ce_pnl'] = ce_pnl
                    intraday_data.loc[index,'pe_pnl'] = pe_pnl

                    print('pe sl was hit and now other one is also hit')

                    pnl = ce_pnl + pe_pnl

                    break


                elif (row['datetime'] == exit_datetime):

                    ce_pnl = ce_entry_price - ce_ltp

                    ce_stop_loss_counter = 1

                    ce_exit_price = ce_ltp

                    ce_exit_datetime = row['datetime']

                    intraday_data.loc[index,'ce_pnl'] = ce_pnl
                    intraday_data.loc[index,'pe_pnl'] = pe_pnl

                    print('ce sl was hit and now other exited based on exit time')

                    pnl = ce_pnl + pe_pnl

                    break


            #update the pnl during the normal course of the day
            elif (((ce_stop_loss_counter == 0) & (pe_stop_loss_counter == 0)) | ((ce_stop_loss_counter == 1) & (pe_stop_loss_counter == 0))  | ((ce_stop_loss_counter == 0) & (pe_stop_loss_counter == 1)) | ((ce_stop_loss_counter == 1) & (pe_stop_loss_counter == 1))) or row['datetime'] <= exit_datetime:

                ce_pnl = ce_entry_price - ce_ltp
                pe_pnl = pe_entry_price - pe_ltp

                intraday_data.loc[index,'ce_pnl'] = ce_pnl
                intraday_data.loc[index,'pe_pnl'] = pe_pnl

                pnl = ce_pnl + pe_pnl

        intraday_trade_log = intraday_trade_log.append({'Entry_Datetime':entry_datetime,
                                                        'Future_Traded_Price':futures_entry_price,
                                                        'ATM':atm,
                                                        'Days_to_Expiry':(nearest_expiry - entry_datetime.date()).days,
                                                        'CE_Symbol':ce_symbol,
                                                        'CE_Entry_Price':ce_entry_price,
                                                        'CE_Exit_Price':ce_exit_price,
                                                        'CE_Exit_Datetime':ce_exit_datetime,
                                                        'PE_Symbol':pe_symbol,
                                                        'PE_Entry_Price':pe_entry_price,
                                                        'PE_Exit_Price':pe_exit_price,
                                                        'PE_Exit_Datetime':pe_exit_datetime,
                                                        'PnL':pnl},ignore_index=True)
    except Exception as e:
        print(e)
        print(row['location'])

intraday_trade_log['PnL'].cumsum().plot()
