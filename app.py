from pymongo import MongoClient
from bson.objectid import ObjectId
from flask import Flask,render_template,jsonify,json,request
import pandas as pd
from bs4 import BeautifulSoup

# from fabric.api import *

application = Flask(__name__)

client = MongoClient('mongodb://drunk:27017/')
db = client.arthur_sacred

def doc_to_dict(document):
    dic_doc = {}
    ### ID
    dic_doc["id"] = document['_id']
    #### STATUS
    status = document['status']
    dic_doc['status'] = status

    #### START TIME
    #     print(document['start_time'])
    dic_doc['start_time'] = document['start_time']
    if status != 'RUNNING':
        #         print(document['stop_time'])
        dic_doc['stop_time'] = document['stop_time']

    ###
    experiment = document['experiment']
    #     print(experiment['name'])
    #     print(experiment['mainfile'])
    dic_doc['name'] = experiment['name']
    dic_doc['mainfile'] = experiment['mainfile']

    ####
    config = document['config']
    dic_config = config_to_dict(config)
    dic_doc = dict(dic_doc, **dic_config)
    ###
    dic_doc['result'] = document['result']

    # ###
    # try:
    #     info = document['info']
    #     #         print(info)
    #     #         print(info['tensorflow']['logdirs'])
    #     dic_doc['tensorboard_file'] = info['tensorflow']['logdirs']
    # except:
    #     dic_doc['tensorboard_file'] = None
    #     pass

    return dic_doc

def config_to_dict(config, skip=[]):
    retour = {}
    for key, value in config.items():
        if isinstance(value, dict):
            for key_2, value_2 in value.items():
                retour["config."+key+"."+key_2]= value_2
        else:
            retour[key] = value
    return retour

def cursor_to_pandas(cursor):
    list_dict = []
    for document in cursor:
        list_dict.append(doc_to_dict(document))
    return pd.DataFrame(list_dict)


@application.route('/')
def showMachineList():
    return render_template('list.html')

def get_button(df):
    cols = df.columns.tolist()
    list_button = ""
    for i,c in enumerate(cols):
        list_button+= "<a class=\"toggle-vis\" data-column=\"{}\">{}</a> - ".format(i+1,c)
    return list_button

def add_footer(df):
    cols = df.columns
    footer ="""
    <tfoot>
    <tr>
   
    """
    end_footer = """
    </tr>
    </tfoot>

    """
    # print(c)
    for c in cols.get_level_values(2):
        print(c)
        footer +=" <th> {} </th> ".format(c)
    footer+= end_footer
    return footer




@application.route("/getExpeList",methods=['POST'])
def getExpeList():
    try:
        runs = db.runs.find()
        df = cursor_to_pandas(runs)
        df = df.set_index('id')
        cols = df.columns.tolist()
        cols = sorted(cols)
        cols_dic = {cols[i]: i for i in range(len(cols))}


        cols = [cols[cols_dic['name']] , cols[cols_dic['status']] , cols[cols_dic['result']],  cols[cols_dic['start_time']],  cols[cols_dic['stop_time']]] + [cols[cols_dic[i]] for i in cols_dic.keys() if i not in ['name', 'status', 'result', 'start_time', 'stop_time']]

        df = df[cols]

        list_button = get_button(df)


        col_tuple = []

        for nc in cols:
            nc = nc.split('.')
            if len(nc) == 1:
                nc = ("info","info", nc[0])
            col_tuple.append(nc)
        multi_cols = pd.MultiIndex.from_tuples(col_tuple, names=['Experiment', 'Config', 'Under Config'])

        df.columns = multi_cols

        footer = add_footer(df)



        pd_html = df.to_html(justify='left')

        # print(pd_html)
        soup = BeautifulSoup(pd_html, 'html.parser')
        table = soup.find('table')
        table["class"] = "display compact nowrap"
        table["style"] ="width:100%"
        table["border"] = 0
        table["id"] = "example"

        # print(soup.prettify()[:-9])
        print(list_button+"\n"+soup.prettify()[:-9]+"\n"+footer + "</table>")
        return list_button+"\n"+soup.prettify()[:-9]+"\n"+footer + "</table>"

        runsList = []
        for run in runs:
            run_item = doc_to_dict(run)
            print(run_item)
            runsList.append(run_item)
    except Exception as e:
        print(str(e))
        return str(e)
    return json.dumps(runsList)




if __name__ == "__main__":
    application.run(host='0.0.0.0')



