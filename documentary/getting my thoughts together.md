lp<# How does our code work ?
- append adds the single lap dataframes together for one race in our loop where we iterate through the laps by each race 
- laps is already a whole dataframe it just adds it to a list 
- like this:
|LapNumber|Driver|LapTime|
|----1|----|HAM|-1:30.5-|
|----2|----|HAM|-1:30.2-|


this raises the question why not just use concat directly and forget about the list inbetween. The reason for that is that if we were to do something like this
pandas would create a brand new dataframe everytime
```python
laps_all = pd.DataFrame()
for session in sessions:
    laps = session.laps.copy()
    laps_all = pd.concat([laps_all, laps], ignore_index=True)
```

- after this we have a list in one iteration of each lap of that session/race
- we concat it so we create a dataframe out of the list and add it at the end of the dataframe
- we do this for every session object so at the end 
# Merging on time deltas
- For weather we are using time + date combine it both
- for laps we use lapstartdate
- and for telemtry we jst use daaate
## laps what to keep
- keep laptime and covnert to seconds
- keep driver number 
- delete driver
- keep time convert to seconds make this basically the duration of the race
- keep lapnumber
- keep pitouttime,pitintime convert to seconds or maybe make aa hot encoding out opf this somehow
- keep sectortimes 
- keep all speed columns
- keep compound
- keep tyrelyfe
- freshtyre
- hotencode team
- positon might need hotencode since i think it sa float
- season and round
- date can be removed at training point
- track status 
- so first we label the laap before then we remove the safety car kaps
- create distance to driver ahead on lap adn secotr level 
- create a how close the whole pack is feature 