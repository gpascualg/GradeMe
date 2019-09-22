import PageLayout from './components/page-layout';

// Secondary components
import Splash from './components/splash-loader/index';
import MaintenancePage from './components/maintenance-layout/index';

// Main pages
import IndexPage from './pages/landing-page';
import LoginPage from './pages/login-page';
import ResultsPage from './pages/results-page'

// Database
import { onceDBReady, fetch } from '../database';

// Websockets
import io from 'socket.io-client';

const $root = document.body.querySelector('#root');

let socketio_url = $root.dataset.mode == 'development' ? 'localhost:9090' : 'grade-me.education';
const socket = io('http://' + socketio_url);


function lazyLoad(page, dataLoader) {
    return {
        onmatch(params) {
            // Show Loader until the promise has been resolved or rejected.
            m.render($root, m(PageLayout, m(Splash))); 

            return onceDBReady.then((db) => {
                let loadingPromise = new Promise((resolve, reject) => {
                    dataLoader(resolve, reject, db, params);
                }).then(v => v, v => v).catch((/* e */) => {
                    // In case of server error we can show the maintenance page.
                    return MaintenancePage;
                });
                return loadingPromise;
            });
        },
        render(vnode) {
            if (vnode.tag == MaintenancePage || vnode.tag == LoginPage) {
                // If onmatch returns a component or a promise that resolves to a component, comes here.
                return m(PageLayout, m(vnode.tag));
            }
            else if (typeof vnode.tag === 'function') {
                return m(PageLayout, m(page, vnode.tag()));
            }

            return m(PageLayout, m(page));
        },
    };
}

// Some user information
let onceSocketReady = new Promise((resolve) => {
    socket.on('connect', () => {
        socket.emit('is-logged');
    });

    socket.on('login-status', function(result) {
        resolve([socket, result]);
    });
});

const Routes = {
    '/splash': {
        render: function() {
            return m(PageLayout, m(Splash));
        },
    },
    '/login': {
        render: function() {
            return m(PageLayout, m(LoginPage));
        },
    },
    '/results/:org/:repo/:hash' : lazyLoad(ResultsPage, (resolve, reject, db, params) => {
        onceSocketReady.then(([socket, user_information]) => {
            if (user_information != null) {
                socket.once('instance-result', (repo) => {
                    console.log(repo);
                    resolve(() => {
                        return {
                            'repo': repo
                        }
                    });
                });

                socket.emit('fetch-instance-result', {
                    'org': parseInt(params.org), 
                    'repo': parseInt(params.repo), 
                    'hash': params.hash
                });
            } 
            else {
                reject(LoginPage);
            }
        });
    }),
    '/index': lazyLoad(IndexPage, (resolve, reject, db) => {
        onceSocketReady.then(([socket, user_information]) => {
            if (user_information != null) {
                fetch(db, 'data').then((data) => {
                    var config = {}
                    for (let i = 0; i < data.length; ++i) {
                        config[data[i].key] = data[i].value;
                    }

                    socket.once('user-instances', (instances) => {
                        resolve(() => {
                            return {
                                'repos': instances,
                                'user': user_information,
                                'config': config
                            }
                        });
                    });

                    socket.emit('fetch-instances', config.search || null);
                });
            } 
            else {
                reject(LoginPage);
            }
        });
    }),
};

const DefaultRoute = '/index';

export { Routes, DefaultRoute };
