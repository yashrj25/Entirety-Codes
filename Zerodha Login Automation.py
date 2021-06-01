from selenium import webdriver
#chrome options class is used to manipulate various properties of Chrome driver
from selenium.webdriver.chrome.options import Options
#waits till the content loads
from selenium.webdriver.support.ui import WebDriverWait
#finds that content
from selenium.webdriver.support import expected_conditions as EC
#find the above condition/conntent by the xpath, id etc.
from selenium.webdriver.common.by import By

#zerodha
from kiteconnect import KiteConnect
from time import sleep
import urllib.parse as urlparse
import pandas as pd

#credentials
api_key = 'xxxxxxxxxxxx'
api_secret = 'xxxxxxxxxxxx'
account_username = 'xxxxxxxxxxxx'
account_password = 'xxxxxxxxxxxx'
account_two_fa = int(111111)

kite = KiteConnect(api_key=api_key)

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
driver = webdriver.Chrome(executable_path='/Users/entirety/Desktop/chromedriver',options=options)

driver.get(kite.login_url())

#//tagname[@attribute='value']
#tagname = div,

#identify login section
form = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//div[@class="login-form"]')))

#enter the ID
driver.find_element_by_xpath("//input[@type='text']").send_keys(account_username)


#enter the password
driver.find_element_by_xpath("//input[@type='password']").send_keys(account_password)


#submit
driver.find_element_by_xpath("//input[@type='submit']").click()


#sleep for a second so that the page can submit and proceed to upcoming question (2fa)
sleep(1)
form = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//div[@class="login-form"]//form')))

#identify login section for 2fa
#enter the 2fa code
driver.find_element_by_xpath("//input[@type='password']").send_keys(account_two_fa)

#submit
driver.find_element_by_xpath("//input[@type='submit']").click()
sleep(1)
current_url = driver.current_url

driver.close()

parsed = urlparse.urlparse(current_url)
request_token = urlparse.parse_qs(parsed.query)['request_token'][0]

access_token = kite.generate_session(request_token=request_token,api_secret=api_secret)['access_token']

kite.set_access_token(access_token)

kite.ltp('MCX:CRUDEOIL21JUNFUT')