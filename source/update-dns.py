import json
import boto3
import re
import time
import random
from datetime import datetime

def get_zone_id(zone_name):
    """This function returns the zone id for the zone name that's passed into the function."""
    if zone_name[-1] != '.':
        zone_name = zone_name + '.'
    hosted_zones = route53.list_hosted_zones()
    for x in hosted_zones['HostedZones']:
        print ('looking for %s in %s' % (zone_name,x['Name']))
        if x['Name'] == zone_name:
            return x['Id'].partition('/hostedzone/')[2]

    return None

def is_valid_hostname(hostname):
    """This function checks to see whether the hostname entered into the zone and cname tags is a valid hostname."""
    if hostname is None or len(hostname) > 255 or len(hostname) == 0:
        return False
    if hostname[-1] == ".":
        hostname = hostname[:-1]
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))


print('Loading function ' + datetime.now().time().isoformat())
route53 = boto3.client('route53')
ec2 = boto3.resource('ec2')
compute = boto3.client('ec2')

def lambda_handler(event, context):

    # Set variables
    # Get the state from the Event stream
    state = event['detail']['state']

    # Get the instance id, region, and tag collection
    instance_id = event['detail']['instance-id']
    region = event['region']

    if state == 'running':
        time.sleep(60)
        instance = compute.describe_instances(InstanceIds=[instance_id])
        # Remove response metadata from the response
        instance.pop('ResponseMetadata')

    try:
        tags = instance['Reservations'][0]['Instances'][0]['Tags']
    except:
        tags = []
    # Get instance attributes
    try:
        public_ip = instance['Reservations'][0]['Instances'][0]['PublicIpAddress']
        public_dns_name = instance['Reservations'][0]['Instances'][0]['PublicDnsName']
        public_host_name = public_dns_name.split('.')[0]
    except BaseException as e:
        print ('Instance has no public IP or host name', e)

    # Create the public  hosted zone collections.  These are collections of zones in Route 53.
    hosted_zones = route53.list_hosted_zones()
    public_hosted_zones = hosted_zones['HostedZones']
    public_hosted_zones_collection = []
    for x in public_hosted_zones:
        public_hosted_zones_collection.append(x['Name'])
    
    print(list(public_hosted_zones_collection))
    # Wait a random amount of time.  This is a poor-mans back-off if a lot of instances are launched all at once.
    time.sleep(random.random())

    # Loop through the instance's tags, looking for the DNS tag. 
    # to make sure that the name is valid.  If it is and if there's a matching zone in DNS, create A record.
    for tag in tags:
        if 'DNS' in tag.get('Key',{}).lstrip().upper():
            domain = tag.get('Value')
            if is_valid_hostname(domain):
                subdomain = domain[0:domain.find('.')]
                zone = domain.partition('.')[2] + '.'
                print('zone %s' % zone )
                if zone in public_hosted_zones_collection:
                    print ('Public zone found', zone)
                    zone_id = get_zone_id(zone)
                    # create A record in public zone
                    if state =='running':
                        try:
                            if domain[-1] != '.':
                                domain = domain + '.'
                            create_resource_record(zone_id, domain, public_ip)
                        except BaseException as e:
                            print (e)
                else:
                    print ('No matching zone found for %s' % zone )
                    print (list(public_hosted_zones_collection))
                    print (tag.get('Value'))
            else:
                print ('%s is not a valid host name' % tag.get('Value'))
        # Consider making this an elif CNAME
        else:
            print ('The tag \'%s\' is not a DNS tag' % tag.get('Key'))
        
def create_resource_record(zone_id, host_name, value):
    """This function creates resource records in the hosted zone passed by the calling function."""
    print ('Updating A record %s in zone %s to %s' % (host_name, zone_id, value))
    if host_name[-1] != '.':
        host_name = host_name + '.'
    response = route53.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch={
                    "Comment": "Updated by Lambda DDNS",
                    "Changes": [
                        {
                            "Action": "UPSERT",
                            "ResourceRecordSet": {
                                "Name": host_name,
                                "Type": "A",
                                "TTL": 60,
                                "ResourceRecords": [
                                    {
                                        "Value": value
                                    },
                                ]
                            }
                        },
                    ]
                }
            )
    print(response)

   
