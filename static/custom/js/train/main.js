function TrainComponent($container) {
    var self = this;

    self._$container = $container;

    self._selectizeProblem = null;
    self._selectizeAlgo = null;

    self._agent = new Agent();

    self._createAlgosOptions = function () {
        return self._$container.find('#select-algorithm option').map(function () {
            return {
                'value': $(this).attr('value'),
                'description': $(this).data('description'),
                'stateSpace': $(this).data('state-space'),
                'actionSpace': $(this).data('action-space')
            }
        });
    }
    self._createProblemsOptions = function () {
        return self._$container.find('#select-problem option').map(function () {
            return {
                'value': $(this).attr('value'),
                'description': $(this).data('description'),
                'stateSpace': $(this).data('state-space'),
                'actionSpace': $(this).data('action-space')
            }
        });
    }

    self._renderItem = function (item, escale) {
        return '<div>' +
            '<span class="value">' + item.value + '</span>' +
            '<span class="description">' + item.description.split('\n').filter(function (item) { return item.length }).join('<br />') + '</span>' +
            '<span class="state-space">' + item.stateSpace + '</span>' +
            '<span class="action-space">' + item.actionSpace + '</span>' +
            '</div>';
    }

    self._onPickProblem = function (item) {
        self._hyperParametersOverride.renderProblemPick(item);
    }

    self._onPickAlgo = function (item) {
        self._hyperParametersOverride.renderAlgoPick(item);
    }

    self.initialize = function () {
        self._hyperParametersOverride = new HyperParametersPick(self._$container.find('#hyper-parameters-override'))
        var problemOptions =  self._createProblemsOptions();
        self._$container.find('#select-problem').selectize({
            options: problemOptions,
            render: {
                option: self._renderItem,
                item: self._renderItem
            },
            onItemAdd: self._onPickProblem
        });
        self._selectizeProblem = self._$container.find('#select-problem')[0].selectize;
        var algoOptions = self._createAlgosOptions();
        self._$container.find('#select-algorithm').selectize({
            options: algoOptions,
            render: {
                option: self._renderItem,
                item: self._renderItem
            },
            onItemAdd: self._onPickAlgo
        })
        self._selectizeAlgo = self._$container.find('#select-algorithm')[0].selectize;

        self._hyperParametersOverride.renderProblemPick(problemOptions[0].value);
        self._hyperParametersOverride.renderAlgoPick(algoOptions[0].value);
        self._hyperParametersOverride.renderAgentPick();

        // selectize weird display hack
        $('.selectize-input input')
            .css('opacity', '0')
            .css('position',  'absolute')
            .css('left', '-10000px;');

        self._$container.find('#submit').click(self.onTrain);
    };

    // called when clicking on the 'train' button;
    self.onTrain = function () {
        self._agent.train(
            self._selectizeProblem.getValue(),
            self._hyperParametersOverride.getProblemParams(),
            self._selectizeAlgo.getValue(),
            self._hyperParametersOverride.getAlgoParams(),
            self._hyperParametersOverride.getAgentParams());
    }

    self.initialize()
}

