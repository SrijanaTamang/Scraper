#!/usr/bin/env python
# coding: utf-8

# In[6]:


from icalendar import Calendar, Event
from urllib.request import urlopen 
import urllib.request 
import requests
from bs4 import BeautifulSoup
import ssl   
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# In[7]:


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


# In[10]:


def CB12(ical,session):
    context = ssl._create_unverified_context()
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    hdr={'User-Agent':user_agent,} 
    req=urllib.request.Request(ical,None,hdr)
    response = urllib.request.urlopen(req,context = context).read() 
    cal = Calendar.from_ical(response)
    events_dict = {}
    #iterrate through events in cal with new events from each 'vevent' 
    #add time,date, title and details to events_dict
    for i, event in enumerate(cal.walk('vevent')):
        date = event.get('dtstart')
        try:
            time =  date.dt.hour
            if(date.dt.hour > 12):
                time = time - 12 
                time = str(time)+ ":"+str(date.dt.minute).zfill(2)+" PM"
            else:
                time = str(time)+ ":"+str(date.dt.minute).zfill(2)+" AM"
        except:
            continue
        location = event.get('location')
        topic = event.get('summary')
        description = event.get('DESCRIPTION')

        events_dict[i] = {
              'date': str(date.dt.month) + "/"+ str(date.dt.day),
              'time': time,
              'topic': str(topic).strip(), 
              'location': str(location),
              'description': str(description).replace('\n',' ').replace('\xa0',' ').strip()
          }
    districtNumber = 112
    #remove previous entries
    session.query(Event).filter(Event.district == districtNumber).delete()
    session.commit()

    #add events_dict items to database
    for event in events_dict.values():
        row = Event(title=event['topic'], date=event['date'],
                    details= f'Location: {event["location"]}\n{event["description"]}',
                    time=event['time'], district= districtNumber)
        session.add(row)
    session.commit()


# In[12]:


CB12('https://cbmanhattan.cityofnewyork.us/cb12/calendar/?ical=1',session)


# In[13]:


#print all users
for event in session.query(Event).filter(Event.district == 112):
    print(event,'\n\n')

