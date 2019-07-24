
var GLOBAL_EDIT_ID = 0;
var DECK_ID = 0;
var DATABASE = openDatabase('flashdash', '0.1', 'FlashDash user decks', 2 * 1024 * 1024, on_db_init);

function on_db_init(db)
{
    DATABASE.transaction((tran) => {
        tran.executeSql('CREATE TABLE IF NOT EXISTS decks (id INTEGER PRIMARY KEY, name TEXT)');
        tran.executeSql('CREATE TABLE IF NOT EXISTS cards (id INTEGER PRIMARY KEY, deck_id INTEGER, front TEXT, back TEXT, FOREIGN KEY (deck_id) REFERENCES decks (id))');
    });
}

function save_card(editors, id)
{
    DATABASE.transaction((tran) => {
        tran.executeSql('INSERT OR REPLACE INTO cards (id, deck_id, front, back) VALUES (?, ?, ?, ?)',
            [id, DECK_ID, editors[0].value(), editors[1].value()]);
    })
}

function new_card(id, front_content, back_content)
{
    had_id = typeof(id) !== "undefined";
    id = id || GLOBAL_EDIT_ID;
    
    var $template = $('#template').clone();
    $template.attr('id', 'card' + id);
    $template.find('#front').attr('id', 'front' + id);
    $template.find('#back').attr('id', 'back' + id);
    
    $('body').append($template);

    var editors = [['front', front_content], ['back', back_content]].map(el => {
        var editor = new SimpleMDE({ 
            element: document.getElementById(el[0] + id), 
            status: false,
            autofocus: !had_id && el[0] == 'front',
            // toolbar: false
        });
        editor.codemirror.options.extraKeys['Tab'] = false;
        editor.codemirror.options.extraKeys['Shift-Tab'] = false;

        if (el[1])
        {
            editor.value(el[1]);
        }

        return editor;
    });

    // Autosave callback
    editors.forEach(editor => {
        editor.codemirror.on("change", () => {
            save_card(editors, id);
        });
    });

    GLOBAL_EDIT_ID = id + 1;
    $template.show();

    if (!had_id)
    {
        console.log(id);
        $('body').scrollTo($template, 800); 
    }
}

DATABASE.transaction((trans) => {
    trans.executeSql('SELECT * FROM cards WHERE deck_id = ?;', [DECK_ID], (trans, results) => {
        for (i = 0; i < results.rows.length; ++i){
            var row = results.rows.item(i);
            new_card(row.id, row.front, row.back);
        }
    });
});