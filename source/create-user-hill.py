import boto3
import sys, re, json

tags = [ { 'Key': 'DNS', 'Value': '' },
         { 'Key': 'Name', 'Value': '' },
         ]


# Run agent for scoring ownership
ctf_scoring = '''cd /root
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
'''

password_auth = '''
# Allow SSH password access
sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication/PasswordAuthentication/g' /etc/ssh/sshd_config
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

def resetUser(config_data, username):


    setup = re.sub(r'<USER>', username, usersetup ) # + re.sub(r'<USER>', username, attacks1 )
    for t in tags:
        t['Value'] = username + '.cyber-unh.org'
        
    # Add shell commands to setup the box
    commands = ''
    for a in config_data['command_list']:
        commands += a + "\n"
    if config_data['password_authentication'] == 'true':
        commands += password_auth
    if config_data['ctf_scoring'] == 'true':
        commands += ctf_scoring
    for a in config_data['reboot_commands']:
        commands += a + "\n"
        
    ec2 = boto3.resource('ec2', region_name=config_data['region'])

    # create a new EC2 instance
    instances = ec2.create_instances(
            ImageId=config_data['ami'],
             MinCount=1,
             MaxCount=1, # if more than 1 AWS will create that many
             InstanceType='t2.micro',
             KeyName=config_data['sshkey'],
             UserData=commands, # userdata is executed once the instance is started
             SecurityGroupIds=config_data['sg'], # your defined security group
             TagSpecifications=[{ 'ResourceType': 'instance', 'Tags': tags },]
        )

    print(instances)

# Find the current DNS tagged instance (terminate if any found)
def terminateInstance(config_data, username):
    ec2 = boto3.client('ec2', region_name=config_data['region'])

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
    #open the file
    with open(config) as f:
        config_data = json.load(f)    
    
    username = sys.argv[2]
    terminateInstance(config_data, username + '.' + config_data['domain'] )
    resetUser(config_data, username)

# EOF