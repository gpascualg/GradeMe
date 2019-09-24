import { Db } from 'zangodb';

let db = new Db('grademe-db', 3, {
    repos: ['id.org', 'id.repo'],
    data: ['key']
});

db.on('blocked', () => {
    db.drop();
});

function upsert(db, col, query, data) {
    return new Promise((resolve) => {
        db.collection(col).findOne(query).then((doc) => {
            if (doc) {
                db.collection(col)
                    .update(query, data)
                    .finally(() => resolve());
            }
            else {
                db.collection(col)
                    .insert(data)
                    .finally(() => resolve());
            }
        }).catch((e) => resolve(e));
    });
}

export { db, upsert }

