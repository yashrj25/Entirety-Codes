#!/usr/bin/env python
# coding: utf-8

# In[1]:


def get_holidays():
    
    try:
        import datetime
        from dateutil.relativedelta import relativedelta, TH

        import requests
        import pandas as pd
        from bs4 import BeautifulSoup

        def thursday_holidays(year, offset=0):
            link = f'https://zerodha.com/z-connect/traders-zone/holidays/trading-holidays-{year}-nse-bse-mcx'
            soup = requests.get(link)
            table = BeautifulSoup(soup.text, 'html.parser').find_all('table')
            holidays = pd.read_html(str(table))[offset]
            holidays.columns = holidays.iloc[0]
            holidays.drop(0, inplace=True)
            holidays.reset_index(drop=True, inplace=True)

            if (holidays.columns != ['Holidays', 'Date', 'Day']).all() or (holidays.columns != ['Holiday', 'Date', 'Day']).all():
                holidays = holidays.shift()
                holidays.loc[0] = holidays.columns
                holidays.columns = ['Holidays', 'Date', 'Day']
                holidays['Date'] = holidays['Date'].apply(lambda x: datetime.datetime.strptime(x,'%B %d, %Y'))
                holidays['Date'] = holidays['Date'].apply(lambda x: x.date())
                #holidays = holidays[holidays['Day'] == 'Thursday']

            elif (holidays.columns == ['Holidays', 'Date', 'Day']).all() or (holidays.columns == ['Holiday', 'Date', 'Day']).all():
                holidays['Date'] = holidays['Date'].apply(lambda x: datetime.datetime.strptime(x,'%B %d, %Y').date())
                #holidays = holidays[holidays['Day'] == 'Thursday']

            return holidays

        all_thursdays_holidays = pd.DataFrame()

        for year in range(2018, (datetime.date.today().year+1)):
            all_thursdays_holidays = all_thursdays_holidays.append(thursday_holidays(year,0))

        all_thursdays_holidays.reset_index(drop=True,inplace=True)

        return list(all_thursdays_holidays['Date'])
    
    except:
        all_thursdays_holidays = [datetime.date(2018, 1, 26), datetime.date(2018, 2, 13), datetime.date(2018, 3, 2), datetime.date(2018, 3, 29), datetime.date(2018, 3, 30), datetime.date(2018, 5, 1), datetime.date(2018, 8, 15), datetime.date(2018, 8, 22), datetime.date(2018, 9, 13), datetime.date(2018, 9, 20), datetime.date(2018, 10, 2), datetime.date(2018, 10, 18), datetime.date(2018, 11, 7), datetime.date(2018, 11, 8), datetime.date(2018, 11, 23), datetime.date(2018, 12, 25), datetime.date(2019, 3, 4), datetime.date(2019, 3, 21), datetime.date(2019, 4, 17), datetime.date(2019, 4, 19), datetime.date(2019, 4, 29), datetime.date(2019, 5, 1), datetime.date(2019, 6, 5), datetime.date(2019, 8, 12), datetime.date(2019, 8, 15), datetime.date(2019, 9, 2), datetime.date(2019, 9, 10), datetime.date(2019, 10, 2), datetime.date(2019, 10, 8), datetime.date(2019, 10, 21), datetime.date(2019, 10, 28), datetime.date(2019, 11, 12), datetime.date(2019, 12, 25), datetime.date(2020, 2, 21), datetime.date(2020, 3, 10), datetime.date(2020, 4, 2), datetime.date(2020, 4, 6), datetime.date(2020, 4, 10), datetime.date(2020, 4, 14), datetime.date(2020, 5, 1), datetime.date(2020, 5, 25), datetime.date(2020, 10, 2), datetime.date(2020, 11, 16), datetime.date(2020, 11, 30), datetime.date(2021, 1, 26), datetime.date(2021, 3, 11), datetime.date(2021, 3, 29), datetime.date(2021, 4, 2), datetime.date(2021, 4, 14), datetime.date(2021, 4, 21), datetime.date(2021, 5, 13), datetime.date(2021, 7, 21), datetime.date(2021, 8, 19), datetime.date(2021, 9, 10), datetime.date(2021, 10, 15), datetime.date(2021, 11, 4), datetime.date(2021, 11, 5)]
        return all_thursdays_holidays