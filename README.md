# psx-grp-flt - user's posixGroup memberships against pgMemberOf (memberOf)

A simple Python 2.7 script that stores each user's ***posixGroup*** (***POSIX Group***) associations in their ***pgMemberOf*** (***memberOf***) attribute. The purpose is to enable search filters like below...

MODEL

```
ldapsearch -x -H '<OPENLDAP_URI>' -b '<PERSONS_OU>,<BASE_DN>' \
    -D '<ADM_USER_DN>' \
    -w '<ADM_USER_PASSWORD>' \
    '(&(pgMemberOf=cn=<PSX_GROUP_CN>,<GROUPS_OU>,<BASE_DN)(uid=<PERSON_UID>))'
```

EXAMPLE

```
ldapsearch -x -H 'ldap://127.0.0.1:389' -b 'ou=persons,dc=domain,dc=abc,dc=de' \
    -D 'cn=admin,dc=domain,dc=abc,dc=de' \
    -w 'mySecretValue' \
    '(&(pgMemberOf=cn=certaingroup,ou=groups,dc=domain,dc=abc,dc=de)(uid=certainuid))'
```

This script is useful for cases where we already have an OpenLDAP installed and we want to make filters available for ***POSIX Groups*** that already exists in a very simple way and without creating new types of groups. Also useful when unable to install overlays or when this process is too laborious or risky.

**IMPORTANT:** We recommend backing up your OpenLDAP data before testing our solution.

[Ref(s).: http://blog.oddbit.com/post/2013-07-22-generating-a-membero/ ,
https://github.com/DeBortoliWines/psx-grp-flt ]

## How It Works

Queries all ***posixGroup*** objects for their ***memberUid*** field, then aggregates all the results together. Then populates the ***pgMemberOf*** attribute of each listed user in the aggregation.

## Installation

Modify your OpenLDAP Schema to support the new operational ***pgMemberOf*** attribute and made it available to your ***person*** (users) object class. So, we're going to define this new attribute type that is largely identical to the ***memberOf*** attribute, and a new auxiliary object class (***posixGrpFlt***) that allows it...

```
ldapadd -Y EXTERNAL -H ldapi:// <<EOF
dn: cn=supplGrpFlt,cn=schema,cn=config
objectClass: olcSchemaConfig
cn: supplGrpFlt
olcAttributeTypes: ( 1.1.3.4.1.1.1.1
    NAME 'pgMemberOf'
    DESC 'Distinguished name of a (posix) group of which the object is a member'
    EQUALITY distinguishedNameMatch
    SYNTAX 1.3.6.1.4.1.1466.115.121.1.12 )
olcObjectClasses: ( 1.1.3.4.1.2.1.1
    NAME 'posixGrpFlt'
    DESC 'Posix group supplementary filter'
    AUXILIARY MAY ( pgMemberOf ) )
EOF
```

**IMPORTANT:** If you use replication for OpenLDAP, you will probably have to run the above command also on the replications (consumers) or conforming the strategy you used to replicate your OpenLDAP.
[Ref(s).: https://www.openldap.org/doc/admin24/replication.html ]

**NOTE:** supplGrpFlt - Supplementary Group Filter; posixGrpFlt - POSIX Group Filter; pgMemberOf - POSIX Group Member Of.

### Install Python 2.7 needed package

Install pip 2.7 (Python 2.7)...

**NOTE:** Commands for Centos 7. Adjust to your reality if necessary.

```
yum install -y python-pip
```

### Install psx-grp-flt

Install the git package, download the *psx-grp-flt* repository, move it to a proper location and install its Python 2.7 dependency...

```
yum install -y git-core
cd /usr/local/src
git clone https://github.com/eduardolucioac/psx-grp-flt.git
mv ./psx-grp-flt /usr/local/
cd /usr/local/psx-grp-flt
pip install ldap3==2.4
```

### Create the password file

Create the password file that has the password in plaintext for the given user...

MODEL

```
tee "/usr/local/psx-grp-flt/ldap_admin" << EOF
<ADM_USER_PASSWORD>
EOF
```

EXAMPLE

```
tee "/usr/local/psx-grp-flt/ldap_admin" << EOF
mySecretValue
EOF
```

## Usage

### Instructions

Usage instructions...

```
[root@ldap_provider psx-grp-flt]# /bin/python2.7 /usr/local/psx-grp-flt/psx_grp_flt.py --help
usage: psx_grp_flt.py [-h] -D BINDDN -y FILE -H URI -b BASEDN -g PERSONS_OU

A simple Python 2.7 script that stores each user's posixGroup associations in
their pgMemberOf (memberOf) attribute.

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

Usage model and example...

MODEL

```
/bin/python2.7 /usr/local/psx-grp-flt/psx_grp_flt.py -D "<ADM_USER_DN>" \
    -y "<ADM_USER_PWD_FILE_PATH>" \
    -H "<OPENLDAP_URI>" \
    -b "<BASE_DN>" \
    -g "<PERSONS_OU>"
```

EXAMPLE

```
/bin/python2.7 /usr/local/psx-grp-flt/psx_grp_flt.py -D "cn=admin,dc=domain,dc=abc,dc=de" \
    -y "/usr/local/psx-grp-flt/ldap_admin" \
    -H "ldap://127.0.0.1:389" \
    -b "dc=domain,dc=abc,dc=de" \
    -g "ou=persons"
```

### Add a job (crontab)

As the root user open the crontab editor to create a new job...

```
crontab -e
```

**NOTE:** Behaves like vi/vim.

...and add the line...

MODEL

```
*/15 * * * * /bin/python2.7 /usr/local/psx-grp-flt/psx_grp_flt.py -D "<ADM_USER_DN>" -y "<ADM_USER_PWD_FILE_PATH>" -H "<OPENLDAP_URI>" -b "<BASE_DN>" -g "<PERSONS_OU>"
```

EXAMPLE

```
*/15 * * * * /bin/python2.7 /usr/local/psx-grp-flt/psx_grp_flt.py -D "cn=admin,dc=domain,dc=abc,dc=de" -y "/usr/local/psx-grp-flt/ldap_admin" -H "ldap://127.0.0.1:389" -b "dc=domain,dc=abc,dc=de" -g "ou=persons"
```

**NOTE:** In the example above the script runs every 15 minutes.

**IMPORTANT:** Since crontab does not have the correct shell variables, we need to add the current user (root) path definition to the crontab jobs. In this way add (if it doesn't already exist) as the first line (before any scheduling) the output of the command below...

```
echo "PATH=$PATH"
```

... that will be something like this...

```
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/root/bin
```

## License

Licensed under The 3-Clause BSD License ( https://opensource.org/licenses/BSD-3-Clause ). See the [LICENSE](/LICENSE) file.

## Next steps

Create a service and a logs scheme.

**Thanks! =D**

## About

psx-grp-flt 🄯 BSD-3-Clause  
Eduardo Lúcio Amorim Costa  
Brazil-DF

<img border="0" alt="Brazil-DF" src="http://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Map_of_Brazil_with_flag.svg/180px-Map_of_Brazil_with_flag.svg.png" height="15%" width="15%"/>
