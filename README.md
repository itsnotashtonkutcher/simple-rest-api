# Geo location interview REST API

API consists of 3 endpoints: POST, GET, and DELETE geolocation.

POST is not implemented in "classical" form, where all data have to be provided, as it is obtained through Ipstack API. 
For that reason all endpoints accept **IP** or **URL** as parameter.
Additionally, in each endpoint there are two dependencies: database session and locator object.

### Locator class
Locator object is responsible for finding ip address, if url was passed (through socket library, as free version of Ipstack does not allow direct usage of url), and for making call to Ipstack to get the data.
The reason behind passing separate instance of Locator to each call is that I'm not sure whether GeoLookup object is thread-safe, and extending it to a point when it stops to be as such would not create additional bugs.

### Models
Moving forward, in models.py there is a definition of GeoLocation table.
Beside the fact, that I've decided that IP (or url resolved to it) is real key in my API, I added simple numeric id, which whole purpose was just to meet standard requirement, that string should not be used as one.
Next field in the model is obviously IP address that geo location data corresponds to. 
I decided to not use primary key as "pointer" for resource for simplicity of API usage.
In more complicated scenarios I would probably use UUID to determine resources within the API.

It is worth mentioning, that I don't store URL data as **many URLs might resolve to same IP address**, hence IP cannot be resolved to single URL.
If there was a strong requirement to differentiate URLs in single IP range (for example to eliminate situation when someone added 3 different URLs, which share same IP, and with single delete, with URL specified, all 3 are gone), then I would add field for URL and fill only one field at the time (or create separate models). 
That way I would differentiate "paths"- one when IP is specified and the other when URL. 

### Database choice
As I was more focused on implementation rather than perfect setup of environment, I decided to go with sqlite, as it helped me with easy prototyping.
In real-life development I would probably choose normal sql server, like postgresql.

### Security aspects
As it is simple application with lack of personalized resources I decided to not implement it.
What I would rather go for, is some kind of request limitation, so application cannot be "overused", by one particular user.

## How to run application
***
### Running locally:
1. create virtual environment, activate it, install poetry and then packages:
```commandline
python -m venv .venv
# linux
source .venv/bin/activate
# windows
./.venv/Scripts/Activate.ps1
pip install poetry
poetry install
```
2. run application:
```commandline
uvicorn app:app
```

### Running container:
1. create image:
```commandline
docker build -t app .
```
2. run image:
```commandline
docker run -p8000:8000 app
```
