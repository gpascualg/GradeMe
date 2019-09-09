import PageLayout from './components/page-layout';

// Secondary components
import Splash from './components/splash-loader/index';
import MaintenancePage from './components/maintenance-layout/index';

// Main pages
import IndexPage from './pages/landing-page';
import LoginPage from './pages/login-page';

// Websockets
import io from 'socket.io-client';

const $root = document.body.querySelector('#root');

let socketio_url = $root.dataset.mode == 'development' ? 'localhost:9090' : 'grademe.education';
const socket = io('http://' + socketio_url);

let onceDBReady = new Promise((resolve) => {
    var request = indexedDB.open('grademe', 2);
    
    request.onsuccess = () => {
        resolve(request.result);
    };

    request.onupgradeneeded = (event) => {
        console.log('UPGRADE');
        var db = event.target.result;
      
        // Decks table
        var decksStore = db.createObjectStore('tests', { keyPath: 'id' });
        decksStore.createIndex('hash', 'hash', { unique: true });

        var lastStore = db.createObjectStore('last', { keyPath: 'id' });
        lastStore.createIndex('hash', 'hash', { unique: true });
    };
});

function cursor(db, table, index_or_where, where) {
    var objectStore = db.transaction(table).objectStore(table);

    if (typeof index_or_where == 'undefined' || typeof where == 'undefined') {
        return objectStore.openCursor(index_or_where);
    }

    return objectStore.index(index_or_where).openCursor(where);
}

function fetch(db, table, index_or_where, where) {
    return new Promise((resolve) => {
        let data = [];

        cursor(db, table, index_or_where, where).onsuccess = (event) => {
            var cursor = event.target.result;
            if (cursor) {
                data.push(cursor.value);
                cursor.continue();
            }
            else {
                resolve(data);
            }
        };
    });
}

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
        resolve(result);
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
    '/index': lazyLoad(IndexPage, (resolve, reject, db) => {
        onceSocketReady.then((user_information) => {
            if (!user_information) {
                fetch(db, 'last', 'id').then((data) => {
                    console.log(data);
                    resolve(() => {
                        return {
                            'instances': [
                                {id: 1, name: 'test', color: 'red'},
                                {id: 2, name: 'test', color: 'green'},
                                {id: 3, name: 'test', color: 'orange'},
                                {id: 4, name: 'test', color: 'gren'},
                                {id: 5, name: 'test', color: 'red'},
                            ],
                        };
                    });
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