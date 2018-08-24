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
        if value >= 400:
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
    )])

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

app = dash.Dash()

app.layout = html.Div([
    dcc.Input(id='my-id', placeholder='Enter a Mac...', value='', type='text'),
    html.Div(id='output-data-upload'),
    html.Div(dt.DataTable(rows=[{}]), style={'display': 'none'})
])

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
    Output(component_id='output-data-upload', component_property='children'),
    [Input(component_id='my-id', component_property='value')]
)

def update_output_div(input_value):
    if len(input_value) == 12:
        try:
            wan = SnmpGetWanIp(CMTS,input_value)
        except:
            return html.Div(style={'color': '#f70404'}, children=('Get IP Error!!'))
        modemsys = str(Snmp.SnmpGet(wan,snmp_oid('sysDescr'),'0'))
        sysinfo = html.Div(style={'color': '#5031c6'}, children=(modemsys))
        waninfo = html.Div(style={'color': '#5031c6'}, children=('WAN : ' + wan))
        dsIdDic = getDsId(wan)
        queritems = ['docsIfDownChannelFrequency','docsIfDownChannelPower','docsIf3SignalQualityExtRxMER']
        DsInfo = pd.DataFrame(query_ds_snmp(wan, dsIdDic, queritems))
        DsOrder = ['docsIfDownChannelId','docsIfDownChannelIdx']+queritems
        print(DsInfo) 
        if 'No SNMP response' in modemsys:
            return waninfo, sysinfo
        return waninfo, sysinfo, generate_table(DsInfo, DsOrder)
    elif len(input_value) == 0:
        return html.Div(style={'color': '#5031c6'}, children=('Input Mac, Start Query Snmp!!'))
    else:
        return html.Div(style={'color': '#f70404'}, children=('Mac Error'))

app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
# Loading screen CSS
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/brPBPO.css"})

if __name__ == '__main__':
    app.run_server(debug=True,host='0.0.0.0')