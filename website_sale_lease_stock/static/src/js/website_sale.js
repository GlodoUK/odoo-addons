odoo.define("website_sale_lease_stock.website_sale", function (require) {
    "use strict";

    var ajax = require("web.ajax");
    var publicWidget = require("web.public.widget");

    // Needed to ensure we load after website_sale
    require("website_sale.website_sale");
    var events = publicWidget.registry.WebsiteSale.prototype.events || {};

    publicWidget.registry.WebsiteSale.include({
        events: _.extend(events, {
            'change select[name="lease"]': "onChangeVariant",
        }),

        _onProductReady: function () {
            // We need to inject our lease field, because Odoo doesn't just do a
            // normal field submission. Because why would it?
            this.rootProduct.lease = this.$form.find('select[name="lease"]').val();

            return this._super.apply(this, arguments);
        },

        _getCombinationInfo: function (ev) {
            // We've had to completely override this function just to inject the
            // leasing option.
            var self = this;

            if ($(ev.target).hasClass("variant_custom_value")) {
                return Promise.resolve();
            }

            var $parent = $(ev.target).closest(".js_product");
            var qty = $parent.find('input[name="add_qty"]').val();
            var combination = this.getSelectedVariantValues($parent);
            var parentCombination = $parent
                .find("ul[data-attribute_exclusions]")
                .data("attribute_exclusions").parent_combination;
            var productTemplateId = parseInt(
                $parent.find(".product_template_id").val(),
                10
            );
            var leasing = $parent.find("select[name='lease']").val();

            self._checkExclusions($parent, combination);

            return ajax
                .jsonRpc(this._getUri("/sale/get_combination_info"), "call", {
                    product_template_id: productTemplateId,
                    product_id: this._getProductId($parent),
                    combination: combination,
                    add_qty: parseInt(qty, 10),
                    pricelist_id: this.pricelistId || false,
                    parent_combination: parentCombination,
                    leasing: leasing,
                })
                .then(function (combinationData) {
                    self._onChangeCombination(ev, $parent, combinationData);
                });
        },

        _onChangeCombination: function (ev, $parent, combination) {
            this._super.apply(this, arguments);
            var leasing = $parent.find('select[name="lease"]');
            var options = leasing.find("option[value!='']");
            var current_opts = [];
            for (var i = 0; i < options.length; i++) {
                current_opts.push(options[i].value);
            }
            var valid_opts = [];

            if (combination.lease_ok) {
                leasing.removeClass("disabled");
            } else {
                leasing.addClass("disabled");
            }

            if (combination.lease_pricing_rules !== undefined) {
                for (const [key, value] of Object.entries(
                    combination.lease_pricing_rules
                )) {
                    valid_opts.push(key);
                    if (!current_opts.includes(key)) {
                        leasing.append(new Option(value.name, key));
                    }
                }
            }

            for (var j = 0; j < options.length; j++) {
                if (!valid_opts.includes(options[j].value)) {
                    options[j].remove();
                }
            }
        },
    });
});
