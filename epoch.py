import csv
import datetime

# Convert the epoch timestamp to a human-readable format
epoch_timestamp = 1612254374
converted_date = datetime.date.fromtimestamp(epoch_timestamp)

# Read the CSV file to get the list of dates and their corresponding versions
version_date_mapping = {}
with open('versions.csv', 'r') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # Skip the header row
    for row in reader:
        version = row[0].strip()
        date = row[1].strip().replace('(', '').replace(')', '')
        version_date_mapping[date] = version

print(f"The converted epoch timestamp is: {converted_date}")

# Filter out dates that are after the converted epoch timestamp
preceding_dates = [date for date in version_date_mapping.keys() if datetime.datetime.strptime(date, '%Y-%m-%d').date() <= converted_date]

# If there are no preceding dates, handle this case
if not preceding_dates:
    print("There are no versions released before or on the converted epoch timestamp.")
else:
    # Find the closest preceding date to the converted epoch timestamp
    closest_date = max(preceding_dates)
    print(f"The closest preceding date from the list to the converted epoch timestamp is: {closest_date}")
    print(f"The version associated with this date is: {version_date_mapping[closest_date]}")
