from gevent import monkey
monkey.patch_all()

from servers.webhooks.main import main

if __name__ == '__main__':
    main(False)
else:
    app = main(True)
