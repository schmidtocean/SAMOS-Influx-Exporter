# SAMOS-Influx-Exporter
Python Utility used to build and optionally submit SAMOS data extracted from InfluxDB

# Install
## Clone repo
Clone the local repo to the desired destination
```
git clone https://github.com/schmidtocean/SAMOS-Influx-Exporter.git /opt/samos_influx_exporter
```

## Setup python env
Setup a python venv for the project
```
cd /opt/samos_influx_exporter
python3 -m venv venv
source /opt/samos_influx_exporter/venv/bin/activate
pip install influxdb_client requests  pytz pyyaml
```
## Create the settings file

### Create the settings file from the included template
```
cp settings.py.dist settings.py
```

### Modify the required fields
This includes all the parts of the file where the variable name is capitalized. i.e. `<SHIP_NAME>`

### Optional SAMOS configuration file
The settings file includes a `INLINE_CONFIG` yaml-formatted string for defining how to map the InfluxDB data export to the SAMOS data format.  This part of the settings file can be overridden via the `--config_file <config_file>` command-line argument.  The contents of this config file must be a valid yaml object matching the schema of the INLINE_CONFIG string.