#!/usr/bin/env python
# coding: utf-8

# In[1]:


from selenium import webdriver
import os
import re
import time
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import pandas
from sqlalchemy import create_engine, Column, String, Integer, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# In[2]:


#init connection to sqlite 
engine = create_engine("sqlite:///events.db")
#create session to cache commands for sqlite engine instance
Session = sessionmaker(bind = engine)
session = Session()


# In[3]:


#provide table definition
Base = declarative_base()

class Event(Base):
    __tablename__ = 'event'
    id = Column('id',Integer, primary_key = True)
    district = Column(Integer)
    title = Column(String(100))
    date = Column(String(50))
    details = Column(String(1000))
    time = Column(String(50))

    def __init__(self, title, date, details,time,district):
        self.title = title
        self.date = date
        self.details = details
        self.time = time
        self.district = district
        
    #for print    
    def __repr__(self):
        return f'{self.title} - {self.date}: {self.time}\n {self.details}'
#call to metadata to generate schema
Base.metadata.create_all(engine)


# In[4]:


# Headless option with window-size()
options = webdriver.ChromeOptions()
options.add_argument('--headless')
#set downloads dir to current dir
cwd = os.getcwd()
prefs = {'download.default_directory' : cwd}
options.add_experimental_option('prefs', prefs)
options.add_argument('window-size=1920x1080');
driver = webdriver.Chrome(options=options)
#open airtable, click on 'Donwload SCV'
#wait until the file is donwloaded in current dir
driver.get('https://airtable.com/embed/shrEZxc5vi8McZNFb?backgroundColor=blue')
try:
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH,"//div[contains(text(),'Download CSV')]")))
    element.click()
finally:
    while not os.path.exists(cwd + '/CB11M Meetings Calendar.csv'):
        time.sleep(1)
    if os.path.isfile(cwd + '/CB11M Meetings Calendar.csv'):
        driver.quit()
    else:
        raise ValueError("%s isn't a file!" % file_path)


# In[17]:


#read csv donwloaded from airtable
cwd = os.getcwd()
path = cwd + '/CB11M Meetings Calendar.csv'
df = pandas.read_csv(path)
#copy only 2021 data from csv
currentYear = df[df['Start Time'].str.contains('2021')]
#add new column 'details' and concact with relevent details
currentYear['details'] = currentYear['Location'] +' '+ currentYear['Register to Attend']+ ' ' + currentYear['Meeting Agenda and Files']
#rename column to regular standards
currentYear.rename(columns={'Name': 'title', 'Start Time': 'time','Meeting Agenda and Files':'details'}, inplace=True)
#copy all event title,time and details from currentYear df and convert it to dict
event = currentYear[['title','time','details']].copy()
events_dict = event.to_dict('records')
district = 111
#remove previous entries
session.query(Event).filter(Event.district == district).delete()
session.commit()
#add items to database
for event in events_dict: 
    eDate = re.search(r"^(\d*[/]\d*[/]\d*)",str(event['time']))
    eTime = re.search(r"((1[0-2]|0?\d):(\d\d)([AaPp][Mm]))",event['time'])  
    row = Event(title=event['title'], time = eTime.group(0) if eTime else '',
                    details=event['details'], date = eDate.group(0) if eDate else '', district= district)
    session.add(row)
session.commit()


# In[18]:


#print all users
for event in session.query(Event).filter(Event.district == 111):
    print(event,"\n-------------------------------")


# In[ ]:




