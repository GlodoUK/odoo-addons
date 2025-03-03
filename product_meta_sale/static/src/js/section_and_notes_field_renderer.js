odoo.define("product_meta_sale.section_and_note_backend", function (require) {
    "use strict";

    var SectionAndNoteListRenderer = require("account.section_and_note_backend");

    /* eslint-disable no-unused-vars */
    var MetaSectionAndNoteListRenderer = SectionAndNoteListRenderer.include({
        _renderBodyCell: function (record, node, index, options) {
            var $cell = this._super.apply(this, arguments);

            var isSection = record.data.display_type === "line_section";
            var isNote = record.data.display_type === "line_note";

            if (!isSection && !isNote && index === 1 && record.data.meta_tmpl_line_id) {
                $cell.addClass("o_data_cell_product_meta_indent");
            }

            return $cell;
        },
    });

    return MetaSectionAndNoteListRenderer;
});
