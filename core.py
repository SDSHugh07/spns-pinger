import requests
import os
import urllib
import json

DEBUG_ON = False

#HMB
#SPNS_URL = "http://192.168.1.12"

#Tahoe
SPNS_URL = "http://192.168.42.5"

# SPNS_URL = "http://192.168.1.199"

# SPNS_URL="http://192.168.43.247"

SPNS_KEY = "5a219595-57b7-46c2-be9b-4a9f7d07566e"

SPNS_HEALTH_HEALTHY = 100
SPNS_HEALTH_NEEDS_CHECK = 70  # C's get degrees!
SPNS_HEALTH_NOT_HEALTHY = 0
SPNS_HEALTH_NOT_SET = -1

SYSTEM_MEMORY_MIN = 90
SYSTEM_DISK_MIN = 90    

CACHE_ENABLE = 0
CACHE_DISABLE = 1

PORT_CORPUS_MANAGER = 8889
PORT_DCT_INDEXER = 8893
PORT_DISPATCHER = 8887
PORT_GDICT = 8892
PORT_LOOKUP = 8891
PORT_ROUTING = 9999
PORT_CONSOLE_NON_SSL = 3001
PORT_CONSOLE_SSL = 3443
PORT_GATEWAY_NON_SSL = 8903
PORT_GATEWAY_SSL = 8904
PORT_TM_INDEXER = 8890
PORT_TRM = 8888
PORT_TRS_CONSOLE_NON_SSL = 3002
PORT_TRS_CONSOLE_SSL = 3445

SYSTRAN_COMPONENT_PORTS = [
    {'name':'CORPUS_MANAGER', 'port':PORT_CORPUS_MANAGER},
    {'name':'DCT_INDEXER', 'port':PORT_DCT_INDEXER},
    {'name':'DISPATCHER', 'port':PORT_DISPATCHER},
    {'name':'GDICT', 'port':PORT_GDICT},
    {'name':'LOOKUP', 'port':PORT_LOOKUP},
    {'name':'ROUTING', 'port':PORT_ROUTING},
    {'name':'CONSOLE_NON_SSL', 'port':PORT_CONSOLE_NON_SSL},
    # {'name':'CONSOLE_SSL', 'port':PORT_CONSOLE_SSL},
    {'name':'GATEWAY_NON_SSL', 'port':PORT_GATEWAY_NON_SSL},
    # {'name':'GATEWAY_SSL', 'port':PORT_GATEWAY_SSL},
    {'name':'TM_INDEXER', 'port':PORT_TM_INDEXER},
    {'name':'TRM', 'port':PORT_TRM},
    {'name':'TRS_CONSOLE_NON_SSL', 'port':PORT_TRS_CONSOLE_NON_SSL}
    # {'name':'TRS_CONSOLE_SSL', 'port':PORT_TRS_CONSOLE_SSL}
]

def probe_system_health():
    if DEBUG_ON:
        print ("probe_system_health")

    dct_spns_probe_result = probe_spns()
    dct_spns_errors = {}
    spns_health = SPNS_HEALTH_NOT_SET
    num_total_errors = 0

    if DEBUG_ON:
        print(json.dumps(dct_spns_probe_result, indent=4, sort_keys=True))

    for health_metric in dct_spns_probe_result:
        lst_health_metric_errors = []
        num_health_metric_errors = 0

        for item in dct_spns_probe_result[health_metric]:
            if not item['status']:
                spns_health = SPNS_HEALTH_NOT_HEALTHY
                num_total_errors += 1
                num_health_metric_errors += 1
                lst_health_metric_errors.append(item)

        if num_health_metric_errors:
            dct_spns_errors[health_metric] = lst_health_metric_errors

    if 0 == num_total_errors:
        spns_health = SPNS_HEALTH_HEALTHY

    return spns_health, dct_spns_probe_result, dct_spns_errors

def probe_spns():
    if DEBUG_ON:
        print ("probe_spns")

    spns_status = {}

    spns_status["translations"] = probe_translations()
    spns_status["systran_components"] = probe_systran_components()
    spns_status["system_resources"] = probe_system_resources()

    if DEBUG_ON:
        print(json.dumps(spns_status["translations"], indent=4, sort_keys=True))

    return spns_status

def probe_translations():
    if DEBUG_ON:
        print ("probe_translations")

    ## check all profiles of the server

    resp = requests.get(SPNS_URL + ':' + str(PORT_GATEWAY_NON_SSL) + '/translation/profiles?key=' + SPNS_KEY).json()
    result_translations = []

    for profile in resp["profiles"]:
        output_text = ('').encode('utf-8')
        source = profile["source"]
        target = profile["target"]
        domain = profile["selectors"]["domain"]
        profileid = profile["id"]

        input_filename = "/opt/site24x7/monagent/plugins/spns/test/test-" + profile["source"] + "-1.txt"

        F = open(input_filename, "r")
        text = urllib.quote(F.read())

        translation_request = SPNS_URL + ':' + str(PORT_GATEWAY_NON_SSL) + "/translation/text/translate?key=" +\
                              SPNS_KEY + "&input=" + text + "&source=" + source + "&target=" + target + "&domain=" +\
                              domain + "&profile=" + profileid + "&no_cache=" + str(CACHE_DISABLE)

        translation_resp = requests.get(translation_request).json()

        for output in translation_resp["outputs"]:
            output_text = output["output"].encode('utf-8')

        oldtranslation = ""
        if os.path.isfile('/opt/site24x7/monagent/plugins/spns/test/output/' + profileid + '.txt'):
            f = open('/opt/site24x7/monagent/plugins/spns/test/output/' + profileid + '.txt', "r")
            oldtranslation = f.read()

        newfile = open('/opt/site24x7/monagent/plugins/spns/test/output/' + profileid + '.txt', "w")
        newfile.write(output_text)  ## updating output file with new translation

        status = (oldtranslation == output_text)

        result_translations.append(
            {"source": source, "target": target, "domain": domain, "translation": output_text, "profile": profileid,
             "old_translation": oldtranslation, "status": status})

    return result_translations

def probe_system_resources():
    if DEBUG_ON:
        print("def probe_system_resources()")

    lst_system_resources = []

    system_memory_used = probe_system_memory()
    dct_system_memory = {'name': 'MEMORY', 'status':(SYSTEM_MEMORY_MIN > system_memory_used), 'used': system_memory_used}

    system_disk_used = probe_system_disk()
    dct_system_disk = {'name': 'DISK', 'status':(SYSTEM_DISK_MIN > system_disk_used), 'used': system_disk_used}

    lst_system_resources.append(dct_system_memory)

    lst_system_resources.append(dct_system_disk)

    return lst_system_resources

def probe_systran_components():
    if DEBUG_ON:
        print ("probe_systran_components")

    result_systran_components = []

    for port in SYSTRAN_COMPONENT_PORTS:
        temp_component = {"name": port['name'], "port": port['port'], "status": query_systran_component(port['port'])}

        result_systran_components.append(temp_component)

    return result_systran_components

def query_systran_component(systran_component_port):
    if DEBUG_ON:
        print ("query_systran_component")

    try:
        str_api_query = SPNS_URL + ':' + str(systran_component_port) + '/status'
        resp = requests.get(str_api_query).json()

        return resp["status"]

    except Exception as e:
        return False

def probe_system_memory():
    if DEBUG_ON:
        print ("probe_system_memory")

    resp = requests.get(SPNS_URL + ':' + str(PORT_TRM) + '/status/system').json()

    available = resp['system']['memory']['available']
    total = resp['system']['memory']['total']
    
    used = 100 - ((float(available) / (float(total))) * 100)

    return int(used)

def probe_system_disk():
    if DEBUG_ON:
        print ("probe_system_disk")

    resp = requests.get(SPNS_URL + ':' + str(PORT_TRM) + '/status/system').json()

    available = resp['system']['disk']['available']
    total = resp['system']['disk']['total']

    used = 100 - ((float(available) / (float(total))) * 100)

    return int(used)









