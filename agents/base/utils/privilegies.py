import os
import pwd
import grp

def drop_privileges(self):
    if os.getuid() != 0:
        return False

    # Get the uid/gid from the name
    running_uid = pwd.getpwnam('agent').pw_uid
    running_gid = grp.getgrnam('agent').gr_gid

    # Remove group privileges
    os.setgroups([])

    # Try setting the new uid/gid
    os.setgid(running_gid)
    os.setuid(running_uid)

    # Ensure a very conservative umask
    old_umask = os.umask(0o077)
    return True
