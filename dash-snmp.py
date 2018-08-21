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

def parse_contents(data):
    return html.Div([
        html.H5('file name'),
        html.H6(datetime.datetime.fromtimestamp(time.time())),
        dt.DataTable(rows=data.to_dict('records'),editable=False),
        html.Hr()
    ])

def query_snmp(wan, items):
    dic = {}
    for oid_name in items:
        data = Snmp.SnmpWalk(wan,snmp_oid(oid_name))
        oid_list,index_list,value_list,name_list = [],[],[],[]
        for ch in data:
            oid = ch.split(' ')[0]
            index = ch.split(' ')[0].split('.')[-1]
            value = ch.split(' ')[-1]
            name = oid_name+'.{}'.format(index)
            # dic.update({oid_name+'.{}'.format(index):[oid,index,value]})
            oid_list.append(oid); index_list.append(index), value_list.append(value), name_list.append(name)
        dic.update({
            "*CHANNEL" : list(range(len(index_list))),
            "*INDEX" : index_list,
            oid_name : value_list
        })
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
            return 'Get IP Error!!'
        modemsys = str(Snmp.SnmpGet(wan,snmp_oid('sysDescr'),'0'))
        sysinfo = html.Div(style={'color': '#5031c6'}, children=(modemsys))
        waninfo = html.Div(style={'color': '#5031c6'}, children=('WAN : ' + wan))
        groups = ["Name","OID",'Index','Value']
        queritems = ['docsIfDownChannelFrequency','docsIfDownChannelPower']
        freq = pd.DataFrame(query_snmp(wan,queritems))
        print(freq)
        if 'No SNMP response' in modemsys:
            return waninfo, sysinfo
        return waninfo, sysinfo, parse_contents(freq), parse_contents(df)
    elif len(input_value) == 0:
        return html.Div(style={'color': '#5031c6'}, children=('Input Mac, Start Query Snmp!!'))
    else:
        return html.Div(style={'color': '#f70404'}, children=('Mac Error'))

app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
# Loading screen CSS
app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/brPBPO.css"})

if __name__ == '__main__':
    app.run_server(debug=True,host='0.0.0.0')