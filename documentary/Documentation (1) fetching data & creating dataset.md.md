# Setup
- We set our logging level to critical so that the API doesn't spam us with print statements.
- We enable the caching function so that we don't have to pull data every time we run the cell in our Jupyter notebook.

```python
import logging
import fastf1

logging.getLogger('fastf1').setLevel(logging.CRITICAL)
fastf1.Cache.enable_cache('cache')
```
--- 
# Variables for Our For Loop

- We create the necessary variables we need:
    
    - `season`: an integer representing the season we use for training.
        
    - `races_per_season`: a dictionary mapping each season to the number of races in that season.
        
    - Lists to store the fetched data: `all_laps`, `all_weather`, `all_trackStatus`, and `all_telemetry`. These lists will be filled inside the loop.
    
```python
Season = 2023

races_per_season = {2023: 23}

all_laps = []
all_weather = []
all_trackStatus = []
all_telemetry = []
```
--- 
## Main For Loop for Fetching Data

- The script iterates over multiple race rounds using a `for` loop.
    
- The variable `round_num` represents the **round number of a Formula 1 season**, which corresponds to a specific Grand Prix in that season (e.g., Round 1 = Bahrain GP, Round 2 = Saudi Arabian GP, etc.)
    
- We continue to get a session since its in a for loop we are getting every race session from every Grand Prix weekend of 2023.
- After getting the session we have to load it since getting it doesn't mean downloading yet 
- in the load function we define what of the session we want to get specifically in our case that is telemetry, weather, messages and laps
 ```python
for round_num in range(1, races_per_season[season] + 1):

    print(f"Loading Season {season} Round {round_num}")

    session = fastf1.get_session(season, round_num, "R")
    session.load(laps=True, telemetry=True, weather=True, messages=False)

    
    laps = session.laps.copy()
    laps["Season"] = season
    laps["Round"] = round_num
    all_laps.append(laps)

    
    weather = session.weather_data.copy()
    weather["Season"] = season
    weather["Round"] = round_num
    all_weather.append(weather)

    
    trackStatus = session.track_status.copy()
    trackStatus["Season"] = season
    trackStatus["Round"] = round_num
    all_trackStatus.append(trackStatus)
    ```
--- 
### Parameters of the session
- the API explains here what attributes are available via a session
![[Pasted image 20251106005904.png]]