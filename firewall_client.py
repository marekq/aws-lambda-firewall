#!/usr/bin/python
# marek.kuczynski
# @marekq
# www.marek.rocks

import requests, sys
from optparse import OptionParser

# enter the API key provided by your API gateway
k 		= {'x-api-key': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'}

# enter the URL used by your API gateway
u		= 'https://xxxxxxxx.execute-api.eu-west-1.amazonaws.com'


##### do not touch anything below this line #####


parser = OptionParser()
parser.add_option("-p", "--port", 	dest="port", 	default="22", help="the port to whitelist on all EC2 instances, default is 22")
parser.add_option("-i", "--ip", 	dest="ip", 	default="", help="the external ip address to whitelist, default is your currentl ipinfo.io address")
parser.add_option("-x", 		dest="proto", 	default="tcp", help="specify tcp or udp as whitelist, default is tcp")
parser.add_option("-t", "--time", 	dest="dura",	default="30", help="amount of minutes for the whitelist to be active before being removed, default is 10 minutes")
(options, args) = parser.parse_args()


def get_ip(ip):
    if len(ip) == 0:
        r               = requests.get('http://ipinfo.io/ip', timeout=5)

        if r.status_code == int(200):
            return r.text.strip()

        else:
            return '127.0.0.1'
    else:
        return ip


def whitelist():
	ip	= get_ip(options.ip)
	q	= '/prod/firewall?ip='+ip+'&port='+options.port+'&duration='+options.dura+'&proto='+options.proto

	r 	= requests.get(u+q, headers = k)
	print r.content


whitelist()

