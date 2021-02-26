#!/usr/bin/env python
# coding: utf-8

# In[11]:


import urllib.request
import calendar
import pandas as pd
from tabula import wrapper
import re
from sqlalchemy import create_engine, Column, String, Integer, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# In[12]:


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


# In[13]:


def dataPrep(url):
    #download file
    fileName = 'cb10.pdf'
    pdf = urllib.request.urlretrieve(url, fileName)
    tables = wrapper.read_pdf(fileName, lattice = True, multiple_tables = True)
    #select largest table
    largest = pd.DataFrame()

    for i in tables:
        if i.size >= largest.size:
            largest = i
            
    #get rid of the top columns names
    table = largest.copy()
    
    dayOfWeekRow = None
    for index, row in table.iterrows():
        dayChars = [d[:2] for d in calendar.day_name[:]]
        rowString = [str(i).strip('\r').title()[:2] for i in list(row) if not pd.isna(i)]
        if len(set(dayChars) & set(rowString)) >= 7 :
            dayOfWeekRow = index

    table.columns = table.iloc[dayOfWeekRow]
    table = table[dayOfWeekRow + 1:]

    #drop nan column
    table = table.loc[:,table.columns.notnull()]

    #drop nan with blank string
    table = table.fillna('')
    
    events = []
    for column in table:
        dayOfWeek = column
        values = table[column].values
        event = {}
        #if day in first row has value init weeknumber to 0 otherwise init to 1
        if table[:1].get(column).values != '':
            weekNumber = 0
        else: 
            weekNumber = 1
        #go though each cell of the column and check for an integer, 
        #if there is an integer start day otherwise just append the text
        for cell in values:
            date = re.search(r"^(\d*)",cell).group(0)
            if(date):
                weekNumber += 1
                event[column] = {
                    'text' : cell,
                    'weekNumber' : weekNumber 
                }

                if event[column].items not in events:
                    events.append(event)
                    event = {}
    return events


# In[14]:


def getDayOfMonth(year,month,weekNumber,dayOfWeek):
    if month > 12:
        print("Month is invalid")
        return 0

    #Print message when week number is out of bound
    weeksInMonth = calendar.monthcalendar(year,month)
    if weekNumber > len(weeksInMonth):
        print("Week Number out of bound")
        return 0

    daysInWeek = weeksInMonth[weekNumber-1]
    
    dayChars = [d[:2] for d in calendar.day_name[:]]
    dayCharsOfWeek = dayOfWeek[:2].title()
    if dayCharsOfWeek not in dayChars:
        print("Day of week invalid")
        return 0

    indexInWeek = dayChars.index(dayCharsOfWeek)
    return daysInWeek[indexInWeek]


# In[15]:


def eventSearch(text, weekNumber, dayOfWeek,month):
    events_dict = {}
    day = getDayOfMonth(2021,month,weekNumber,dayOfWeek)
    search = re.search(r"((?:1[0-2]:\d\d.?)[AaPp]?[Mm]?|(?:\d:\d\d.?)[AaPp]?[Mm]?)([\s\S]+)", text)
    try:
        time = search.group(1)
        details = search.group(2)
        title = ""
    except:
        time = ""
        details = text
        title = ""

    if "http" in details:
        linkSplit = details.split('http')
        title = linkSplit[0].replace('Via ZOOM', '')
        details = 'http' + linkSplit[1]
        details=details.replace(" ","")
        
    events_dict['title'] = title.strip()
    events_dict['date']  = f'{month}/{day}'
    events_dict['time'] = time
    events_dict['details'] = details  
    return events_dict


# In[16]:


def CB10(month,events):
    #add events found from eventSearch to events_arr 
    events_arr = []
    for event in events:
        for k,v in event.items():
            text = v['text'].replace('\r', ' ')
            if len(text.strip())>2:
                #two events in one cell
                manyEventsSearch = re.search(r"([^_]*)_{3,}([^_]*)", text)
                if manyEventsSearch != None: 
                    for e in manyEventsSearch.groups():
                        events_arr.append(eventSearch(e, v['weekNumber'], k,month))
                else:
                    events_arr.append(eventSearch(text, v['weekNumber'], k,month))
                    
    district = 110
    #remove previous entries
    session.query(Event).filter(Event.district == district).delete()
    session.commit()

    #add items to database
    for event in events_arr:
        row = Event(title=event['title'], date=event['date'],
                    details=event['details'], time=event['time'], district= district)
        session.add(row)
    session.commit()


# In[17]:


CB10(2,dataPrep('https://www1.nyc.gov/html/mancb10/downloads/pdf/february_2021_calendar.pdf'))


# In[18]:


#print all users
for event in session.query(Event).filter(Event.district == 110):
    print(event,"\n-------------------------------")

