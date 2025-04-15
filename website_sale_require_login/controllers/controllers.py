from werkzeug.urls import url_encode

from odoo.http import request, route

from odoo.addons.website_sale.controllers.main import WebsiteSale


class RequireLogin(WebsiteSale):
    # We don't just use auth="user" because that throws a session expired if
    # the user is not logged in.
    # We want to redirect.

    def _check_ecommerce_login_required(self):
        if not request.website:
            return False

        if not request.website.ecommerce_requires_login:
            return None

        if request.uid and (request.uid != request.website.user_id.id):
            return None

        try:
            status_code = int(
                request.website.ecommerce_requires_login_status_code or "302"
            )
        except ValueError:
            status_code = 302

        qs = url_encode({"redirect": request.httprequest.full_path})

        return request.redirect(
            f"/web/login?{qs}",
            status_code,
        )

    @route()
    def shop(
        self,
        page=0,
        category=None,
        search="",
        min_price=0.0,
        max_price=0.0,
        ppg=False,
        **post,
    ):
        ecommerce_requires_login = self._check_ecommerce_login_required()
        if ecommerce_requires_login is not None:
            return ecommerce_requires_login

        return super().shop(
            page=page,
            category=category,
            search=search,
            min_price=min_price,
            max_price=max_price,
            ppg=ppg,
            **post,
        )

    @route()
    def product_document(self, product_template, document_id):
        ecommerce_requires_login = self._check_ecommerce_login_required()
        if ecommerce_requires_login is not None:
            return ecommerce_requires_login

        return super().product_document(product_template, document_id)

    @route()
    def old_product(self, product, category="", search="", **kwargs):
        ecommerce_requires_login = self._check_ecommerce_login_required()
        if ecommerce_requires_login is not None:
            return ecommerce_requires_login

        return super().old_product(product, category=category, search=search, **kwargs)

    @route()
    def product(self, product, category="", search="", **kwargs):
        ecommerce_requires_login = self._check_ecommerce_login_required()
        if ecommerce_requires_login is not None:
            return ecommerce_requires_login

        return super().product(product, category=category, search=search, **kwargs)

    @route()
    def pricelist(self, promo, **post):
        ecommerce_requires_login = self._check_ecommerce_login_required()
        if ecommerce_requires_login is not None:
            return ecommerce_requires_login

        return super().pricelist(promo, **post)

    @route()
    def cart(self, access_token=None, revive="", **post):
        ecommerce_requires_login = self._check_ecommerce_login_required()
        if ecommerce_requires_login is not None:
            return ecommerce_requires_login

        return super().cart(access_token=access_token, revive=revive, **post)

    @route()
    def cart_update(
        self,
        product_id,
        add_qty=1,
        set_qty=0,
        product_custom_attribute_values=None,
        no_variant_attribute_values=None,
        express=False,
        **kwargs,
    ):
        ecommerce_requires_login = self._check_ecommerce_login_required()
        if ecommerce_requires_login is not None:
            return ecommerce_requires_login

        return super().cart_update(
            product_id,
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values,
            express=express,
            **kwargs,
        )

    @route()
    def cart_update_json(
        self,
        product_id,
        line_id=None,
        add_qty=None,
        set_qty=None,
        display=True,
        product_custom_attribute_values=None,
        no_variant_attribute_values=None,
        **kw,
    ):
        ecommerce_requires_login = self._check_ecommerce_login_required()
        if ecommerce_requires_login is not None:
            return ecommerce_requires_login

        return super().cart_update_json(
            product_id,
            line_id=line_id,
            add_qty=add_qty,
            set_qty=set_qty,
            display=display,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values,
            **kw,
        )

    @route()
    def address(self, **kw):
        ecommerce_requires_login = self._check_ecommerce_login_required()
        if ecommerce_requires_login is not None:
            return ecommerce_requires_login

        return super().address(**kw)

    @route()
    def checkout(self, **post):
        ecommerce_requires_login = self._check_ecommerce_login_required()
        if ecommerce_requires_login is not None:
            return ecommerce_requires_login

        return super().checkout(**post)

    @route()
    def confirm_order(self, **post):
        ecommerce_requires_login = self._check_ecommerce_login_required()
        if ecommerce_requires_login is not None:
            return ecommerce_requires_login

        return super().confirm_order(**post)

    @route()
    def extra_info(self, **post):
        ecommerce_requires_login = self._check_ecommerce_login_required()
        if ecommerce_requires_login is not None:
            return ecommerce_requires_login

        return super().extra_info(**post)

    @route()
    def shop_payment(self, **post):
        ecommerce_requires_login = self._check_ecommerce_login_required()
        if ecommerce_requires_login is not None:
            return ecommerce_requires_login

        return super().shop_payment(**post)
