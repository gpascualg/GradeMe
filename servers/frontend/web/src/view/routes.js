import PageLayout from './components/page-layout';

// Secondary components
import Splash from './components/splash-loader/index';
import MaintenancePage from './components/maintenance-layout/index';

// Main pages
import IndexPage from './pages/landing-page';
import LoginPage from './pages/login-page';
import ResultsPage from './pages/results-page'

// Database
import { db, upsert } from '../database';

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

            let loadingPromise = new Promise((resolve, reject) => {
                dataLoader(resolve, reject, db, params);
            }).then(v => v, v => v).catch((/* e */) => {
                // In case of server error we can show the maintenance page.
                return MaintenancePage;
            });
            return loadingPromise;
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
    '/results/:org/:repo/:branch/:hash' : lazyLoad(ResultsPage, (resolve, reject, db, params) => {        
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
                    'branch': params.branch,
                    'hash': params.hash
                });
            } 
            else {
                reject(LoginPage);
            }
        });
    }),
    '/index': lazyLoad(IndexPage, (resolve, reject, db) => {
        db.collection('data').find().toArray((error, docs) => {
            onceSocketReady.then(([socket, user_information]) => {
                if (user_information != null) {
                    var config = {}
                    for (let i = 0; i < docs.length; ++i) {
                        config[docs[i].key] = docs[i].value;
                    }
    
                    socket.once('user-repos', (repos) => {
                        // Change _id to id, to work with zango
                        for (let i = 0; i < repos.length; ++i) {
                            repos[i].id = repos[i]._id;
                            delete repos[i]._id;
                        }

                        // Only update inner storage if search query is empty
                        if (!config.search || !config.search.length)
                        {
                            let promises = []

                            // We are only 
                            // Do we need to update last?
                            if (repos && repos.length && repos[0].instances.length) {
                                // Do not update "last" if status is pending (yeah.. we could actually find the prev one, not now!)
                                if (repos[0].instances[0].status != 'pending') {
                                    let timestamp = repos[0].instances[0].timestamp;
                                    promises.push(upsert(db, 'data', {key: 'last'}, {key: 'last', value: timestamp}));
                                }
                            }

                            // Either update or save repos
                            for (let i = 0; i < repos.length; ++i) {
                                promises.push(upsert(db, 'repos', {id: repos[i]['id']}, repos[i]));
                            }

                            // Fetch from local storage once it is updated
                            Promise.all(promises).then(() => {
                                db.collection('repos')
                                    .find()
                                    .sort({'instances.0.timestamp': -1})
                                    .limit(10)
                                    .toArray((error, docs) => {
                                        resolve(() => {
                                            return {
                                                'repos': docs,
                                                'user': user_information,
                                                'config': config
                                            }
                                        });
                                    });
                            });
                        }
                        else {
                            // Otherwise, simply show results as obtained
                            resolve(() => {
                                return {
                                    'repos': repos,
                                    'user': user_information,
                                    'config': config
                                }
                            });
                        }
                    });
    
                    socket.emit('fetch-repos', { 
                        search: config.search || null,
                        last: config.last || 0
                    });
                } 
                else {
                    reject(LoginPage);
                }
            });
        })
    }),
};

const DefaultRoute = '/index';

export { Routes, DefaultRoute };
