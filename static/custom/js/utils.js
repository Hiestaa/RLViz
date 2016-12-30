// A utility function to connecto to a websocket endpoint using sockjs.
// This function will make sure to reopen any unexpectedly closed connection.
// This function takes three parameters:
// * the websocket endpoint as a string, e.g.: `/nlp/subscribe/autotag-report`
// * a callback to be called when the connection is ready and each time the
//   connection is re-opened after an unexpected close.
//   This callback will be given a function that should be called to send a
//   JSON-serializable message over the socket.
// * a callback to be called when a message is pushed from the server.
//   This message will be a json-deserialized object.
// Returns the send function that will also be given to the `onOpen` callback.
function WSConnect(url, onOpen, onMessage) {
    _interrupted = false
    _ready = false
    _conTimer = null;

    var socket = new WebSocket(url);

    var send = function (data) {
        if (_interrupted || !_ready) {
            if (window.alerts)
                alerts.danger("Working to connect with the server. Please try again in a few seconds.");
            console.error("Working to connect with the server. Please try again in a few seconds.");
        }
        else
            socket.send(JSON.stringify(data));
    }

    var api = {
        send: send,
        close: function () {
            socket.close()
        }
    };

    socket.onopen = function () {
        _interrupted = false;
        _ready = true;
        onOpen(api);
    }
    socket.onclose = function (e) {
        _interrupted = true;
        if (_conTimer)
            clearTimeout(_conTimer);
        if (e.code != 1000 /* normal closure */)
            _conTimer = setTimeout(function () {
                WSConnect(url, onOpen, onMessage)
            }, 2000);
    }
    socket.onmessage = function (event) {
        onMessage(JSON.parse(event.data));
    }

    console.log("Opening connection...")
    return api
}
