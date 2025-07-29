#!/usr/bin/env python3
"""
FILE:           samos_data_builder.py

DESCRIPTION:    This script builds samos data using data pulled from influxDB.

BUGS:
NOTES:
AUTHOR:     Webb Pinner
COMPANY:    Schmidt Ocean Institute
VERSION:    1.0
CREATED:    2022-04-09
REVISION:   2022-10-27

LICENSE INFO:   This code is licensed under GPLv3 license (see LICENSE.txt for
                details). Copyright (C) Schmidt Ocean Institute 2022
"""

import logging
import re
import sys
from datetime import datetime, timedelta
from os.path import dirname, realpath

import pytz
from influxdb_client import Dialect, InfluxDBClient
from influxdb_client.rest import ApiException
from urllib3.exceptions import (ConnectTimeoutError, NewConnectionError,
                                ProtocolError)

sys.path.append(dirname(realpath(__file__)))
from samos_fields import SAMOS_FIELDS  # noqa: E402
from settings import (INFLUX_BUCKET, INFLUX_ORG,  # noqa: E402
                      INFLUX_SERVER_URL, INFLUX_TOKEN)

# Example of SAMOS format
# $SAMOS:001,CS:KAOU,YMD:20030907,HMS:000011,AT:17.40,BP:1010.27,WSP:5.6,WDP:354.4,TWP:5.4,TIP:278.3,WSS:6.7,WDS:350.5,TWS:6.6,TIS:274.4,LA:44.66956,LO:-130.35859,COG:149.5,SOG:0.9,GY:284.7,CS8:23  # noqa: E501


class SAMOSDataBuilder:
    """
    Class that handles the construction of an influxDB query and using the
    resulting data to build the SAMOS csv format.
    """

    def __init__(self, samos_data_config, influxdb_client=None):

        self.influxdb_client = influxdb_client or InfluxDBClient(
            url=INFLUX_SERVER_URL, token=INFLUX_TOKEN, org=INFLUX_ORG,
            timeout=5_000  # in milliseconds (5 seconds)
        )
        self._influxdb_client_api = self.influxdb_client.query_api()

        self.callsign = samos_data_config["callsign"]
        self._query_measurements = samos_data_config["measurements"]
        self._query_fields = [
            v for _, v in samos_data_config["fields"].items()
        ]
        self._fields = samos_data_config["fields"]

        self._influx_query_result = None
        self.logger = logging.getLogger(__name__)

        for field in self._fields.keys():
            if (
                field[:2] not in SAMOS_FIELDS
                or re.search("^[A-Z]{2}[0-9]?", field) is None
            ):
                logging.warning(
                    "Field: %s is not a standard SAMOS field identifier", field
                )

    @staticmethod
    def _build_query_range(ts):  # pylint: disable=invalid-name
        """
        Builds the temporal range for the influxDB query based on the provided
        timestamp (ts).
        """

        try:
            start_ts = ts.replace(tzinfo=pytz.utc)
            stop_ts = start_ts + timedelta(days=1)
            return (
                f'start: {start_ts.strftime("%Y-%m-%dT00:00:00.000Z")}, '
                f'stop: {stop_ts.strftime("%Y-%m-%dT00:00:00.000Z")}'
            )

        except Exception as err:
            logging.debug(str(err))

        return None

    def _build_query(self, ts=None):  # pylint: disable=invalid-name
        """
        Builds the complete influxDB query using the provided timestamp (ts)
        and the query_measurements and query_fields class properties.
        """

        if ts is None:
            ts = datetime.utcnow()

        query_range = self._build_query_range(ts)

        try:
            query = f'from(bucket: "{INFLUX_BUCKET}")\n'
            query += f"|> range({query_range})\n"
            query += "|> filter(fn: (r) => {})\n".format(
                " or ".join(
                    [
                        'r["_measurement"] == "{}"'.format(q_measurement)
                        for q_measurement in self._query_measurements
                    ]
                )
            )
            query += "|> filter(fn: (r) => {})\n".format(
                " or ".join(
                    [
                        'r["_field"] == "{}"'.format(q_field)
                        for q_field in self._query_fields
                    ]
                )
            )
            query += '|> keep(columns: ["_time", "_field", "_value"])'
            query += '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'  # noqa: E501
        except Exception as err:
            logging.error("Error building query string")
            logging.error(" - Range: %s", query_range)
            logging.error(" - Measurements: %s", self._query_measurements)
            logging.error(" - Fields: %s", self._query_fields)
            raise err

        logging.debug("Query:\n  %s", query
                      .replace('\n', '\n  ')
                      .replace(' or ', '\n     or '))
        return query

    def build_samos_csv(self, ts):  # pylint: disable=too-many-branches
        """
        Build the SAMOS csv output for the given timestamp (ts)
        """

        if self._influx_query_result is None:
            try:
                self.retrieve_samos_data(ts)
            except Exception:
                sys.exit(1)

        if self._influx_query_result is None:
            logging.info("Did not find any data for %s",
                         ts.strftime("%Y-%m-%d"))
            yield None

        csv_result = self._influxdb_client_api.query_csv(
            self._build_query(ts),
            dialect=Dialect(
                header=True,
                delimiter=",",
                comment_prefix="#",
                annotations=[],
                date_time_format="RFC3339",
            ),
        )

        try:
            header = next(csv_result)
        except StopIteration:
            pass

        errors = []
        for _, csv_line in enumerate(csv_result):
            if not len(csv_line) == 0:
                columns = [
                    "$SAMOS:001",
                    f"CS:{self.callsign}",
                    f'YMD:{csv_line[header.index("_time")][:10].replace("-","")}',  # noqa: E501
                    f'HMS:{csv_line[header.index("_time")][11:19].replace(":","")}',  # noqa: E501
                ]
                for key, val in self._fields.items():
                    try:
                        columns.append(f"{key}:{csv_line[header.index(val)]}")
                    except ValueError as err:
                        if str(err) not in errors:
                            errors.append(str(err))
                            logging.warning(str(err))
                        columns.append(f"{key}:NaN")

                yield ",".join(columns) + "\n"

    def retrieve_samos_data(self, ts=None):
        """
        Retrive the SAMOS data from InfluxDB.
        """

        logging.info("Retrieving SAMOS Data")

        query = self._build_query(ts)

        # run the query against the influxDB
        try:
            self._influx_query_result = self._influxdb_client_api.query(
                query=query)

        except NewConnectionError as err:
            logging.error(
                "New connection error, verify URL: %s", INFLUX_SERVER_URL
            )
            raise err

        except ProtocolError as err:
            logging.error(
                "Connection protocol error, verify URL: %s", INFLUX_SERVER_URL
            )
            raise err

        except ConnectTimeoutError as err:
            logging.error(
                "Connection timeout error, verify URL: %s", INFLUX_SERVER_URL
            )
            raise err

        except ApiException as err:
            _, value, _ = sys.exc_info()

            if str(value).startswith("(400)"):
                logging.error("InfluxDB API error, verify org: %s", INFLUX_ORG)
            elif str(value).startswith("(401)"):
                logging.error("InfluxDB API error, verify token: %s",
                              INFLUX_TOKEN)
            elif str(value).startswith("(404)"):
                logging.error("InfluxDB API error, verify bucket: %s",
                              INFLUX_BUCKET)
            else:
                logging.error("Unknown API error")
            raise err

        except Exception as err:
            logging.error("Error with query:")
            logging.error(query)
            raise err

    @property
    def samos_fields(self):
        """
        Getter method for the samos_fields property
        """
        return self._fields

    @property
    def measurements(self):
        """
        Getter method for the _query_measurements property
        """
        return self._query_measurements

    @property
    def fields(self):
        """
        Getter method for the _query_fields property
        """
        return self._query_fields

    @property
    def query_result(self):
        """
        Getter method for the _influx_query_result property
        """
        return self._influx_query_result
