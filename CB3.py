#!/usr/bin/env python
# coding: utf-8

# In[33]:


from bs4 import BeautifulSoup
from bs4 import BeautifulSoup, NavigableString, Tag
import requests
import re
import calendar
from sqlalchemy import create_engine, Column, String, Integer, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# In[34]:


#init connection to sqlite 
engine = create_engine("sqlite:///events.db")
#create session to cache commands for sqlite engine instance
Session = sessionmaker(bind = engine)
session = Session()
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


# In[35]:


def CB3(url,session,monthInteger):
    #convert the webpage to soup
    page = requests.get(url)
    soup = BeautifulSoup(page.text, features = 'lxml')
    #find the webpage body with event details
    body = soup.find_all(class_='bodytext')[1]
    
    blocks = []
    block = []
    for tag in body:
        #find start of event with every hr tag and append it to blocks
        if len(block) == 0 and tag.name == 'hr':
            block.append(tag)
            continue
        if len(block) > 0 and tag.name == 'hr':
            blocks.append(block)
            block = []
            continue
        #if hr tag not found append the tag to previous block
        block.append(tag)
        
    events = []
    event = {
        'title': None,
        'date': None,
        'details': ''
    }

    #iterate over tags for each event, search for title,date,time and details and add to event dict
    for block in blocks:
        for i,tag in enumerate(block):
            for item in str(tag).split('<br/>'):
                text = BeautifulSoup(item,features = 'lxml').text
                #if event title and date found append to event otherwise init event to None
                #if <b> tag found add as title
                if event['title'] is None and '<b>' in item:
                    event['title'] = text
                    continue
                #if current month found get date and time
                if event['date'] is None and calendar.month_name[monthInteger] in item:
                    date = re.search(r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|(Nov|Dec)(?:ember)?) (([1-3]\d)|(\d))",text)
                    time = re.search(r"((1[0-2]|0?\d):(\d\d)([AaPp][Mm]))",text)
                    event['date'] = str(monthInteger) + '/' + date.group(2) if date else ''
                    event['time'] = time.group(0) if time else ''
                    continue
                #add rest of the tags in event as details
                event['details'] += " " + str(text).replace('\xa0',' ') 
        if not(event['title'] and event['date']):
            event = {
                'title': None,
                'date': None,
                'details': ''
            }
            continue
        #append event with title and date to events list and init event dict to None
        events.append(event)
        event = {
                'title': None,
                'date': None,
                'details': ''
            }
    district = 103
    #remove previous entries
    session.query(Event).filter(Event.district == district).delete()
    session.commit()

    #add items to database
    for event in events:
        row = Event(title=event['title'], date=event['date'],
                    details=event['details'], time=event['time'], district= district)
        session.add(row)
    session.commit()


# In[36]:


CB3('https://www1.nyc.gov/html/mancb3/html/calendar/calendar.shtml',session,2)


# In[37]:


#print all users
for event in session.query(Event).filter(Event.district == 103):
    print(event,"\n-------------------------------")

