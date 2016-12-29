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

    self._currentAlgo = null;
    self._currentProblem = null;

    // param name -> param picker instance
    self._problemParamPickers = {}
    self._algoParamPickers = {}

    self.renderAlgoPick = function (algo) {
        console.log("Rendering algo: ", algo)
        self._currentAlgo = algo;

        self._$algoForm.html('<legend>Tune parameters for ' + algo + '</legend>')

        var params = Object.keys(window.STATIC_DATA.algorithmsParams[algo]);
        self._algoParamPickers = {}  // reset - GC should unload all
        for (var i = 0; i < params.length; i++) {
            var param = params[i]
            self._algoParamPickers[param] = new ParamPicker(
                self._$algoForm,
                param,
                window.STATIC_DATA.algorithmsParams[algo][param],
                window.STATIC_DATA.algorithmsParamsDomain[algo][param],
                window.STATIC_DATA.algorithmsParamsDefault[algo][param],
                window.STATIC_DATA.algorithmsParamsDescription[algo][param]);
        }
    }

    self.renderProblemPick = function (problem) {
        console.log("Rendering problem: ", problem)
        self._currentProblem = problem;

        self._$problemForm.html('<legend>Tune parameters for ' + problem + '</legend>')

        var params = Object.keys(window.STATIC_DATA.problemsParams[problem]);
        self._problemParamPickers = {}  // reset - GC should unload all
        for (var i = 0; i < params.length; i++) {
            var param = params[i]
            self._problemParamPickers[param] = new ParamPicker(
                self._$problemForm,
                param,
                window.STATIC_DATA.problemsParams[problem][param],
                window.STATIC_DATA.problemsParamsDomain[problem][param],
                window.STATIC_DATA.problemsParamsDefault[problem][param],
                window.STATIC_DATA.problemsParamsDescription[problem][param]);
        }
    }

    self.getAlgoParams = function () {

    }

    self.getProblemParams = function () {

    }
}

function ParamPicker($appendTo, id, type, domain, defaultVal, description) {
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

        self._$container = $('<div class="form-group col-md-3 col-sm-4 col-xs-6">' +
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
                if (type == 'Number')
                    value = parseInt(value);
                if (domain.range.length == 2 && value <= domain.range[1] && value >= domain.range[0])
                    return;
                self._selectize.removeOption(value);
            },
            create: type == 'Number',  // string have fixed definite choices
            onFocus: function () {
                self._$container.find('input').css('width', '0px');
            }
        });
        self._selectize = self._$container.find('select')[0].selectize;
        self._$container.find('.parameter-help').tooltip({placement: 'top'})
    }

    self.initialize();
}