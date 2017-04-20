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
        'ValueFunctionInspector': ValueFunctionWidget,
        'EfficiencyInspector': EfficiencyWidget
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
            self._$container, params, {
                onRemove: function () {
                    self.removeInspector(uid, name)
                }
            });
        self._agent.registerInspector(name, uid, params);
    }

    self.removeInspector = function (uid, name) {
        var inspector = self._inspectors[uid]

        self._agent.removeInspector(uid, name, function () {
            delete self._inspectors[uid];
        });

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

    // notifies all inspectors that we're going to train a new agent.
    self.newSession = function (command) {
        for (var uid in self._inspectors) {
            self._inspectors[uid].newSession(command);
        }
    }

    self.initialize();
}

/*
===================> WARNING <================
I'm too lazy to do some kind of inspectors inheritance in javascript.
Yes. Because it shouldn't be as hard as it is with prototype and stuff.
All inspectors should thus follow the same structure as the `ProgressInspector`,
exlusion done of all methods starting with `_`.
Parameters description
* $container: jquery container for all widgets. Widgets should be prepended to
  this container when created
* params: user-defined parameter values provided to create this inspector as a
  key-value mapping. The keys depend on the corresponding python Inspector.
* options: some additional options provided by the inspector manager.
  This includes the following keys:
  * onRemove: function to be called when the widget is remove to forward the
    information to the server so that it destroys the corresponding inspector.
*/
function ProgressWidget($container, params, options) {
    var self = this;

    // parameters are given as a key-value store, keys being the names of the
    // parameters as defined in the corresponding inspector.
    self._params = params;

    // save container, create widget, append to the container
    self._$container = $container;
    self._$widget = $(
        '<div class="col-xs-12 inspector-widget">' +
        '<div class="panel panel-default">' +
        '   <div class="panel-heading">' +
        '       <h3 class="panel-title">Progression</h3>' +
        '       <div class="btn-group" role="group" aria-label="controls">' +
        '           <button type="button" id="delete" class="btn btn-default"><span class="glyphicon glyphicon-remove" aria-hidden="true"></span></button>' +
        '        </div>' +
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
    self._$container.find('#delete').click(function () {
        options.onRemove()
        self._$widget.remove();
    });

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

    /*
    Notifies the inspector widget that a new training session just started.
    `command` is the command sent to the server. See `agent.js`.
    */
    self.newSession = function (command) {
        self._$widget.find('.progress-bar')
            .attr('aria-valuenow', '0')
            .css('width', '0%');
        self._$widget.find('#message').text('Episode 0 / 0 - Return = 0');
    }
}

function ValueFunctionWidget($container, params) {
    var self = this;

    // save container, create widget, append to the container
    self._params = params
    self._$container = $container;
    self._sliders = {};  // contains slider instances
    self._slidersValues = {};  // contains list of ordered unique values each parameter can have
    self._lastMessage = null;

    self._$widget = $('<div class="col-xs-12 col-lg-6"></div>');
    self._$container.prepend(self._$widget)

    self._data3d = null;
    self._options3d = null;
    self._graph3d = null;
    self._graph2d = null;

    // Create and populate a data table.
    self._setup3D = function (xLabel, yLabel) {
        self._$widget.html(
            '<div class="panel panel-default">' +
            '   <div class="panel-heading">' +
            '       <h3 class="panel-title">Value Function (3D)</h3>' +
            '   </div>' +
            '   <div class="panel-body">' +
            '       <div id="plot"></div>' +
            '       <div id="sliders"></div>' +
            '   </div>' +
            '</div>');
        self._data3d = new vis.DataSet();
        var counter = 0;
        var steps = self._params.precision;  // number of datapoints will be steps*steps
        var xStepVal = 2 / steps
        var yStepVal = 1.0 / steps
        var xAxisMax = steps * xStepVal;
        var yAxisMax = steps * yStepVal;
        for (var x = 0; x < xAxisMax; x+=xStepVal) {
            for (var y = 0; y < yAxisMax; y+=yStepVal) {
                self._data3d.add({id:counter++,x:x,y:y,z:0,style:0});
            }
        }
        self._options3d = {
            width:  (self._$widget.width() - 20) + 'px',
            height: ((self._$widget.width() - 20) * 0.7) + 'px',
            style: 'surface',
            showPerspective: true,
            showGrid: true,
            showShadow: false,
            keepAspectRatio: false,
            verticalRatio: 0.5,
            yCenter: '40%',
            xLabel: xLabel || "Unknown Yet",
            yLabel: yLabel || "Unknown Yet",
            zLabel: "Estimated Return"
        };
        var graphContainer = self._$widget.find('#plot')[0];
        self._graph3d = new vis.Graph3d(graphContainer, self._data3d, self._options3d);
        self._graph2d = null;
    }

    self._setup2D = function () {
        self._$widget.html(
            '<div class="panel panel-default">' +
            '   <div class="panel-heading">' +
            '       <h3 class="panel-title">Value Function (2D)</h3>' +
            '   </div>' +
            '   <div class="panel-body">' +
            '       <canvas id="plot"/>' +
            '       <div id="sliders"></div>' +
            '   </div>' +
            '</div>');

        var data = [];
        var counter = 0
        var steps = self._params.precision;  // number of datapoints will be steps*steps
        var xStepVal = 2 / steps
        var xAxisMax = steps * xStepVal;
        for (var x = 0; x < xAxisMax; x+=xStepVal) {
            data.push({x: x, y: 0});
        }

        var options = {}
        var graphContainer = self._$widget.find('#plot')[0];
        self._graph3d = null;
        self._graph2d = new Chart(graphContainer, {
            type: 'line',
            data: {
                datasets: [{
                    label: "Learned Value Function",
                    data: data,
                    borderColor: '#00B6D9',
                    pointColor: '#00B6D9'
                }]
            },
            options: {
                scales: {
                    xAxes: [{
                        type: 'linear',
                        position: 'bottom',
                        scaleLabel: {
                            display: true,
                            labelString: "Unknown Yet"
                        }
                    }],
                    yAxes: [{
                        type: 'linear',
                        position: 'left',
                        scaleLabel:  {
                            display: true,
                            labelString: "Estimated Return (from this state onward)"
                        }
                    }]
                }
            }
        });
    }

    if (self._params.shape == '2D')
        self._setup2D();
    else
        self._setup3D();

    // designed to be called for each message
    // this will discard all sliders not part of the message data, add any that
    // may not be present yet, and do nothing otherwise.
    self._setupSliders = function (message) {
        params = Object.keys(message.low);

        // do we need to delete anything?
        for (var param in self._sliders) {
            // a slider exist for a parameter that is not part of the message
            if (!message.low[param]) {
                // discard all sliders
                self._$widget.find('#sliders').html('');
                self._sliders = {};
                self._slidersValues = {};
                break;
            }

        };

        // now gather all unique values that exist for each parameter
        allValues = {}
        for (var i = 0; i < params.length; i++) {
            var param = params[i];
            if (param == 'x' || param == 'y' || param == 'z')
                continue;
            if (self._$widget.find('#sliders #' + param).length)
                continue;
            allValues[param] = {}
        }
        if (Object.keys(allValues).length == 0)
            return;  // stop if no slider should be added

        for (var i = 0; i < message.data.length; i++) {
            var item = message.data[i];
            for (var prop in item) {
                if (allValues[prop]) {
                    if (allValues[prop][item[prop]])
                        allValues[prop][item[prop]] += item.z
                    else
                        allValues[prop][item[prop]] = item.z
                }
            }
        }
        // need a closure here
        Object.keys(allValues).forEach(function (param) {
            var vals = Object.keys(allValues[param]).map(parseFloat).sort(function (a, b) { return a - b });
            var current = vals.length / 2;
            var min = message.low[param];
            var max = message.high[param];
            var step = message.stepSizes[param];
            var name = message.dimensionNames[param];

            self._$widget.find('#sliders').append(
                '<b>' + name + ': </b>' +
                '<input type="text" class="span12" value="' + current + '" id="' + param + '" ><br/>'
            );
            self._sliders[param] = self._$widget.find('#sliders #' + param).slider({
                min: 0,
                max: vals.length,
                step: 1,
                value: current,
                formater: function (idx) {
                    return vals[Math.min(idx, vals.length)]
                }
            }).on('slide', function () {
                self.dispatch(self._lastMessage, true)
            });
            self._slidersValues[param] = vals;
        });
    }

    self._getFixedParams = function () {
        var fixed = {}
        Object.keys(self._sliders).forEach(function (param) {
            var idx = parseInt(self._sliders[param][0].value);
            fixed[param] = self._slidersValues[param][
                Math.min(idx, self._slidersValues[param].length)];
        });
        return fixed
    }

    // tells the update functions whether a point should be skipped.
    // We'll only plot points that have all their 'param' attributes equal to
    // the given `fixedParams`
    self._shouldSkipPoint = function (messageData, i, fixedParams) {
        for (var param in fixedParams) {
            if (messageData[i][param] != fixedParams[param]) {
                return true;
            }
        }
        return false;
    }

    self._update3D = function (messageData, nbDims, iEpisode, dimensionNames) {
        if (self._options3d.xLabel != dimensionNames.x || self._options3d.yLabel != dimensionNames.y) {
            self._setup3D(dimensionNames.x, dimensionNames.y)
        }
        var update = []
        // TODO: when there is more parameters than what can be displayed
        // we should show sliders to set the value of non-plotted dimensions
        var fixedParams = {}
        if (nbDims > 2) {
            fixedParams = self._getFixedParams();
        }
        var dotsCount = 0
        for (var i = 0; i < messageData.length; i++) {
            if (nbDims > 2 && self._shouldSkipPoint(messageData, i, fixedParams))
                continue;
            var upd = {
                id: dotsCount,
                x: messageData[i].x,
                y: messageData[i].y,
                z: messageData[i].z,
                style: messageData[i].z
            }
            upd[dimensionNames.x] = messageData[i].x;
            upd[dimensionNames.y] = messageData[i].y;
            upd['Estimated Return'] = messageData[i].z
            update.push(upd);
            dotsCount++;
        }
        self._data3d.update(update);
    }


    self._update2D = function (message, nbDims, iEpisode, dimensionNames) {
        var fixedParams = {}
        var messageData = message;
        if (nbDims > 1) {
            fixedParams = self._getFixedParams();
        }
        var data = []
        data = self._graph2d.data.datasets[0].data;
        self._graph2d.data.datasets[0].label = "Learned Value Function (episode " + iEpisode + ")";
        var dotsCount = 0
        for (var i = 0; i < messageData.length; i++) {
            if (nbDims > 1 && self._shouldSkipPoint(messageData, i, fixedParams))
                continue;
            if (dotsCount < data.length) {
                data[dotsCount].x = messageData[i].x;
                data[dotsCount].y = messageData[i].z;
            }
            else {
                data.push({
                    x: messageData[i].x,
                    // if y is provided it bears the second parameter value -
                    // use z instead for the actual return of the value function
                    y: messageData[i].z
                });
            }
            dotsCount++;
            self._graph2d.update();
        };
        if (data.length > dotsCount)
            data = data.slice(0, messageData.length);
        if (messageData.length > 0)
            self._graph2d.options.scales.xAxes[0].scaleLabel.labelString = dimensionNames.x;
        self._graph2d.update();
    }

    self._lastUpdate = null;
    // WARNING: to lower the bandwidth usage, this is also implemented server-side
    self._maxRefreshRate = Math.max(
        self._params.precision * self._params.precision / 5,
        // precision 100 will update every 100 * 100 / 5 = 2000ms = 2s
        // precision 10 will update every 10 * 10 / 5 = 20ms => 100ms
        100);
    self._update = function (messageData, nbDims, iEpisode, dimensionNames, force) {
        // todo: add sliders for param<I>, enable 2D drawing when shape is 2D
        if (!force && self._lastUpdate && new Date() - self._lastUpdate < self._maxRefreshRate) {
            return;  // less than 1 update per seconds to keep reasonable performances
        }
        self._lastUpdate = new Date();
        if (self._params.shape == '3D' && nbDims >= 2)
            self._update3D(messageData, nbDims, iEpisode, dimensionNames);
        else if (self._params.shape == '2D')
            self._update2D(messageData, nbDims, iEpisode, dimensionNames);
        else
            console.error("Invalid Number of dimension for " + self._params.shape + " graph: ", nbDims);
    }
    /*
    Dispatch a message to this widget.
    It is expected that the message holds the following fields:
    * nbDims: number of dimensions of the value function. This is the number of
      dimensions of the state spaces.
    * data: list of dicts, each holding the following fields:
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
    self.dispatch = function (message, force) {
        self._lastMessage = message;
        self._setupSliders(message);
        self._update(message.data, message.nbDims, message.iEpisode, message.dimensionNames, force);
    }

    self.newSession = function (command) {
        if (self._params.shape == '2D')
            self._setup2D();
        else
            self._setup3D();
    }
}

function EfficiencyWidget($container, params) {
    var self = this;

    // parameters are given as a key-value store, keys being the names of the
    // parameters as defined in the corresponding inspector.
    self._params = params;
    // save container, create widget, append to the container
    self._$container = $container;
    self._$widget = $('<div class="col-xs-12 col-lg-6"></div>');
    self._$container.prepend(self._$widget);
    self._nbRuns = 0
    self._runColors = [
        '#0021E5',
        // '#003FE3',
        // '#005DE1',
        '#007BDF',
        // '#0098DD',
        // '#00B4DB',
        '#00D0D9',
        // '#00D7C1',
        // '#00D5A3',
        '#00D384',
        // '#00D167',
        // '#00CF49',
        '#00CD2D',
        // '#00CB11',
        // '#0AC900',
        '#25C700',
        // '#3FC500',
        // '#59C300',
        '#73C100',
        // '#8BBF00'
    ];

    self._setup = function () {
        self._nbRuns = 0;
        self._$widget.html(
            '<div class="panel panel-default">' +
            '   <div class="panel-heading">' +
            '       <h3 class="panel-title">Training Efficiency (' + self._params.metric + ' per episode)</h3>' +
            '   </div>' +
            '   <div class="panel-body">' +
            '       <canvas id="plot"/>' +
            '       <div id="sliders"></div>' +
            '   </div>' +
            '</div>');

        var graphContainer = self._$widget.find('#plot')[0];

        self._graph2d = new Chart(graphContainer, {
            type: 'line',
            data: {
                datasets: []
            },
            options: {
                scales: {
                    xAxes: [{
                        type: 'linear',
                        position: 'bottom',
                        scaleLabel: {
                            display: true,
                            labelString: "Episodes"
                        }
                    }],
                    yAxes: [{
                        type: 'linear',
                        position: 'left',
                        scaleLabel: {
                            display: true,
                            labelString: '# of ' + self._params.metric
                        }
                    }]
                }
            }
        });
    }

    self._setup();


    self._addDataset = function () {
        self._graph2d.data.datasets.push({
            label: self._params.metric + ' per episode (run ' + (self._nbRuns + 1) + ')' ,
            data: [],
            borderColor: self._runColors[self._nbRuns],
            pointColor: self._runColors[self._nbRuns],
            borderWidth: 1,
            pointBorderWidth: 1,
            pointRadius: 1
        });
        self._graph2d.update();
        self._nbRuns++;
    }

    self._getMetricData = function (message, metric) {
        var mapping = {
            'Return': 'episodeReturn',
            'Steps': 'episodeSteps',
            'Time': 'episodeDuration'
        }
        return message[mapping[metric] || 'episodeSteps'];
    }

    /*
    Dispatch a message to this widget.
    It is expected that the message holds the following fields:
    * pcVal: Percentage value of the progression, range [0-100],
    * iEpisode: i-th episode of the run,
    * nEpisodes: total number of episodes this run,
    * episodeReturn: total return for the i-th episode
    * episodeSteps: total number of steps in the i-th episode
    * episodeDuration: total time it took to generate this episode.
    */
    self.dispatch = function (message) {
        if (!self._graph2d.data.datasets[self._nbRuns - 1]) {
            self._addDataset();  // add a dataset if we don't have one yet
        }
        self._graph2d.data.datasets[self._nbRuns - 1].data.push({
            x: message.iEpisode,
            y: self._getMetricData(message, self._params.metric)
        });
        self._graph2d.update();
    }

    self.newSession = function (command) {
        if (self._params.reset)
            self._setup();
        self._addDataset();
    }
}