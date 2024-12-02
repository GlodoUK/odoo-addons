odoo.define(
    "product_meta_sale_product_configurator.OptionalProductsModal",
    function (require) {
        "use strict";

        var OptionalProductsModal = require("sale_product_configurator.OptionalProductsModal");

        var MetaOptionalProductsModal = OptionalProductsModal.include({
            /**
             * Returns the list of meta child products.
             *
             * @returns {Array} products
             *   {integer} product_id
             *   {integer} quantity
             *   {Array} product_custom_variant_values
             *   {Array} no_variant_attribute_values
             *   {integer} meta_line_id: the originating product.template.meta.line
             * @public
             */
            getAndCreateMetaProducts: async function () {
                var self = this;
                const products = [];
                for (const product of self.$modal.find(".js_product.meta_product")) {
                    var $item = $(product);

                    var metaLineId = parseInt(product.dataset.metaLineId, 10);

                    const productCustomVariantValues =
                        self.getCustomVariantValues($item);
                    const noVariantAttributeValues =
                        self.getNoVariantAttributeValues($item);

                    var parentUniqueId = product.dataset.parentUniqueId;
                    var uniqueId = product.dataset.uniqueId;

                    const productID = await self.selectOrCreateProduct(
                        $item,
                        parseInt($item.find("input.product_id").val(), 10),
                        parseInt($item.find("input.product_template_id").val(), 10),
                        true
                    );

                    products.push({
                        product_id: productID,
                        product_template_id: parseInt(
                            $item.find("input.product_template_id").val(),
                            10
                        ),
                        parent_unique_id: parentUniqueId,
                        unique_id: uniqueId,
                        product_custom_attribute_values: productCustomVariantValues,
                        no_variant_attribute_values: noVariantAttributeValues,
                        meta_line_id: metaLineId,
                    });
                }
                return products;
            },

            /**
             * Returns the list of selected products.
             * The root product is added on top of the list.
             *
             * @returns {Array} products
             *   {integer} product_id
             *   {integer} quantity
             *   {Array} product_custom_variant_values
             *   {Array} no_variant_attribute_values
             * @public
             */
            getAndCreateSelectedProducts: function () {
                // Update the upstream products return with our own meta_attrs data.

                return Promise.all([
                    this._super.apply(this),
                    this.getAndCreateMetaProducts(),
                ]).then(([prods, meta]) => {
                    const products = prods.map((p) => {
                        p.meta_attrs = {};
                        return p;
                    });

                    for (let i = 0; i < meta.length; i++) {
                        const current = meta[i];

                        const idx = products.findIndex((p) => {
                            return p.unique_id === current.parent_unique_id;
                        });

                        if (idx < 0) {
                            continue;
                        }

                        products[idx].meta_attrs[current.meta_line_id] = current;
                    }

                    return products;
                });
            },
        });

        return MetaOptionalProductsModal;
    }
);
