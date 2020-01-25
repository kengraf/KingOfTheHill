# KingOfTheHill

Purpose: Create an attack & defend competition in the Cloud

Users (competitiors) are each given identical systems with security flaws.
Defend: Users claim ownership, escaluate privilege, and harden their system.
Attack: Using knowlege gained on defence attack the weaknesses in their conpetitor's systems

Actions:
Register:
Prior to the event each competitor creates an account based on email.
The email name will be used to create a DNS record to allow access to system.

Create:
Called one time just prior to the event starting.
Remove all security group ingress to block traffic until the start. 
Clear the database of previous scoring data.
Creates an instance for every user registered.
DNS records updated when the instance is started.  <name>.koth.cyber-unh.edu

Start:
Create security group rule to allow access to systems.
Start the scoring process.

Score:
Retrieve results from database, publicly present as koth.cyber-unh.org/score

DeployUser:
Remove existing instance< if one.
Create new instance.
Update DNS record.

Stop:
Stop scoring updates.
Remove ingress security group rules, to block access.

Destroy:
Terminiate all instances.

Convert HTML: Wildrydes to Kingofthehill