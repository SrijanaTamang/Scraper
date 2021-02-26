#!/usr/bin/env python
# coding: utf-8

# In[50]:


from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
import calendar
from sqlalchemy import create_engine, Column, String, Integer, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# In[51]:


#init connection to sqlite 
engine = create_engine("sqlite:///events.db")
#create session to cache commands for sqlite engine instance
Session = sessionmaker(bind = engine)
session = Session()


# In[52]:


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


# In[53]:


def CB6(url,monthInteger,session):
    #read url page to find calender box with events
    hdr = {'User-Agent': 'Mozilla/5.0'}
    req = Request(url,headers=hdr)
    page = urlopen(req)
    soup = BeautifulSoup(page, features = 'lxml')
    calBox = soup.find_all(class_='meetings_calendar_box')
    event_dict = {
    'title': None,
    'date': None,
    'time' : None,
    'details': ''}
    events = []
    
    #iterate over tags for each event from calender box, search for title,date,time and details and add to event dict
    for div in calBox:
        for tag in div:
            for item in tag:
            #if event title and date found append to event otherwise init event to None
                #find h2 tag, add as title
                if event_dict['title'] is None and 'h2' in str(item):
                    event_dict['title'] = item.text
                    continue
                 #find tag with current month, get date,time
                if event_dict['date'] is None and calendar.month_name[monthInteger] in str(item):
                    date = re.search(r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|(Nov|Dec)(?:ember)?) (([1-3]\d)|(\d))",item.text)
                    event_dict['date'] = str(monthInteger) + '/' + date.group(2) if date else None
                    time = re.search(r"((1[0-2]|0?\d):(\d\d)([AaPp][Mm]))",item.text)
                    event_dict['time'] = time .group(0)if time else None
                    continue
                #add rest of the tag as detils
                event_dict['details']  += " " + item.text.replace('\xa0','').replace('View Calendar »Subscribe »','').replace('\n','').replace('Click here to register to join the meeting via Zoom','').replace('Click to show the meeting agenda','')      
                if 'zoom.us/webinar' in str(item):
                    s = BeautifulSoup((str(item)), features = 'lxml')
                    for a in s.find_all('a', href=True): 
                        event_dict['details'] += 'Zoom Link: ' + a['href'] 
                        
        if not(event_dict['title'] and event_dict['date']):
            event_dict = {
                'title': None,
                'date': None,
                'time' : None,
                'details': ''
            }
            continue
        #append event with title and date to events list and init event dict to None
        events.append(event_dict)
        event_dict = {
                'title': None,
                'date': None,
                'time' : None,
                'details': ''
            }
    district = 106
    #remove previous entries
    session.query(Event).filter(Event.district == district).delete()
    session.commit()

    #add items to database
    for event in events:
        row = Event(title=event['title'], date=event['date'],
                    details=event['details'], time=event['time'], district= district)
        session.add(row)
    session.commit()


# In[54]:


CB6('https://cbsix.org/meetings-calendar',3,session)


# In[55]:


#print all users
for event in session.query(Event).filter(Event.district == 106):
    print(event,"\n-------------------------------")

