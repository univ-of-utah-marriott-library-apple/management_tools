#!/usr/bin/env python

import argparse
import email
import os
import smtplib
import sys

from management_tools import loggers

def set_globals():
    global options
    options = {}
    options['long_name']     = "Management Email Helper"
    options['name']          = '_'.join(options['long_name'].lower().split()) + '.py'
    options['version']       = '1.0'

    options['smtp_server']   = os.getenv('MANAGEMENT_SMTP_SERVER', 'mail.example.com')
    options['smtp_port']     = os.getenv('MANAGEMENT_SMTP_PORT', '25')
    options['smtp_username'] = os.getenv('MANAGEMENT_SMTP_USER')
    options['smtp_password'] = os.getenv('MANAGEMENT_SMTP_PASS')
    options['smtp_from']     = os.getenv('MANAGEMENT_SMTP_FROM', 'sender@example.com')
    options['smtp_to']       = os.getenv('MANAGEMENT_SMTP_TO', 'recipient@example.com')
    options['file']          = None
    options['subject']       = None
    options['message']       = None

def parse_options():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-v', '--version', action='store_true')
    parser.add_argument('-n', '--no-log', action='store_true')
    parser.add_argument('-l', '--log')
    parser.add_argument('-f', '--file')
    parser.add_argument('-u', '--subject')
    parser.add_argument('-s', '--smtp-server')
    parser.add_argument('-p', '--smtp-port')
    parser.add_argument('-U', '--smtp-username')
    parser.add_argument('-P', '--smtp-password')
    parser.add_argument('-F', '--smtp-from')
    parser.add_argument('-T', '--smtp-to')
    parser.add_argument('message', nargs='?')
    args = parser.parse_args()

    if args.help:
        help()
    if args.version:
        version()
    options['log'] = not args.no_log
    options['log_dest'] = args.log
    # The following loop will stick the new values into the variables, but only
    # if they have been declared in the command line.
    for arg in args.__dict__:
        if arg == 'help' or arg == 'version' or arg == 'log' or arg == 'no-log':
            continue
        if args.__dict__[arg]:
            options[arg] = args.__dict__[arg]

def send_email():
    logger.info("Sending mail...")
    logger.info("    server:port: " + str(options['smtp_server']) + ":" + str(options['smtp_port']))
    logger.info("    username:    " + str(options['smtp_username']))
    logger.info("    to:          " + str(options['smtp_to']))
    logger.info("    from:        " + str(options['smtp_from']))
    logger.info("    subject:     " + str(options['subject']))
    logger.info("    file:        " + str(options['file']))
    msg = email.MIMEMultipart.MIMEMultipart()
    body = email.MIMEText.MIMEText(options['message'])
    msg.attach(body)
    if options['file']:
        attachment = email.MIMEBase.MIMEBase('text', 'plain')
        attachment.set_payload(open(options['file']).read())
        attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(options['file']))
        email.encoders.encode_base64(attachment)
        msg.attach(attachment)
    if options['subject']:
        msg.add_header('Subject', options['subject'])
    msg.add_header('From', options['smtp_from'])
    msg.add_header('To', options['smtp_to'])

    mailer = smtplib.SMTP(options['smtp_server'], options['smtp_port'])
    if options['smtp_username'] and options['smtp_password']:
        mailer.login(options['smtp_username'], options['smtp_password'])
    mailer.sendmail(options['smtp_from'], [options['smtp_to']], msg.as_string())
    mailer.close()
    logger.info("Message sent.")

def version():
    print "{name}, version {version}\n".format(name=options['long_name'],
                                               version=options['version'])
    sys.exit(0)

def help():
    try:
        version()
    except SystemExit:
        pass

    print '''\
usage: {} [-hvn] [-l log] [-f file] [-u subject] [-s server]
         [-p port] [-U user] [-P pass] [-F from] [-T to] (message)

Easily send emails in one line!

    h : prints this helpful information and quits
    v : prints the version information and quits
    n : prevents logs from being written to file (goes to standard output)

    l log      : use 'log' as the file to send logging information to
    f file     : attaches the plaintext 'file' as to the email
    u subject  : uses 'subject' as the message's subject
    s server   : sends the mail through 'server'
    p port     : set the port to use to connect to the server
    U username : sends mail under this username
    P password : used to connect with a particular username
    F from     : the 'sent from' address
    T to       : the recipient of the email

ENVIRONMENT DEFAULTS
    This script has the ability to utilize environment variables to make the
    sending process simpler in managed environments. The available variables
    which are checked are:

    Variable Name          | Correlating command-line flag
    -----------------------|------------------------------
    MANAGEMENT_SMTP_SERVER | -s --smtp-server
    MANAGEMENT_SMTP_PORT   | -p --smtp-port
    MANAGEMENT_SMTP_USER   | -U --smtp-username
    MANAGEMENT_SMTP_PASS   | -P --smtp-password
    MANAGEMENT_SMTP_FROM   | -F --smtp-from
    MANAGEMENT_SMTP_TO     | -T --smtp-to

    To set these variables prior to running the script, simply do:

    $ export VARIABLE_NAME="value"\
'''.format(options['name'])

    sys.exit(0)

def setup_logger():
    '''Creates the logger to be used throughout.

    If it was not specified not to create a log, the log will be created in either
    the default location (as per helpful_tools) or a specified location.

    Otherwise, the logger will just be console output.
    '''

    global logger
    if options['log']:
        # Write the logs to files.
        if not options['log_dest']:
            # If no destination is explicitly given, use the defaults.
            logger = loggers.file_logger(options['name'])
        else:
            # Otherwise, use the specified value.
            logger = loggers.file_logger(options['name'], path=options['log_dest'])
    else:
        # A dummy logger.  It won't record anything to file.
        logger = loggers.stream_logger(1)

def main():
    set_globals()
    parse_options()
    setup_logger()
    send_email()

if __name__ == '__main__':
    main()
