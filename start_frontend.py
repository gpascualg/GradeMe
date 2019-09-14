from servers.frontend.main import main
from shutil import copytree

if __name__ == '__main__':
    # In docker mode, expose static folder to host
    # TODO(gpascualg): Change try/except for an actual flag
    try:
        copytree('/code/servers/frontend/static/', '/static/')
    except:
        pass

    main()
