odoo.define(
    "helpdesk_split_ticket/static/src/components/message/message.js",
    function (require) {
        const patchMixin = require("web.patchMixin");
        const PatchableMessage = patchMixin(
            require("mail/static/src/components/message/message.js")
        );
        const MessageList = require("mail/static/src/components/message_list/message_list.js");

        PatchableMessage.patch("glodo_helpdesk_split_ticket.SplitTicket", (T) => {
            class SplitTicket extends T {
                _onClickSplitTicket() {
                    const action = {
                        type: "ir.actions.act_window",
                        name: this.env._t("Split message to new ticket"),
                        res_model: "split.ticket.wizard",
                        view_mode: "form",
                        views: [[false, "form"]],
                        target: "new",
                        context: {
                            default_message_id: this.message.id,
                        },
                        res_id: false,
                    };

                    this.env.bus.trigger("do-action", {
                        action,
                        options: {
                            on_close: () => {
                                this.trigger("reload", {keepChanges: true});
                            },
                        },
                    });
                }
            }
            return SplitTicket;
        });
        MessageList.components.Message = PatchableMessage;
    }
);
