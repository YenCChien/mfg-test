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

CMTS = '192.168.45.254'


def parse_contents(data,order=None):
    if not order:
        order = data.columns
    return html.Div([
        html.H5('Downstream'),
        html.H6(datetime.datetime.fromtimestamp(time.time())),
        dt.DataTable(
            rows=data.to_dict('records'),
            editable=False, 
            sortable=True,
            resizable=False,
            columns=(order)
            ),
        html.Hr()
    ])

def text_style(valued, col):
    if col == 'docsIf3SignalQualityExtRxMER':
        style = {}
        value = float(valued)
        if value >= 40:
            style = {
                'color': '#008000'
            }
        else:
            style = {
                'color': '#f41111'
            }
    elif col == 'docsIfDownChannelPower':
        style = {}
        value = float(valued)
        if abs(value-0) < 2:
            style = {
                'color': '#008000'
            }
        else:
            style = {
                'color': '#f41111'
            }
    else: 
        style = {'color': '#000000'}
    style.update({'background': '#d8e8a9'})
    return style

def generate_table(dataframe, order, max_rows=10):
    return html.Div([
        html.H5('Downstream'),
        html.H6(datetime.datetime.fromtimestamp(time.time())),
        html.Table(
        # Header
        [html.Tr([html.Th(col) for col in order])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col], style=text_style(dataframe.iloc[i][col],col)) for col in order
        ]) for i in range(min(len(dataframe), max_rows))]
        ),
        html.Hr()
        ])

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
        html.H4('N/A',style={'color': '#000000'}),
        html.Br()
        ])
    retult_dic = {}
    for c in order:
        retult_dic[c] = 'N/A'
        if c == 'docsIf3SignalQualityExtRxMER': retult_dic[c] = 'PASS'
        if c == 'docsIfDownChannelPower': retult_dic[c] = 'PASS'

    x = [[dataframe.iloc[i][col] for col in order] for i in range(len(dataframe))]
    # for i in range(len(dataframe)):
    #     print(i)
    #     for col in order:
    #         print(dataframe[i][col])
    #         if col == 'docsIf3SignalQualityExtRxMER':
    #             if dataframe[i][col] < 40: retult_dic[col] = 'FAIL'
    #         elif col == 'docsIfDownChannelPower':
    #             if abs(dataframe[i][col]-0) > 2: retult_dic[col] = 'FAIL'
    #         else: continue

    return html.Div([
        html.Table(
        # Header
        [html.Tr([html.Th(col) for col in order])] 

        # Body
        # [html.Tr([
        #     html.Td('PASS') for col in order
        # ])]
        ),
        html.H4('PASS',style={'color': '#008000'}),
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

############################################### web view ################################################

app = dash.Dash()

app.layout = html.Div([
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
        mac = Snmp.SnmpGet(wan,snmp_oid('ifPhysAddress'),'2')
        sysinfo = html.Div(style={'color': '#5031c6'}, children=('system : ' + modemsys))
        waninfo = html.Div(style={'color': '#5031c6'}, children=('Snmp query(MAC : ' + str(mac)[2:].upper() + ', WAN : ' + wan +') '+
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
        mac = Snmp.SnmpGet(wan,snmp_oid('ifPhysAddress'),'2')
        sysinfo = html.Div(style={'color': '#5031c6'}, children=('System : ' + modemsys))
        waninfo = html.Div(style={'color': '#5031c6'}, children=('Snmp query(MAC : ' + str(mac)[2:].upper() + ', WAN : ' + wan +') '+
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

@app.callback(
    Output(component_id='output-data-3', component_property='children'),
    [Input(component_id='id-3', component_property='value')]
)

def update_output_3(input_value):
    if len(input_value) == 12:
        try:
            wan = SnmpGetWanIp(CMTS,input_value)
        except:
            return html.Div(style={'color': '#f70404'}, children=('Get IP Error!!'))
        modemsys = str(Snmp.SnmpGet(wan,snmp_oid('sysDescr'),'0'))
        mac = Snmp.SnmpGet(wan,snmp_oid('ifPhysAddress'),'2')
        sysinfo = html.Div(style={'color': '#5031c6'}, children=('system : ' + modemsys))
        waninfo = html.Div(style={'color': '#5031c6'}, children=('Snmp query(MAC : ' + str(mac)[2:].upper() + ', WAN : ' + wan +') '+
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


@app.callback(
    Output(component_id='output-data-4', component_property='children'),
    [Input(component_id='id-4', component_property='value')]
)

def update_output_4(input_value):
    if len(input_value) == 12:
        try:
            wan = SnmpGetWanIp(CMTS,input_value)
        except:
            return html.Div(style={'color': '#f70404'}, children=('Get IP Error!!'))
        modemsys = str(Snmp.SnmpGet(wan,snmp_oid('sysDescr'),'0'))
        mac = Snmp.SnmpGet(wan,snmp_oid('ifPhysAddress'),'2')
        sysinfo = html.Div(style={'color': '#5031c6'}, children=('system : ' + modemsys))
        waninfo = html.Div(style={'color': '#5031c6'}, children=('Snmp query(MAC : ' + str(mac)[2:].upper() + ', WAN : ' + wan +') '+
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

@app.callback(
    Output(component_id='output-data-5', component_property='children'),
    [Input(component_id='id-5', component_property='value')]
)

def update_output_5(input_value):
    if len(input_value) == 12:
        try:
            wan = SnmpGetWanIp(CMTS,input_value)
        except:
            return html.Div(style={'color': '#f70404'}, children=('Get IP Error!!'))
        modemsys = str(Snmp.SnmpGet(wan,snmp_oid('sysDescr'),'0'))
        mac = Snmp.SnmpGet(wan,snmp_oid('ifPhysAddress'),'2')
        sysinfo = html.Div(style={'color': '#5031c6'}, children=('system : ' + modemsys))
        waninfo = html.Div(style={'color': '#5031c6'}, children=('Snmp query(MAC : ' + str(mac)[2:].upper() + ', WAN : ' + wan +') '+
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

@app.callback(
    Output(component_id='output-data-6', component_property='children'),
    [Input(component_id='id-6', component_property='value')]
)

def update_output_6(input_value):
    if len(input_value) == 12:
        try:
            wan = SnmpGetWanIp(CMTS,input_value)
        except:
            return html.Div(style={'color': '#f70404'}, children=('Get IP Error!!'))
        modemsys = str(Snmp.SnmpGet(wan,snmp_oid('sysDescr'),'0'))
        mac = Snmp.SnmpGet(wan,snmp_oid('ifPhysAddress'),'2')
        sysinfo = html.Div(style={'color': '#5031c6'}, children=('system : ' + modemsys))
        waninfo = html.Div(style={'color': '#5031c6'}, children=('Snmp query(MAC : ' + str(mac)[2:].upper() + ', WAN : ' + wan +') '+
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

@app.callback(
    Output(component_id='output-data-7', component_property='children'),
    [Input(component_id='id-7', component_property='value')]
)

def update_output_7(input_value):
    if len(input_value) == 12:
        try:
            wan = SnmpGetWanIp(CMTS,input_value)
        except:
            return html.Div(style={'color': '#f70404'}, children=('Get IP Error!!'))
        modemsys = str(Snmp.SnmpGet(wan,snmp_oid('sysDescr'),'0'))
        mac = Snmp.SnmpGet(wan,snmp_oid('ifPhysAddress'),'2')
        sysinfo = html.Div(style={'color': '#5031c6'}, children=('system : ' + modemsys))
        waninfo = html.Div(style={'color': '#5031c6'}, children=('Snmp query(MAC : ' + str(mac)[2:].upper() + ', WAN : ' + wan +') '+
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

@app.callback(
    Output(component_id='output-data-8', component_property='children'),
    [Input(component_id='id-8', component_property='value')]
)

def update_output_8(input_value):
    if len(input_value) == 12:
        try:
            wan = SnmpGetWanIp(CMTS,input_value)
        except:
            return html.Div(style={'color': '#f70404'}, children=('Get IP Error!!'))
        modemsys = str(Snmp.SnmpGet(wan,snmp_oid('sysDescr'),'0'))
        mac = Snmp.SnmpGet(wan,snmp_oid('ifPhysAddress'),'2')
        sysinfo = html.Div(style={'color': '#5031c6'}, children=('system : ' + modemsys))
        waninfo = html.Div(style={'color': '#5031c6'}, children=('Snmp query(MAC : ' + str(mac)[2:].upper() + ', WAN : ' + wan +') '+
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