#!/usr/bin/env python3
"""
FILE:           samos_fields.py

DESCRIPTION:    This file contains the SAMOS fields used by the SAMOS-related
                functions.

BUGS:
NOTES:
AUTHOR:     Webb Pinner
COMPANY:    Schmidt Ocean Institute
VERSION:    1.0
CREATED:    2022-04-08
REVISION:

LICENSE INFO:   This code is licensed under GPLv3 license (see LICENSE.txt for
                details). Copyright (C) Schmidt Ocean Institute 2022
"""

SAMOS_FIELDS = {
    "AT": {"description": "Air Temperature", "units": "C"},
    "AX": {"description": "Auxiliary Air Temperature", "units": "C"},
    "BC": {"description": "Barometric Pressure Temperature", "units": "C"},
    "BP": {"description": "Barometric Pressure", "units": "mbar"},
    "CR": {"description": "Vessel Course Over Ground", "units": "deg"},
    "DP": {"description": "Dew Point", "units": "C"},
    "FL": {"description": "Fluorometer", "units": "\u03BCg/l"},
    "GY": {"description": "Vessel Heading", "units": "deg"},
    "LA": {"description": "Latitude", "units": "ddeg"},
    "LB": {"description": "LWR Body Temperature", "units": "K"},
    "LD": {"description": "LWR Dome Temperature", "units": "K"},
    "LO": {"description": "Longitude", "units": "ddeg"},
    "LT": {"description": "LWR Thermopile", "units": "volts"},
    "LW": {
        "description": "Long Wave Radiation [LWR] from Pyrgeometer",
        "units": "W/m2 ",
    },
    "OG": {"description": "Oxygen Consentration", "units": "mg/l"},
    "OS": {"description": "Oxygen Saturation", "units": "ml/l"},
    "OT": {"description": "Oxygen Temperature", "units": "C"},
    "OX": {"description": "Oxygen", "units": "ml/l"},
    "PH": {"description": "Alkalinity", "units": "pH"},
    "PR": {"description": "Precipitation", "units": "mm"},
    "PT": {"description": "Precipitation rate", "units": "mm/hr"},
    "RH": {"description": "Relative Humidity", "units": "%"},
    "RT": {"description": "Air Temperature", "units": "C"},
    "SA": {"description": "Salinity", "units": "PSU"},
    "SH": {"description": "Ashtech Heading", "units": "deg"},
    "SL": {"description": "Vessel Speed Over water", "units": "m/s"},
    "SM": {"description": "Ashtech Pitch", "units": "deg"},
    "SP": {"description": "Vessel Speed Over Ground", "units": "m/s"},
    "SR": {"description": "Ashtech Roll", "units": "deg"},
    "ST": {"description": "Sea Surface Temperature", "units": "C"},
    "SV": {"description": "Sound Velocity [Chen/Millero]", "units": "m/s"},
    "SW": {
        "description": "Short Wave Radiation [SWR] from Pyranometer",
        "units": "W/m2 ",
    },
    "TB": {"description": "Turbidity", "units": "NTU"},
    "TC": {"description": "SBE21 Conductivity", "units": "mS/m"},
    "TI": {
        "description": "True Wind Direction; Direction wind is coming from",
        "units": "deg",
    },
    "TK": {"description": "True Wind Speed", "units": "m/s"},
    "TR": {"description": "Transmissometer", "units": "%"},
    "TT": {"description": "SBE21 Temperature", "units": "C"},
    "TW": {"description": "True Wind Speed", "units": "m/s"},
    "VH": {"description": "VRU Heave", "units": "m"},
    "VP": {"description": "VRU Pitch", "units": "deg"},
    "VR": {"description": "VRU Roll", "units": "deg"},
    "VX": {"description": "Vessel Trim", "units": "deg"},
    "VY": {"description": "Vessel List", "units": "deg"},
    "WD": {"description": "Wind Direction, Relative to bow;", "units": "deg"},
    "WS": {"description": "Wind Speed, Relative to vessel", "units": "m/s"},
    "WT": {"description": "Auxiliary Water Temperature", "units": "C"},
    "ZD": {
        "description": "GPS Date Time GMT",
        "units": "Seconds Since 00:00:00 01/01/1970",
    },
    "HM": {
        "description": (
            "Hour, minute, second (hhmmss) time of reported spot or average "
            "observation in GMT"
        ),
        "units": "",
    },
    "YM": {
        "description": (
            "Year, month, day (YYYYMMDD) of reported spot or average "
            "observation in GMT"
        ),
        "units": "",
    },
    "DT": {
        "description": (
            "Date and time (YYYYMMDDhhmmss) of reported spot or average "
            "observation in GMT"
        ),
        "units": "",
    },
}
