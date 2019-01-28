const TelegramServer = require('telegram-test-api');
let serverConfig = {port: 9000};
let server = new TelegramServer(serverConfig);
server.start();
