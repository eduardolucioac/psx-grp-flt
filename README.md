# psx-grp-flt - user's "posixGroup" memberships against "pgMemberOf" ("memberOf")

A simple Python script that stores a user's "posixGroup" memberships against "pgMemberOf" ("memberOf") attribute.

## How It Works

Queries all "posixGroup" objects for their "memberUid" field, then aggregates all the results together.

Then populates the "pgMemberOf" attribute of each listed user in the aggregation.

## Installation

Modify your OpenLDAP Schema to support the new operational "pgMemberOf" attribute and made it available to your "user"/"person" object class. So, we’re going to define this new attribute type that is largely identical to the "memberOf" attribute, and a new auxiliary object class ("obPerson" "posixGrpFlt") that allows it.

```
ldapadd -Y EXTERNAL -H ldapi:// <<EOF
dn: cn=supplGrpFlt,cn=schema,cn=config
objectClass: olcSchemaConfig
cn: supplGrpFlt
olcAttributeTypes: ( 1.1.3.5.1.1.1.1 
 NAME 'pgMemberOf' 
 DESC 'Distinguished name of a (posix) group of which the object is a member' 
 EQUALITY distinguishedNameMatch 
 SYNTAX 1.3.6.1.4.1.1466.115.121.1.12 )
olcObjectClasses: ( 1.1.3.5.1.2.1.1 
 NAME 'posixGrpFlt' 
 DESC 'Posix group supplementary filter' 
 AUXILIARY MAY ( pgMemberOf ) )
EOF
```

IMPORTANT: If you use replication for OpenLDAP, you will probably have to run the above command also on replications (consumers) or conforming the strategy you used to replicate your OpenLDAP.
[Ref(s).: https://www.openldap.org/doc/admin24/replication.html ]

### Install Python 2.7 needed packages

Install Python 2.7 and pip 2.7...

```
yum install -y python-setuptools
yum install -y python-pip
```

NOTE: Commands for Centos 7. Adjust to your reality.

### Install psx-grp-flt

Vai instalar o pacote git, baixar o repositório "psx-grp-flt", move-lo para o local adequado e instalar a sua dependência Python 2.7...

```
yum install -y git-core
cd /usr/local/src
git clone https://github.com/eduardolucioac/psx-grp-flt.git
mv ./psx-grp-flt /usr/local/
cd /usr/local/psx-grp-flt
pip install ldap3==2.4
```

## Usage

### Instructions

```
[root@ldap_provider psx-grp-flt]# /bin/python2.7 /usr/local/psx-grp-flt/psx_grp_flt.py.py --help
usage: psx_grp_flt.py.py [-h] -D BINDDN -y FILE -H URI -b BASEDN -g PERSONS_OU

Syncs memberOf attribute onto users (inetOrgPerson) that are in posixGroups.

optional arguments:
  -h, --help            show this help message and exit
  -D BINDDN, --binddn BINDDN
                        user DN with correct permissions, such as Directory
                        Manager
  -y FILE, --file FILE  password file with the password in plaintext for the
                        given user DN
  -H URI, --URI URI     OpenLDAP Uniform Resource Identifier
  -b BASEDN, --basedn BASEDN
                        base DN for search
  -g PERSONS_OU, --persons-ou PERSONS_OU
                        persons (users) OU
```

### Model and example

MODEL

```
/bin/python2.7 /usr/local/psx-grp-flt/psx_grp_flt.py -D "<ADM_USER_DN>" \
    -y "<PASSWORD_FILE_PATH>" \
    -H "<OPENLDAP_URI>" \
    -b "<BASE_DN>" \
    -g "<PERSONS_OU>"
```

EXAMPLE

```
/bin/python2.7 /usr/local/psx-grp-flt/psx_grp_flt.py -D "cn=admin,dc=domain,dc=abc,dc=de" \
    -y "/usr/local/ldap-sync-memberof/ldap_admin" \
    -H "ldap://127.0.0.1:389" \
    -b "dc=domain,dc=abc,dc=de" \
    -g "ou=person"
```

### Add a job (crontab)

As root use crontab to register a new job...

```
crontab -e
```

NOTE: Behaves like vi/vim.

...and add the line...

MODEL

```
*/15 * * * * /bin/python2.7 /usr/local/psx-grp-flt/psx_grp_flt.py -D "<ADM_USER_DN>" -y "<PASSWORD_FILE_PATH>" -H "<OPENLDAP_URI>" -b "<BASE_DN>" -g "<PERSONS_OU>"
```

EXAMPLE

```
*/15 * * * * /bin/python2.7 /usr/local/psx-grp-flt/psx_grp_flt.py -D "cn=admin,dc=domain,dc=abc,dc=de" -y "/usr/local/ldap-sync-memberof/ldap_admin" -H "ldap://127.0.0.1:389" -b "dc=domain,dc=abc,dc=de" -g "ou=person"
```

IMPORTANT: Since crontab does not have the correct shell variables, we need to add the current user (root) path definition to the crontab jobs. In this way add (if it doesn't already exist) as the first line (before any scheduling) the output of the command below...

```
echo "PATH=$PATH"
```

... that will be something like this...

```
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/root/bin
``` .

## License

Licensed under The 3-Clause BSD License ( https://opensource.org/licenses/BSD-3-Clause ). See the [LICENSE](/LICENSE) file.

Thanks! =D
