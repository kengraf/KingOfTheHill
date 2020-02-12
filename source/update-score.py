import boto3
import requests

from botocore.exceptions import ConnectionError


# Find the current DNS tagged instances
def scoreInstances():
    ec2 = boto3.client('ec2')

    response = ec2.describe_instances()
    dnslist = []
    for r in (response["Reservations"]):
        for i in r["Instances"]:
            if i['State']['Name'] == 'running':
                dnslist.append(i['Tags'][0]['Value'])
            
    # store in database
    html = "Machine,Root,User\n"
    for d in dnslist:
        URL = "http://" + d + ":12345"
        try:
            r = requests.get(URL)
            data = r.json()
            html += d.split('.')[0] + ',' + data[0]['ROOT'] + ',' + data[0]['USER'] + '\n'
        except ConnectionError as e:
            print(e)            
    
    # Method S3 put
    s3 = boto3.resource('s3')
    object = s3.Object('unh-kingofthehill', 'score.csv')
    object.put(Body=html, ContentType='text/html')
    

    # wait a minute
    
    # fire again
    # async invoke ???
    
    
if __name__=='__main__':
    targetlist = scoreInstances()

# EOF