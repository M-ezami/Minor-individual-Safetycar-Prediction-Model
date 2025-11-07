# How does our code work ?
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

# how does the data work together
- so we have session time its a differnet time stamp than laptime do they allign with  each other