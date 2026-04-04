# Youtube Scraper App
This `flet` app parses the feed of a list of youtube channels and returns the new videos by confronting the current video list with the previous video list, saved in a `json` file. 
The videos are displayed as a list of links.

This version also stores the new videos found in the previous 5 successful runs, and displays them under the new videos.

This app is completely built using `Python`, with the `flet` library for building the UI and the `feedparser` library to parse the channel feeds.

The channels are saved on a database created using `sqlite3`, and they can be managed from the `Channels` tab in the app.