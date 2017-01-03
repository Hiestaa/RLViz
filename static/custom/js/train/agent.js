/*
The agent is the proxy object for communication with the agent training websocket
handler, server side.
It handles the communication protocols and dispatch messages sent by the server
to the corresponding inspector.
*/

function Agent($inspectorsPanel) {
    var self = this;

    // stores all user-defined data for problem, algo and agent
    // required to re-create the whole env upon disconnect
    self._problemName = null;
    self._problemParams = null;
    self._algoName = null;
    self._algoParams = null;
    self._agentParams = null;
    // stores data for created inspector name and user-defined parameters
    // inspector name + ':' + inspector uid
    //      -> inspector picked param name
    //          -> inspector picked param value
    self._inspectorParams = {};
    self._inspectorsManager = new InspectorsManager($inspectorsPanel, self);
    self._connection = null;

    self.initialize = function () {
        WSConnect(
            'ws://localhost:8888/subscribe/train',
            self._onOpen, self._onMessage, self._onClose);
    }

    self._onOpen = function (connection) {
        if (self._connection != null) {
            alerts.hide();
            alerts.success("Sucessfully reconnected! Inspectors will be re-created server-side, but any on-going training process will have to be restarted.")
        }
        self._connection = connection;
        console.log("Connection opened");

        // register all inspectors again
        for (var key in self._inspectorParams) {
            var name = key.split(':')[0];
            var uid = key.split(':')[1];
            var params = self._inspectorParams[key];
            self.registerInspector(name, uid, params);
        }
    }

    self._onClose = function () {
        alerts.danger("Connection Interrupted. Attempting to reconnect...");
    }

    self._onMessage = function (message) {
        routes = {
            'inspect': self._inspectorsManager.dispatch
        }
        if (message.route && routes[message.route])
            return routes[message.route](message);

        console.error("Route " + route + " not found.", message);
    }

    self._waitForConnect = function (fn) {
        return function () {
            if (self._connection == null || !self._connection.isReady()) {
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

        self._inspectorsManager.newSession(command);
        self._connection.send(command);
    });

    self.registerInspector = self._waitForConnect(function (name, uid, params) {
        var key = name + ':' + uid
        self._inspectorParams[key] = params;

        var command = {
            'command': 'registerInspector',
            'name': name,
            'uid': uid,
            'params': params
        }
        console.log("Command: ", command);
        self._connection.send(command);
    });

    self.initialize();
}