odoo.define("web_list_min_width.ListRenderer", function (require) {
    "use strict";

    const ListRenderer = require("web.ListRenderer");
    const pyUtils = require("web.py_utils");
    ListRenderer.include({
        _getColMinWidth: function (column) {
            // Backwards compat - allow an attr called "min-width".
            // This is not recommended going forward as it does not work
            // properly outside of forms.
            if (column.attrs["min-width"]) {
                return column.attrs["min-width"];
            }

            if (column.attrs.options !== undefined) {
                const options = _.isObject(column.attrs.options)
                    ? column.attrs.options
                    : pyUtils.py_eval(column.attrs.options);

                if (options["min-width"] !== undefined) {
                    return options["min-width"];
                }
            }
        },

        _getColInitialWidth: function (column) {
            if (column.attrs.options !== undefined) {
                const options = _.isObject(column.attrs.options)
                    ? column.attrs.options
                    : pyUtils.py_eval(column.attrs.options);

                if (options["initial-width"] !== undefined) {
                    return options["initial-width"];
                }
            }
        },

        _updateColumnMinInitialWidths: function (th, column) {
            const minWidth = this._getColMinWidth(column);
            const initialWidth = this._getColInitialWidth(column);

            if (minWidth === undefined && initialWidth === undefined) {
                return th;
            }

            if (minWidth || initialWidth) {
                th.style.width = "";
                th.style.wordWrap = "break-word";
            }

            if (minWidth !== undefined) {
                th.style.minWidth = minWidth;
            }

            if (initialWidth !== undefined) {
                th.style.width = initialWidth;
                th.style.maxWidth = initialWidth;
            }

            return th;
        },

        /**
         * @override
         * @private
         */
        _computeDefaultWidths: function () {
            const res = this._super.apply(this, arguments);

            this.columns.forEach((column) => {
                const th = this._getColumnHeader(column);
                this._updateColumnMinInitialWidths(th, column);
            });

            return res;
        },

        /**
         * @override
         * @private
         */
        _renderHeaderCell: function (node) {
            const $th = this._super.apply(this, arguments);
            this._updateColumnMinInitialWidths($th[0], node);
            return $th;
        },
    });
});
