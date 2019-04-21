
function trymax() {
    var exampleSocket = new WebSocket('wss://127.0.0.1:5000');
    exampleSocket.onmessage = function (event) {
        console.log(event.data);
        console.log('qwe');
    }
    
}