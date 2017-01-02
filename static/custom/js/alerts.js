/*
API allowing easy manipulation to the alerts
The `alerts` object provides the functions:
    * danger(msg, timeout): display the danger message during the given timeout
    * warning(msg, timeout): display the warning message during the given timeout
    * info(msg, timeout): display the info message during the given timeout
    * success(msg, timeout): display the success message during the given timeout
*/
$(function () {
    var types = ['danger', 'warning', 'info', 'success']
    alerts = {
        tags: {
            divs: {},
            content: {}
        },
        timeout_ids: {},
        default_timeout: 10000,
        hide: function () {
            for (var i = 0; i < types.length; i++) {
                var type = types[i]
                alerts.tags.divs[type].hide();
                alerts.tags.content[type].html('')
                clearTimeout(alerts.timeout_ids[type]);
                alerts.timeout_ids[type] = null;
            };
        }
    }

    // initialization: for each available alert type
    for (var i = 0; i < types.length; i++) {
        // initialize the type
        alerts.tags.divs[types[i]] = $('#module-alerts #' + types[i] + '-alert')
        alerts.tags.content[types[i]] = $('#module-alerts #' + types[i] + '-msg')

        // set timeout ids to null
        alerts.timeout_ids[types[i]] = null

        // create the corresponding function
        f = function (type) {
            alerts[type] = function (msg, timeout) {
                // default timeout parameter
                if (timeout === undefined)
                    timeout = alerts.default_timeout;

                // clear last timeout set for this alert type
                if (alerts.timeout_ids[type])
                    clearTimeout(alerts.timeout_ids[type]);

                // display the alert
                alerts.tags.content[type].html(msg);
                alerts.tags.divs[type].show();

                // set timeout to close
                alerts.timeout_ids[type] = setTimeout(function () {
                    alerts.tags.divs[type].hide();
                }, timeout);
            }
        }
        f(types[i])
    };

});
