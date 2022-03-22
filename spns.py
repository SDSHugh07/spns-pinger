#!/usr/bin/python

import json 
import argparse


from spns_abstraction_layer import evaluate_system_disk, evaluate_system_memory, evaluate_system_health

PLUGIN_VERSION = 1  ###Mandatory -If any changes in the plugin metrics, increment the version number.
HEARTBEAT = "true"  ###Mandatory -Set this to true to receive alerts when there is no data from the plugin within the poll interval
METRIC_UNITS = {"Disk":"%","Memory":"%","HEALTH": "%"} ###OPTIONAL - The unit defined here will be displayed in the Dashboard.

class Plugin():
    def __init__(self):
        self.data = {}
        self.data["plugin_version"] = PLUGIN_VERSION
        self.data["heartbeat_required"] = HEARTBEAT
        self.data["units"] = METRIC_UNITS   ###Comment this line, if you haven't defined METRIC_UNITS
        self.data["HEALTH"] = 0

    def getData(self):  ### The getData method contains Sample data. User can enhance the code to fetch Original data
        try: ##set the data object based on the requirement
            self.data["Name"] = "SPNS Pinger - site24x7"

            self.data["Disk"] = evaluate_system_disk()
            self.data["Memory"] = evaluate_system_memory()
            self.data["HEALTH"], self.data["spns_errors"] = evaluate_system_health()

        except Exception as e:
            self.data['status'] = 0    ###OPTIONAL-In case of any errors,Set 'status'=0 to mark the plugin as down.
      
            self.data['msg'] = str(e)  ###OPTIONAL- Set the custom message to be displayed in the "Errors" field of Log Report
        return self.data

##validation method - This is only for Output validation purpose
def validatePluginData(result):
     obj,mandatory ={'Errors':""},['heartbeat_required','plugin_version']

     value={'heartbeat_required':["true","false",True,False],'status':[0,1]}

     for field in mandatory:
        if field not in result:
            obj['Errors']=obj['Errors']+"# Mandatory field "+field+" is missing #"

     for field,val in value.items():
        if field in result and result[field] not in val:
            obj['Errors']=obj['Errors']+"# "+field+" can only be "+str(val)

     if 'plugin_version' in result and not isinstance(result['plugin_version'],int):
        obj['Errors']=obj['Errors']+"# Mandatory field plugin_version should be an integer #"

     RESERVED_KEYS='plugin_version|heartbeat_required|status|units|msg|onchange|display_name|AllAttributeChart'

     attributes_List=[]

     for key,value in result.items():
         if key not in RESERVED_KEYS:
            attributes_List.append(key)

     if len(attributes_List) == 0:
        obj['Errors'] = obj['Errors']# There should be at least one \"Number\" type data metric present #"

     if obj['Errors'] != "":
        obj['Result'] = "**************Plugin output is not valid************"
     else:
        obj['Result'] = "**************Plugin output is valid**************"
        del obj['Errors']

     result['validation output'] = obj
      
if __name__ == '__main__':
    plugin = Plugin()

    data = plugin.getData()
    parser = argparse.ArgumentParser()
    parser.add_argument("param", nargs='?', default="dummy")
    args = parser.parse_args()
    if args.param != 'skipvalidation':
        validatePluginData(data)
    print(json.dumps(data, indent=4, sort_keys=True))  ###Print the output in JSON format

