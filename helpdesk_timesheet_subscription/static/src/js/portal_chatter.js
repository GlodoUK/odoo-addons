odoo.define("logtime.portal.chatter", function (require) {
    "use strict";

    var portalChatter = require("portal.chatter");
    var PortalChatter = portalChatter.PortalChatter;

    PortalChatter.include({
        preprocessMessages: function () {
            const messages = this._super.apply(this, arguments);
            _.each(messages, (message) => {
                const published_date_str = message.published_date_str;
                const float_time_logged = message.time_logged;
                if (
                    typeof float_time_logged === "number" &&
                    !Number.isNaN(float_time_logged)
                ) {
                    var hours = Math.floor(float_time_logged);
                    var minutes = Math.round(
                        (Math.floor((float_time_logged % 1) * 100) / 100) * 60
                    );
                    while (minutes.toString().length < 2) {
                        minutes = "0" + minutes;
                    }
                    while (hours.toString().length < 1) {
                        hours = "0" + hours;
                    }
                    message.published_date_str = `${published_date_str}
                        (Logged time ${hours}:${minutes})`;
                }
            });
            return messages;
        },
    });
});
