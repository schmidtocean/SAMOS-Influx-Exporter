# SAMOS-Influx-Exporter
Python utility for compiling a UTC day's worth of 1-min bin averaged Met/Seawater data with vessel position and export it in the SAMOS data format. Optionally save to file. Optionally email to SAMOS.  This utility is intended for vessels using OpenRVDAS coupled with InfluxDB.

# Install
1. Clone the local repo to the desired destination
```
cd ~
git clone https://github.com/schmidtocean/SAMOS-Influx-Exporter.git
sudo cp -r ./SAMOS-Influx-Exporter /opt/samos_influx_exporter
```

2. Setup a python venv for the project
```
cd /opt/samos_influx_exporter
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```

3. Create the settings file from the included template:
```
cp /opt/samos_influx_exporter/settings.py.dist /opt/samos_influx_exporter/settings.py
```

### Modify the required fields
This includes all the parts of the file where the variable name is capitalized. i.e. `<SHIP_NAME>`

## Optional SAMOS configuration file
The settings file includes a `INLINE_CONFIG` yaml-formatted string for defining how to map the InfluxDB data export to the SAMOS data format.  This part of the settings file can be overridden via the `--config_file <config_file>` command-line argument.  The contents of this config file must be a valid yaml object matching the following schema:

```
callsign: "KAOU"
measurements: [ "posmv","true_wind_port","mpp_port" ]
fields:
    AT: MPP_Port_AirTemp
    BP: MPP_Port_AirPres
    CR: POSMV_CourseTrue
    GY: POSMV_HeadingTrue
    LA: POSMV_Latitude
    LO: POSMV_Longitude
    SP: POSMV_SpeedKt
    TI: Port_TrueWindDir
    TW: Port_TrueWindSpd
    WD: MPP_Port_WindDir
    WS: MPP_Port_WindSpd
```

## Setup Influx Task
Create the InfluxDB task to compile the 1-minutes binned dataset using the following:
```
option task = {name: "SAMOS Data Builder", every: 1h, offset: 1m}

from(bucket: "openrvdas")
	|> range(start: -1h)
	|> filter(fn: (r) =>
		(r["_measurement"] == "posmv"))
	|> filter(fn: (r) =>
		(r["_field"] == "POSMV_Latitude" or r["_field"] == "POSMV_Longitude" or r["_field"] == "POSMV_HeadingTrue" or r["_field"] == "POSMV_SpeedKt" or r["_field"] == "POSMV_CourseTrue"))
	|> aggregateWindow(every: 1m, fn: last, createEmpty: false)
	|> to(bucket: "daily_minute_data", org: "openrvdas")
from(bucket: "openrvdas")
	|> range(start: -1h)
	|> filter(fn: (r) =>
		(r["_measurement"] == "mpp_port"))
	|> filter(fn: (r) =>
		(r["_field"] == "MPP_Port_AirPres" or r["_field"] == "MPP_Port_AirTemp" or r["_field"] == "MPP_Port_WindDir" or r["_field"] == "MPP_Port_WindSpd"))
	|> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
	|> to(bucket: "daily_minute_data", org: "openrvdas")
from(bucket: "openrvdas")
	|> range(start: -1h)
	|> filter(fn: (r) =>
		(r["_measurement"] == "true_wind_port"))
	|> filter(fn: (r) =>
		(r["_field"] == "Port_TrueWindDir" or r["_field"] == "Port_TrueWindSpd"))
	|> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
	|> to(bucket: "daily_minute_data", org: "openrvdas")
```

# Usage
```
usage: samos_exporter.py [-h] [-q] [-v] [-d DATE] [-e] [-s] [-f CONFIG_FILE]

SAMOS Data Exporter

optional arguments:
  -h, --help            Show this help message and exit
  -q, --quiet           Reduce vebosity to only errors
  -v, --verbosity       Increase output verbosity
  -d DATE, --date DATE  Date to export (YYYY-mm-dd)
  -e, --email           Email exported data to SAMOS
  -s, --save            Save exported data to file
  -f CONFIG_FILE, --config_file CONFIG_FILE Used the specifed configuration file
```

By default the script will return the SAMOS-formatted data to stdout. If the `-s` or `-e` flags are specified the data will NOT appear on stdout.

- If no date is specified then the script will export for the *PREVIOUS* UTC day.

- If the `-s` argument is used then the destination path must exist and be writable by the user calling the script.

- If the `-e` argument is used then the Mailgun setting within `settings.py` must be completed and valid.

- If the `-f CONFIG_FILE` argument is used then it supersedes the INLINE_CONFIG variable in the settings.py file.

# Running automatically
Simpliest way to automatically run the script is `cron`. Here is the cron configuration to run the exporter at 5 minutes passed UTC midnight each UTC day.
```
# m h  dom mon dow   command
5 0 * * * su mt -c "/opt/samos_influx_exporter/venv/bin/python /opt/samos_influx_exporter/samos_exporter.py -q -s"
```
