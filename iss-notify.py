#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#todo : collect and cache TLE
#todo : set colour codes
#todo : allow ledborg and piglow
#done : am and pm

import configparser
import math
import time
import datetime
import ephem

#read config
config = configparser.ConfigParser()
config.read('config.ini')
LOC = config['LOC']
TLE = config['TLE']
VIS = config['VIS']
#TIM = config['TIM']

sat = ephem.readtle(TLE['LINE1'], TLE['LINE2'], TLE['LINE3'])
sun = ephem.Sun()

#seed now with now
now = datetime.datetime.utcnow()

observer = ephem.Observer()
observer.lat = str(LOC['LAT'])
observer.lon = str(LOC['LON'])
observer.elevation = int(LOC['ELE'])
observer.horizon = str(LOC['HOZ'])
observer.temp = int(LOC['TMP'])
observer.epoch = now.year

#observer.compute_pressure()

# code from https://gist.github.com/RobertSudwarts/acf8df23a16afdb5837f
def deg_to_card(d):
    d = math.degrees(d)
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    #ix = int((d + 11.25)/22.5)
    ix = int((d + 11.25)/22.5 - 0.02)
    return dirs[ix % 16]

# code from http://space.stackexchange.com/questions/4339/calculating-which-satellite-passes-are-visible
def seconds_between(d1, d2):
    return abs((d2 - d1).seconds)

# code from http://space.stackexchange.com/questions/4339/calculating-which-satellite-passes-are-visible
def datetime_from_time(tr):
    year, month, day, hour, minute, second = tr.tuple()
    dt = datetime.datetime(year, month, day, hour, minute, int(second))
    return dt

def get_next_pass(dtim):
    observer.date = dtim

    # assume we can see sat, until some reason says we cant
    vis = True

    # assume we show a pass, until some reason says we cant
    show = True

    sat.compute(observer)
    rt, ra, tt, ta, st, sa = observer.next_pass(sat)
    dr = seconds_between (datetime_from_time(rt), datetime_from_time(st))

    # only care if visible at transit time
    # set observer date to transit time

    observer.date = tt
    sat.compute(observer)
    sun.compute(observer)
    sat_te = sat.eclipsed

    sat_alt = math.degrees(ta)
    if sat_alt < int(VIS['ALT']):
        vis = False
        print ("rise :", ephem.localtime(rt), "- sat is to low :", (sat_alt))

    if sat.eclipsed is True:
        vis = False
        print ("rise :", ephem.localtime(rt), "- sat is eclipsed:", (sat.eclipsed))

    sun_alt = math.degrees(sun.alt)
    if sun_alt > -5:
        vis = False
        print ("rise :", ephem.localtime(rt), "- sun is to high:", (sun_alt))

    ampm = datetime.datetime.strftime(ephem.localtime(tt), '%p')
    if VIS['TOD'].upper() == "AM" or VIS['TOD'].upper() == "PM":
        if ampm != VIS['TOD'].upper():
            vis = False
            print ("rise :", ephem.localtime(rt), "- outside of show window:", vis)

    if vis:
        card_ra = deg_to_card(ra)
        card_sa = deg_to_card(sa)

        print ("rise :", ephem.localtime(rt), "-", card_ra)
        print ("max  :", ephem.localtime(tt), "-", round(sat_alt,2))
        print ("set  :", ephem.localtime(st), "-", card_sa)
        print ("dur  :", dr)
        print ("sun  :", round(sun_alt,2))
        print ("ampm :", ampm)
    else:
        print ()

    return rt, st, vis

#assume we just missed a pass
settime = ephem.Date(now)
visible = False

while not visible:
    risetime, settime, visible = get_next_pass(ephem.Date(settime + ephem.minute))

print ("rt in:", seconds_between(now, datetime_from_time(risetime)), "seconds")
print ("st in:", seconds_between(now, datetime_from_time(settime)), "seconds")

