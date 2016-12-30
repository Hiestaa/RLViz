/*
The agent is the proxy object for communication with the agent training websocket
handler, server side.
It handles the communication protocols and dispatch messages sent by the server
to the corresponding inspector.
*/

function Agent() {
    var self = this;

    self._problemName = null;
    self._problemParams = null;
    self._algoName = null;
    self._algoParams = null;
    self._agentParams = null;

    self._connection = null;

    self.initialize = function () {
        WSConnect(
            'ws://localhost:8888/subscribe/train', self._onOpen, self._onMessage);
    }

    self._onOpen = function (connection) {
        self._connection = connection;
        console.log("Connection (re)opened");
    }

    self._onMessage = function (message) {
        console.log('Message: ', message);
    }

    self._waitForConnect = function (fn) {
        return function () {
            if (self._connection == null) {
                console.log('Agent command suspended.  Waiting for connection, will retry in 1s...');
                return setTimeout(self._waitForConnect(fn), 1000);
            }
            fn.apply(null, arguments);
        }
    }

    self.train = self._waitForConnect(function (problemName, problemParams, algoName, algoParams, agentParams) {
        self._problemName = problemName;
        self._problemParams = problemParams;
        self._algoName = algoName;
        self._algoParams = algoParams;
        self._agentParams = agentParams;

        var command = {
            'command': 'train',
            'algorithm': {
                'name': self._algoName,
                'params': self._algoParams
            },
            'problem': {
                'name': self._problemName,
                'params': self._problemParams
            },
            'agent': {
                'params': self._agentParams
            }
        };
        console.log("Command: ", command);

        self._connection.send(command);
    });

    self.initialize();
}