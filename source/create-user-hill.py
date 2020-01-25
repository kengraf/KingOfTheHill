import boto3
import sys, re

# Amazon Linux 2 AMI in Ohio
ohioaws = { "region": "us-east-2", 
                 "sg": ["sg-08fc1700d2eccec0f",], # OPEN_HOME_UNH
                 "sshkey": "ohio",
                 "ami": "ami-0dacb0c129b49f529"
                 }

# Amazon Linux 2 AMI in Ohio
ohioubuntu = { "region": "us-east-2", 
                 "sg": ["sg-06c9b734c321734ca",], # KOTH
                 "sshkey": "ohio",
                 "ami": "ami-0d5d9d301c853a04a"
                 }

# IT666 lab wants a London based deployment
openvpn = { "local": { "region": "eu-west-2", 
                       "sg": ["sg-0c51113a91a64fa42",], # OPEN_HOME_UNH
                       "sshkey": "london2",
                       "ami": "ami-05f37c3995fffb4fd"
                       },
            "tags": [ { 'Key': 'DNS',
                        'Value': 'openvpn.cyber-unh.org'
                        },
                      { 'Key': 'Name',
                        'Value': 'openvpn.cyber-unh.org'
                        },
                      ]
            }

# CTF run in Ohio
spec_json = { "local": { "region": "us-east-2", 
                         "sg": ["sg-06c9b734c321734ca",], # KOTH
                         "sshkey": "ohio",
                         "ami": "ami-0dacb0c129b49f529"
                         },
              "tags": [ { 'Key': 'DNS',
                          'Value': 'ctf.cyber-unh.org'
                          },
                        { 'Key': 'Name',
                          'Value': 'ctf.cyber-unh.org'
                          },
                        ]
              }


docker_userdata = '''
'''

# OpenVPN Access Server install
openvpnas_userdata = '''
'''


# Run agent for scoring ownership
scoring = '''wget https://s3.amazonaws.com/cyber-unh.org/ctf-scripts/ctf-ownership-scoring.py
python ctf-ownership-scoring.py &

'''

def main():
        # Two command arguments in fixed order: username configs
        # example:  python start-ec2-instance.py kmh722 "ssh_backup_keys,ctf_scoring"
        username = sys.argv[1]
        attack_string = sys.argv[2]
        
        # The system setup substring
        system_setup = '''#! /bin/bash
sudo -i
yum update -y

'''
        
        # The user setup substring
        usersetup = '''# Create user
useradd <USER>
passwd <USER> << EOF
<USER>
<USER>
EOF
cd /home/<USER>
echo "<USER>" > OWNERSHIP
chmod 644 OWNERSHIP
chown <USER> OWNERSHIP
chgrp <USER> OWNERSHIP

cd /root
echo "unclaimed" > OWNERSHIP
chmod 644 OWNERSHP
        
# Allow SSH password access
sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
systemctl restart sshd

'''        
        usersetup = re.sub(r'<USER>', username, usersetup )
        
        # Expand attack list to needed shell commands
        attack_list = attack_string.split(",")
        attacks = ""
        for a in attack_list:
                attacks += "wget https://s3.amazonaws.com/cyber-unh.org/ctf-scripts/" + a + "\nchmod +x ./" + a + "\n./" + a + " " + username +"\n"
        
        # pick the location specification to use
        spec = spec_json
        userdata = system_setup + usersetup + attacks + scoring
        
        ec2 = boto3.resource('ec2', region_name=spec['local']['region'])
        
        # create a new EC2 instance
        instances = ec2.create_instances(
             ImageId=spec['local']['ami'],
             MinCount=1,
             MaxCount=1, # if more than 1 AWS will create that many
             InstanceType='t2.micro',
             KeyName=spec['local']['sshkey'],
             UserData=userdata, # userdata is executed once the instance is started
             SecurityGroupIds=spec['local']['sg'], # your defined security group
             TagSpecifications=[{ 'ResourceType': 'instance', 'Tags': spec['tags'] },]
        )
        
        print(instances)

if __name__=='__main__':
    main()

# EOF