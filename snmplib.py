import os,Snmp,time,re

def SnmpGetWanIp(cmtsip,cmMac):
    for i in range(5):
        try:
            cmtsIpDic = Snmp.SnmpWalk(cmtsip,snmp_oid('docsIfCmtsCmStatusMacAddress'))
            break
        except:
            print("Retry Snmp Query IP Index %d"%i)
            if i == 4:raise Exception('Query Ip Index Fail!!')
            time.sleep(2)
            continue
    ipIdx = ''
    for v in cmtsIpDic:
        if str(v.split(' ')[-1].upper())[2:] == cmMac:
            ipIdx = v.split(' ')[0].split('.')[-1]
    if not ipIdx: raise Exception('Invalid Mac Address!!')
    return Snmp.SnmpGet(cmtsip,snmp_oid('docsIfCmtsCmStatusIpAddress'),ipIdx)

def UsSnrMer(*argv):
    mac = argv[2][0]
    term = argv[1][-1]
    SNR = int(argv[-3](argv[-2],'SNR'))
    MER = int(argv[-3](argv[-2],'MER'))
    us_channel = int(argv[-3](argv[-2],'us_channel'))
    cmts = argv[-3]('Base','CMTSIP')
    ipaddr = SnmpGetWanIp(cmts,mac)
    log = argv[-4]
    ################check SC SNR################
    for i in range(10):
        try:
            cmtsIpDic = Snmp.SnmpWalk(cmts,snmp_oid('docsIfCmtsCmStatusIpAddress'))
            ipIdx = cmtsIpDic.keys()[cmtsIpDic.values().index(ipaddr)].split('.')[-1]
            break
        except:
            print("Rery Snmp Query IP Index %d"%i)
            if i == 9:raise Except('Query Ip Index Fail!!')
            time.sleep(2)
            continue
    
    for retry in range(3):
        snrDic = Snmp.SnmpWalk(cmts,snmp_oid('docsIf3CmtsCmUsStatusSignalNoise')+'.'+ipIdx)
        print(snrDic)
        time.sleep(2)
        chList = []
        for i,s in enumerate(sorted(snrDic)):
            snr = snrDic[s]/10.0
            if snr > 100: continue
            if snr < 10: continue
            if snr >= SNR:
                chList.append(snr) 
                log('Channel:%s Index:%s SNR : %d (=> %d)'%(i,s.split('.')[-1],snr,SNR))
            #else:
            #    log('Channel:%s Index:%s SNR : %d (=> %d)'%(i,s.split('.')[-1],snr,SNR),1)
        if len(chList) >= us_channel: 
            log('SC-QAM US SNR check pass',2)
            break
        if retry == 2: raise Except('SCQAM SNR Fail!!')
    for re in range(3):
        ofdmalist = []
        snrOfdmaList = Snmp.SnmpWalk(cmts,snmp_oid('docsIf31CmtsCmUsOfdmaChannelMeanRxMer')+'.'+ipIdx).values()
        time.sleep(2)
        for a in snrOfdmaList:
            snr = a/100.0
            if snr >= MER:
                ofdmalist.append(snr)
                log('OFDMA SNR : %d (=> %d)'%(snr,MER))
            else:
                log('OFDMA SNR : %d (=> %d)'%(snr,MER),1)
        if len(ofdmalist) == 1: 
            log('OFDMA SNR check pass',2)
            break
        if re == 2: raise Except('OFDMA SNR Fail!!')
    
def WaitCMregistor(mac,cmtsip,timeout):
    s_time=timeout+time.time()+0.1
    while time.time() < s_time:
          value=getWlanip(mac,cmtsip)
          print(value)
          #print('registor :',)
          #print(value)
          if value[0]:
             break 
    return value

def SnmpCheckUsSignal(*argv):
    '''
    argv :
        dutid,terms,labels,Panel,Log,Config,flow,[Return])
        terms : ccu , cb , sw , vm ,dut 
    ''' 
    mac = argv[2][0]
    term = argv[1][-1]   
    log = argv[-4]
    usChannel = int(argv[-3](argv[-2],'usChannel'))
    ofdmaChannel = int(argv[-3](argv[-2],'ofdmaChannel'))
    cmts = argv[-3]('Base','CMTSIP')
    ipaddr = SnmpGetWanIp(cmts,mac)
    # lWaitCmdTerm(term,'shell','#',3,3)
    # ipaddr = GetWanIP(term)
    #system_uspower = eval(argv[-3]('Base','system_uspower'))
    ofdm_uspower = eval('ofdm_uspower')
    #ofdm_uspower = int(argv[-3]('Base','ofdm_uspower'))
    uspower_offset = eval(argv[-3]('Base','uspower_offset'))
    us_ofdm_offset = eval(argv[-3]('Base','us_ofdm_offset'))
    freq_step = argv[-3]('Base','freq_step')
    #freq_uspower_NA = eval('uspower_%s'%freq_step)
    # freq_uspower_NA = {38800000: 0, 37000000: 0, 40600000: 0, 35200000: 0}
    idxFreqDic = {}
    for i in range(5):
        try:
            us_freq_dic = Snmp.SnmpWalk(ipaddr,snmp_oid('docsIfUpChannelFrequency'))
            break
        except:
            print("Retry Snmp Query US SC-QAM Frequency %d"%i)
            if i == 4:raise Except('Query US SC-QAM Frequency Fail!!')
            time.sleep(2)
            continue
    for try_ in range(3):
        for freq in us_freq_dic:
            if us_freq_dic[freq] !=0:
                idxFreqDic.update({us_freq_dic[freq]: freq.split('.')[-1]})
        msg_us_lock = "US Channel Lock: %d (%d)"%(len(idxFreqDic),usChannel)
        if len(idxFreqDic) != usChannel:
            if try_ == 2: 
                log(msg_us_lock,1)
                raise Except("ErrorCode(E00242): US Channel Lock  FAIL")
            else: continue 
        else:
            log(msg_us_lock,2)
            break
    test_fail = 0
    #print(idxFreqDic)
    for freq in idxFreqDic:     # US power comparison
        #print(freq)
        freq = int(freq)
        pwr =  Snmp.SnmpGet(ipaddr,snmp_oid('docsIf3CmStatusUsTxPower')+'.'+idxFreqDic[freq]).values()[0]/10.0
        print(type(pwr))
        #system_uspower = cmts_uspwr[freq]
        msg_pwr = "US Freq = %.2f MHz, Base Power = %.2f Report = %.2f, diff = %.2f (%.2f ~ %.2f)"%(freq/1000000.0,freq_uspower_NA[freq],pwr,pwr - freq_uspower_NA[freq], uspower_offset*-1,uspower_offset)
        pwr =  pwr - freq_uspower_NA[freq]
        #print(pwr)
        if abs(pwr) > uspower_offset:
            test_fail+=1
            log(msg_pwr,1)
        else:
            log(msg_pwr,2)
    if test_fail > 4: raise Except("ErrorCode(E00242): US Power Check  FAIL")
    
    ############### OFDMA ###############
    idxOfdmaFreqDic = {}
    for i in range(5):
        try:
            ofdma_freq_dic = Snmp.SnmpWalk(ipaddr,snmp_oid('docsIf31CmUsOfdmaChanSubcarrierZeroFreq'))
            break
        except:
            print("Retry Snmp Query OFDMA Frequency %d"%i)
            if i == 4:raise Except('Query OFDMA Frequency Fail!!')
            time.sleep(2)
    for try_ in range(3):
        for freq in ofdma_freq_dic:
            if ofdma_freq_dic[freq] !=0:
                idxOfdmaFreqDic.update({ofdma_freq_dic[freq]: freq.split('.')[-1]})
        msg_ofdma_lock = "OFDMA Channel Lock: %d (%d)"%(len(idxOfdmaFreqDic),ofdmaChannel)
        if len(idxOfdmaFreqDic) != ofdmaChannel:
            if try_ == 2:
                log(msg_ofdma_lock,1)
                raise Except("ErrorCode(E00242): OFDMA Channel Lock FAIL")
            else: continue 
        else:
            log(msg_ofdma_lock,2)
            break
    log('\n')
    test_fail = 0
    for freq in idxOfdmaFreqDic:     # US power comparison
        #print(freq)
        pwr =  Snmp.SnmpGet(ipaddr,snmp_oid('docsIf31CmUsOfdmaChanTxPower')+'.'+idxOfdmaFreqDic[freq]).values()[0]/4.0
        #print(pwr)
        #system_uspower = cmts_uspwr[freq]
        pwrOffset =  pwr - ofdm_uspower
        msg_pwr = "Check US OFDM repower  = %.2f, Base Power = %.2f , Offset = %.2f (%.2f ~ %.2f)"%(pwr,ofdm_uspower,pwrOffset,us_ofdm_offset*-1,us_ofdm_offset)
        #print(pwr)
        if abs(pwrOffset) > us_ofdm_offset:
            test_fail+=1
            log(msg_pwr,1)               
        else:
            log(msg_pwr,2)
    if test_fail: raise Except("ErrorCode(E00242): OFDMA Power Check FAIL")

def SnmpCheckDsSignal(*argv):
    '''
    argv :
        dutid,terms,labels,Panel,Log,Config,flow,[Return])
        terms : ccu , cb , sw , vm ,dut 
    ''' 
    mac = argv[2][0]
    cmts = argv[-3]('Base','CMTSIP')
    term = argv[1][-1]   
    log = argv[-4]
    pn = argv[-3]('Base','PN')
    dsChannel = int(argv[-3](argv[-2],'dsChannel'))
    ofdmChannel = int(argv[-3](argv[-2],'ofdmChannel'))
    #ds_snr_oid = '1.3.6.1.2.1.10.127.1.1.4.1.5'
    ipaddr = SnmpGetWanIp(cmts,mac)
    freq_step = argv[-3]('Base','freq_step')
    system_snr = eval(argv[-3]('Base','system_snr'))
    snr_offset = eval(argv[-3]('Base','snr_offset'))
    dspower_offset = eval(argv[-3]('Base','dspower_offset'))
    port =argv[0]+1
    if port > 4 : port -= 4
    for try_ in range(3): 
        sn=lWaitCmdTerm(argv[1][1],'sn','sn',3,3).split()[-1]
        if len(sn)==12:break
    dspower=eval('dspower_%s_%s_%s'%(freq_step,sn,port))
    # dspower = {639: 0, 645: 0, 615: 0, 627: 0, 609:0, 603: 0, 633: 0, 621: 0}
    idxFreqDic = {}
    for i in range(5):
        try:
            ds_freq_dic = Snmp.SnmpWalk(ipaddr,snmp_oid('docsIfDownChannelFrequency'))
            break
        except:
            print("Retry Snmp Query DS Frequency %d"%i)
            if i == 4:raise Except('Query DS Frequency Fail!!')
            time.sleep(2)
    for try_ in range(3):       
        for freq in ds_freq_dic:
            if ds_freq_dic[freq] !=0:
                idxFreqDic.update({ds_freq_dic[freq]: freq.split('.')[-1]})
        msg_lock = "DS Channel Lock: %d (%d)"%(len(idxFreqDic),dsChannel)
        if len(idxFreqDic) != dsChannel:
            if try_ == 2: 
                log(msg_lock,1)
                raise Except("ErrorCode(E00242): %s DS Channel Lock  FAIL"%ipaddr)
            else: continue
        else:
            log(msg_lock,2)
            break
    log('\n')
    test_fail = 0
    for f in sorted(idxFreqDic):     # DS power comparison
        freq = f/1000000.0
        pwr = Snmp.SnmpGet(ipaddr,snmp_oid('docsIfDownChannelPower')+'.'+idxFreqDic[f]).values()[0]/10.0      
        msg_pwr = "DS Freq = %.2f MHz, Base Power = %.2f Report = %.2f, diff = %.2f (%.2f ~ %.2f)"%(freq,dspower[freq],pwr,pwr - dspower[freq], dspower_offset*-1,dspower_offset)
        pwr = pwr - dspower[freq]
        if abs(pwr) > dspower_offset:
            test_fail+=1 
            log(msg_pwr,1)
        else:
            log(msg_pwr,2)
    if test_fail : raise Except("ErrorCode(E00242): %s DS Power Check  FAIL"%ipaddr)            
    log('\n')            
    test_fail = 0
    for f in sorted(idxFreqDic):     # US power comparison
        freq = f/1000000.0
        snr =  Snmp.SnmpGet(ipaddr,snmp_oid('docsIf3SignalQualityExtRxMER')+'.'+idxFreqDic[f]).values()[0]/10.0 
        msg_snr = "DS Freq = %.2f MHz, RxMER = %.2f ( > %.2f)"%(freq, snr,system_snr)
        if snr < system_snr : 
            test_fail+=1 
            log(msg_snr,1)
        else:
            log(msg_snr,2)
    if test_fail: raise Except("ErrorCode(E00242): %s DS RxMER Check  FAIL"%ipaddr)
    ############### OFDM ###################
    idxOfdmFreqDic = {}
    for i in range(5):
        try:
            ofdm_freq_dic = Snmp.SnmpWalk(ipaddr,snmp_oid('docsIf31CmDsOfdmChanSubcarrierZeroFreq'))
            break
        except:
            print("Retry Snmp Query OFDM Frequency %d"%i)
            if i == 4:raise Except('Query Query OFDM Frequency Fail!!')
            time.sleep(2)
    for try_ in range(3):       
        for freq in ofdm_freq_dic:
            if ofdm_freq_dic[freq] !=0:
                idxOfdmFreqDic.update({ofdm_freq_dic[freq]: freq.split('.')[-1]})
        msg_lock = "OFDM Channel Lock: %d (%d)"%(len(idxOfdmFreqDic),ofdmChannel)
        if len(idxOfdmFreqDic) != ofdmChannel:
            if try_ == 2: 
                log(msg_lock,1)
                raise Except("ErrorCode(E00242): %s OFDM Channel Lock  FAIL"%ipaddr)
            else: continue
        else:
            log(msg_lock,2)
            break
    test_fail = 0
    # ofdm_dspower = {820:-1,801:-5,807:-1.5,813:-0.8,819:-2,825:-1.5,831:-1,837:0.66,843:-1,849:-12}
    for s in sorted(idxOfdmFreqDic):     # DS power comparison
        idxOfdmChCenFreqDic = {}
        cenFreqDic = Snmp.SnmpWalk(ipaddr,snmp_oid('docsIf31CmDsOfdmChannelPowerCenterFrequency')+'.'+idxOfdmFreqDic[s])
        for q in cenFreqDic:
            idxOfdmChCenFreqDic.update({cenFreqDic[q]: q.split('.')[-1]})
        for f in idxOfdmChCenFreqDic:
            if idxOfdmChCenFreqDic[f] == '3' or idxOfdmChCenFreqDic[f] == '7':
                freq = f/1000000.0
                pwr = Snmp.SnmpGet(ipaddr,snmp_oid('docsIf31CmDsOfdmChannelPowerRxPower')+'.'+idxOfdmFreqDic[s]+'.'+idxOfdmChCenFreqDic[f]).values()[0]/10.0      
                msg_pwr = "DS Freq = %.2f MHz, Base Power = %.2f, Report = %.2f, diff = %.2f (%.2f ~ %.2f)"%(freq, ofdm_dspower[freq],pwr ,pwr - ofdm_dspower[freq], dspower_offset*-1,dspower_offset)
                pwr = pwr - ofdm_dspower[freq]
                if abs(pwr) > dspower_offset:
                    test_fail+=1 
                    log(msg_pwr,1)
                else:
                    log(msg_pwr,2)
            else:continue
    if test_fail: raise Except("ErrorCode(E00242): %s OFDM Power Check  FAIL"%ipaddr)
    test_fail = 0
    for f in sorted(idxOfdmFreqDic):
        freq = f/1000000.0
        snr =  Snmp.SnmpGet(ipaddr,snmp_oid('docsPnmCmDsOfdmRxMerMean')+'.'+idxOfdmFreqDic[s]).values()[0]/100.0 
        msg_snr = "OFDM Freq = %.2f MHz, RxMER = %.2f ( > %.2f)"%(freq, snr,system_snr)
        if snr < system_snr : 
            test_fail+=1 
            log(msg_snr,1)
        else:
            log(msg_snr,2)
    if test_fail: raise Except("ErrorCode(E00242): %s OFDM RxMER Check FAIL"%ipaddr)
           
def find_object(name):
    mibpath = os.getcwd()+'/mibs/'
    s = [x for x in os.listdir(mibpath)]
    for x in s:
        e = open(mibpath+x,'r')
        data = e.read()
        datalist = data.split('\n')
        for line in datalist:
            if name in line:
                # print(line)
                if any(c in line for c in ['OBJECT-TYPE','MODULE-IDENTITY','OBJECT IDENTIFIER']):
                    # print(x)
                    # objIdxLocat = data.find(data[data.find(name):].split('\n')[0])
                    objIdxLocat = data.find(line)
                    # print(objIdxLocat)
                    objIdxStart = data[objIdxLocat:].find('::=')
                    # print(objIdxStart)
                    objIdxEnd = data[objIdxLocat+objIdxStart:].find('}')
                    # print(objIdxEnd)
                    objdata = data[(objIdxLocat+objIdxStart):(objIdxLocat+objIdxStart+objIdxEnd+1)]
                    # print(objdata)
                    m = re.match(".*\{(.*)\}.*", objdata)
                    # print(m.group(1).strip().split(' '))
                    if m.group(1).strip().split(' ')[0] == name:continue
                    return m.group(1).strip().split(' ')
            # elif name and 'MODULE-IDENTITY' in data[data.find(name):].split('\n')[0]
    return [None,name]

def snmp_oid(name):
    oid = ''
    while True:
        getmib = find_object(name)
        if not getmib[0]:break
        if getmib[0] == name:break
        name = getmib[0]
        oid = '%s.'%getmib[1]+oid
    return '1.'+oid[:-1]