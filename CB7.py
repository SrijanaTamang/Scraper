#!/usr/bin/env python
# coding: utf-8

# In[39]:


from bs4 import BeautifulSoup
import unicodedata
import requests
import re
import calendar
from sqlalchemy import create_engine, Column, String, Integer, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# In[40]:


#init connection to sqlite 
engine = create_engine("sqlite:///events.db")
#create session to cache commands for sqlite engine instance
Session = sessionmaker(bind = engine)
session = Session()


# In[41]:


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


# In[42]:


def CB7(url,session,monthinteger):
    page = requests.get(url)
    soup = BeautifulSoup(page.text,'html.parser')
    paragraphs = soup.find(class_='about-description').find_all('p')
    events = []
    for par in paragraphs:
        #replace <br> will \n
        par = BeautifulSoup((str(par).replace('<br/>','\n')),features="lxml")
        #check if there is an event
        items = par.find_all(recursive = False)
        for item in items:
            if item.text != ' ' and item.text != '':
                events.append(item.text )
                event_details = [elem.strip().split('\n') for elem in events]

    events_dict = {}
    #iterate over event_details, add title,date,time,details to events_dict
    for i,details in enumerate(event_details):
        time = re.search(r"((1[0-2]|0?\d):(\d\d) ([AaPp][Mm]))",str(details))
        date = re.search(r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|(Nov|Dec)(?:ember)?) (([1-3]\d)|(\d))",str(details))
        try:
            dateTimeLine = [line for line in details if calendar.month_name[monthinteger] in line][0]
            dateTimeIndex = details.index(dateTimeLine)
            urlLine = [line for line in details if 'http' in line][0]
            urlIndex = details.index(urlLine)
            titleLine = '\n'.join(details[:dateTimeIndex])
            detailsLine = '\n'.join(details[urlIndex:])
        except:
            continue
        events_dict[i]={
            'title' : titleLine.replace('\xa0',' ').replace('\n',' '),
            'date': str(monthinteger) + '/' + date.group(2) if date else '',
            'time' : time.group(0) if time else '',
            'details': detailsLine.replace('\xa0',' ').replace('\n',' ')
        }
        
    districtNumber = 107
    #remove previous entries
    session.query(Event).filter(Event.district == districtNumber).delete()
    session.commit()

    #add items to database
    for event in events_dict.values():
        row = Event(title=event['title'], date=event['date'],
                    details=event['details'], time=event['time'], district= districtNumber)
        session.add(row)

    session.commit()


# In[43]:


CB7('https://www1.nyc.gov/site/manhattancb7/meetings/committee-agendas.page',session,2)


# In[44]:


# print all users
for event in session.query(Event).filter(Event.district == 107):
    print(event,"\n-------------------------------")

