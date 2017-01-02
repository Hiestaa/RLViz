/*
When initialized in a specific container, this object is able to display
the value picker of the right type (usually selectize instances) for each
tunable hyper parameter of the existing problems and algorithms.
The instance is bound to `STATIC_DATA` to gather the domain, default values
and type of data the parameter expect.

API:
* `renderAlgoPick(algo)`: renders the controls for the given algorithm
* `renderProblemPick(problem)`: renders the controls for the given problem
* `getAlgoParams()`: gather control values and return an object where keys
  are hyperparameter names and values are user-defined values (or the default
  ones if these haven't been touched)
* `getProblemParams()`: same as `getAlgoParams()`, for the last rendered problem
*/
function HyperParametersPick($container) {
    var self = this;

    self._$container = $container;

    self._$container.html(
        '<div class="col-xs-12" id="problem-parameters"></div><div class="col-xs-12" id="algorithm-parameters"></div>')
    self._$problemForm = $('<form></form>').appendTo(self._$container.find('#problem-parameters'));
    self._$algoForm = $('<form></form>').appendTo(self._$container.find('#algorithm-parameters'));
    self._$agentForm = $('<form></form>').appendTo(self._$container.find('#algorithm-parameters'));

    self._currentAlgo = null;
    self._currentProblem = null;

    // param name -> param picker instance
    self._problemParamPickers = {}
    self._algoParamPickers = {}
    self._agentParamPickers = {}

    self._renderPickers = function (paramsTypes, paramsDomain, paramsDefault, paramsDescription, $form) {
        var params = Object.keys(paramsTypes);
        var store = {}
        for (var i = 0; i < params.length; i++) {
            var param = params[i]
            store[param] = new ParamPicker(
                $form,
                param,
                paramsTypes[param],
                paramsDomain[param],
                paramsDefault[param],
                paramsDescription[param]);
        }
        return store;
    }

    self._getValues = function (paramPickers) {
        var params = Object.keys(paramPickers);
        var values = {}
        for (var i = 0; i < params.length; i++) {
            values[params[i]] = paramPickers[params[i]].getValue();
        }
        return values;
    }

    self.renderAlgoPick = function (algo) {
        self._currentAlgo = algo;

        self._$algoForm.html('<legend>Tune parameters for ' + algo + '</legend>')

        self._algoParamPickers = self._renderPickers(  // reset - GC should unload all
            window.STATIC_DATA.algorithmsParams[algo],
            window.STATIC_DATA.algorithmsParamsDomain[algo],
            window.STATIC_DATA.algorithmsParamsDefault[algo],
            window.STATIC_DATA.algorithmsParamsDescription[algo],
            self._$algoForm);
    }

    self.renderProblemPick = function (problem) {
        self._currentProblem = problem;

        self._$problemForm.html('<legend>Tune parameters for ' + problem + '</legend>')

        self._problemParamPickers = self._renderPickers(  // reset - GC should unload all
            window.STATIC_DATA.problemsParams[problem],
            window.STATIC_DATA.problemsParamsDomain[problem],
            window.STATIC_DATA.problemsParamsDefault[problem],
            window.STATIC_DATA.problemsParamsDescription[problem],
            self._$problemForm);
    }

    self.renderAgentPick = function () {
        self._$agentForm.html('<legend>Tune parameters for agent</legend>')

        self._agentParamPickers = self._renderPickers(  // reset - GC should unload all
            window.STATIC_DATA.agentParams,
            window.STATIC_DATA.agentParamsDomain,
            window.STATIC_DATA.agentParamsDefault,
            window.STATIC_DATA.agentParamsDescription,
            self._$agentForm);
    }

    self.getAlgoParams = function () {
        return self._getValues(self._algoParamPickers);
    }

    self.getProblemParams = function () {
        return self._getValues(self._problemParamPickers);
    }

    self.getAgentParams = function () {
        return self._getValues(self._agentParamPickers);
    }
}

function ParamPicker($appendTo, id, type, domain, defaultVal, description, widthCssClass) {
    var self = this;

    domain = {
        values: domain.values || [],
        range: domain.range || []
    }

    self._selectize = null;
    self._$container = null;

    self.initialize = function () {
        var placeholder = '(range [' + domain.range.join('-') + '])';
        if (domain.range.length != 2)
            placeholder = 'Pick from the list';

        var width = widthCssClass || 'col-md-3 col-sm-4 col-xs-6 col-lg-2'

        self._$container = $('<div class="form-group' + width + '">' +
            '<label for="' + id + '">' + id +
            '<span class="glyphicon glyphicon-question-sign parameter-help" data-toggle="tooltip" title="' + description + '">' +
            '</span></label>' +
            '<select class="form-control" id="' + id + '" placeholder="' + id + ' ' + placeholder + '">' +
            '</select>' +
            '</div>').appendTo($appendTo);
        self._$container.find('select').selectize({
            options: domain.values.concat([defaultVal]).map(function (val) {
                return {value: val, text: val};
            }),
            items: [defaultVal],
            onOptionAdd: function (value, data) {
                if (type == 'String')
                    return;
                if (domain.values.indexOf(value) >= 0)
                    return;
                if (type == 'Number')
                    value = parseFloat(value);
                if (domain.range.length == 2 && value <= domain.range[1] && value >= domain.range[0])
                    return;
                self._selectize.removeOption(value);
            },
            // string have fixed definite choices
            // one can only create new entries for numbers for which we have a
            // definite allowed range value
            create: type == 'Number' && domain.range.length == 2,
            onFocus: function () {
                self._$container.find('input').css('width', '0px');
            }
        });
        self._selectize = self._$container.find('select')[0].selectize;
        self._$container.find('.parameter-help').tooltip({placement: 'top'})
        self._$container.find('input').css('width', '0px');
    }

    self.getValue = function () {
        var value = self._selectize.getValue()
        if (type == 'Number' && domain.values.indexOf(value) == -1)
            return parseFloat(value)
        return value;
    }

    self.initialize();
}