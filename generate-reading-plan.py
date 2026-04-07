import pandas as pd
from pathlib import Path
from datetime import datetime, date, timedelta
import math

## ===== variable config start =====

# logic variables
user_name = 'Nic Cohn'
use_rec_rule = True
use_libby_rules = True

# pace variables
pace_mode = 'auto'  # 'manual' or 'auto'
manual_pace_type = 'pages'  # 'pages', 'fixed_days', or 'percent'
manual_days_per_book = 6
manual_pages_per_day = 75
manual_percent_per_day = 0.1

# timing variables
months_to_plan = 3

# tag variables
next_tag = 'next'
rec_tag = 'jubie'
rec_per_month = 1

# Libby rules
libby_delays = {
    77197: 1,
    210300489: 8,
    18739426: 4,
    51057191: 8
}

## ===== variable config end =====

base_dir = Path(__file__).resolve().parent
path = base_dir / 'goodreads_library_export.csv'

gr = pd.read_csv(path)
columns_to_keep = [
    'Book Id', 'Title', 'Author', 'ISBN', 'My Rating', 'Average Rating',
    'Number of Pages', 'Date Read', 'Date Added', 'Bookshelves', 'Exclusive Shelf'
]
gr = gr[columns_to_keep]

gr.columns = gr.columns.str.strip().str.lower().str.replace(' ', '_')
gr['book_id'] = pd.to_numeric(gr['book_id'], errors='coerce').astype('Int64')

read = gr[gr['exclusive_shelf'].str.lower() == 'read'].copy()

read['date_read'] = pd.to_datetime(read['date_read'], errors='coerce')
read['number_of_pages'] = pd.to_numeric(read['number_of_pages'], errors='coerce')

read = read.dropna(subset=['date_read', 'number_of_pages']).copy()
read = read.sort_values('date_read')

read['days_between'] = read['date_read'].diff().dt.days
read = read[(read['days_between'] > 0) & (read['days_between'] < 60)]

if pace_mode == 'manual':
    if manual_pace_type == 'pages':
        days_per_book = None
        pages_per_day = manual_pages_per_day
    elif manual_pace_type == 'fixed_days':
        days_per_book = manual_days_per_book
        pages_per_day = None
    elif manual_pace_type == 'percent':
        days_per_book = math.ceil(1 / manual_percent_per_day)
        pages_per_day = None
    else:
        raise ValueError('manual_pace_type must be \'pages\', \'fixed_days\', or \'percent\'')
elif pace_mode == 'auto':
    days_per_book = read['days_between'].median()
    avg_pages = read['number_of_pages'].mean()
    pages_per_day = avg_pages / days_per_book
else:
    raise ValueError('pace_mode must be \'manual\' or \'auto\'')

print('Pace mode:', pace_mode)
print('Manual pace type:', manual_pace_type if pace_mode == 'manual' else 'n/a')
print('Days/book:', round(days_per_book, 2) if days_per_book is not None else 'varies by book')
print('Pages/day:', round(pages_per_day, 2) if pages_per_day is not None else 'varies by book')

def get_book_duration_days(book_pages, pace_mode, manual_pace_type, manual_days_per_book, manual_pages_per_day, manual_percent_per_day, auto_pages_per_day):
    if pd.isna(book_pages) or book_pages <= 0:
        book_pages = 300

    if pace_mode == 'manual':
        if manual_pace_type == 'pages':
            return max(1, math.ceil(book_pages / manual_pages_per_day))
        elif manual_pace_type == 'fixed_days':
            return manual_days_per_book
        elif manual_pace_type == 'percent':
            return max(1, math.ceil(1 / manual_percent_per_day))
        else:
            raise ValueError('manual_pace_type must be \'pages\', \'fixed_days\', or \'percent\'')

    elif pace_mode == 'auto':
        return max(1, math.ceil(book_pages / auto_pages_per_day))

    else:
        raise ValueError('pace_mode must be \'manual\' or \'auto\'')

def get_earliest_available_date(book_id, use_libby_rules, libby_delays):
    earliest_date = date.today()

    if use_libby_rules and pd.notna(book_id):
        book_id = int(book_id)
        if book_id in libby_delays:
            earliest_date = date.today() + timedelta(days=(libby_delays[book_id] * 7))

    return earliest_date

def is_available_now(row, current_date, use_libby_rules, libby_delays):
    earliest_available_date = get_earliest_available_date(
        row['book_id'],
        use_libby_rules,
        libby_delays
    )
    return earliest_available_date <= current_date

def escape_ics_text(text):
    if pd.isna(text):
        return ''
    text = str(text)
    text = text.replace('\\', '\\\\')
    text = text.replace(';', '\\;')
    text = text.replace(',', '\\,')
    text = text.replace('\n', '\\n')
    return text

def write_ics(schedule, output_path):
    now_utc = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        f'PRODID:-//{user_name}//Reading Planner//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH'
    ]

    for item in schedule:
        uid = f'reading-plan-{item["book_id"]}-{item["start_date"]}@reading-planner'
        title = escape_ics_text(item['title'])
        author = escape_ics_text(item['author'])
        tags = escape_ics_text(', '.join(item['tags']))

        description = escape_ics_text(
            f'Author: {item["author"]}\n'
            f'Goodreads Book ID: {item["book_id"]}\n'
            f'Tags: {", ".join(item["tags"])}'
        )

        start_str = item['start_date'].strftime('%Y%m%d')

        end_exclusive = item['end_date'] + timedelta(days=1)
        end_str = end_exclusive.strftime('%Y%m%d')

        lines.extend([
            'BEGIN:VEVENT',
            f'UID:{uid}',
            f'DTSTAMP:{now_utc}',
            f'SUMMARY:Read {title}',
            f'DESCRIPTION:{description}',
            f'DTSTART;VALUE=DATE:{start_str}',
            f'DTEND;VALUE=DATE:{end_str}',
            'STATUS:CONFIRMED',
            'TRANSP:TRANSPARENT',
            'END:VEVENT'
        ])

    lines.append('END:VCALENDAR')

    with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines))

gr['bookshelves'] = gr['bookshelves'].fillna('').str.lower()
gr['tags'] = gr['bookshelves'].apply(lambda x: [tag.strip() for tag in x.split(',') if tag.strip()])

to_read = gr[gr['exclusive_shelf'].str.lower() == 'to-read'].copy()
currently_reading = gr[gr['exclusive_shelf'].str.lower() == 'currently-reading'].copy()

remaining = to_read.copy()
schedule = []
current_date = date.today()

for _, row in currently_reading.iterrows():
    duration = get_book_duration_days(
        row['number_of_pages'],
        pace_mode,
        manual_pace_type,
        manual_days_per_book,
        manual_pages_per_day,
        manual_percent_per_day,
        pages_per_day
    )

    start_date = current_date
    end_date = current_date + timedelta(days=duration - 1)

    schedule.append({
        'title': row['title'],
        'author': row['author'],
        'start_date': start_date,
        'end_date': end_date,
        'month_label': start_date.strftime('%B %Y'),
        'tags': row['tags'],
        'book_id': row['book_id']
    })

    current_date = end_date + timedelta(days=1)

end_horizon = current_date + timedelta(days=months_to_plan * 31)

while current_date <= end_horizon and len(remaining) > 0:
    current_month_label = current_date.strftime('%B %Y')

    available_remaining = remaining[
        remaining.apply(
            lambda row: is_available_now(row, current_date, use_libby_rules, libby_delays),
            axis=1
        )
    ].copy()

    if len(available_remaining) == 0:
        next_available_date = min(
            get_earliest_available_date(book_id, use_libby_rules, libby_delays)
            for book_id in remaining['book_id']
            if pd.notna(book_id)
        )
        current_date = next_available_date
        continue

    if use_rec_rule:
        rec_already_scheduled_this_month = any(
            (rec_tag in item['tags']) and (item['month_label'] == current_month_label)
            for item in schedule
        )
    else:
        rec_already_scheduled_this_month = True

    if use_rec_rule and not rec_already_scheduled_this_month:
        rec_candidates = available_remaining[
            available_remaining['tags'].apply(lambda tags: rec_tag in tags)
        ]
        if len(rec_candidates) > 0:
            next_row = rec_candidates.iloc[0]
        else:
            next_candidates = available_remaining[
                available_remaining['tags'].apply(lambda tags: next_tag in tags)
            ]
            if len(next_candidates) > 0:
                next_row = next_candidates.iloc[0]
            else:
                next_row = available_remaining.iloc[0]
    else:
        next_candidates = available_remaining[
            available_remaining['tags'].apply(lambda tags: next_tag in tags)
        ]
        if len(next_candidates) > 0:
            next_row = next_candidates.iloc[0]
        else:
            next_row = available_remaining.iloc[0]

    remaining = remaining[remaining['book_id'] != next_row['book_id']]

    duration = get_book_duration_days(
        next_row['number_of_pages'],
        pace_mode,
        manual_pace_type,
        manual_days_per_book,
        manual_pages_per_day,
        manual_percent_per_day,
        pages_per_day
    )

    start_date = current_date
    end_date = current_date + timedelta(days=duration - 1)

    schedule.append({
        'title': next_row['title'],
        'author': next_row['author'],
        'start_date': start_date,
        'end_date': end_date,
        'month_label': start_date.strftime('%B %Y'),
        'tags': next_row['tags'],
        'book_id': next_row['book_id']
    })

    current_date = end_date + timedelta(days=1)

for item in schedule:
    print(
        f'{item["book_id"]} | '
        f'{item["title"]} by {item["author"]} | '
        f'{item["start_date"]} to {item["end_date"]} | '
        f'{item["month_label"]} | '
        f'{item["tags"]}'
    )

ics_path = base_dir / 'reading-plan.ics'
write_ics(schedule, ics_path)
print(f'\nICS file created: {ics_path}')