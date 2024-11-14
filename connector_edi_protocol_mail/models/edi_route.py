from uuid import uuid4

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import ValidationError


class EdiEnvelopeRoute(models.Model):
    _name = "edi.envelope.route"
    _inherit = ["mail.thread", "mail.alias.mixin", "edi.envelope.route"]

    protocol = fields.Selection(
        selection_add=[("mail", "Email")], ondelete={"mail": "cascade"}
    )

    def _alias_get_creation_values(self):
        vals = super(EdiEnvelopeRoute, self)._alias_get_creation_values()
        vals["alias_model_id"] = self.env["ir.model"]._get(self._name).id
        if self.id:
            vals["alias_defaults"] = {"edi_route_id": self.id}
        return vals

    @api.model
    def message_update(self, msg_dict, update_vals=None):
        raise NotImplementedError(
            _("Updating an existing message attached to an edi.route is not supported.")
        )

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """
        Overrides mail_thread message_new(), called by the mailgateway through
        message_process, to manually process this mail.
        """
        if not custom_values:
            custom_values = {}

        route_id = custom_values.get("edi_route_id")

        if not route_id:
            raise UserWarning("Could not determine the edi.route to use")

        if "message" not in custom_values:
            raise UserWarning("Raw message missing")

        envelope_route_id = self.env["edi.envelope.route"].sudo().browse(route_id)

        if envelope_route_id.protocol != "mail":
            raise UserWarning(
                "Can only handle message_new for envelope routes of type 'mail'"
            )

        # switch to the SUPERUSER_ID to ensure that sales are not automatically assigned to the emailing partner
        envelope_id = (
            self.env["edi.envelope"]
            .with_user(SUPERUSER_ID)
            .sudo()
            .create(
                {
                    "backend_id": envelope_route_id.backend_id.id,
                    "external_id": msg_dict.get("message_id", ""),
                    "body": custom_values.get("message").as_string(),
                    "route_id": envelope_route_id.id,
                    "direction": "in",
                }
            )
        )
        return envelope_id

    @api.constrains("protocol", "direction", "protocol_in_trigger")
    def _constrains_mail_protocol(self):
        for record in self.filtered(lambda r: r.protocol == "mail"):
            if record.direction != "in":
                raise ValidationError(
                    _(
                        "connector_edi_protocol_mail only supports inbound"
                        " mail at this time"
                    )
                )

            if record.protocol_in_trigger != "none":
                raise ValidationError(
                    _(
                        "connector_edi_protocol_mail only supports"
                        " protocol_in_trigger of 'none'"
                    )
                )

    # flake8: noqa: E101, W191, B950
    def action_mail_demo(self):
        mime = """Received: from ROCKINGHAM.E4W.local (192.168.40.5) by ROCKINGHAM.E4W.local
 (192.168.40.5) with Microsoft SMTP Server (TLS) id 15.0.847.32 via Mailbox
 Transport; Mon, 7 Aug 2017 11:02:36 +0100
Received: from ROCKINGHAM.E4W.local (192.168.40.5) by ROCKINGHAM.E4W.local
 (192.168.40.5) with Microsoft SMTP Server (TLS) id 15.0.847.32; Mon, 7 Aug
 2017 11:02:35 +0100
Received: from pmta2.delivery8.ore.mailhop.org (54.148.222.11) by
 ROCKINGHAM.E4W.local (192.168.40.5) with Microsoft SMTP Server id 15.0.847.32
 via Frontend Transport; Mon, 7 Aug 2017 11:02:35 +0100
Received: from smtp.example.com (unknown [91.192.195.243])	by
 inbound1.ore.mailhop.org (Halon) with ESMTP	id
 52b28df3-7b57-11e7-93cc-bb360a9caeff;	Mon, 07 Aug 2017 10:01:04 +0000 (UTC)
Received: from mail pickup service by smtp.example.com with Microsoft
 SMTPSVC;	 Mon, 7 Aug 2017 11:01:03 +0100
From: Sales <sales@example.com>
To: Queries <{alias}@{domain}>
Subject: OFO CSV {now}
Thread-Topic: OFO CSV
Thread-Index: AdMPZBRAbjFx6xIhRK+4Safyg/4FfA==
Date: Mon, 7 Aug 2017 10:01:03 +0000
Message-ID: {uuid}
X-MS-Exchange-Organization-AuthSource: ROCKINGHAM.E4W.local
X-MS-Has-Attach: yes
X-MS-TNEF-Correlator:
x-mailer: Microsoft CDO for Windows 2000
x-originalarrivaltime: 07 Aug 2017 10:01:03.0681 (UTC)
 FILETIME=[145F4310:01D30F64]
MIME-Version: 1.0
X-Priority: 3
Importance: Normal
Content-Type: multipart/mixed;
	boundary="------_=_NextPart_001_A12FFC79.D0FC87A1"
This is a multipart MIME message.
--------_=_NextPart_001_A12FFC79.D0FC87A1
Content-Type: multipart/alternative;
	boundary="------_=_NextPart_002_3553006D.03DDA0AE"
--------_=_NextPart_002_3553006D.03DDA0AE
Content-Type: text/plain;
	charset="utf-8"
Trump Chairs - SEATING
Item Count 7
Export ID 107033
Last Export 07/08/2017 10:00:59
Last Export Count 0
--------_=_NextPart_002_3553006D.03DDA0AE
Content-Type: text/html;
	charset="utf-8"
Content-Transfer-Encoding: quoted-printable
Content-ID: <B0B45B51E78F744F989EFDFC873B4575@example.com>
<html><head><meta=20http-equiv=3D"Content-Type"=20content=3D"text/html;=20c=
harset=3Diso-8859-1"></Head><body>Trump=20Chairs=20-=20SEATING<br>=0D=0AIte=
m=20Count=207<br>=0D=0AExport=20ID=20107033<br>=0D=0A<br>=0D=0ALast=20Expor=
t=2007/08/2017=2010:00:59<br>=0D=0ALast=20Export=20Count=200=20</Body></Htm=
l>
--------_=_NextPart_002_3553006D.03DDA0AE--
--------_=_NextPart_001_A12FFC79.D0FC87A1
Content-Disposition: attachment;
	filename="OFO1-07082017-000101.csv"
Content-Type: application/octet-stream;
	name="OFO1-07082017-000101.csv"
Content-Transfer-Encoding: base64
Content-ID: <9D0373C3D914764B9B9B3BF0817BCC90@example.com>
T3JkZXIjLCBPcmRlciBUaW1lLCBQcm9kdWN0IENvZGUsIEJveGVzLCBPcmRlcmVkIFF0eSwgV2Vp
Z2h0LCAgRGVsaXZlcnkgTmFtZSwgRGVsaXZlcnkgQWRkcmVzczEsICBEZWxpdmVyeSBBZGRyZXNz
MiwgIERlbGl2ZXJ5IEFkZHJlc3MzLCAgRGVsaXZlcnkgQWRkcmVzczQsICBUb3duL0NpdHksIENv
dW50eSwgUG9zdGNvZGUsIFRlbGVwaG9uZSwgTm90ZXMsIFByaWNlLCBPRk8gQ29kZSwgTkFWIENv
ZGUsIEVtYWlsDQo0Mjc4MzIxLDAxLzA4LzIwMTcgMTE6MzA6NDEsQ0gwNzA3UkIvQUMxMDQ2LDIs
MiwzNixDYXJtZW4gTW9vcmUsUmV2b2x2aW5nIERvb3JzIEFnZW5jeSxTb3V0aCBCYW5rIFRlY2hu
b3BhcmssOTAgTG9uZG9uIFJvYWQsLExvbmRvbiwsU0UxIDZMTiwiMDIwNyAgNDA3IDA3NDciLCIt
LSBEQVkgT0YgQ0hPSUNFIFdlZG5lc2RheSAwMi8wOC8yMDE3IC0tICAiLDY0Ljc1LCIxMjE4NkJB
UkIiLCJOQVYwMDczMzM3IiwiY2FybWVuLm1vb3JlQHJldm9sdmluZy1kb29ycy5vcmcudWsiDQo0
Mjc5OTE5LDAzLzA4LzIwMTcgMTY6NDA6MTcsQUMxMDQ3LDEsMSwxOCxNcnMgSGVsZW4gTWNpbnR5
cmUsaWNvbiBlbGVjdHJvbmljcyBsdGQuLHVuaXQgMyAgR3JvdmUgUm9hZC4sQ29zaGFtLCxQb3J0
c21vdXRoLEhhbXBzaGlyZSxQTzYgMUxYLCIwMjM5IDIzMTYwODciLCIyIGRlbGl2ZXJpZXMgIiwy
Mi4wOSwiQUMxMDQ3IiwiTkFWMjE2NDEwMCIsImhlbGVuLm1jaW50eXJlQGljb25lbGVjdHJvbmlj
cy5jby51ayINCjQyODAxNzgsMDQvMDgvMjAxNyAxMTozNzoxMSxPRjAxMDBFTVJCLDEsMSwxOCxN
cnMgU2lhbiBKZW5raW5zLFN0YXRpb24gQ291cmllcnMsVW5pdCBELE1vY2hkcmUgSW5kdXN0cmlh
bCBFc3RhdGUsTW9jaGRyZSxOZXd0b3duLFBvd3lzLFNZMTYgNExFLCIwMTY4IDYgNjIxMTkwIiwi
LS0gREFZIE9GIENIT0lDRSBNb25kYXkgMDcvMDgvMjAxNyAtLSAgIiwxOTguNTksIjEyMjg5UkIi
LCJOQVYwMDczNDg2Iiwic2lhbi5qZW5raW5zQHN0YXRpb25jb3VyaWVycy5jby51ayINCjQyODAz
NjQsMDQvMDgvMjAxNyAxNTowMjoxNSxDSDA2NzZXQSwzLDMsNTQsTXJzIFNob25hIE1jR3JhdGgs
Q29tcGV0ZW5jZSBNYXR0ZXJzIEx0ZCw1NiBEZWVyZHlrZXMgVmlldyxDdW1iZXJuYXVsZCwsR2xh
c2dvdyxOb3J0aCBMYW5hcmtzaGlyZSxHNjggOUhOLCIwNzc4IDggMzc1NjkxIiwiLS0gREFZIE9G
IENIT0lDRSBUdWVzZGF5IDA4LzA4LzIwMTcgLS0gICIsMTEyLjY5LCIzNjQzMFciLCJOQVYwMDcz
Nzk4Iiwic21jZ3JhdGhAY29tcGV0ZW5jZW1hdHRlcnMuY28udWsiDQo0MjgwNTE4LDA1LzA4LzIw
MTcgMTA6MjE6MDEsQ0gwODAyQ0gsMiwyLDM2LE1yIENsaXZlIEVhdG9uLEhlbHAgZm9yIFBzeWNo
b2xvZ3ksVGhlIEdyYW5nZSw2MiBTcGl4d29ydGggUm9hZCxPbGQgQ2F0dG9uLE5vcndpY2gsTm9y
Zm9sayxOUjYgN05GLCIwNzg3IDk4ODIyMzIiLCItLSBEQVkgT0YgQ0hPSUNFIFR1ZXNkYXkgMDgv
MDgvMjAxNyAtLSAgIiw3MC4wNywiMTIxODJDSCIsIk5BVjAwNzMyMzMiLCJvZmZpY2VAaGVscDRw
c3ljaG9sb2d5LmNvLnVrIg0KNDI4MDUzMCwwNS8wOC8yMDE3IDEyOjAwOjI1LE9GMDIwMUVNLDIs
MiwzNixNciBTdHVhcnQgQmxhY2tsZXksU2hyb3BzaGlyZSBJbm4sTmV3cG9ydCBSb2FkLEhhdWdo
dG9uLCxTdGFmZm9yZCwsU1QxOCA5SkgsIjAxNzggNTc4MDkwNSIsIi0tIERBWSBPRiBDSE9JQ0Ug
VHVlc2RheSAwOC8wOC8yMDE3IC0tICAiLDYzLjk1LCIzNjY3NyIsIk5BVjAwNzQyMjEiLCJTaHJv
cHNoaXJlaW5uQG91dGxvb2suY29tIg0KNDI4MDczMCwwNy8wOC8yMDE3IDA5OjMzOjExLExJVEUw
MjEsMSwxLDE4LE1yIEFsZXggV2FzcyxWb3J0ZXggRGlzdHJpYnV0aW9uIEx0ZCxVbml0IDMsTGFy
Y2h3b29kIEF2ZW51ZSwsSGF2YW50LEhhbXBzaGlyZSxQTzkgM0JFLCIwMjM5IDI0NTQ0NTUiLCIt
LSBEQVkgT0YgQ0hPSUNFIFR1ZXNkYXkgMDgvMDgvMjAxNyAtLSAgIiw0MS44MiwiMTU0Nzc3Iiwi
TkFWMTA0NjY5MyIsImFsZXhAdm9ydGV4cGFydHMuZXUiDQo=
--------_=_NextPart_001_A12FFC79.D0FC87A1--
""".format(
            alias=self.alias_name,
            now=fields.Datetime.now().isoformat(),
            uuid=uuid4(),
            domain=self.env["ir.config_parameter"]
            .sudo()
            .get_param("mail.catchall.domain"),
        )
        self.env["mail.thread"].sudo().message_process(False, mime)
