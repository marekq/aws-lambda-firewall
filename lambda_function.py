import boto3, re, time

# set the bucketname where the security group log should be written to. If left blank, no log will be written. 
bucketn     = 'lambdafirewall'  


##### do not touch anything below this line #####

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
                            resu.append(str(a))

                for z in range(len(x[u'Instances'][int(y)][u'SecurityGroups'])):
                    groid       = x[u'Instances'][int(y)][u'SecurityGroups'][int(z)][u'GroupId']
                    
                    if sgs.has_key(inst):
                        sgs[inst].append(groid)
                    else:
                        sgs[inst] = [groid]
    
    f       = open('/tmp/index.htm', 'w')
    
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
            if re.search(' ', desc):
                unixt   = desc.split(' ')[1]
            
                if re.search(r"\b\d{10}\b", unixt):
                    z       = int(time.time()) - int(unixt)
                        
                    if z > int(0):
                        if groid in sgs[x]:
                            sgs[x].remove(groid)
                            
                        if y[u'GroupName'] not in dele:
                            dele.append(y[u'GroupName'])
                            
                        modi    = True
            
                        print 'DEL: removing '+groid+' from '+x+', age '+str(z/60)+' minutes'
                    else:
                        print 'DEL: keeping  '+groid+' from '+x+', age '+str(z/60)+' minutes'
                else:
                    print 'DEL: keeping  '+groid+' from '+x+', age '+str(z/60)+' minutes'
        
            else:
                print 'DEL: keeping  '+groid+' from '+x
        
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

        print 'DESC:', desc, grona, groid

        if 'VpcId' in sg.keys():
            vpcid   = sg['VpcId']
        else:
            vpcid   = ''

        for ipp in sg['IpPermissions']:
            frpt    = ipp['FromPort']
            topt    = ipp['ToPort']

            for ipr in ipp['IpRanges']:
                cid = ipr['CidrIp']
                z   = '"'+groid+'","'+str(frpt)+'","'+str(topt)+'","'+cid+'","'+desc+'","'+grona+'","'+vpcid+'"'

            sgdi[groid]     = [frpt, topt, cid, grona, desc]
            timd[groid]     = desc
            
            glist.append(cid+'_'+str(topt))

            if prnt == 'Y':
                print z+'\n'
                
    return glist


def create_sg(s, cidr_ip, port, dura, proto, glist):
    for iid in set(ec2id):
        name        = cidr_ip+'/32_' + str(port)
        crea        = int(time.time())
        expire      = crea + (60 * int(dura))
        desc        = str(crea) + ' ' + str(expire) + ' ' + str(time.strftime("%d-%m-%Y_%H-%M"))

        if name not in glist:
            resp    = s.create_security_group(GroupName = name, Description = desc)
            sgid    = resp.get(u'GroupId')
            
            s.authorize_security_group_ingress(GroupId = sgid, IpProtocol = proto, CidrIp = cidr_ip+'/32', FromPort = int(port), ToPort = int(port))
            glist.append(name)

        else:
            for k, v in sgdi.iteritems():
                if name     == v[2]+'_'+str(v[1]):
                    sgid    = k

        a           = sgs[iid]

        a.append(sgid)
        s.modify_instance_attribute(Groups = a, InstanceId = iid)


def delete_sg(s, d):
    for x in d:
        try:
            s.delete_security_group(GroupName = x)
        except Exception as e:
            print 'FAIL: failed deleting ', str(x), e


def write_s3(s, filen, bucketn):
    if len(bucketn) != 0:
        t   = str(int(time.time()))+'.txt'
        s.upload_file(filen, Bucket = bucketn, Key = t)


def handler(event, context):
    s       = get_session('ec2')
    g       = get_secgroups(s, 'N')
    d, r    = get_fw_rules(s, g, 'N')

    create_sg(s, event['ip'], event['port'], event['duration'], event['proto'], g)
    delete_sg(s, d)

    g       = get_secgroups(s, 'Y')
    d, r    = get_fw_rules(s, g, 'Y')
    
    t       = get_session('s3')
    write_s3(t, '/tmp/index.htm', bucketn)
    
    return 'FIN: created security group for source '+event['ip']+' on port '+event['port']+' to IP\'s '+str(' '.join(ips))