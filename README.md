# konachan100.github.io
View most recent 100 posts from Konachan.net:    https://konachan100.github.io/

## Why this project
- Konachan.net index page may unavaliable due to your ISP but its posts still accessable. 
- I always need a quick look of new posts.
- Mobile device users want a suitable HTML layout

## How does it work
Page updating is done by a cloud server that can access Konachan web API, and post content updates once per 5 min, see shell script for detail. during each update, the program fetches post.json and generate static web pages, then git-push to this repo.

**Warning:** Do not try to build a konachan mirror site on your cloud server, 
your server instance will be blocked for political-right reason.

## Dev Requirement
- Python 3.x
- Python Library
  - Jinja2
