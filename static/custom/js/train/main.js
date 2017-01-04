function TrainComponent($container) {
    var self = this;

    self._$container = $container;

    self._selectizeProblem = null;
    self._selectizeAlgo = null;

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
            // .css('opacity', '0')
            .css('position',  'absolute')
            .css('left', '-10000px;');

        self._agent = new Agent(self._$container.find('#inspectors-panel'), {
            error: self.onError,
            success: self.onSuccess
        });

        self._$container.find('#submit').click(self.onTrain);
        self._$container.find('#interrupt').click(self.onInterrupt);
    };

    // called when clicking on the 'train' button that should start the
    // training of the agent and reveal the 'interrupt' button
    self._lastTrain = new Date();
    self.onTrain = function () {
        if (new Date() - self._lastTrain < 500)
            return;  // ignore any double query in less than 500ms
        self._agent.train(
            self._selectizeProblem.getValue(),
            self._hyperParametersOverride.getProblemParams(),
            self._selectizeAlgo.getValue(),
            self._hyperParametersOverride.getAlgoParams(),
            self._hyperParametersOverride.getAgentParams());
        self._$container.find('#submit').toggleClass('hidden')
        self._$container.find('#interrupt').toggleClass('hidden')
    }

    // called when clicking on the 'interrupt' button that should interrupt any
    // ongoing progress and reveal the 'train' button back.
    self.onInterrupt = function () {
        if (new Date() - self._lastTrain < 500)
            return;  // ignore any double query in less than 500ms
        self._agent.interrupt();
        self._$container.find('#submit').toggleClass('hidden')
        self._$container.find('#interrupt').toggleClass('hidden')
    }

    // called when an error occurs during the agent training
    self.onError = function (message) {
        if (self._$container.find('#submit').hasClass('hidden')) {
            self._$container.find('#submit').toggleClass('hidden')
            self._$container.find('#interrupt').toggleClass('hidden')
        }
        alerts.danger(message.message);
    }

    // called when the agent training succeeds
    self.onSuccess = function (message) {
        if (self._$container.find('#submit').hasClass('hidden')) {
            self._$container.find('#submit').toggleClass('hidden')
            self._$container.find('#interrupt').toggleClass('hidden')
        }
        alerts.success(message.message);
    }

    self.initialize()
}

