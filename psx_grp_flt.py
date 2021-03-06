#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import ldap3


class PsxGrpFlt():
    """Stores each user's posixGroup associations in their pgMemberOf (memberOf)
    attribute.
    """

    def __init__(self, ldap_uri, ldap_binddn, ldap_passwd, ldap_basedn, ldap_persons_ou):
        """ PsxGrpFlt class constructor.

        Args:
            ldap_uri (str) - OpenLDAP Uniform Resource Identifier;
            ldap_binddn (str) - The user DN with correct permissions, such as Directory
                Manager;
            ldap_passwd (str) - The password for the the given user DN;
            ldap_basedn (str)- Base DN for search;
            ldap_persons_ou (str)- The persons (users) OU.
        """

        self.server = ldap3.Server(ldap_uri, get_info=ldap3.ALL)
        self.conn = ldap3.Connection(self.server,
                user=ldap_binddn,
                password=ldap_passwd,
                auto_bind=True)
        self.ldap_basedn = ldap_basedn
        self.ldap_persons_ou = ldap_persons_ou

    def get_psx_grps(self):
        """Get the list of posix groups from the Base DN.

        Get the list of all the posix groups of the informed Base DN.
        """

        self.conn.search("%s" % (self.ldap_basedn), "(objectClass=posixGroup)")
        return self.conn.entries

    def get_psx_grps_n_mbr_uids(self):
        """Get the list of memberUids from each posix group from the Base DN.

        Get the list of all memberUids from each posix group of the informed
        Base DN.
        """

        psx_grps_dn = [item.entry_dn for item in self.get_psx_grps()]
        psx_grps_n_mbr_uids = {}
        for psx_grp_dn in psx_grps_dn:
            self.conn.search(psx_grp_dn,
                    "(objectClass=posixGroup)",
                    attributes=["memberUid"])
            if "memberUid" in self.conn.entries[0]:
                psx_grps_n_mbr_uids[psx_grp_dn] = \
                        self.conn.entries[0]["memberUid"].values

        return psx_grps_n_mbr_uids

    def get_mbr_uids_n_psx_grps(self):
        """Get the list of posix groups from each memberUid from the Base DN.

        Get the list of all posix groups from each memberUid of the informed
        Base DN.
        """

        psx_grps_n_mbr_uids = self.get_psx_grps_n_mbr_uids()
        mbr_uids_n_psx_grps = {}
        for psx_grp_dn, mbrs_uids in psx_grps_n_mbr_uids.iteritems():
            for mbr_uid in mbrs_uids:
                if not mbr_uid in mbr_uids_n_psx_grps:
                    mbr_uids_n_psx_grps[mbr_uid] = []

                mbr_uids_n_psx_grps[mbr_uid].append(psx_grp_dn)

        return mbr_uids_n_psx_grps

    # Get memberUid Status and Data
    def get_mbr_uid_sts_n_data(self, mbr_uid):
        """Get some status and data from the memberUid (UID) informed from the Base
        DN.

        Args:
            mbr_uid (str): Person's memberUid (UID).

        Returns:
            dict: "mbr_uid_found" - If the memberUid (UID) was found; "mbr_uid_cn"
            - CN linked to memberUid (UID); "has_posixgrpflt" - If the memberUid
            (UID) has already the posixGrpFlt "olcObjectClasses"; "pgmemberof" -
            pgMemberOf values from the memberUid (UID).
        """

        # NOTE: Searches the defined Base DN checking if the candidate for update
        # user UID has the object classes ("objectClass") "inetOrgPerson" or "posixAccount".
        # By Questor
        # [Ref(s).: https://ldap3.readthedocs.io/en/latest/searches.html ]
        self.conn.search("%s, %s" % (self.ldap_persons_ou, self.ldap_basedn),
                "(&(|(objectClass=inetOrgPerson)(objectClass=posixAccount))"\
                "(uid=%s))" % (mbr_uid),
                attributes=["cn", "objectClass", "pgMemberOf"])

        mbr_uid_found = len(self.conn.entries) > 0
        mbr_uid_cn = ""
        has_posixgrpflt = True
        pgmemberof = []
        if mbr_uid_found:
            mbr_uid_cn = self.conn.entries[0]["cn"].value
            if not "posixGrpFlt" in self.conn.entries[0]["objectClass"].values:
                has_posixgrpflt = False

            if "pgMemberOf" in self.conn.entries[0]:
                pgmemberof = self.conn.entries[0]["pgMemberOf"].values

        return {"mbr_uid_found": mbr_uid_found,
                "mbr_uid_cn": mbr_uid_cn,
                "has_posixgrpflt": has_posixgrpflt,
                "pgmemberof": pgmemberof}

    def modify_obj(self, obj_cn, obj_uid, attrs_to_mdf, use_obj_cn=True):
        """Modifies an object from the Base DN.

        Modifies an object from the informed Base DN according to the parameters and
        settings informed in the attrs_to_mdf parameter.

        Args:
            obj_cn (str): Object CN;
            obj_uid (str): Object UID;
            attrs_to_mdf (dict): A dictionary of changes to be performed on the
                specified object conforming the ldap3's library specifications;
            use_obj_cn (Optional[bool]): Whether the object will be located by CN
                or UID.
        """
        # [Ref(s).: https://ldap3.readthedocs.io/en/latest/modify.html ]

        try_by_uid = True
        if use_obj_cn:

            # NOTE: For some reason some objects cannot be located by a DN consisting
            # of CN plus base DN. In these cases we try to locate the object by UID
            # plus base DN. The object will be searched using UID if it was not found
            # by CN. The "modify()" method (below) returns "False" if the object
            # was not found or in case of another failure. The parameter "use_obj_cn"
            # serves to avoid a new search with CN if a fault already happened in
            # a previous moment. By Quaestor
            try_by_uid = self.conn.modify("cn=%s, %s, %s" % (obj_cn,
                    self.ldap_persons_ou,
                    self.ldap_basedn),
                    attrs_to_mdf)

        if not try_by_uid or not use_obj_cn:
            self.conn.modify("uid=%s, %s, %s" % (obj_uid,
                    self.ldap_persons_ou,
                    self.ldap_basedn),
                    attrs_to_mdf)

        return try_by_uid

    def comp_two_lsts(self, list_a, list_b):
        """Compare two Python lists.

        Args:
            list_a (list): First list;
            list_b (list): Second list.

        Returns:
            bool: True - If the lists are equal; False - If not.
        """

        list_a.sort()
        list_b.sort()

        # [Ref(s).: https://www.tutorialspoint.com/how-to-compare-two-lists-in-python ]
        if (list_a == list_b):
            return False
        else:
            return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A simple Python 2.7 script that"\
" stores each user's posixGroup associations in their pgMemberOf (memberOf) attribute.")

    # NOTE: Get the CLI args. By Questor
    parser.add_argument(
        "-D",
        "--binddn",
        help="user DN with correct permissions, such as Directory Manager",
        required=True
    )
    parser.add_argument(
        "-y",
        "--file",
        help="password file with the password in plaintext for the given user DN",
        required=True
    )
    parser.add_argument(
        "-H",
        "--URI",
        help="OpenLDAP Uniform Resource Identifier",
        required=True
    )
    parser.add_argument(
        "-b",
        "--basedn",
        help="base DN for search",
        required=True
    )
    parser.add_argument(
        "-g",
        "--persons-ou",
        help="persons (users) OU",
        required=True
    )

    cli_args = parser.parse_args()

    # NOTE: Get password from file. By Questor
    with open(cli_args.file, "r") as content_file:
        ldap_passwd = content_file.read().strip()

    psx_grp_flt = PsxGrpFlt(cli_args.URI,
            cli_args.binddn,
            ldap_passwd,
            cli_args.basedn,
            cli_args.persons_ou)
    mbr_uids_n_psx_grps = psx_grp_flt.get_mbr_uids_n_psx_grps()

    # NOTE: Application execution main looping. By Questor
    for mbr_uid, psx_grps_dns in mbr_uids_n_psx_grps.iteritems():
        mbr_uid_info = psx_grp_flt.get_mbr_uid_sts_n_data(mbr_uid)
        if mbr_uid_info["mbr_uid_found"]:

            # NOTE: The object class "posixGrpFlt" is required to be use "pgMemberOf"
            # attribute. This object class will be added if the user does not have
            # one. By Questor
            use_obj_cn = True
            if not mbr_uid_info["has_posixgrpflt"]:
                use_obj_cn = psx_grp_flt.modify_obj(obj_cn=mbr_uid_info["mbr_uid_cn"],
                        obj_uid=mbr_uid,
                        attrs_to_mdf={
                            "objectClass": [(ldap3.MODIFY_ADD, ["posixGrpFlt"])]
                        })

            # NOTE: Check if update the person's groups ("pgmemberof") list is
            # needed. Avoids redundant update processes causing performance problems
            # and creating risks to the OpenLDAP database"s integrity.By Questor
            if psx_grp_flt.comp_two_lsts(mbr_uid_info["pgmemberof"], psx_grps_dns):
                psx_grp_flt.modify_obj(obj_cn=mbr_uid_info["mbr_uid_cn"],
                        obj_uid=mbr_uid,
                        attrs_to_mdf={
                            "pgMemberOf": [(ldap3.MODIFY_REPLACE, psx_grps_dns)]
                        },
                        use_obj_cn=use_obj_cn)
                print "Synced \"pgMemberOf\" attribute for the \"%s\" UID!" % (mbr_uid)
            else:
                print "The \"pgMemberOf\" attribute is up to date for the \"%s\""\
                        " UID!" % (mbr_uid)

        else:
            print "The \"%s\" UID does not exist or does not have the object class"\
                    " \"inetOrgPerson\" or \"posixAccount\", so not syncing!" % mbr_uid

    # NOTE: Perform the unbind operation ("close" connection). By Questor
    # [Ref(s).: https://ldap3.readthedocs.io/en/latest/unbind.html ]
    psx_grp_flt.conn.unbind()
