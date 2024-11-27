from odoo.tools.safe_eval import wrap_module

from odoo.addons.component.core import AbstractComponent

wrapped_pandas = wrap_module(
    __import__("pandas"),
    [
        "read_csv",
        "read_excel",
        "read_feather",
        "read_fwf",
        "read_hdf",
        "read_html",
        "read_json",
        "read_parquet",
        "read_pickle",
        "read_sas",
        "read_sql",
        "read_table",
        "read_xml",
        "read_gbq",
        "read_stata",
        "array",
        "bdate_range",
        "concat",
        "crosstab",
        "cut",
        "date_range",
        "describe_option",
        "factorize",
        "from_dummies",
        "get_dummies",
        "get_option",
        "isna",
        "isnull",
        "melt",
        "merge",
        "merge_asof",
        "merge_ordered",
        "notna",
        "notnull",
        "period_range",
        "pivot",
        "pivot_table",
        "qcut",
        "reset_option",
        "set_option",
        "timedelta_range",
        "to_datetime",
        "to_numeric",
        "to_timedelta",
        "unique",
        "wide_to_long",
    ],
)


class AbstractEdiComponent(AbstractComponent):
    _inherit = "edi.connector"

    def _get_default_eval_context(self):
        res = super()._get_default_eval_context()
        res.update(
            {
                "pd": wrapped_pandas,
            }
        )
        return res
