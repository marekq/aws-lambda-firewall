#!/usr/bin/python

# marek.kuczynski
# @marekq
# www.marek.rocks

# set the bucketname where the security group log should be written to. If left blank, no log will be written. 
bucketn     = 'lambda-firewall'  

##### do not touch anything below this line #####

import boto3, re, time

ec2id       = []
ips         = []
delgr       = []

sgs         = {}
sgdi        = {}
timd        = {}


def get_fw_rules(s, glist, prnt):
    resu            = []
    inst            = s.describe_instances()

    for x in inst[u'Reservations']:
        for y in range(len(x[u'Instances'])):
            inst    = x[u'Instances'][int(y)][u'InstanceId']
            stat    = x[u'Instances'][int(y)][u'State'][u'Name']
            ec2id.append(inst)
            
            if stat == 'running':
                pubi        = x[u'Instances'][int(y)][u'PublicIpAddress']
                if pubi not in ips:
                    ips.append(pubi)

                for z in range(len(x[u'Instances'][int(y)][u'NetworkInterfaces'])):
                    for a in range(len(x[u'Instances'][int(y)][u'NetworkInterfaces'][int(z)][u'Groups'])):
                        sggr        = x[u'Instances'][int(y)][u'NetworkInterfaces'][int(z)][u'Groups'][int(a)][u'GroupId']
                 
                        frpt        = sgdi[sggr][0]
                        topt        = sgdi[sggr][1]
                        cidr        = sgdi[sggr][2]
                        grona       = sgdi[sggr][3]
                        desc        = sgdi[sggr][4]

                        if prnt == 'Y':
                            a       = pubi, inst, desc, grona, sggr, str(topt), str(frpt), cidr
                            b       = ' '.join(a)
                            resu.append(str(b))

                for z in range(len(x[u'Instances'][int(y)][u'SecurityGroups'])):
                    groid       = x[u'Instances'][int(y)][u'SecurityGroups'][int(z)][u'GroupId']
                    
                    if sgs.has_key(inst):
                        sgs[inst].append(groid)
                    else:
                        sgs[inst] = [groid]
    
    f       = open('/tmp/index.txt', 'w')
    
    for x in resu:
        f.write(str(x).strip())
        print 'RES: '+str(x).strip()
    f.close()
    
    secg    = s.describe_security_groups()
    dele    = []
    
    for x in set(ec2id):
        modi            = False
        
        for y in secg[u'SecurityGroups']:
            groid       = y[u'GroupId']
            desc        = y[u'Description']
            grona       = y[u'GroupName']
          
            if re.search('/32_', grona):
                unixt   = desc.split(' ')[3]
            
                if re.search(r"\b\d{10}\b", unixt):
                    z   = int(time.time()) - int(unixt)
                        
                    if z > int(0):
                        if groid in sgs[x]:
                            sgs[x].remove(groid)
                            
                        if y[u'GroupName'] not in dele:
                            dele.append(y[u'GroupName'])
                            
                        modi    = True
            
                        print 'DEL: removing '+groid+', '+grona+' from '+x+', age '+str(z/60)+' minutes, '+desc
                    else:
                        print 'DEL: keeping '+groid+', '+grona+' from '+x+', age '+str(z/60)+' minutes, '+desc
                else:
                    print 'DEL: keeping '+groid+', '+grona+' from '+x+', age '+str(z/60)+' minutes, '+desc
        
            else:
                print 'DEL: keeping '+groid+', '+grona+' from '+x+' , '+desc
        
        if modi:
            s.modify_instance_attribute(Groups = sgs[x], InstanceId = x)

    return dele, resu
    
        
def get_session(serv):
    s               = boto3.session.Session()
    session         = s.client(serv, region_name = 'eu-west-1')
    return session
    

def get_secgroups(s, prnt):
    glist           = []
    delgr           = []
    sgs             = s.describe_security_groups()
    
    for sg in sgs['SecurityGroups']:
        desc        = sg['Description']
        grona       = sg['GroupName']
        groid       = sg['GroupId']

        if 'VpcId' in sg.keys():
            vpcid   = sg['VpcId']
        else:
            vpcid   = ''

        print sg['IpPermissions']

        for ipp in sg['IpPermissions']:
            frpt    = ipp['FromPort']
            topt    = ipp['ToPort']

            for ipr in ipp['IpRanges']:
                cid = ipr['CidrIp']
                z   = '"'+groid+'","'+str(frpt)+'","'+str(topt)+'","'+cid+'","'+desc+'","'+grona+'","'+vpcid+'"'

            sgdi[groid]     = [frpt, topt, cid, grona, desc]
            timd[groid]     = desc
            
            glist.append(cid+'/32_'+str(topt))

            if prnt == 'Y':
                print z+'\n'
                
    return glist


def create_sg(s, cidr_ip, port, dura, proto, glist):
    for iid in set(ec2id):
        name        = cidr_ip+'/32_' + str(port)
        modi        = False

        crea_u      = int(time.time())
        crea_t      = time.strftime('%Y-%m-%d %H-%M-%S', time.localtime(crea_u))
        
        expire_u    = crea_u + int(dura)
        expire_t    = time.strftime('%Y-%m-%d %H-%M-%S', time.localtime(expire_u))

        desc        = str(crea_u) + ' ' + str(crea_t) + ' ' + str(expire_u) + ' ' + str(expire_t) 

        if name not in glist:
            try:
                resp    = s.create_security_group(GroupName = name, Description = desc)
                sgid    = resp.get(u'GroupId')
            
                s.authorize_security_group_ingress(GroupId = sgid, IpProtocol = proto, CidrIp = cidr_ip+'/32', FromPort = int(port), ToPort = int(port))
                glist.append(name)
                modi    = True
                
            except Exception as e:
                print 'ERROR: '+str(e)

        else:
            for k, v in sgdi.iteritems():
                if name     == v[2]+'_'+str(v[1]):
                    sgid    = k

        a           = sgs[iid]

        if modi:
            a.append(sgid)
            s.modify_instance_attribute(Groups = a, InstanceId = iid)


def delete_sg(s, d):
    for x in d:
        try:
            s.delete_security_group(GroupName = x)
        
        except Exception as e:
            print 'FAIL: failed deleting ', str(x), e


def write_s3(s, filen, bucketn, k):
    s.upload_file(filen, Bucket = bucketn, Key = k)


def handler(event, context):
    s       = get_session('ec2')
    g       = get_secgroups(s, 'N')
    d, r    = get_fw_rules(s, g, 'N')
    delete_sg(s, d)

    a       = event.get('ip', 'False')
    if a != 'False':
        t1      = str(event['duration'])
        t2      = int(event['duration']) * 60
        
        i       = event['ip']
        p       = event['port']
        o       = event['proto']
        
        print 'add groups '+str(g)
        create_sg(s, i, p, t2, o, g)
    
    g       = get_secgroups(s, 'Y')
    d, r    = get_fw_rules(s, g, 'Y')

    s       = get_session('s3')
    k       = str(int(time.time()))+'.txt'

    write_s3(s, '/tmp/index.txt', bucketn, k)
    write_s3(s, '/tmp/index.txt', bucketn, 'index.txt')
    
    if a != 'False':
        return 'FIN: created security group for source IP '+i+' on port '+p+' for '+t1+' minutes to IP\'s '+', '.join(ips)
    
    else:  
        return r
