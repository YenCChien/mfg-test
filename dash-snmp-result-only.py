import datetime
import time
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
from dash.dependencies import Input, Output
from flask import request
import Snmp
from snmplib import *
import pandas as pd


### Basic Setting ###
CMTS = '192.168.45.254'
MongoServer = '192.168.12.90'
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
DsPower = {603:0,609:0.5,615:0.9,621:0.5,627:0.2,633:-0.5,639:-0.4,645:-0.5}
UsPower = {35.2:48.5,37:49,38.8:48,40.6:47}
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
    
def generate_result(dsdata, usdata, order, max_rows=10):
    if dsdata.empty or usdata.empty:
        return html.Div([
        html.Table(
        # Header
        [html.Tr([html.Th(col) for col in order])] 
        ),
        html.H3('N/A',style={'color': '#000000'}),
        html.Br()
        ])
    # create dic of test status for all test items
    retult_dic = {}
    for c in order:retult_dic[c] = 'PASS'
    # confirm Ds signal 
    for i in range(len(dsdata)):
        # print(i)
        for col in order:
            ## Debug
            if col == 'docsIf3CmStatusUsTxPower' or col == 'docsIf3CmtsCmUsStatusSignalNoise': continue
            print(dsdata.iloc[i][col])
            if col == 'docsIf3SignalQualityExtRxMER':
                if dsdata.iloc[i][col] < RxMER: retult_dic[col] = 'FAIL'
            elif col == 'docsIfDownChannelPower':
                refDsFreq = int(dsdata.iloc[i]['docsIfDownChannelFrequency'])
                # print(dataframe.iloc[i][col])
                if abs(dsdata.iloc[i][col]-DsPower[refDsFreq/1000000]) > 2: retult_dic[col] = 'FAIL'
            else: continue
    # print(retult_dic)
    # with pd.option_context('display.max_rows', 20, 'display.max_columns', 10):
    #     print(usdata)
    # confirm Us signal
    for i in range(len(usdata)):
        for col in order:
            if col == 'docsIfDownChannelPower' or col == 'docsIf3SignalQualityExtRxMER': continue
            if col == 'docsIf3CmStatusUsTxPower':
                refUsFreq = int(usdata.iloc[i]['docsIfUpChannelFrequency'])
                if abs(usdata.iloc[i][col]-UsPower[refUsFreq/1000000]) > 2: retult_dic[col] = 'FAIL'
            elif col == 'docsIf3CmtsCmUsStatusSignalNoise':
                if usdata.iloc[i][col] < UsSNR: retult_dic[col] = 'FAIL'
    if 'FAIL' in [x for x in retult_dic.values()]:
        status = 'FAIL'
    else:
        status = 'PASS'
    return html.Div([
        html.Table(
        # Header
        [html.Tr([html.Th(children=getKeysByValues(col),style=text_style(retult_dic[col])) for col in order])] 
        # Body
        # [html.Tr([
        #     html.Td('PASS') for col in order
        # ])]
        ),
        html.H3(status,style=text_style(status)),
        html.Br()
        ])

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
    dic = {'docsIfDownChannelId' : chid, 'docsIfDownChannelIdx' : chidx, 'docsIfUpChannelFrequency' : chfreq}
    txPower = Snmp.SnmpWalk(wan,snmp_oid('docsIf3CmStatusUsTxPower'))
    chPList = []
    for idx in dic['docsIfDownChannelIdx']:
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
    # find out channel SNR base on cmts and cm channel index
    cmtsUsSnrList = [cmtsUsSnrIdx[cmtsUsFreqIdx[x]] for x in dic['docsIfUpChannelFrequency']]
    dic.update({'docsIf3CmtsCmUsStatusSignalNoise':cmtsUsSnrList})
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

def initView(msg,items,color):
    init = html.Div(style={'color': color}, children=(msg))
    DsInfo = pd.DataFrame()
    UsInfo = pd.DataFrame()
    return init, generate_result(DsInfo, UsInfo, items)
############################################### web view ################################################

app = dash.Dash()

app.layout = html.Div([
    dcc.Input(id='id-1', placeholder='Enter a Mac...', value='', type='text'),
    html.Div(id='output-data-1'),
    dcc.Input(id='id-2', placeholder='Enter a Mac...', value='', type='text'),
    html.Div(id='output-data-2'),
    # html.Div(dt.DataTable(rows=[{}]), style={'display': 'none'})
],style={'columnCount': 2})

# groups = ["Movies", "Sports", "Coding", "Fishing", "Dancing", "cooking"]  
# num = [46, 8, 12, 12, 6, 58]
# dict = {"groups": groups,  
#         "num": num
#        }
# df = pd.DataFrame(dict)

def generate_output_id(value):
    return 'output-data-{}'.format(value)

def generate_input_id(value):
    return 'id-{}'.format(value)

def generate_output_callback(datasource_1_value):
    def output_callback(input_value):
        if len(input_value) == 12:
            # print('--------------',request.remote_addr)
            try:
                wan = SnmpGetWanIp(CMTS,input_value)
            except:
                return initView('Query IP Fail !!',mibs.keys(),'#f70404')
            modemsys = str(Snmp.SnmpGet(wan,snmp_oid('sysDescr'),'0'))
            mac = str(Snmp.SnmpGet(wan,snmp_oid('ifPhysAddress'),'2'))[2:].upper()
            if mac != str(input_value):
                return initView('MAC Error: Input( {0} ) != Snmp( {1} )'.format(input_value,mac), mibs.keys(),'#f70404')
            sysinfo = html.Div(style={'color': '#5031c6'}, children=('system : ' + modemsys))
            waninfo = html.Div(style={'color': '#5031c6'}, children=('Snmp Query(MAC : ' + mac + ', WAN : ' + wan +') '+
                str(datetime.datetime.fromtimestamp(time.time()))))
            dsIdDic = getDsId(wan)
            usIdDic = getUsId(wan)
            dsInfo = pd.DataFrame(query_ds_snmp(wan, dsIdDic))
            usInfo = pd.DataFrame(query_us_snmp(wan, usIdDic))
            # testOrder = ['docsIfDownChannelId','docsIfDownChannelIdx']+queritems
            testOrder = ['docsIf3SignalQualityExtRxMER','docsIf3CmtsCmUsStatusSignalNoise','docsIf3CmStatusUsTxPower','docsIfDownChannelPower']
            print(usInfo)
            if 'No SNMP response' in modemsys:
                return initView(waninfo+sysinfo,mibs.keys(),'#f70404')
            return waninfo, generate_result(dsInfo, usInfo, testOrder)
        elif len(input_value) == 0:
            return initView('Input Mac, Start Query Snmp!!',mibs.keys(),'#5031c6')
        else:
            # Mac Error view
            return initView('Mac Error', mibs.keys(),'#f70404')
    return output_callback

app.config.supress_callback_exceptions = True

for value in range(1,3):
    app.callback(
        Output(generate_output_id(value), 'children'),
        [Input(generate_input_id(value), 'value')])(
        generate_output_callback(value)
    )
    

# @app.callback(
#     Output(component_id='output-data-1', component_property='children'),
#     [Input(component_id='id-1', component_property='value')]
# )

# def update_output(input_value):
#     if len(input_value) == 12:
#         try:
#             wan = SnmpGetWanIp(CMTS,input_value)
#         except:
#             return initView('Query IP Fail !!',mibs.keys(),'#f70404')
#         modemsys = str(Snmp.SnmpGet(wan,snmp_oid('sysDescr'),'0'))
#         mac = str(Snmp.SnmpGet(wan,snmp_oid('ifPhysAddress'),'2'))[2:].upper()
#         if mac != str(input_value):
#             return initView('MAC Error: Input( {0} ) != Snmp( {1} )'.format(input_value,mac), mibs.keys(),'#f70404')
#         sysinfo = html.Div(style={'color': '#5031c6'}, children=('system : ' + modemsys))
#         waninfo = html.Div(style={'color': '#5031c6'}, children=('Snmp Query(MAC : ' + mac + ', WAN : ' + wan +') '+
#             str(datetime.datetime.fromtimestamp(time.time()))))
#         dsIdDic = getDsId(wan)
#         usIdDic = getUsId(wan)
#         queritems = ['docsIfDownChannelFrequency','docsIfDownChannelPower','docsIf3SignalQualityExtRxMER']
#         dsInfo = pd.DataFrame(query_ds_snmp(wan, dsIdDic, queritems))
#         # testOrder = ['docsIfDownChannelId','docsIfDownChannelIdx']+queritems
#         testOrder = ['docsIf3SignalQualityExtRxMER','docsIf3CmtsCmUsStatusSignalNoise','docsIf3CmStatusUsTxPower','docsIfDownChannelPower']
#         print(dsInfo)
#         if 'No SNMP response' in modemsys:
#             return initView(waninfo+sysinfo,mibs.keys(),'#f70404')
#         return waninfo, generate_result(dsInfo, testOrder)
#     elif len(input_value) == 0:
#         return initView('Input Mac, Start Query Snmp!!',mibs.keys(),'#5031c6')
#     else:
#         # Mac Error view
#         return initView('Mac Error', mibs.keys(),'#f70404')

app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
# Loading screen CSS
# app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/brPBPO.css"})

if __name__ == '__main__':
    app.run_server(debug=True,host='0.0.0.0')
