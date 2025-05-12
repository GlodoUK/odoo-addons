from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import test_python_expr

from odoo.addons.queue_job.job import identity_exact

INTERVAL_TYPES = [
    ("minutes", "Minutes"),
    ("hours", "Hours"),
    ("days", "Days"),
    ("weeks", "Weeks"),
    ("months", "Months"),
]

QUEUE_PRIORITY_DEFAULT = 10


class EdiEnvelopeRoute(models.Model):
    _name = "edi.envelope.route"
    _description = "EDI Envelope Route"
    _order = "sequence ASC"
    _inherit = ["edi.external_id.warning.mixin"]

    name = fields.Char(
        required=True,
    )

    sequence = fields.Integer()

    backend_id = fields.Many2one(
        "edi.backend",
        index=True,
        ondelete="cascade",
        required=True,
    )

    active = fields.Boolean(
        related="backend_id.active",
        store=True,
    )

    codec = fields.Selection(
        [("simple", "Simple / Single Message"), ("code", "Python Code")],
        required=True,
        string="Envelope Codec",
    )

    direction = fields.Selection(
        [("in", "In"), ("out", "Out"), ("both", "In & Out")],
        required=True,
    )

    protocol = fields.Selection(
        [("file", "File"), ("code", "Code")],
        required=True,
    )

    protocol_in_trigger = fields.Selection(
        [("none", "On-Demand"), ("schedule", "Schedule")],
        copy=False,
        default="none",
        required=True,
    )

    protocol_out_trigger = fields.Selection(
        [("none", "On-Demand"), ("schedule", "Schedule")],
        copy=False,
        default="none",
        required=True,
    )

    protocol_in_cron_interval_number = fields.Integer(
        default=5,
    )

    protocol_in_cron_interval_type = fields.Selection(
        INTERVAL_TYPES,
        default="minutes",
    )

    protocol_in_cron_id = fields.Many2one(
        "ir.cron",
        "Protocol In Schedule",
        copy=False,
    )

    protocol_out_cron_interval_number = fields.Integer(
        default=5,
    )

    protocol_out_cron_interval_type = fields.Selection(
        INTERVAL_TYPES,
        default="minutes",
    )

    protocol_out_cron_id = fields.Many2one(
        "ir.cron",
        "Protocol Out Schedule",
        copy=False,
    )

    codec_code_enclose = fields.Text(
        string="Enclose Codec Code",
    )

    codec_code_open = fields.Text(
        string="Open Codec Code",
    )

    code_in = fields.Text(
        string="Input Code",
    )
    code_out = fields.Text(
        string="Ouput Code",
    )

    file_path_archive = fields.Char(
        default="/tmp/archive/{datetime:%Y}/{datetime:%m}/{datetime:%d}/",
        help="Archive File Path",
    )

    file_path_in = fields.Char(
        default="/tmp/in/*.txt",
        help="Input File Glob",
    )

    file_path_out = fields.Char(
        default="/tmp/{route.id}-{record.id}-{datetime:%Y-%m-%dT%H-%M-%S}.txt",
        help="Output File",
    )

    file_path_in_use_done_mode = fields.Selection(
        [("none", "Do not use"), ("suffix", "Suffix .DONE")],
        help="A DONE file is a marker file that indicates to a user that the"
        " file is complete and ready. It is commonly used in shared"
        " repositories to differentiate between files that should or should"
        " not be accessed by another user.",
        default="none",
    )

    file_path_out_use_done_mode = fields.Selection(
        [("none", "Do not use"), ("suffix", "Suffix .DONE")],
        help="A DONE file is a marker file that indicates to a user that the"
        " file is complete and ready. It is commonly used in shared"
        " repositories to differentiate between files that should or should"
        " not be accessed by another user.",
        default="none",
    )

    encoding = fields.Selection(
        [
            ("binary", "Binary / Raw"),
            # https://docs.python.org/3.5/library/codecs.html#standard-encodings
            # there does not seem to be a reliable way to do this in code?
            ("ascii", "ascii, 646, us-ascii"),
            ("big5", "big5, big5-tw, csbig5"),
            ("big5hkscs", "big5hkscs, big5-hkscs, hkscs"),
            ("cp037", "cp037, IBM037, IBM039"),
            ("cp273", "cp273, 273, IBM273, csIBM273"),
            ("cp424", "cp424, EBCDIC-CP-HE, IBM424"),
            ("cp437", "cp437, 437, IBM437"),
            ("cp500", "cp500, EBCDIC-CP-BE, EBCDIC-CP-CH, IBM500"),
            ("cp720", "cp720"),
            ("cp737", "cp737"),
            ("cp775", "cp775, IBM775"),
            ("cp850", "cp850, 850, IBM850"),
            ("cp852", "cp852, 852, IBM852"),
            ("cp855", "cp855, 855, IBM855"),
            ("cp856", "cp856"),
            ("cp857", "cp857, 857, IBM857"),
            ("cp858", "cp858, 858, IBM858"),
            ("cp860", "cp860, 860, IBM860"),
            ("cp861", "cp861, 861, CP-IS, IBM861"),
            ("cp862", "cp862, 862, IBM862"),
            ("cp863", "cp863, 863, IBM863"),
            ("cp864", "cp864, IBM864"),
            ("cp865", "cp865, 865, IBM865"),
            ("cp866", "cp866, 866, IBM866"),
            ("cp869", "cp869, 869, CP-GR, IBM869"),
            ("cp874", "cp874"),
            ("cp875", "cp875"),
            ("cp932", "cp932, 932, ms932, mskanji, ms-kanji"),
            ("cp949", "cp949, 949, ms949, uhc"),
            ("cp950", "cp950, 950, ms950"),
            ("cp1006", "cp1006"),
            ("cp1026", "cp1026, ibm1026"),
            ("cp1125", "cp1125, 1125, ibm1125, cp866u, ruscii"),
            ("cp1140", "cp1140, ibm1140"),
            ("cp1250", "cp1250, windows-1250"),
            ("cp1251", "cp1251, windows-1251"),
            ("cp1252", "cp1252, windows-1252"),
            ("cp1253", "cp1253, windows-1253"),
            ("cp1254", "cp1254, windows-1254"),
            ("cp1255", "cp1255, windows-1255"),
            ("cp1256", "cp1256, windows-1256"),
            ("cp1257", "cp1257, windows-1257"),
            ("cp1258", "cp1258, windows-1258"),
            ("cp65001", "cp65001"),
            ("euc_jp", "euc_jp, eucjp, ujis, u-jis"),
            ("euc_jis_2004", "euc_jis_2004, jisx0213, eucjis2004"),
            ("euc_jisx0213", "euc_jisx0213, eucjisx0213"),
            (
                "euc_kr",
                (
                    "euc_kr, euckr, korean, ksc5601, ks_c-5601,"
                    " ks_c-5601-1987, ksx1001, ks_x-1001"
                ),
            ),
            (
                "gb2312",
                (
                    "gb2312, chinese, csiso58gb231280, euc-cn, euccn,"
                    " eucgb2312-cn, gb2312-1980, gb2312-80, iso- ir-58"
                ),
            ),
            ("gbk", "gbk, 936, cp936, ms936"),
            ("gb18030", "gb18030, gb18030-2000"),
            ("hz", "hz, hzgb, hz-gb, hz-gb-2312"),
            ("iso2022_jp", "iso2022_jp, csiso2022jp, iso2022jp, iso-2022-jp"),
            ("iso2022_jp_1", "iso2022_jp_1, iso2022jp-1, iso-2022-jp-1"),
            ("iso2022_jp_2", "iso2022_jp_2, iso2022jp-2, iso-2022-jp-2"),
            ("iso2022_jp_2004", "iso2022_jp_2004, iso2022jp-2004, iso-2022-jp-2004"),
            ("iso2022_jp_3", "iso2022_jp_3, iso2022jp-3, iso-2022-jp-3"),
            ("iso2022_jp_ext", "iso2022_jp_ext, iso2022jp-ext, iso-2022-jp-ext"),
            ("iso2022_kr", "iso2022_kr, csiso2022kr, iso2022kr, iso-2022-kr"),
            (
                "latin_1",
                "latin_1, iso-8859-1, iso8859-1, 8859, cp819, latin, latin1, L1",
            ),
            ("iso8859_2", "iso8859_2, iso-8859-2, latin2, L2"),
            ("iso8859_3", "iso8859_3, iso-8859-3, latin3, L3"),
            ("iso8859_4", "iso8859_4, iso-8859-4, latin4, L4"),
            ("iso8859_5", "iso8859_5, iso-8859-5, cyrillic"),
            ("iso8859_6", "iso8859_6, iso-8859-6, arabic"),
            ("iso8859_7", "iso8859_7, iso-8859-7, greek, greek8"),
            ("iso8859_8", "iso8859_8, iso-8859-8, hebrew"),
            ("iso8859_9", "iso8859_9, iso-8859-9, latin5, L5"),
            ("iso8859_10", "iso8859_10, iso-8859-10, latin6, L6"),
            ("iso8859_11", "iso8859_11, iso-8859-11, thai"),
            ("iso8859_13", "iso8859_13, iso-8859-13, latin7, L7"),
            ("iso8859_14", "iso8859_14, iso-8859-14, latin8, L8"),
            ("iso8859_15", "iso8859_15, iso-8859-15, latin9, L9"),
            ("iso8859_16", "iso8859_16, iso-8859-16, latin10, L10"),
            ("johab", "johab, cp1361, ms1361"),
            ("koi8_r", "koi8_r"),
            ("koi8_t", "koi8_t"),
            ("koi8_u", "koi8_u"),
            ("kz1048", "kz1048, kz_1048, strk1048_2002, rk1048"),
            ("mac_cyrillic", "mac_cyrillic, maccyrillic"),
            ("mac_greek", "mac_greek, macgreek"),
            ("mac_iceland", "mac_iceland, maciceland"),
            ("mac_latin2", "mac_latin2, maclatin2, maccentraleurope"),
            ("mac_roman", "mac_roman, macroman, macintosh"),
            ("mac_turkish", "mac_turkish, macturkish"),
            ("ptcp154", "ptcp154, csptcp154, pt154, cp154, cyrillic-asian"),
            ("shift_jis", "shift_jis, csshiftjis, shiftjis, sjis, s_jis"),
            ("shift_jis_2004", "shift_jis_2004, shiftjis2004, sjis_2004, sjis2004"),
            ("shift_jisx0213", "shift_jisx0213, shiftjisx0213, sjisx0213, s_jisx0213"),
            ("utf_32", "utf_32, U32, utf32"),
            ("utf_32_be", "utf_32_be, UTF-32BE"),
            ("utf_32_le", "utf_32_le, UTF-32LE"),
            ("utf_16", "utf_16, U16, utf16"),
            ("utf_16_be", "utf_16_be, UTF-16BE"),
            ("utf_16_le", "utf_16_le, UTF-16LE"),
            ("utf_7", "utf_7, U7, unicode-1-1-utf-7"),
            ("utf_8", "utf_8, U8, UTF, utf8"),
            ("utf_8_sig", "utf_8_sig"),
        ],
        required=True,
        default="utf_8",
    )

    queue_identity_exact = fields.Boolean()

    queue_enclose_messages_identity_exact = fields.Boolean()

    queue_open_messages_identity_exact = fields.Boolean()

    queue_channel = fields.Char()

    queue_enclose_messages_channel = fields.Char()

    queue_open_messages_channel = fields.Char()

    queue_priority = fields.Integer(
        default=QUEUE_PRIORITY_DEFAULT,
    )

    queue_enclose_messages_priority = fields.Integer(
        default=QUEUE_PRIORITY_DEFAULT,
    )

    queue_open_messages_priority = fields.Integer(
        default=QUEUE_PRIORITY_DEFAULT,
    )

    queue_max_retries = fields.Integer(
        default=0,
    )

    vacuum_content = fields.Boolean()

    vacuum_content_after_days = fields.Integer(
        default=14,
    )

    def action_vacuum_content(self):
        for route_id in self.filtered_domain([("vacuum_content", "=", True)]):
            cut_off = fields.Datetime.now() - relativedelta(
                days=route_id.vacuum_content_after_days
            )
            while True:
                with self.pool.cursor() as new_cr:
                    env = api.Environment(new_cr, self.env.uid, self.env.context)
                    envelope_ids = env["edi.envelope"].search(
                        [
                            ("route_id", "=", route_id.id),
                            ("state", "=", "done"),
                            ("date_done", "<=", cut_off),
                        ],
                        limit=10,
                    )
                    if not envelope_ids:
                        break
                    envelope_ids.unlink()

    def _with_delay_options(self, usage=None):
        self.ensure_one()
        opts = {}

        prefix = "queue"

        if usage in ["enclose_messages", "open_messages"]:
            prefix = f"queue_{usage}"

        for suffix in ["channel", "priority"]:
            value = getattr(self, f"{prefix}_{suffix}")
            if value:
                opts.update({suffix: value})

        if self.queue_max_retries:
            opts.update({"max_retries": self.queue_max_retries})

        if getattr(self, f"{prefix}_identity_exact"):
            opts.update({"identity_key": identity_exact})

        return opts

    def collect_envelopes(self, **kwargs):
        for route in self.filtered(lambda r: r.direction in ["in", "both"]):
            route.with_delay(**route._with_delay_options())._run_in(**kwargs)

    def send_envelopes(self, **kwargs):
        for route in self.filtered(lambda r: r.direction in ["out", "both"]):
            route.with_delay(**route._with_delay_options())._run_out(**kwargs)

    def _run_in(self, **kwargs):
        self.ensure_one()

        if self.direction not in ("in", "both"):
            msg = _("Must be an In or Both route to use the _run_in method")
            raise UserError(msg)

        with self.backend_id.work_on("edi.envelope") as work:
            usage = f"import.{self.protocol}"
            component = work.component(usage=usage)
            component.run(self, **kwargs)

    def _run_out(self, **kwargs):
        self.ensure_one()

        if self.direction not in ("out", "both"):
            msg = _("Must be an Out or Both route to use the _run_out method")
            raise UserError(msg)

        with self.backend_id.work_on("edi.envelope") as work:
            usage = f"export.{self.protocol}"
            component = work.component(usage=usage)
            component.run(self, **kwargs)

    def unlink(self):
        cron_ids = self.mapped("protocol_in_cron_id")
        cron_ids |= self.mapped("protocol_out_cron_id")
        cron_ids.unlink()
        return super().unlink()

    def _cron_in_vals(self):
        self.ensure_one()

        ir_model_id = self.env["ir.model"].search([("model", "=", self._name)], limit=1)

        return {
            "name": f"EDI: {self.backend_id.name} - Envelope Route In {self.name}",
            "active": self.active,
            "interval_number": self.protocol_in_cron_interval_number,
            "interval_type": self.protocol_in_cron_interval_type,
            "model_id": ir_model_id.id,
            "code": """
record = model.browse(%d)
record.with_delay(**record._with_delay_options())._run_in()
"""
            % (self.id),
        }

    def _cron_out_vals(self):
        self.ensure_one()

        ir_model_id = self.env["ir.model"].search([("model", "=", self._name)], limit=1)

        return {
            "name": f"EDI: {self.backend_id.name} - Envelope Route Out {self.name}",
            "active": self.active,
            "interval_number": self.protocol_out_cron_interval_number,
            "interval_type": self.protocol_out_cron_interval_type,
            "model_id": ir_model_id.id,
            "code": """
record = model.browse(%d)
record.with_delay(**record._with_delay_options())._run_out()
"""
            % (self.id),
        }

    def _cron_in_sync(self):
        self.ensure_one()

        if self.protocol_in_trigger != "schedule" and self.protocol_in_cron_id:
            self.protocol_in_cron_id.unlink()

        vals = self._cron_in_vals()

        if self.protocol_in_trigger == "schedule" and self.protocol_in_cron_id:
            self.protocol_in_cron_id.sudo().write(vals)

        if self.protocol_in_trigger == "schedule" and not self.protocol_in_cron_id:
            self.protocol_in_cron_id = self.env["ir.cron"].sudo().create(vals)

        if self.protocol_in_cron_id:
            self.protocol_in_cron_id.active = self.active

    def _cron_out_sync(self):
        self.ensure_one()

        if self.protocol_out_trigger != "schedule" and self.protocol_out_cron_id:
            self.protocol_out_cron_id.unlink()

        vals = self._cron_out_vals()

        if self.protocol_out_trigger == "schedule" and self.protocol_out_cron_id:
            self.protocol_out_cron_id.sudo().write(vals)

        if self.protocol_out_trigger == "schedule" and not self.protocol_out_cron_id:
            self.protocol_out_cron_id = self.env["ir.cron"].sudo().create(vals)

        if self.protocol_out_cron_id:
            self.protocol_out_cron_id.active = self.active

    def action_sync_cron(self):
        for route in self:
            route._cron_in_sync()
            route._cron_out_sync()

    def write(self, vals):
        res = super().write(vals)

        if self.env.context.get("edi_connector_envelope_route_skip_cron_sync"):
            return res

        trigger_fields = [
            "active",
            "protocol_in_trigger",
            "protocol_in_cron_interval_type",
            "protocol_in_cron_interval_number",
            "protocol_out_trigger",
            "protocol_out_cron_interval_type",
            "protocol_out_cron_interval_number",
        ]

        if any(field in vals.keys() for field in trigger_fields):
            self.with_context(
                edi_connector_envelope_route_skip_cron_sync=True
            ).action_sync_cron()

        return res

    @api.constrains("codec", "codec_code_enclose", "codec_code_open")
    def _check_codec_python_code(self):
        for route in self.sudo().filtered(lambda r: r.codec == "code"):
            msg = test_python_expr(
                expr=route.codec_code_open.strip() or "",
                mode="exec",
            )
            if msg:
                raise ValidationError(msg)

            msg = test_python_expr(
                expr=route.codec_code_enclose.strip() or "",
                mode="exec",
            )
            if msg:
                raise ValidationError(msg)

    @api.constrains("code_in", "code_out", "protocol")
    def _check_protocol_python_code(self):
        for route in self.sudo().filtered(lambda r: r.protocol == "code"):
            if route.direction in ("in", "both"):
                msg = test_python_expr(
                    expr=route.code_in.strip() or "",
                    mode="exec",
                )
                if msg:
                    raise ValidationError(msg)

            if route.direction in ("out", "both"):
                msg = test_python_expr(
                    expr=route.code_out.strip() or "",
                    mode="exec",
                )
                if msg:
                    raise ValidationError(msg)

    @api.constrains("encoding", "protocol", "direction")
    def _check_binary_encoding(self):
        for r in self:
            if r.encoding == "binary" and (r.protocol != "file" or r.direction != "in"):  # noqa : E501
                msg = _(
                    "Binary mode is only supported for Protocol=File and Direction=In"
                )  # noqa : E501
                raise ValidationError(msg)
