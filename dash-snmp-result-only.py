import datetime
import time
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
from dash.dependencies import Input, Output
import Snmp
from snmplib import *
import pandas as pd


### Baisc Setting ###
CMTS = '192.168.45.254'
items = {
        'DsQAM':    'docsIfDownChannelPower',
        'RxMER' :   'docsIf3SignalQualityExtRxMER',
        # 'OFDM':     ['docsIf31CmDsOfdmChannelPowerRxPower','docsPnmCmDsOfdmRxMerMean'],
        # 'UsQAM':    ['docsIf3CmStatusUsTxPower'],
        # 'UsSNR':    ['docsIf3CmtsCmUsStatusSignalNoise'],
        # 'OFDMA':    ['docsIf31CmtsCmUsOfdmaChannelMeanRxMer','docsIf31CmUsOfdmaChanTxPower']
        }
RxMER = 40
UsSNR = 40
DsPower = {1:-1.2,2:-9,3:-5,4:-5,5:-1,6:-1.7,7:-1.5,8:-1.7}
UsPower = {1:30,2:30,3:30,4:30}
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

def generate_result(dataframe, order, max_rows=10):
    if dataframe.empty:
        return html.Div([
        html.Table(
        # Header
        [html.Tr([html.Th(col) for col in order])] 
        # Body
        # [html.Tr([
        #     html.Td('PASS') for col in order
        # ])]
        ),
        html.H3('N/A',style={'color': '#000000'}),
        html.Br()
        ])
    ## create dic of test status for all test items
    retult_dic = {}
    for c in order:
        retult_dic[c] = 'N/A'
        if c == items['RxMER'] : retult_dic[c] = 'PASS'
        if c == items['DsQAM'] : retult_dic[c] = 'PASS'
    for i in range(len(dataframe)):
        print(i)
        for col in order:
            print(dataframe.iloc[i][col])
            if col == items['RxMER']:
                if dataframe.iloc[i][col] < 40: retult_dic[col] = 'FAIL'
            elif col == items['DsQAM']:
                if abs(dataframe.iloc[i][col]-0) > 2: retult_dic[col] = 'FAIL'
            else: continue
    return html.Div([
        html.Table(
        # Header
        [html.Tr([html.Th(col,style=text_style(retult_dic[col])) for col in order])] 
        # Body
        # [html.Tr([
        #     html.Td('PASS') for col in order
        # ])]
        ),
        html.H3(retult_dic[col],style=text_style(retult_dic[col])),
        html.Br()
        ])

def query_ds_snmp(wan, dsdicidx, items):
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
    return init, generate_result(DsInfo, items)
############################################### web view ################################################

app = dash.Dash()

app.layout = html.Div([
    dcc.Input(id='id-1', placeholder='Enter a Mac...', value='', type='text'),
    html.Div(id='output-data-1'),
    dcc.Input(id='id-2', placeholder='Enter a Mac...', value='', type='text'),
    html.Div(id='output-data-2'),
    # html.Div(dt.DataTable(rows=[{}]), style={'display': 'none'})
],style={'columnCount': 2})

groups = ["Movies", "Sports", "Coding", "Fishing", "Dancing", "cooking"]  
num = [46, 8, 12, 12, 6, 58]
dict = {"groups": groups,  
        "num": num
       }
df = pd.DataFrame(dict)

# df = pd.read_csv(
#     'https://gist.githubusercontent.com/chriddyp/'
#     'c78bf172206ce24f77d6363a2d754b59/raw/'
#     'c353e8ef842413cae56ae3920b8fd78468aa4cb2/'
#     'usa-agricultural-exports-2011.csv')

@app.callback(
    Output(component_id='output-data-1', component_property='children'),
    [Input(component_id='id-1', component_property='value')]
)

def update_output_1(input_value):
    if len(input_value) == 12:
        try:
            wan = SnmpGetWanIp(CMTS,input_value)
        except:
            return html.Div(style={'color': '#f70404'}, children=('Get IP Error!!'))
        modemsys = str(Snmp.SnmpGet(wan,snmp_oid('sysDescr'),'0'))
        mac = str(Snmp.SnmpGet(wan,snmp_oid('ifPhysAddress'),'2'))[2:].upper()
        if mac != str(input_value):
            return initView('MAC Error: Input( {0} ) != Snmp( {1} )'.format(input_value,mac), items.keys(),'#f70404')
        sysinfo = html.Div(style={'color': '#5031c6'}, children=('system : ' + modemsys))
        waninfo = html.Div(style={'color': '#5031c6'}, children=('Snmp query(MAC : ' + mac + ', WAN : ' + wan +') '+
            str(datetime.datetime.fromtimestamp(time.time()))))
        try:
            dsIdDic = getDsId(wan)
        except Exception as err:
            return html.Div(style={'color': '#f70404'}, children=(err))
        queritems = ['docsIfDownChannelFrequency','docsIfDownChannelPower','docsIf3SignalQualityExtRxMER']
        DsInfo = pd.DataFrame(query_ds_snmp(wan, dsIdDic, queritems))
        # DsOrder = ['docsIfDownChannelId','docsIfDownChannelIdx']+queritems
        print(DsInfo)
        if 'No SNMP response' in modemsys:
            return waninfo, sysinfo
        return waninfo, generate_result(DsInfo, items.keys())
    elif len(input_value) == 0:
        return initView('Input Mac, Start Query Snmp!!',items.keys(),'#5031c6')
    else:
        # Mac Error view
        return initView('Mac Error', items.values(),'#f70404')

@app.callback(
    Output(component_id='output-data-2', component_property='children'),
    [Input(component_id='id-2', component_property='value')]
)

def update_output_2(input_value):
    if len(input_value) == 12:
        try:
            wan = SnmpGetWanIp(CMTS,input_value)
        except:
            return html.Div(style={'color': '#f70404'}, children=('Get IP Error!!'))
        modemsys = str(Snmp.SnmpGet(wan,snmp_oid('sysDescr'),'0'))
        mac = str(Snmp.SnmpGet(wan,snmp_oid('ifPhysAddress'),'2'))[2:].upper()
        sysinfo = html.Div(style={'color': '#5031c6'}, children=('System : ' + modemsys))
        waninfo = html.Div(style={'color': '#5031c6'}, children=('Snmp query(MAC : ' + mac + ', WAN : ' + wan +') '+
            str(datetime.datetime.fromtimestamp(time.time()))))
        try:
            dsIdDic = getDsId(wan)
        except Exception as err:
            return html.Div(style={'color': '#f70404'}, children=(err))
        queritems = ['docsIfDownChannelFrequency','docsIfDownChannelPower','docsIf3SignalQualityExtRxMER']
        DsInfo = pd.DataFrame(query_ds_snmp(wan, dsIdDic, queritems))
        # DsOrder = ['docsIfDownChannelId','docsIfDownChannelIdx']+queritems
        DsOrder = queritems
        print(DsInfo)
        if 'No SNMP response' in modemsys:
            return waninfo, sysinfo
        return waninfo, generate_result(DsInfo, DsOrder)
    elif len(input_value) == 0:
        # Inital view
        init = html.Div(style={'color': '#5031c6'}, children=('Input Mac, Start Query Snmp!!'))
        DsInfo = pd.DataFrame()
        DsOrder = ['docsIfDownChannelFrequency','docsIfDownChannelPower','docsIf3SignalQualityExtRxMER']
        return init, generate_result(DsInfo, DsOrder)
    else:
        # Mac Error view
        err = html.Div(style={'color': '#f70404'}, children=('Mac Error'))
        DsInfo = pd.DataFrame()
        DsOrder = ['docsIfDownChannelFrequency','docsIfDownChannelPower','docsIf3SignalQualityExtRxMER']
        return err, generate_result(DsInfo, DsOrder)

app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
# Loading screen CSS
# app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/brPBPO.css"})

if __name__ == '__main__':
    app.run_server(debug=True,host='0.0.0.0')