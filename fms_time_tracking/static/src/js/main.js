 odoo.define('fms_time_tracking.main', function (require) {
"use strict";

var FormController = require('web.FormController');

FormController.include({

    _onButtonClicked: function (event) {
         if(event.data.attrs.mode === "action_time_check"){
             var self = this;
             if ("geolocation" in navigator){
                navigator.permissions.query({name:'geolocation'}).then(function(result) {
                    // result.state Will return ['granted', 'prompt', 'denied']
                    if (result.state != 'denied'){
                        navigator.geolocation.getCurrentPosition(function(position) {
                            self.update_time_check(event, position.coords.latitude, position.coords.longitude);
                        });
                    } else {
                        self.update_time_check(event, '', '');
                    }
                });
             }
         } else {
            this._super(event);
         }
     },

    update_time_check: function (event, latitude, longitude) {
        var self = this;
        this._rpc({
            model: 'fms.freight',
            method: 'action_time_check',
            args: [event.data.record.data.id, latitude, longitude],
        })
            .then(function(result) {
                if (result.action) {
                    self.trigger_up('reload');
                } else if (result.warning) {
                    self.do_warn(result.warning);
                }
            });
    },
});

});
