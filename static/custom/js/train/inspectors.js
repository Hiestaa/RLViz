/*
Manages the creation of inspectors and dispatch of events to proper inspector.
*/
function InspectorsManager($container, agent) {
    var self = this;

    self._agent = agent;
    self._$container = $container
    self._$selector = null;
    self._selectizeName = null;
    // param name -> ParamPicker instance
    self._paramPickers = {}

    // inspector name -> widget class
    self._inspectorWidgets = {
        'ProgressInspector': ProgressWidget,
        'ValueFunctionInspector': ValueFunctionWidget
    }

    // uid -> Inspector instance
    self._inspectors = {}

    self._uidSeed = 0
    self.uid = function () {
        self._uidSeed += 1;
        return self._uidSeed;
    }

    self.initialize = function () {
        self.setupSelector();
    }

    // renders the inspector selector at the bottom of the container.
    self.setupSelector = function () {
        self._$selector = $(
            '<div class="col-xs-12">' +
            '<div class="panel panel-default">' +
            '   <div class="panel-heading">' +
            '       <h3 class="panel-title">Add Inspector</h3>' +
            '   </div>' +
            '   <div class="panel-body">' +
            '       <div class="col-xs-12 col-sm-4 col-lg-3 form-group">' +
            '           <label for="select-inspector">Select Inspector</label>' +
            '           <select id="select-inspector"></select>' +
            '       </div>' +
            '       <div class="col-xs-12"></div>' +
            '       <div class="row" id="inspector-parameters"></div>' +
            '       <div class="col-xs-12"></div>' +
            '       <div style="float: right">' +
            '           <button class="btn btn-default" id="submit">Submit</button>' +
            '       </div>' +
            '    </div>' +
            '</div></div>').appendTo(self._$container);
        self._$selector.find('#select-inspector').selectize({
            options: STATIC_DATA.inspectors.map(function (item) {
                return {value: item, text: item}
            }),
            onItemAdd: self.onPickInspector,
            onClean: self.onClearInspector,
            onDelete: self.onClearInspector,
            placeholder: 'Inspector (required)'
        });
        self._selectizeName = self._$selector.find("#select-inspector")[0].selectize;
        self._$selector.find('#submit').click(self.onSubmitInspector);
    }

    // setup ParamPicker instances for the parameters of the
    // given inspector
    self.setupParams = function (name) {
        var params = Object.keys(STATIC_DATA.inspectorsParams[name]);
        var $inspectorParameters = self._$selector.find('#inspector-parameters');
        self._paramPickers = {};
        for (var i = 0; i < params.length; i++) {
            var paramName = params[i]
            self._paramPickers[paramName] = new ParamPicker(
                $inspectorParameters,
                paramName,
                STATIC_DATA.inspectorsParams[name][paramName],
                STATIC_DATA.inspectorsParamsDomain[name][paramName],
                STATIC_DATA.inspectorsParamsDefault[name][paramName],
                STATIC_DATA.inspectorsParamsDescription[name][paramName]);
        }
    }

    self.resetSelector = function () {
        self._selectizeName.clear();
    }

    self.addInspector = function (name, params) {
        if (!self._inspectorWidgets[name])
            return console.error("Inspector Widget " + name + " not implemented yet.")
        var uid = self.uid();
        self._inspectors[uid] = new self._inspectorWidgets[name](
            self._$container, params);
        self._agent.registerInspector(name, uid, params);
    }


    self.onSubmitInspector = function () {
        var name = self._selectizeName.getValue();
        if (!name.trim().length)
            return console.error("Pick an inspector first");
        var paramNames = Object.keys(self._paramPickers);
        var params = {};
        for (var i = 0; i < paramNames.length; i++) {
            params[paramNames[i]] = self._paramPickers[paramNames[i]].getValue();
        }
        self.addInspector(name, params);
    }

    self.onPickInspector = function (name) {
        self._$selector.find('#inspector-parameters').html('');
        self.setupParams(name);
    }

    self.onClearInspector = function () {
        console.log("Clearing parameters section");
        self._$selector.find('#inspector-parameters').html('');
    }

    // dispatch a message intented to an inspector widget to the proper widget
    // all messages should be dispatched. If the uid doesn't match any existing
    // widget, it will simply be ignored.
    self.dispatch = function (message) {
        if (!self._inspectors[message.uid])
            return
        self._inspectors[message.uid].dispatch(message);
    }

    self.initialize();
}

/*
===================> WARNING <================
I'm too lazy to do some kind of inspectors inheritance in javascript.
Yes. Because it shouldn't be as hard as it is with prototype and stuff.
All inspectors should thus follow the same structure as the `ProgressInspector`,
exlusion done of all methods starting with `_`.
*/
function ProgressWidget($container, params) {
    var self = this;

    // parameters are given as a key-value store, keys being the names of the
    // parameters as defined in the corresponding inspector.
    self._params = params;
    // save container, create widget, append to the container
    self._$container = $container;
    self._$widget = $(
        '<div class="col-xs-12">' +
        '<div class="panel panel-default">' +
        '   <div class="panel-heading">' +
        '       <h3 class="panel-title">Progression</h3>' +
        '   </div>' +
        '   <div class="panel-body">' +
        '       <div class="progress">' +
        '            <div class="progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%;">0%' +
        '            </div>' +
        '        </div>' +
        '        <p id="message">Waiting for message from training progress inspector...</p>' +
        '   </div>' +
        '</div>')
    self._$container.prepend(self._$widget);

    /*
    Dispatch a message to this widget.
    It is expected that the message holds the following fields:
    * pcVal: Percentage value of the progression, range [0-100],
    * iEpisode: i-th episode of the run,
    * nEpisodes: total number of episodes this run,
    * episodeReturn: total return for the i-th episode
    */
    self.dispatch = function (message) {
        self._$widget.find('.progress-bar')
            .attr('aria-valuenow', message.pcVal)
            .css('width', message.pcVal + '%')
            .text(message.pcVal + '%');
        self._$widget.find('#message').text(
            'Episode ' + message.iEpisode + ' / ' + message.nEpisodes +
            ' - Return = ' + message.episodeReturn);
    }
}

function ValueFunctionWidget($container, params) {
    var self = this;

    // save container, create widget, append to the container
    self._params = params
    self._$container = $container;
    self._$widget = $(
        '<div class="col-xs-12 col-lg-6">' +
        '<div class="panel panel-default">' +
        '   <div class="panel-heading">' +
        '       <h3 class="panel-title">Value Function</h3>' +
        '   </div>' +
        '   <div class="panel-body">' +
        '       <div id="plot">' +
        '   </div>' +
        '</div>');
    self._$container.prepend(self._$widget);

    // Create and populate a data table.
    self._data = new vis.DataSet();
    var counter = 0;
    var steps = self._params.precision;  // number of datapoints will be steps*steps
    var xStepVal = 2 / steps
    var yStepVal = 1.0 / steps
    var xAxisMax = steps * xStepVal;
    var yAxisMax = steps * yStepVal;
    for (var x = 0; x < xAxisMax; x+=xStepVal) {
        for (var y = 0; y < yAxisMax; y+=yStepVal) {
            self._data.add({id:counter++,x:x,y:y,z:0,style:0});
        }
    }
    var options = {
        width:  (self._$widget.width() - 20) + 'px',
        height: ((self._$widget.width() - 20) * 0.7) + 'px',
        style: 'surface',
        showPerspective: true,
        showGrid: true,
        showShadow: false,
        keepAspectRatio: false,
        verticalRatio: 0.5,
        yCenter: '40%'
    };
    var graphContainer = document.getElementById('plot');
    self._graph3d = new vis.Graph3d(graphContainer, self._data, options);
    self._graph2d = null;

    self._lastUpdate = null;
    self._maxRefreshRate = self._params.precision * self._params.precision;
    self._update = function (messageData) {
        // todo: add sliders for param<I>, enable 2D drawing when shape is 2D
        if (self._lastUpdate && new Date() - self._lastUpdate < self._maxRefreshRate) {
            return;  // less than 1 update per seconds to keep reasonable performances
        }
        self._lastUpdate = new Date();
        var update = []
        self._t += 1;
        for (var i = 0; i < messageData.length; i++) {
            update.push({
                id: i,
                x: messageData[i].x,
                y: messageData[i].y,
                z: messageData[i].z,
                style: messageData[i].z
            });
        }
        self._data.update(update);
    }
    /*
    Dispatch a message to this widget.
    It is expected that the message holds the following fields:
    * data: list of dicts,
    * `x`: position on the x axis, this is the dimension 0 of the
      state space
    * [`y`: position on the y axis, only if `shape` is `3D`. This is
       the dimension 1 of the state space, and will shift all dimension
       numbers indicated below by 1 if present]
    * `z`: corresponding value of the action value function for all other
      parameters.
    * `param<I>`: starting at 1, value of the ith dimension of the sample
      of the state space (or (i+1)th dimension if plotting in 3D).
    */
    self.dispatch = function (message) {
        self._update(message.data);
    }
}