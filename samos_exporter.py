#!/usr/bin/env python3
'''
FILE:           samos_exporter.py

DESCRIPTION:    This process export data from InfluxDB in the SAMOS data format.

BUGS:
NOTES:
AUTHOR:     Webb Pinner
COMPANY:    Schmidt Ocean Institute
VERSION:    1.1
CREATED:    2022-04-08
REVISION:   2024-08-14

LICENSE INFO:   This code is licensed under GPLv3 license (see LICENSE.txt for
                details). Copyright (C) Schmidt Ocean Institute 2024
'''

import os
import sys
import json
import logging
import tempfile
import itertools
import yaml
from datetime import datetime, timedelta

from os.path import dirname, realpath
sys.path.append(dirname(dirname(realpath(__file__))))

from samos_data_builder import SAMOSDataBuilder
from settings import MAILER_SUBJECT, MAILER_FROM, MAILER_TO, MAILER_CC, \
                     MAILER_TEXT, EMAIL_FN_PREFIX, FN_PREFIX, DEST_DIR, \
                     INLINE_CONFIG


import logging
from gmailer_oauth import gMailer

logging.basicConfig(level=logging.INFO)

def send_samos_email(dt:datetime, samos_data_fp):
    mailer = gMailer(
        token_file='token.json',
        client_secret_file='client_secret.json',
        sender=MAILER_FROM,
        recipient=MAILER_TO,
    )
    try:
        mailer.send_email(f'{MAILER_SUBJECT} - {dt.strftime("%Y-%m-%d")}', MAILER_TEXT.replace('<date>', dt.strftime("%Y-%m-%d")), [f'{EMAIL_FN_PREFIX}_{dt.strftime("%Y-%m-%d")}.csv'])

    except Exception as err:
        logging.error("Problem emailing SAMOS data")
        logging.debug(str(err))

def save_to_file(dt: datetime, samos_data_fp):
    '''
    Save exported SAMOS data to file
    '''

    try:
        samos_filename = os.path.join(DEST_DIR, f'{FN_PREFIX}_{dt.strftime("%Y-%m-%d")}.csv')

        with open(samos_filename, 'w') as fp:
            fp.write(samos_data_fp.read())

    except Exception as err:
        logging.error("Problem saving SAMOS data to file")
        logging.debug(str(err))

# -------------------------------------------------------------------------------------
# The main function of the utility
# -------------------------------------------------------------------------------------
if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='SAMOS Data Exporter')

    parser.add_argument('-q', '--quiet', action='store_true',
                        help='Reduce output verbosity')

    parser.add_argument('-v', '--verbosity', dest='verbosity',
                        default=1, action='count',
                        help='Increase output verbosity')

    parser.add_argument('-d', '--date', default=(datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d'),
                        type=lambda s: datetime.strptime(s, '%Y-%m-%d'),
                        help='Specify date of data to export (YYYY-mm-dd)')

    parser.add_argument('-e', '--email', default=False,
                        action='store_true',
                        help='Send email containing exported data to SAMOS')

    parser.add_argument('-s', '--save', default=False,
                        action='store_true',
                        help='Save exported data to file')

    parser.add_argument('-f', '--config_file', help='Used the specifed configuration file')

    parsed_args = parser.parse_args()

    ############################
    # Set up logging before we do any other argument parsing (so that we
    # can log problems with argument parsing).

    LOGGING_FORMAT = '%(asctime)-15s %(levelname)s - %(message)s'
    logging.basicConfig(format=LOGGING_FORMAT)

    LOG_LEVELS = {0: logging.ERROR, 1: logging.WARNING, 2: logging.INFO, 3: logging.DEBUG}

    if parsed_args.quiet:
        logging.getLogger().setLevel(LOG_LEVELS[0])
    else:
        parsed_args.verbosity = min(parsed_args.verbosity, max(LOG_LEVELS))
        logging.getLogger().setLevel(LOG_LEVELS[parsed_args.verbosity])

    samos_data_config = None # pylint: disable=invalid-name

    if parsed_args.config_file:
        try:
            with open(parsed_args.config_file, "r", encoding='utf-8') as file:
                samos_data_config = yaml.safe_load(file)
        except yaml.parser.ParserError:
            logging.error("Invalid YAML syntax")
            sys.exit(1)
    else:
        try:
            samos_data_config = yaml.safe_load(INLINE_CONFIG)
        except yaml.parser.ParserError:
            logging.error("Invalid YAML syntax")
            sys.exit(1)

    logging.debug(json.dumps(samos_data_config, indent=2))

    logging.info("Exporting data starting at: %s", parsed_args.date)

    samos_data_builder = SAMOSDataBuilder(samos_data_config)
    output = samos_data_builder.build_samos_csv(parsed_args.date)

    # If there is no output, exit
    peek = next(output, None)
    if peek is None:
        logging.info("No data found, Quitting")
        sys.exit(0)

    fd, path = tempfile.mkstemp()

    try:
        with os.fdopen(fd, 'r+') as fp:
            for line in itertools.chain([peek], output):
                fp.write(line)

            # If the data should be emailed to SAMOS
            if parsed_args.email:
                logging.info("Emailing exported data to: %s", MAILER_TO)
                fp.seek(0)
                send_samos_email(parsed_args.date, fp)

            # If the data should be emailed to SAMOS
            if parsed_args.save:
                logging.info("Saving exported data to: %s", os.path.join(DEST_DIR, f'{FN_PREFIX}_{parsed_args.date.strftime("%Y-%m-%d")}.csv'))
                fp.seek(0)
                save_to_file(parsed_args.date, fp)

            # If the data was not emailed or saved to file, send to stdout
            if not (parsed_args.email or parsed_args.save):
                fp.seek(0)
                print(fp.read())

    finally:
        os.remove(path)
