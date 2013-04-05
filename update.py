#!/usr/bin/python

import make_table
import httplib
import datetime
import operator
import copy
import report
import logging

def get_usage_cluster(probename = None):
    host = "rcf-gratia.unl.edu"
    base_url = "/gratia/csv/osg_vo_hours?starttime=%(starttime)s&endtime=%(endtime)s&probe=%(probename)s"
    toReturn = {}
    default_group_stats = {'hours': 0.0,  'weekly_hours': 0.0, 'monthly_hours': 0.0}


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

def main():
    
    table = make_table.Table(add_numbers = False)

    tusker_usage = get_usage_cluster("pbs-lsf:tusker.unl.edu")
    firefly_usage = get_usage_cluster("pbs-lsf:ff-head.unl.edu")
    # Merge!
    merged = mergeDict(tusker_usage, firefly_usage, ['hours', 'weekly_hours', 'monthly_hours'])
    sandhills_usage = get_usage_cluster("slurm:sandhills.unl.edu")

    merged = mergeDict(sandhills_usage, merged, ['hours'])

    table.setHeaders(["Group", "1 day", "7 days", "30 days"])
    sorted_groups = sorted(merged.iteritems(), key=get_hours, reverse=True)
    for group in sorted_groups:
        table.addRow([group[0], "%.2f" % group[1].get('hours', '0.00'), "%.2f" % group[1].get('weekly_hours', 0), "%.2f" % group[1].get('monthly_hours', 0)])

    log = logging.getLogger("test")
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    report.sendEmail(("Derek Weitzel", "dweitzel@cse.unl.edu"), (["dweitzel@cse.unl.edu"], ["dweitzel@cse.unl.edu"]), "cse.unl.edu", "HCC Usage: %s" % (yesterday.strftime("%m/%d/%y")), table.plainText(), table.html(), log)




if __name__ == "__main__":
    main()


