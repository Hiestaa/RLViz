/*
The agent is the proxy object for communication with the agent training websocket
handler, server side.
It handles the communication protocols and dispatch messages sent by the server
to the corresponding inspector.
*/

function Agent($inspectorsPanel, callbacks) {
    var self = this;

    self._errorCb = (callbacks || {}).error;
    self._successCb = (callbacks || {}).success;
    self._disconnectCb = (callbacks || {}).disconnect;

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
        var progressInspectorAdded = false;
        // register all inspectors again
        for (var key in self._inspectorParams) {
            var name = key.split(':')[0];
            var uid = key.split(':')[1];
            var params = self._inspectorParams[key];
            self.registerInspector(name, uid, params);
            if (name == 'ProgressInspector')
                progressInspectorAdded = true;
        }
        if (!progressInspectorAdded)
            self._inspectorsManager.addInspector('ProgressInspector', {frequency: 1000});
    }

    self._onClose = function () {
        alerts.danger("Connection Interrupted. Attempting to reconnect...");
        self._disconnectCb()
    }

    self._onMessage = function (message) {
        routes = {
            'inspect': self._inspectorsManager.dispatch,
            'error': self._errorCb,
            'success': self._successCb
        }
        if (message.route && routes[message.route])
            return routes[message.route](message);

        console.error("Route " + message.route + " not found.", message);
    }

    // Protect the given function `fn` by making sure a connection will be available
    // before executing the call.
    // This means that the call may be delayed until the connection is available
    // The returned function will have the same signature as the given one,
    // but will accept one optional additional parameter that, if provided,
    // should be a function that will be called once the function `fn` given
    // as parameter has actually been called.
    // FIXME: after we retry, we lose the arguments!!
    self._waitForConnect = function (fn, argsCache) {
        return function () {
            var args = [];
            argsCache = arguments.length ? arguments : argsCache;
            if (self._connection == null || !self._connection.isReady()) {
                console.log('Agent command suspended. Waiting for connection, will retry in 1s...');
                return setTimeout(self._waitForConnect(fn, argsCache), 1000);
            }
            for (var i = 0; i < argsCache.length; i++) {
                args.push(argsCache[i]);
            }
            if (typeof args.slice(-1)[0] == "function") {
                fn.apply(null, args.slice(0, -1));
                args.slice(-1)[0](); // done()
            }
            else {
                fn.apply(null, args);
            }
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

    self.interrupt = self._waitForConnect(function() {
        var command = {
            'command': 'interrupt'
        }
        self._connection.send(command);
    })

    self.registerInspector = self._waitForConnect(function (name, uid, params) {
        var key = name + ':' + uid
        // TODO: wait fot confirmation before actually adding the inspector
        self._inspectorParams[key] = params;

        var command = {
            'command': 'registerInspector',
            'name': name,
            'uid': uid,
            'params': params
        }
        self._connection.send(command);
    });

    self.removeInspector = self._waitForConnect(function (uid, name) {
        var key = name + ':' + uid

        // TODO: wait fot confirmation before actually removing the inspector
        if (self._inspectorParams[key])
            delete self._inspectorParams[key]

        var command = {
            'command': 'removeInspector',
            'uid': uid,
        }
        self._connection.send(command);
    });

    self.initialize();
}