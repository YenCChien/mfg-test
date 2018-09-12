import datetime
import time
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
from dash.dependencies import Input, Output, Event, State
from flask import request
import Snmp
from snmplib import *
import pandas as pd
from mongo import *
import bz2
from collections import defaultdict


'''
### Basic Setting ###
CMTS = '192.168.5.254'
# MongoServer = '192.168.5.20'
mibs = {
        'DsQAM':    ['docsIfDownChannelPower'],
        'RxMER' :   ['docsIf3SignalQualityExtRxMER'],
        # 'OFDM':   ['docsIf31CmDsOfdmChannelPowerRxPower','docsPnmCmDsOfdmRxMerMean'],
        'UsQAM':    ['docsIf3CmStatusUsTxPower'],
        # 'UsSNR':    ['docsIf3CmtsCmUsStatusSignalNoise'],
        # 'OFDMA':  ['docsIf31CmtsCmUsOfdmaChannelMeanRxMer','docsIf31CmUsOfdmaChanTxPower']
        }
RxMER = 38
UsSNR = 40
DsPower = {
            '192.168.10.70':{333:0,339:0.5,345:0.9,351:0.5,357:0.2,363:-0.5,369:-0.4,375:-0.5,381:0.1,387:0,393:0,399:0,405:0,411:0,417:0,423:0},
            '192.168.10.10':{333:0,339:0.5,345:0.9,351:0.5,357:0.2,363:-0.5,369:-0.4,375:-0.5,381:0.1,387:0,393:0,399:0,405:0,411:0,417:0,423:0}
            }
UsPower = {
            '192.168.10.70':{10:48.5,16.4:49,22.8:48,29.2:47},
            '192.168.10.10':{10:48.5,16.4:49,22.8:48,29.2:47}
            }
SaveDB = True
#### defined stattion id & led status
stationList = ['192.168.10.10','192.168.10.70']

## Id_Status is applied to disable input-entry since start test(2d-dict[station][id])
Id_Status = defaultdict(dict)
for s in stationList:
    for n in range(1,9):
        Id_Status[s][n]=False

## Led_Check is showed status of Led before start test(3d-dict[station][id][status])
Led_Check = defaultdict(lambda: defaultdict(dict))

## currLed is keeped to update from interval(3d-dict[station][id][status]) which compare with Led_Check's status
currLed = defaultdict(lambda: defaultdict(dict))
for s in stationList:
    for n in range(1,9):
        for r in ['PASS','FAIL']:
            Led_Check[s][n][r]=0
            currLed[s][n][r]=0

#####################
'''

### Basic Setting ###
CMTS = '192.168.45.254'
MongoServer = '192.168.45.68'
mibs = {
        'DsQAM':    ['docsIfDownChannelPower'],
        'RxMER' :   ['docsIf3SignalQualityExtRxMER'],
        # 'OFDM':   ['docsIf31CmDsOfdmChannelPowerRxPower','docsPnmCmDsOfdmRxMerMean'],
        'UsQAM':    ['docsIf3CmStatusUsTxPower'],
        'UsSNR':    ['docsIf3CmtsCmUsStatusSignalNoise'],
        # 'OFDMA':  ['docsIf31CmtsCmUsOfdmaChannelMeanRxMer','docsIf31CmUsOfdmaChanTxPower']
        }
RxMER = 38
UsSNR = 40
DsPower = {
            '192.168.0.11':{603:0,609:0.5,615:0.9,621:0.5,627:0.2,633:-0.5,639:-0.4,645:-0.5},
            '192.168.0.15':{603:0,609:0.5,615:0.9,621:0.5,627:0.2,633:-0.5,639:-0.4,645:-0.5}
            }
UsPower = {
            '192.168.0.11':{35.2:48.5,37:49,38.8:48,40.6:47},
            '192.168.0.15':{35.2:48.5,37:49,38.8:48,40.6:47}
            }
SaveDB = False
#### defined stattion id & led status
stationList = ['192.168.0.15','192.168.0.11']

## Id_Status is applied to disable input-entry since start test(2d-dict[station][id])
Id_Status = defaultdict(dict)
for s in stationList:
    for n in range(1,9):
        Id_Status[s][n]=False

## Led_Check is showed status of Led before start test(3d-dict[station][id][status])
Led_Check = defaultdict(lambda: defaultdict(dict))

## currLed is keeped to update from interval(3d-dict[station][id][status]) which compare with Led_Check's status
currLed = defaultdict(lambda: defaultdict(dict))
for s in stationList:
    for n in range(1,9):
        for r in ['PASS','FAIL']:
            Led_Check[s][n][r]=0
            currLed[s][n][r]=0

#####################


def text_style(result):
    if result == 'PASS':
        style = {
            'color': '#008000'
        }
    else:
        style = {
            'color': '#f41111'
        }
    # style.update({'background': '#d8e8a9'})
    return style

def getKeysByValues(value):
    for i in mibs:
        if mibs[i][0] == value:
            return i

def generate_result(dsdata, usdata, order, init_result='N/A'):
    if dsdata.empty or usdata.empty:
        if init_result == 'FAIL':
            initStyle = {'color': '#f41111'}
        else:
            initStyle={'color': '#000000'}
        return html.Div([
        html.Table(
        # Header
        [html.Tr([html.Th(col) for col in order])] 
        ),
        html.H3(init_result,style=initStyle),
        html.Br()
        ])
    # create dic of test status for all test items
    retult_dic = {}
    for c in order:retult_dic[c] = 'PASS'
    dsPowerResult,dsRxMerResult = [],[]
    # confirm Ds signal
    for i in range(len(dsdata)):
        for col in order:
            if col == 'docsIf3CmStatusUsTxPower' or col == 'docsIf3CmtsCmUsStatusSignalNoise': continue
            if col == 'docsIf3SignalQualityExtRxMER':
                if dsdata.iloc[i][col] < RxMER:
                    retult_dic[col] = 'FAIL'
                    dsPowerResult.append('FAIL')
                else:
                    dsPowerResult.append('PASS')
            elif col == 'docsIfDownChannelPower':
                refDsFreq = int(dsdata.iloc[i]['docsIfDownChannelFrequency'])
                if abs(dsdata.iloc[i][col]-DsPower[request.remote_addr][refDsFreq/1000000]) > 2:
                    retult_dic[col] = 'FAIL'
                    dsRxMerResult.append('FAIL')
                else:
                    dsRxMerResult.append('PASS')
            else: continue
    usPowerResult,usSnrResult = [],[]
    # confirm Us signal
    for i in range(len(usdata)):
        for col in order:
            if col == 'docsIfDownChannelPower' or col == 'docsIf3SignalQualityExtRxMER': continue
            if col == 'docsIf3CmStatusUsTxPower':
                refUsFreq = int(usdata.iloc[i]['docsIfUpChannelFrequency'])
                if abs(usdata.iloc[i][col]-UsPower[request.remote_addr][refUsFreq/1000000]) > 2:
                    retult_dic[col] = 'FAIL'
                    usPowerResult.append('FAIL')
                else:
                    usPowerResult.append('PASS')
            elif col == 'docsIf3CmtsCmUsStatusSignalNoise':
                if usdata.iloc[i][col] < UsSNR:
                    retult_dic[col] = 'FAIL'
                    usSnrResult.append('FAIL')
                else:
                    usSnrResult.append('PASS')
    # with pd.option_context('display.max_rows', 20, 'display.max_columns', 10):
    #     print(usdata)
    #     print(dsdata)
    DsPwrJson = {"Time":datetime.datetime.fromtimestamp(time.time()),
                "ChannelId":list(dsdata['docsIfDownChannelId']),
                "ChannelIndex":list(dsdata['docsIfDownChannelIdx']),
                "Frequency":list(dsdata['docsIfDownChannelFrequency']),
                "ReportPwr":list(dsdata['docsIfDownChannelPower']),
                "MeasurePwr":[DsPower[request.remote_addr][float(x)/1000000] for x in sorted(dsdata['docsIfDownChannelFrequency'])],
                "ChResult":dsPowerResult,
                "Result":retult_dic['docsIfDownChannelPower']}
    DsRxMerJson = {"Time":datetime.datetime.fromtimestamp(time.time()),
                "ChannelId":list(dsdata['docsIfDownChannelId']),
                "Frequency":list(dsdata['docsIfDownChannelFrequency']),
                "RxMer":list(dsdata['docsIf3SignalQualityExtRxMER']),
                "Criteria":RxMER,
                "ChResult":dsRxMerResult,
                "Result":retult_dic['docsIf3SignalQualityExtRxMER']}
    UsPwrJson = {"Time":datetime.datetime.fromtimestamp(time.time()),
                "ChannelId":list(usdata['docsIfUpChannelId']),
                "ChannelIndex":list(usdata['docsIfUpChannelIdx']),
                "Frequency":list(usdata['docsIfUpChannelFrequency']),
                "ReportPwr":list(usdata['docsIf3CmStatusUsTxPower']),
                "MeasurePwr":[UsPower[request.remote_addr][float(x)/1000000] for x in sorted(usdata['docsIfUpChannelFrequency'])],
                "ChResult":usPowerResult,
                "Result":retult_dic['docsIf3CmStatusUsTxPower']}
    # UsSnrJson = {"Time":datetime.datetime.fromtimestamp(time.time()),
    #             "ChannelId":list(usdata['docsIfUpChannelId']),
    #             "ChannelIndex":list(usdata['docsIfUpChannelIdx']),
    #             "Frequency":list(usdata['docsIfUpChannelFrequency']),
    #             "UsSNR":list(usdata['docsIf3CmtsCmUsStatusSignalNoise']),
    #             "Criteria":UsSNR,
    #             "ChResult":usSnrResult,
    #             "Result":retult_dic['docsIf3CmtsCmUsStatusSignalNoise']}
    if 'FAIL' in [x for x in retult_dic.values()]:
        status = 'FAIL'
    else:
        status = 'PASS'
    return html.Div([
        html.Table(
        # Header
        [html.Tr([html.Th(children=getKeysByValues(col),style=text_style(retult_dic[col])) for col in order])] 
        ),
        html.H3(status,style=text_style(status)),
        html.Br(),
        ]), status, DsPwrJson, DsRxMerJson, UsPwrJson

def query_ds_snmp(wan, dsdicidx):
    items = ['docsIfDownChannelFrequency','docsIfDownChannelPower','docsIf3SignalQualityExtRxMER']
    chidx = [dsdicidx[k] for k in sorted(dsdicidx)]
    dic = {'docsIfDownChannelId' : sorted(dsdicidx), 'docsIfDownChannelIdx' : chidx}
    for oid_name in items:
        value_list = []
        data = Snmp.SnmpWalk(wan,snmp_oid(oid_name))
        for idx in sorted(dsdicidx):
            for v in data:
                snmp_idx = v.split(' ')[0].split('.')[-1]
                snmp_value = v.split(' ')[-1]
                if dsdicidx[idx] == snmp_idx:
                    if oid_name == 'docsIfDownChannelPower' or oid_name == 'docsIf3SignalQualityExtRxMER':
                        snmp_value = float(snmp_value)/10.0
                    value_list.append(snmp_value)
                    break
        dic.update({
            oid_name : value_list
        })
    return dic

def query_us_snmp(wan, usdicidx):
    chidx_ = [usdicidx[k] for k in sorted(usdicidx)]
    id_ = Snmp.SnmpWalk(wan,snmp_oid('docsIfUpChannelId'))
    id_idx = {}
    for idx in chidx_:
        for v in id_:
            snmp_idx = v.split(' ')[0].split('.')[-1]
            snmp_value = v.split(' ')[-1]
            if idx == snmp_idx: 
                id_idx[snmp_value] = idx
                break
    chid = [t[0] for t in sorted(id_idx.items())]
    chidx = [t[1] for t in sorted(id_idx.items())]
    chfreq = [list(usdicidx.keys())[list(usdicidx.values()).index(t)] for t in chidx]
    dic = {'docsIfUpChannelId' : chid, 'docsIfUpChannelIdx' : chidx, 'docsIfUpChannelFrequency' : chfreq}
    txPower = Snmp.SnmpWalk(wan,snmp_oid('docsIf3CmStatusUsTxPower'))
    chPList = []
    for idx in dic['docsIfUpChannelIdx']:
        for p in txPower:
            snmp_idx = p.split(' ')[0].split('.')[-1]
            snmp_value = p.split(' ')[-1]
            if idx == snmp_idx: 
                snmp_value = float(snmp_value)/10.0
                chPList.append(snmp_value)
    dic.update({'docsIf3CmStatusUsTxPower':chPList})
    cmtsIpDic = Snmp.SnmpWalk(CMTS,snmp_oid('docsIfCmtsCmStatusIpAddress'))
    for ip in cmtsIpDic:
        if wan == ip.split(' ')[-1]: 
            cmtsUsIpIdx = ip.split(' ')[0].split('.')[-1]
            break
    ''' ## JingHong 3.0 not support docsIf3CmtsCmUsStatusSignalNoise mibs
    cmtsUsSnrIdx,cmtsUsFreqIdx = {},{}
    # create dic, {Channel Index:cmtsUsSnr}
    for snr in Snmp.SnmpWalk(CMTS,snmp_oid('docsIf3CmtsCmUsStatusSignalNoise')+'.{}'.format(cmtsUsIpIdx)):
        snr_idx = snr.split(' ')[0].split('.')[-1]
        snr_value = snr.split(' ')[-1]
        cmtsUsSnrIdx[snr_idx] = float(snr_value)/10.0
    # create dic, {cmtsUsFreq:Channel Index}
    for f_idx in cmtsUsSnrIdx:
        freq = Snmp.SnmpGet(CMTS,snmp_oid('docsIfUpChannelFrequency'),f_idx)
        ch_idx = freq.split(' ')[0].split('.')[-1]
        ch_value = freq.split(' ')[-1]
        cmtsUsFreqIdx[ch_value] = f_idx
    print('--------------',cmtsUsSnrIdx)
    # find out channel SNR base on cmts and cm channel index
    cmtsUsSnrList = [cmtsUsSnrIdx[cmtsUsFreqIdx[x]] for x in dic['docsIfUpChannelFrequency']]
    dic.update({'docsIf3CmtsCmUsStatusSignalNoise':cmtsUsSnrList})
    '''
    return dic

def getUsId(wan):
    data = Snmp.SnmpWalk(wan,snmp_oid('docsIfUpChannelFrequency'))
    dic = {}
    for ch in data:
        index = ch.split(' ')[0].split('.')[-1]
        value = ch.split(' ')[-1]
        if int(value) == 0: continue
        dic[value] = index
    return dic

def getDsId(wan):
    data = Snmp.SnmpWalk(wan,snmp_oid('docsIfDownChannelId'))
    dic = {}
    for ch in data:
        index = ch.split(' ')[0].split('.')[-1]
        value = ch.split(' ')[-1]
        if int(value) > 32:continue
        print(index, value)
        dic[value] = index
    return dic

def initView(msg,items,color,status='N/A'):
    init = html.Div(style={'color': color}, children=(msg))
    DsInfo = pd.DataFrame()
    UsInfo = pd.DataFrame()
    return init, generate_result(DsInfo, UsInfo, items, status)
############################################### web view ################################################

app = dash.Dash()
app.title = 'AFI-Remote-Station'
app.layout = html.Div([
    # html.Div([
    dcc.Input(id='id-1', placeholder='Enter a Mac...', value='', type='text'),
    html.Div(id='output-data-1'),
    dcc.Input(id='id-2', placeholder='Enter a Mac...', value='', type='text'),
    html.Div(id='output-data-2'),
    dcc.Input(id='id-3', placeholder='Enter a Mac...', value='', type='text'),
    html.Div(id='output-data-3'),
    dcc.Input(id='id-4', placeholder='Enter a Mac...', value='', type='text'),
    html.Div(id='output-data-4'),
    dcc.Input(id='id-5', placeholder='Enter a Mac...', value='', type='text'),
    html.Div(id='output-data-5'),
    dcc.Input(id='id-6', placeholder='Enter a Mac...', value='', type='text'),
    html.Div(id='output-data-6'),
    dcc.Input(id='id-7', placeholder='Enter a Mac...', value='', type='text'),
    html.Div(id='output-data-7'),
    dcc.Input(id='id-8', placeholder='Enter a Mac...', value='', type='text'),
    html.Div(id='output-data-8'),
    dcc.Interval(id='input_interval', interval=2000),
    dcc.ConfirmDialog(id='led-alert-1',message='Check LED Light On ro Not?  ID-1',),
    dcc.ConfirmDialog(id='led-alert-2',message='Check LED Light On ro Not?  ID-2',),
    dcc.ConfirmDialog(id='led-alert-3',message='Check LED Light On ro Not?  ID-3',),
    dcc.ConfirmDialog(id='led-alert-4',message='Check LED Light On ro Not?  ID-4',),
    dcc.ConfirmDialog(id='led-alert-5',message='Check LED Light On ro Not?  ID-5',),
    dcc.ConfirmDialog(id='led-alert-6',message='Check LED Light On ro Not?  ID-6',),
    dcc.ConfirmDialog(id='led-alert-7',message='Check LED Light On ro Not?  ID-7',),
    dcc.ConfirmDialog(id='led-alert-8',message='Check LED Light On ro Not?  ID-8',),
],style={'columnCount': 2})

def generate_output_id(value):
    return 'output-data-{}'.format(value)

def generate_input_id(value):
    return 'id-{}'.format(value)

def display_status(id_):
    def output_callback(submit,cancel):
        global currLed
        # print('--------submit-{}:'.format(id_),submit)
        # print('--------cancel-{}:'.format(id_),cancel)
        if cancel==None: cancel = 0
        if submit==None: submit = 0
        currLed[request.remote_addr][id_]['PASS']=submit
        currLed[request.remote_addr][id_]['FAIL']=cancel
        return Id_Status[request.remote_addr][id_]
    return output_callback

def ckeckLed(id_):
    def output_callback(input_value,state):
        if len(input_value) == 12:
            time.sleep(0.1)
            return True
        return False
    return output_callback

def generate_output_callback(datasource_1_value):
    def output_callback(input_value):
        if len(input_value) == 12:
            # print('--------------',request.remote_addr)
            StationID = request.remote_addr+'-{}'.format(datasource_1_value)
            ## Create Log
            if not os.path.exists(os.getcwd()+'\\log\\'+str(datetime.date.today())):
                os.makedirs(os.getcwd()+'\\log\\'+str(datetime.date.today()))

            a = open(os.getcwd()+'\\log\\'+str(datetime.date.today())+'\\'+input_value+'_'+datetime.datetime.now().strftime("%H%M%S"),'w')
            log = 'Remote IP : '+StationID+'\n'
            log += 'MAC Address :' +input_value+'\n'
            global Id_Status, Led_Check
            Id_Status[request.remote_addr][datasource_1_value] = True
            testTimeStart = time.time()

            while True:
                # print('----------curr:' ,currLed)
                # print('----------after:' ,Led_Check)
                print('--------------',input_value)
                if currLed[request.remote_addr][datasource_1_value]['PASS'] != Led_Check[request.remote_addr][datasource_1_value]['PASS']:break
                if currLed[request.remote_addr][datasource_1_value]['FAIL'] != Led_Check[request.remote_addr][datasource_1_value]['FAIL']:break
                time.sleep(1)
            if currLed[request.remote_addr][datasource_1_value]['PASS'] > Led_Check[request.remote_addr][datasource_1_value]['PASS']:
                ledTest = 'PASS'
                Led_Check[request.remote_addr][datasource_1_value]['PASS'] += 1
                print('-------------PASS')
            else:
                ledTest = 'FAIL'
                Led_Check[request.remote_addr][datasource_1_value]['FAIL'] += 1
                print('-------------FAIL')
                Id_Status[request.remote_addr][datasource_1_value] = False
                log += 'Error : CHECK LED FAIL FAIL !!'
                a.write(log)
                a.close() 
                return initView('ID-{0} CHECK LED FAIL, MAC : {1}'.format(datasource_1_value,input_value),mibs.keys(),'#f70404', 'FAIL')
            try:
                wan = SnmpGetWanIp(CMTS,input_value)
            except:
                Id_Status[request.remote_addr][datasource_1_value] = False
                log += 'Error : Query IP from CMTS FAIL !!'
                a.write(log)
                a.close() 
                return initView('ID-{0} Query IP FAIL, MAC : {1}'.format(datasource_1_value,input_value),mibs.keys(),'#f70404', 'FAIL')
            queryWanStart = time.time()
            while True:
                if time.time()-queryWanStart > 10:
                    Id_Status[request.remote_addr][datasource_1_value] = False
                    log += 'Error : Query Cm Wan System & Check IP FAIL!!'
                    a.write(log)
                    a.close() 
                    return initView('ID-{0} Query Cm Wan System & Check IP FAIL!!, MAC : {1}'.format(datasource_1_value,input_value),mibs.keys(),'#f70404', 'FAIL')
                modemsys = str(Snmp.SnmpGet(wan,snmp_oid('sysDescr'),'0'))
                mac = str(Snmp.SnmpGet(wan,snmp_oid('ifPhysAddress'),'2'))[2:].upper()
                if mac == str(input_value) and 'No SNMP response' not in modemsys:break
                time.sleep(2)
            sysinfo = html.Div(style={'color': '#5031c6'}, children=('system : ' + modemsys))
            waninfo = html.Div(style={'color': '#5031c6'}, children=('Snmp Query(MAC : ' + mac + ', WAN : ' + wan +') '+
                str(datetime.datetime.fromtimestamp(time.time()))))
            dsStartTime = time.time()
            dsIdDic = getDsId(wan)
            dsInfo = pd.DataFrame(query_ds_snmp(wan, dsIdDic))
            dsTestTime = time.time()-dsStartTime
            usStartTime = time.time()
            usIdDic = getUsId(wan)
            usInfo = pd.DataFrame(query_us_snmp(wan, usIdDic))
            usTestTime = time.time()-usStartTime
            # testOrder = ['docsIfDownChannelId','docsIfDownChannelIdx']+queritems
            testOrder = ['docsIf3SignalQualityExtRxMER','docsIf3CmtsCmUsStatusSignalNoise','docsIf3CmStatusUsTxPower','docsIfDownChannelPower']
            testOrder = ['docsIf3SignalQualityExtRxMER','docsIf3CmStatusUsTxPower','docsIfDownChannelPower']
            responseHtml, testResult, DsPwrJson, DsRxMerJson, UsPwrJson = generate_result(dsInfo, usInfo, testOrder)
            DsPwrJson.update({"_id":input_value,"TestTime":dsTestTime,"Station-id":StationID})
            DsRxMerJson.update({"_id":input_value,"TestTime":dsTestTime,"Station-id":StationID})
            UsPwrJson.update({"_id":input_value,"TestTime":usTestTime,"Station-id":StationID})
            # UsSnrJson.update({"_id":input_value,"TestTime":usTestTime,"Station-id":StationID})
            allTestTime = time.time()-testTimeStart

            log += modemsys+'\n'
            log += 'Start Time : '+str(datetime.datetime.fromtimestamp(testTimeStart))+'\n'
            log += '===DsQAM===\n'+pd.DataFrame(DsPwrJson).to_string()+'\n'
            log += '===RxMER===\n'+pd.DataFrame(DsRxMerJson).to_string()+'\n'
            log += '===UsQAM===\n'+pd.DataFrame(UsPwrJson).to_string()+'\n'
            # log += '===UsSNR===\n'+pd.DataFrame(UsSnrJson).to_string()+'\n'
            log += 'Led Check : '+ledTest+'\n'
            log += 'Total Time : '+str(allTestTime)+'\n'
            log += 'Test Result : '+testResult
            bz2log = bz2.compress(log.encode('utf-8'))
            # print(bz2log)
            logJson = {"_id":input_value,"Time":datetime.datetime.fromtimestamp(time.time()),"log":bz2log,"Station-id":StationID}
            ledJson = {"_id":input_value,"Time":datetime.datetime.fromtimestamp(time.time()),"Result":ledTest,"Station-id":StationID}
            a.write(log)
            a.close
            s = bz2.decompress(bz2log)
            # print(str(s, encoding = 'utf-8'))
            if SaveDB:
                saveDB('AFI', 'DsQAM', DsPwrJson, MongoServer)
                saveDB('AFI', 'DsMER', DsRxMerJson, MongoServer)
                saveDB('AFI', 'UsQAM', UsPwrJson, MongoServer)
                # saveDB('AFI', 'UsSNR', UsSnrJson, MongoServer)
                saveDB('AFI', 'Log', logJson, MongoServer)
                saveDB('AFI', 'LED', ledJson, MongoServer)
            Id_Status[request.remote_addr][datasource_1_value] = False
            return waninfo, responseHtml
        elif len(input_value) > 12:
            return initView('Input Mac, ID-{} MAC ERROR'.format(datasource_1_value),mibs.keys(),'#f70404'')
        else:
            return initView('Input Mac, ID-{} Start Query Snmp!!'.format(datasource_1_value),mibs.keys(),'#5031c6')
    return output_callback

app.config.supress_callback_exceptions = True

def generate_led_id(value):
    return 'led-alert-{}'.format(value)

for value in range(1,9):
    app.callback(
        Output(generate_led_id(value), 'displayed'),
        [Input(generate_input_id(value), 'value')],
        [State(generate_led_id(value), 'cancel_n_clicks_timestamp')])(
        ckeckLed(value)
    )
    app.callback(
        Output(generate_input_id(value), 'disabled'),
        [],
        [State(generate_led_id(value), 'submit_n_clicks'),
        State(generate_led_id(value), 'cancel_n_clicks')],
        [Event('input_interval', 'interval')])(
        display_status(value)
    )
    app.callback(
        Output(generate_output_id(value), 'children'),
        [Input(generate_input_id(value), 'value')])(
        generate_output_callback(value)
    )
app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
# Loading screen CSS
# app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/brPBPO.css"})

if __name__ == '__main__':
    app.run_server(host='0.0.0.0')
