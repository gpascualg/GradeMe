if __name__ == '__main__':
    from gevent import monkey
    monkey.patch_all()
    
from servers.frontend.main import main
from distutils.dir_util import copy_tree


# In docker mode, expose static folder to host
# TODO(gpascualg): Change try/except for an actual flag
try:
    copy_tree('/code/servers/frontend/static', '/static')
except:
    pass

if __name__ == '__main__':
    main(False)
else:
    app = main(True)
