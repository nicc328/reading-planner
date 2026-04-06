# Reading Planner → Apple Calendar

Small Python script that turns your Goodreads library into a reading schedule and pushes it to Apple Calendar via an `.ics` file.

## What it does

- Uses your Goodreads export  
- Estimates your reading pace  
- Builds a schedule based on that  
- Supports simple rules (monthly recs, priority tags, Libby waits)  
- Outputs a calendar you can subscribe to  

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/nicc328/reading-planner.git
cd reading-planner
```

### 2. Install pandas

```bash
pip install pandas
```

### 3. Export your Goodreads data

Go to Goodreads → My Books

<img width="1201" height="96" alt="Screenshot 2026-04-06 at 4 14 21 PM" src="https://github.com/user-attachments/assets/ac1eb796-64c9-4308-ac82-f8a5bf021ad5" />

Scroll down and click **Import and export**

<img width="337" height="786" alt="Screenshot 2026-04-06 at 4 14 46 PM" src="https://github.com/user-attachments/assets/3d675cd9-4bb6-48a4-a483-938d7ed9d851" />

Click **Export Library**

<img width="433" height="156" alt="Screenshot 2026-04-06 at 4 15 03 PM" src="https://github.com/user-attachments/assets/5fb620dc-9d30-4189-915c-c0d7c49aa01d" />

### 4. Add it to the project

Rename the file to:

*goodreads_library_export.csv*

Drop it in the main project folder.

## Config

All settings are at the top of the script.

### Turn features on or off

```bash
use_rec_rule = True
use_libby_rules = True
```

### Reading pace
```bash
pace_mode = 'auto'  # or 'manual'
manual_pace_type = 'pages'  # 'pages', 'fixed_days', 'percent'
manual_pages_per_day = 75
manual_days_per_book = 6
manual_percent_per_day = 0.1
```

### Tags

These map to your Goodreads shelves.

```bash
next_tag = 'next'
rec_tag = 'recommended'
rec_per_month = 1
```

Example:

- Anything on the *recommended* shelf → treated as a recommendation
- Ensures 1 per month
  
### Libby (optional)
```bash
libby_delays_weeks = {
    77197: 4
}
```
- Key = Goodreads book ID
- Value = wait time in weeks
  
## Run it
This creates:

*docs/reading-plan.ics*

## Add to Apple Calendar

Use this URL:

https://[your-github-username].github.io/[repo-name]/reading-plan.ics

## Updating

When your list changes:

```bash
git add reading-plan.ics
git commit -m "update plan"
git push
```

Calendar should refresh automatically.
