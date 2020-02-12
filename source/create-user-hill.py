import boto3
import sys, re

# KOTH run in Ohio
spec = { "region": "us-east-2", 
         "sg": "sg-036a520b734a05372", # UNH-CTF
         "sshkey": "ohio",
         "ami": "ami-00d711b946af13548",
         "domain" : ".cyber-unh.org",
         "attack_list" : []
         }

tags = [ { 'Key': 'DNS', 'Value': '' },
         { 'Key': 'Name', 'Value': '' },
         ]


# The system setup substring
system_setup = '''#! /bin/bash
yum update -y

'''

# Run agent for scoring ownership
scoring = '''cd /root
wget https://s3.amazonaws.com/cyber-unh.org/ctf-scripts/ctf-ownership-scoring.py
python ctf-ownership-scoring.py &

'''

# The user setup substring
usersetup = '''# Create user
useradd <USER>
passwd <USER> << EOF
unhsecurity
unhsecurity
EOF
echo "<USER>" > /tmp/OWNERSHIP
chmod 644 /tmp/OWNERSHIP
chown <USER> /tmp/OWNERSHIP
chgrp <USER> /tmp/OWNERSHIP

cd /root
echo "unclaimed" > OWNERSHIP
chmod 644 OWNERSHIP

# Allow SSH password access
sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
systemctl restart sshd

'''        

attacks1 = '''
chmod u+s /bin/tar
mkdir /home/<USER>/.ssh
cd /home/<USER>/.ssh
ssh-keygen -P password -C backup -f id_rsa
cat /root/.ssh/authorized_keys id_rsa.pub > .authorized_keys.bak
chmod 600 .authorized_keys.bak
/bin/cp .authorized_keys.bak /root/.ssh/authorized_keys
chown -R <USER> ../.ssh
chgrp -R <USER> ../.ssh
'''

def resetUser(config, username, attack_list):


    setup = re.sub(r'<USER>', username, usersetup ) # + re.sub(r'<USER>', username, attacks1 )
    for t in tags:
        t['Value'] = username + '.cyber-unh.org'
        
    # Expand attack list to needed shell commands
    attack_list = attack_list.split(",")
    attacks = ""
    for a in config['attack_list']:
        attacks += "\nwget https://s3.amazonaws.com/cyber-unh.org/ctf-scripts/" + a + "\nchmod +x ./" + a + "\n./" + a + " " + username +"\n"

    # build the userdata string
    userdata = system_setup + setup + attacks + scoring

    ec2 = boto3.resource('ec2', region_name=spec['region'])

    # create a new EC2 instance
    instances = ec2.create_instances(
            ImageId=spec['ami'],
            DryRun=True,
             MinCount=1,
             MaxCount=1, # if more than 1 AWS will create that many
             InstanceType='t2.micro',
             KeyName=spec['sshkey'],
             UserData=userdata, # userdata is executed once the instance is started
             SecurityGroupIds=spec['sg'], # your defined security group
             TagSpecifications=[{ 'ResourceType': 'instance', 'Tags': tags },]
        )

    print(instances)

# Find the current DNS tagged instance (terminate if any found)
def terminateInstance(username):
    ec2 = boto3.client('ec2', region_name=spec['local']['region'])

    response = ec2.describe_instances(
        Filters=[
            {
                'Name': 'tag:DNS',
                'Values': [username]
            }
        ]
        )
    for r in (response["Reservations"]):
        for i in r["Instances"]:
            print( "Terminating instance for %s", (username) )
#FIX            i.terminate()
    
# Two command arguments in fixed order: username configs
# example:  python create-user-hill.py configuration.json kmh722   
if __name__=='__main__':
    config = sys.argv[1]
    username = sys.argv[2]
    terminateInstance(username + spec{'domain'] )
    resetUser(config, username)

# EOF