#!/usr/bin/env python
# coding: utf-8

# In[16]:


from icalendar import Calendar, Event
from urllib.request import urlopen 
import requests
from bs4 import BeautifulSoup
import ssl   
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# In[17]:


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


# In[18]:


def CB5(url,session,ical):
    page = requests.get(url,verify = False)
    soup = BeautifulSoup(page.text,'html.parser')
    context = ssl._create_unverified_context()
    req = urlopen(ical, context=context).read()
    cal = Calendar.from_ical(req)
    events_dict = {}
   #iterrate through events in cal with new events from each 'vevent' 
    #search for time,date, title and detaisls and add to events_dict
    for i, event in enumerate(cal.walk('vevent')):
        date = event.get('dtstart')
        time=  date.dt.hour
        if(date.dt.hour> 12):
            time = time - 12 
            time = str(time)+ ":"+str(date.dt.minute).zfill(2)+" PM"
        location = event.get('location')
        topic = event.get('summary')
        #get description from ical to find respective agendas of event
        description = event.get('DESCRIPTION')
        description_id = description.split('/')[-2] 
        div = soup.findAll("div", {"id":description_id })

        for d in div:
              details = d.findAll('ul')      
        details_text =  '\n'.join([item.text for item in details if item.text.strip()])        

        events_dict[i] = {
              'date': str(date.dt.month) + "/"+ str(date.dt.day),
              'time': time,
              'topic': str(topic).replace('CB5 -','').strip(), #remove 'CB5 -' text
              'location': str(location),
              'details':details_text
          }

    districtNumber = 105
    #remove previous entries
    session.query(Event).filter(Event.district == districtNumber).delete()
    session.commit()

    #add items from events_dict to database
    for event in events_dict.values():
        row = Event(title=event['topic'], date=event['date'],
                    details= f'Location: {event["location"]}\n{event["details"]}',
                    time=event['time'], district= districtNumber)
        session.add(row)
    session.commit()


# In[19]:


CB5('https://www.cb5.org/cb5m/calendar/2020-may/',session,'https://www.cb5.org/cb5m/calendar.ics')


# In[20]:


#print all users
for event in session.query(Event).filter(Event.district == 105):
    print(event)

