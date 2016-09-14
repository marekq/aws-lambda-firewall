#!/usr/bin/python

# marek.kuczynski
# @marekq
# www.marek.rocks

# enter the API key provided by your API gateway
k 		= {'x-api-key': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'}

# enter the URL used by your API gateway
u		= 'https://xxxxxxxxxx.execute-api.eu-west-1.amazonaws.com'


##### do not touch anything below this line #####


import requests, sys

if len(sys.argv) == int(5):
	ip	= sys.argv[1]
	po	= sys.argv[2]
	pr	= sys.argv[3]
	du	= sys.argv[4]
else:
	ip = po = pr = du = ''


def get_ip(ip):
    if len(ip) == 0:
        r               = requests.get('http://ipinfo.io/ip', timeout=5)

        if r.status_code == int(200):
            return r.text.strip()
        else:
            return '127.0.0.1'
    else:
        return ip


def get_port(po):
	if len(po) == 0:
		return '22'
	else:
		return str(po)


def get_dura(du):
	if len(du) != 0:
		return str(du)
	else:
		return '10'


def get_proto(pr):
	if len(pr) == 0:
		return 'tcp'
	else:
		return str(pr)


def whitelist():
	i	= get_ip(ip)
	p	= get_port(po)
	d	= get_dura(du)
	t	= get_proto(pr)

	q	= '/prod/firewall?ip='+i+'&port='+p+'&duration='+d+'&proto='+t

	r 	= requests.get(u+q, headers = k)
	print r.content

whitelist()