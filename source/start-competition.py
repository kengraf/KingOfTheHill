import boto3
from botocore.exceptions import ClientError
import os

ec2 = boto3.client('ec2')
cognito = boto3.client('cognito-idp')

try:
    response = ec2.describe_security_groups(GroupNames=['KOTH',])
    security_group_id = response['SecurityGroups'][0]['GroupId']
    sg_permissions = response['SecurityGroups'][0]['IpPermissions']
    print('Security Group %s found.' % (security_group_id))
    
    # Remove all the existing ingress rules
    if len(sg_permissions) > 0:
        response = ec2.revoke_security_group_ingress(
            GroupId=security_group_id, 
            IpPermissions=sg_permissions)    
    
    # add a new rule to allow ingress
    data = ec2.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {'IpProtocol': 'tcp',
             'FromPort': 0,
             'ToPort': 30000,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
        ])
    print('Ingress Successfully Set %s' % data)
   
    # list users in the pool, so we can spin up an instance
    data = cognito.list_users( UserPoolId='us-east-2_pVUBdVE0e' )  
    for u in data['Users']:
        username = u['Username'].split('-at')[0]
        print(username)
        username = username.replace(".","")
        print(username)
        os.system("python3 create-user-hill.py ../configs/metasploitable-linux.json " + username )
   
except ClientError as e:
    print(e)