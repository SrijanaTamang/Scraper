#!/usr/bin/env python
# coding: utf-8

# In[12]:


from bs4 import BeautifulSoup
import unicodedata
import requests
import re
from sqlalchemy import create_engine, Column, String, Integer, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# In[13]:


#init connection to sqlite 
engine = create_engine("sqlite:///events.db")
#create session to cache commands for sqlite engine instance
Session = sessionmaker(bind = engine)
session = Session()


# In[14]:


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


# In[15]:


def CB1(url,session):    
    page = requests.get(url)
    soup = BeautifulSoup(page.text,'html.parser')
    divs = soup.find(class_='about-description').find_all('div', recursive=False)[1]

    events = []
    event_num = None
    event = []
    details = []

    for div in divs.find_all('div'):
        #ends event and starts a new event
        if event_num is not None and re.search(r"^(\d*[/]\d*)",div.text):
            events.append(event)
            event = []
            event_num += 1

        #finds intial event and starts the process
        if event_num is None and re.search(r"^(\d*[/]\d*)",div.text):
            event = []
            event_num = 0

        event.append(div)

    #append the last event
    if len(event):
        events.append(event)
        
    #iterate through events, search for date, time, title, details to events_dict
    events_dict = {}
    for i, event in enumerate(events):
        event_string = ''.join([tag.text for tag in event])
        date = re.search(r"^(\d*[/]\d*)",event_string).group(0)
        if event[0].find('b') is None:
            title = event[0].find('strong').text
        else:
            title = event[0].find('b').text
        details = ''.join([tag.text for tag in event[1:]])
        details = details.strip().replace('\xa0', '')
        time = re.search(r"((1[0-2]|0?\d):(\d\d) ([AaPp][Mm]))",event_string)  

        events_dict[i] = {
            'date': date,
            'time':time.group(0) if time else '',
            'title': title,
            'details':details
        }
    
    district = 101
    #remove previous entries from db
    session.query(Event).filter(Event.district == district).delete()
    session.commit()
    #add items from events_dict to database
    for event in events_dict.values():
        row = Event(title=event['title'], date=event['date'],
                    details=event['details'], time=event['time'], district= district)
        session.add(row)
    session.commit()


# In[16]:


CB1('https://www1.nyc.gov/site/manhattancb1/meetings/committee-agendas.page',session)


# In[17]:


#print all users
for event in session.query(Event).filter(Event.district == 101):
    print(event,"\n-------------------------------")


# In[ ]:




