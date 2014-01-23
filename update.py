#!/usr/bin/python

import make_table
import httplib
import datetime
import operator
import copy
import report
import logging
import optparse

from Cheetah.Template import Template
from premailer import transform

host = "rcf-gratia.unl.edu"

def get_usage_cluster(probename = None):
    base_url = "/gratia/csv/osg_vo_hours?starttime=%(starttime)s&endtime=%(endtime)s&probe=%(probename)s"
    toReturn = {}
    default_group_stats = {'hours': 0.0, 'yesterday_hours': 0.0, 'weekly_hours': 0.0, 'monthly_hours': 0.0}


    starttime = datetime.datetime.now() - datetime.timedelta(days=2)
    endtime = datetime.datetime.now() - datetime.timedelta(days=1)
    string_starttime = starttime.strftime("%Y-%m-%d%%20%H:%M:%S")
    string_endtime = endtime.strftime("%Y-%m-%d%%20%H:%M:%S")

    conn = httplib.HTTPConnection("rcf-gratia.unl.edu")
    query = base_url % { "starttime": string_starttime, "endtime": string_endtime, "probename": probename }

    conn.request("GET", query)
    r1 = conn.getresponse()
    for line in r1.read().split("\n"):
        if len(line) == 0:
            continue
        (group, hours) = line.split(",")
        try:
            hours = float(hours)
        except:
            continue
        toReturn[group] = dict(default_group_stats)
        toReturn[group]["hours"] = hours
        
    # yesterday
    starttime = datetime.datetime.now() - datetime.timedelta(days=3)
    endtime = datetime.datetime.now() - datetime.timedelta(days=2)
    string_starttime = starttime.strftime("%Y-%m-%d%%20%H:%M:%S")
    string_endtime = endtime.strftime("%Y-%m-%d%%20%H:%M:%S")

    conn = httplib.HTTPConnection("rcf-gratia.unl.edu")
    query = base_url % { "starttime": string_starttime, "endtime": string_endtime, "probename": probename }

    conn.request("GET", query)
    r1 = conn.getresponse()
    for line in r1.read().split("\n"):
        if len(line) == 0:
            continue
        (group, hours) = line.split(",")
        try:
            hours = float(hours)
        except:
            continue
        if group not in toReturn:
            toReturn[group] = dict(default_group_stats)
        toReturn[group]["yesterday_hours"] = hours

    # Now 7 days
    starttime = datetime.datetime.now() - datetime.timedelta(days=8)
    endtime = datetime.datetime.now() - datetime.timedelta(days=1)
    string_starttime = starttime.strftime("%Y-%m-%d%%20%H:%M:%S")
    string_endtime = endtime.strftime("%Y-%m-%d%%20%H:%M:%S")

    conn = httplib.HTTPConnection("rcf-gratia.unl.edu")
    query = base_url % { "starttime": string_starttime, "endtime": string_endtime, "probename": probename }

    conn.request("GET", query)
    r1 = conn.getresponse()
    for line in r1.read().split("\n"):
        if len(line) == 0:
            continue
        (group, hours) = line.split(",")
        try:
            hours = float(hours)
        except:
            continue
        if group not in toReturn:
            toReturn[group] = dict(default_group_stats)
        toReturn[group]["weekly_hours"] = hours

    # Now 30 days
    starttime = datetime.datetime.now() - datetime.timedelta(days=31)
    endtime = datetime.datetime.now() - datetime.timedelta(days=1)
    string_starttime = starttime.strftime("%Y-%m-%d%%20%H:%M:%S")
    string_endtime = endtime.strftime("%Y-%m-%d%%20%H:%M:%S")

    conn = httplib.HTTPConnection("rcf-gratia.unl.edu")
    query = base_url % { "starttime": string_starttime, "endtime": string_endtime, "probename": probename }

    conn.request("GET", query)
    r1 = conn.getresponse()
    for line in r1.read().split("\n"):
        if len(line) == 0:
            continue
        (group, hours) = line.split(",")
        try:
            hours = float(hours)
        except:
            continue
        if group not in toReturn:
            toReturn[group] = dict(default_group_stats)
        toReturn[group]["monthly_hours"] = hours

    return toReturn


def mergeDict(dicta, dictb, merge_keys = []):
    to_return = copy.deepcopy(dicta)
    for key in dictb.keys():
        if key not in to_return:
            to_return[key] = {}

        for merge_key in merge_keys:
            if merge_key not in to_return[key]:
                to_return[key][merge_key] = dictb[key][merge_key]
            else:
                to_return[key][merge_key] += dictb[key][merge_key]
    return to_return

def get_hours(item):
    return item[1]['hours']

def get_graph_url(facilities):
    url = "http://rcf-gratia.unl.edu/gratia/status_graphs/status_vo?facility=%(facilities)s&starttime=%(starttime)s&endtime=%(endtime)s"
    starttime = datetime.datetime.now() - datetime.timedelta(days=2)
    endtime = datetime.datetime.now() - datetime.timedelta(days=1)
    string_starttime = starttime.strftime("%Y-%m-%d%%20%H:%M:%S")
    string_endtime = endtime.strftime("%Y-%m-%d%%20%H:%M:%S")
    
    return url % { 'facilities': facilities, 'starttime': string_starttime, 'endtime': string_endtime}


def AddOptions(parser):
    parser.add_option("-e", "--email", dest="email", help="Email address to send the report")

def main():

    parser = optparse.OptionParser()
    AddOptions(parser)

    (options, args) = parser.parse_args()
    
    table = make_table.Table(add_numbers = False)

    tusker_usage = get_usage_cluster("slurm:head.tusker.hcc.unl.edu")

    crane_usage = get_usage_cluster("slurm:head.crane.hcc.unl.edu")
    # Merge!
    merged = mergeDict(tusker_usage, crane_usage, ['hours', 'yesterday_hours', 'weekly_hours', 'monthly_hours'])

    sandhills_usage = get_usage_cluster("slurm:sandhills.unl.edu")

    merged = mergeDict(sandhills_usage, merged, ['hours', 'yesterday_hours', 'weekly_hours', 'monthly_hours'])

    table.setHeaders(["Group", "1 day", "7 days", "30 days"])
    sorted_groups = sorted(merged.iteritems(), key=get_hours, reverse=True)
    for group in sorted_groups:
        table.addRow([group[0], "%.2f" % group[1].get('hours', '0.00'), "%.2f" % group[1].get('weekly_hours', 0), "%.2f" % group[1].get('monthly_hours', 0)])

    # Define a function to sum for each resource
    def sum_key(summed_dict, key, default_value):
        return sum(summed_dict[usage].get(key, default_value) for usage in summed_dict)
        

    resource_sums = {   "Tusker":  {    'hours': "%.2f" % sum_key(tusker_usage, 'hours', 0),
                                        'weekly_hours': "%.2f" %  sum_key(tusker_usage, 'weekly_hours', 0) },
                        "Crane": {  'hours': "%.2f" %  sum_key(crane_usage, 'hours', 0),
                                    'weekly_hours': "%.2f" %  sum_key(crane_usage, 'weekly_hours', 0)},
                        "Sandhills": {  'hours': "%.2f" % sum_key(sandhills_usage, 'hours', 0),
                                        'weekly_hours':  "%.2f" % sum_key(sandhills_usage, 'hours', 0)}
                    }
    
    sorted_resources = sorted(resource_sums.iteritems(), key=lambda resource: resource[0][1], reverse=True)

    log = logging.getLogger("test")
    # Format the users
    users = []
    for group in sorted_groups[:10]:
        user = {}
        user["username"] = group[0]
        user["hours"] = "%.2f" % group[1].get('hours', 0.0)
        user["yesterday_hours"] = "%.2f" % group[1].get('yesterday_hours', 0.00)
        user["weekly_hours"] = "%.2f" % group[1].get('weekly_hours', 0)
        users.append(user)
    
    
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    report_info = { "date": datetime.datetime.now().ctime(), "server": host, "report_date": yesterday.strftime("%b %d, %Y")}
        
    graph_url = get_graph_url("tusker|crane|sandhills")
    
    t = Template(file="email_template.tmpl", searchList = [{'top_users': users, 'top_resources': sorted_resources, 'report_info': report_info, 'graph_url': graph_url}])
    f = open("produced.html", 'w')
    f.write(transform(str(t)))
    
    #print pynliner.fromString(str(t))

    
    #report.sendEmail(("Derek Weitzel", "dweitzel@cse.unl.edu"), ([options.email], [options.email]), "cse.unl.edu", "HCC Usage: %s" % (yesterday.strftime("%m/%d/%y")), table.plainText(), table.html(), log)
    report.sendEmail(("Derek Weitzel", "dweitzel@cse.unl.edu"), ([options.email], [options.email]), "cse.unl.edu", "HCC Usage: %s" % (yesterday.strftime("%m/%d/%y")), table.plainText(), transform(str(t)), log)

    


if __name__ == "__main__":
    main()


