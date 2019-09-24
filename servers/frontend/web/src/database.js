
var onceDBReady = new Promise((resolve) => {
    var request = indexedDB.open('grademe', 3);
    
    request.onsuccess = () => {
        resolve(request.result);
    };

    request.onupgradeneeded = (event) => {
        console.log('UPGRADE');
        var db = event.target.result;
      
        function create_tests_store() {
            // TODO(gpascualg): Is this the most efficient way to store tests?
            var testsStore = db.createObjectStore('tests', { keyPath: 'id' });
            testsStore.createIndex('hash', 'hash', { unique: true });
        }

        function create_data_store() {    
            // Other data
            var dataStore = db.createObjectStore('data', { keyPath: 'key' });
            dataStore.createIndex('value', 'value', { unique: false });

            dataStore.transaction.oncomplete = (/* event */) => {
                var objectStore = db.transaction('data', 'readwrite').objectStore('data');
                objectStore.add({key: 'search', value: null});
            };
        }

        // Upgrade as needed
        switch(db.version) {
            case 0:
                create_tests_store();
                create_data_store();
                break;

            case 1:
            case 2:
                create_data_store();
                break;
        }
        // Tests already fetched so far
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

function update(db, table, data) {
    return new Promise((resolve) => {
        var objectStore = db.transaction(table, 'readwrite').objectStore(table);
        var updateRequest = objectStore.put(data);
        updateRequest.onsuccess = function() {
            resolve(true)
        };
    });
}

export { onceDBReady, cursor, fetch, update };
