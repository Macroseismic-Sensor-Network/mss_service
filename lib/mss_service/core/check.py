# -*- coding: utf-8 -*-
##############################################################################
# LICENSE
#
# This file is part of mss_service.
# 
# If you use mss_service in any program or publication, please inform and
# acknowledge its authors.
# 
# mss_service is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# mss_service is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with mss_dataserver. If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2022 Stefan Mertl
##############################################################################

''' Status check functions.

'''

import os
import re

import obspy


def check_serial(ssh, logger):
    ''' Get the MSS serial number.
    '''
    cmd = 'cat /home/mss/config/mss_serial'
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
    serial = ssh_stdout.readline().strip()

    return serial


def check_ntp(ssh, logger):
    ''' Check for a valid NTP connection.
    '''
    logger.info('Checking the NTP.')
    cmd = 'ntpq -np'
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
    response_list = ssh_stdout.readlines()
    response = "".join(response_list)
    
    working_server = []
    ntp_is_working = False

    if response.lower().startswith("no association id's returned"):
        logger.error("NTP is not running. ntpd response:\n %s", response)
    else:
        # Search for the header line.
        header_token = "===\n"
        header_end = response.find(header_token) + len(header_token)

        if not header_end:
            logger.error("NTP seems to be running, but no expected result was returned by ntpq: %s", response)
            return []

        logger.info("NTP is running.\n%s", response)

        payload = response[header_end:]
        for cur_line in payload.splitlines():
            cur_data = re.split(' +', cur_line)
            if cur_line.startswith("*") or cur_line.startswith("+"):
                if (int(cur_data[4]) <= (int(cur_data[5]) * 2)) and (int(cur_data[6]) > 0):
                    working_server.append(cur_data)

    if not working_server:
        logger.error("No working NTP servers found.")
    else:
        ntp_is_working = True

    return ntp_is_working, response_list


def check_datalink(ssh, logger):
    ''' Check the connection to the datalink server.
    '''
    logger.info('Checking datalink connection.')

    datalink_connected = False

    cmd = 'ping -c 1 mss.mertl-research.at'
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
    error_response = "".join(ssh_stderr.readlines()).strip()
    response = "".join(ssh_stdout.readlines()).strip()

    if error_response or not response:
        logger.error("Error reaching mss.mertl-research.at using ping:\n{:s}".format(error_response))
    else:
        cmd = 'ss -natp'
        ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
        error_response = "".join(ssh_stderr.readlines()).strip()
        response = ssh_stdout.readlines()
        logger.info("Output of ss -natp:\n%s", ''.join(response))

        if response:
            for cur_line in response:
                cur_line = cur_line.strip()
                cur_data = re.split(' +', cur_line)
                if (len(cur_data) == 6) and \
                   (cur_data[0].lower() == 'estab') and \
                   (cur_data[4].lower().endswith(':16000')) and \
                   (cur_data[5].lower().startswith('users:(("mseedscan2dali"')) and \
                   (int(cur_data[2]) <= 10000):
                    datalink_connected = True

    if datalink_connected:
        logger.info("Found a valid mseedscan2dali network connection.")
    else:
        logger.error("No valid mseedscan2dali network connection found.")
    
    return datalink_connected, response


def check_mss_record_service(ssh, logger):
    ''' Check if mss_record is running.
    '''
    logger.info('Checking the mss_record service.')
    cmd = 'systemctl status mss_record.service'
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
    response = ssh_stdout.readlines()

    mssr_is_running = False

    for cur_line in response:
        cur_line = cur_line.strip().lower()
        if cur_line.startswith('active: active (running) '):
            mssr_is_running = True
            break

    if mssr_is_running:
        logger.info("The mss_record service is running.")
    else:
        logger.error("The mss_record service is not running.")
        
    return mssr_is_running


def check_datafiles(ssh, logger):
    ''' Check the writing of miniseed data files.
    '''
    logger.info('Checking the miniseed data.')
    cmd = 'ls /home/mss/mseed/*.msd'
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
    filelist = ssh_stdout.readlines()
        
    data_updated = False
    recent_files = []

    if filelist:
        filedate_list = []
        filelist = sorted(filelist)
        for cur_file in filelist:
            filename = os.path.split(cur_file)[-1]
            filename = os.path.splitext(cur_file)[0]
            parts = filename.split('_')
            file_date = obspy.UTCDateTime(parts[-1])
            filedate_list.append(file_date)

        latest_date = max(filedate_list)
        now = obspy.UTCDateTime()
        
        if (now - latest_date) <= 60:
            data_updated = True
            
        if not data_updated:
            logger.error('No up-to-date miniseed files found. now: %s; last_file: %s;', now, latest_date)

        # Get the most recent files.
        recent_files = sorted(zip(filelist, filedate_list),
                              key = lambda x: x[1])
        recent_files = [x[0] for x in recent_files]
        recent_files = recent_files[-3:]
    else:
        logger.error('No data files found in the mseed folder.')

    if data_updated:
        logger.info("Found up-to-date miniseed data. mss_record is writing data files.")
        logger.info("The latest 3 data files:\n%s", ''.join(recent_files))
    else:
        if recent_files:
            logger.error("The miniseed data is outdated. mss_record is not writing miniseed data.")
            logger.info("The latest 3 data files:\n%s", ''.join(recent_files))
        else:
            logger.error("No miniseed data files found.")

    return data_updated, recent_files


def get_version_info(ssh, logger):
    ''' Get version information of MSS software.
    '''
    logger.info("Gathering MSS software version information.")
    version_info = {}
    
     # Get the mss image version.
    cmd = 'cat /etc/mss_image_version'
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
    version_info['image_version'] = ssh_stdout.readline().strip()

    # Get the mss-record package version.
    cmd = 'apt show python-mssrecord'
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
    for cur_line in ssh_stdout.readlines():
        cur_line = cur_line.lower().strip()
        if cur_line.startswith('version'):
            version_info['python-mssrecord_version'] = cur_line.split(':')[1].strip()

    # Get the mss-suite package version.
    cmd = 'apt show mss-suite'
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
    for cur_line in ssh_stdout.readlines():
        cur_line = cur_line.lower().strip()
        if cur_line.startswith('version'):
            version_info['mss-suite_version'] = cur_line.split(':')[1].strip()

    # Get the mss_record version.
    cmd = 'cat /usr/lib/python3/dist-packages/mss_record/version.py'
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
    version_info['mss_record_git_tag'] = ssh_stdout.readline().split('=')[1].strip().replace('"', '')

    cmd = 'cat /usr/lib/python3/dist-packages/mss_record/__init__.py | grep __version__'
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
    version_info['mss_record_version'] = ssh_stdout.readline().split('=')[1].strip().replace('"', '')

    return version_info


def get_config_info(ssh, logger):
    ''' Get the mss software configuration.
    '''
    logger.info("Gathering MSS software configuration information.")
    
    config_info = {}
    # Get the dali configuration.
    cmd = 'cat /home/mss/config/dali.ini'
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
    config_info['dali_config'] = ssh_stdout.readlines()
    
    # Get the configuration file.
    cmd = 'cat /home/mss/config/mss_record.ini'
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
    config_info['mss_record_config'] = ssh_stdout.readlines()

    return config_info


def get_mss_log_tail(ssh, logger, n_lines = 20):
    ''' Get the last entries of the mss_log file.
    '''
    logger.info("Getting the latest mss_record log file entries.")

    cmd = 'tail -n {:d} /home/mss/log/mss_record.log'.format(n_lines)
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command(cmd)
    log_tail = ssh_stdout.readlines()
    
    return log_tail
    
