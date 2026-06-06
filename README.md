# Channel Watcher

A local-only desktop app for tracking new uploads from a personal list of YouTube channels.

Channel Watcher is built with **Python + Flet** and is designed for **personal use on Windows**. It lets you maintain a saved list of YouTube channel IDs, check their feeds on demand, detect newly published videos, and keep a small history of successful runs.

## What it does

* Stores tracked channels in **SQLite**
* Lets you add channels by **channel ID**
* Automatically resolves the channel title when adding a channel
* Creates an initial baseline when a channel is first added
* Checks YouTube channel feeds on demand
* Detects newly seen videos against the saved baseline
* Shows thumbnails, titles, metadata, and direct video links
* Displays per-channel feed warnings when a feed cannot be read cleanly
* Keeps a short JSON-based history of successful runs
* Packages as a Windows desktop app with a custom icon

## Tech stack

* **Python**
* **Flet** for the desktop UI
* **SQLite** for channel storage
* **feedparser** for reading YouTube feed XML
* Local JSON files for seen-state and recent run history

## Version 2.0.0
Main changes:
- Added Chronological Research tab for YouTube searches
- Improved UI structure and consistency
- Added thumbnail-based result cards for search results
- Improved feedback states, empty states, and error display
- General app refinement and cleanup

Status:
- Personal release for local use
- Validated on packaged build

## Current project layout

```text
.
├── pyproject.toml
├── main.py
├── models.py
├── scraper.py
├── storage.py
├── channel_store.py
├── youtube_search.py
├── requirements.txt
├── ui/
│   ├── theme.py
│   ├── components.py
│   ├── watch_tab.py
│   ├── channels_tab.py
|   └── chron_research_tab.py
└── assets/
    ├── icon.png
    ├── fonts/
    └── images/
```

## UI overview

The app has three tabs:

### Watch

The Watch tab is the main dashboard.

It lets you:

* run a feed check manually
* see the current run status and progress
* review new videos found in the latest run
* inspect feed warnings
* browse recent successful runs

Video cards display:

* video thumbnail
* video title
* channel name
* published date when available
* direct link to open the video in the browser

### Channels

The Channels tab is the management view for the tracked channel list.

It lets you:

* add a channel by YouTube channel ID
* automatically resolve the human-readable channel title
* remove a tracked channel
* open the channel main page directly from the channel name

### Search (NEW!)
The Search tab is the tab that allows to run a chronological search on youtube videos.

It lets you:

* run a simple query and list the results in chronological order through the YouTube Data API
* finetune advanced options such as 

    * number of results to list
    * maximum number of pages to look through
    * maximum number of video candidates to take into consideration
    * minimum duration of the videos (in seconds)

## Data storage

This app is local-only.

No backend, no cloud sync, no account system.

### SQLite

Tracked channels are stored in a local SQLite database:

* `channel_watcher.db`

### JSON files

The app also uses local JSON files for:

* seen video state
* recent successful run history
* optional legacy import fallback

### Data location

On Windows, application data is stored under the current user's app data directory.

The code uses a per-user writable folder, so packaged builds and development builds both store data locally for the current Windows user.

## How new videos are detected

When a feed check runs:

1. The app loads the saved list of tracked channels.
2. It fetches each channel's YouTube feed.
3. It compares the current feed entries against the saved baseline for that channel.
4. New video URLs not present in the previous saved state are treated as new uploads.
5. The saved state is updated after the run.
6. If new videos were found, the run is recorded in the recent history file.

When a channel is added for the first time, the app resolves the channel title and performs an initial baseline creation so existing feed items are not incorrectly treated as new.

## Fonts and visual style

The UI uses:

* **Pixelify Sans** for major headers and section titles
* **Inter** for the rest of the UI

The visual theme is a custom dark palette with a neon mint / cyan accent style.

## Development

### Requirements

* Windows
* Python
* A working virtual environment is recommended
* Flet installed in the development environment

### Install dependencies

```bash
pip install -r requirements.txt
```

If you prefer, you can also install dependencies from your project configuration, depending on how you manage your environment.

### Run in development

From the project root:

```bash
flet run main.py
```

## Packaging for Windows

This app was packaged using **Flet build**, not `flet pack`.

### Build command

From the project root:

```bash
flet build windows --module-name main
```

### Important packaging notes

#### 1. Dependencies

For this project layout, runtime dependencies must be available to the build from:

```text
requirements.txt
```

This was necessary so the packaged app correctly included required Python packages such as `feedparser`.

#### 2. Assets

For `flet build`, the app icon and other runtime assets must live under:

```text
assets/
```

This includes:

* `assets/icon.png`
* `assets/fonts/...`
* `assets/images/...`

#### 3. Custom executable icon

The packaged executable icon is generated from:

```text
assets/icon.png
```

#### 4. Windows Developer Mode

If packaging fails with a symlink-related error, enable **Windows Developer Mode**.

#### 5. Flutter path issues

If the build environment reports conflicting Flutter installations, make sure your PATH points to the intended Flutter SDK only.

## Limitations

* Personal-use project, not designed as a multi-user product
* YouTube feeds are read through feed parsing, so behavior depends on feed availability and parsing reliability
* Seen-state and recent-run history are still JSON-based rather than fully migrated to SQLite
* Channel avatars are not currently stored or displayed
* No automatic background checking or scheduling is included

## Possible future improvements

* move seen-state and run history fully into SQLite
* add import/export for tracked channels
* add optional scheduled checks
* improve warning reporting and diagnostics
* refine packaging metadata further
* add button to update channel list - fetch new name and picture associated to the ID and update the database
* add tags to channels, store them in the DB, and make it possible to check new videos only for channels corresponding to the selected tag(s). Show the tags in the channel page
* ~~add another tab for chronological video research on YouTube using the YT API~~

## Why this exists

This app was built as a personal utility: a lightweight way to monitor a chosen set of YouTube channels without relying on subscriptions, platform notifications, or a browser-based workflow.

After YouTube has taken away the chronological research option, the Search tab was added to bring back this function.

It is intentionally local, simple, and focused.

## Repository notes

This repository contains a complete working version of the app, including:

* source code
* UI theme and assets
* packaging-ready project structure
* custom app icon support for the packaged Windows executable
