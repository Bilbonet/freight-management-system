# Copyright 2020 Jesus Ramiro <jesus@bilbonet.net>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.osv.expression import OR


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):

        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        expedition_count = request.env['fms.freight'].search_count([])
        values['expedition_count'] = expedition_count
        return values

    def _expedition_get_page_view_values(self, expedition, access_token, **kwargs):
        values = {
            'page_name': 'expedition',
            'expedition': expedition,
        }
        return self._get_page_view_values(expedition, access_token, values, 'my_expeditions_history', False, **kwargs)

    @http.route(['/my/expeditions', '/my/expeditions/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_expeditions(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None, search_in='all', **kw):
        values = self._prepare_portal_layout_values()
        AccountExpedition = request.env['fms.freight']

        searchbar_sortings = {
            'name': {'label': _('Expedition'), 'order': 'name desc'},
            'state': {'label': _('Status'), 'order': 'state'},
            'partner_delivery_note': {'label': _('Delivery Note'),
                                      'order': 'partner_delivery_note desc'},
            'partner_order_doc': {'label': _('Order'),
                                  'order': 'partner_order_doc desc'},
            'partner_sale_doc': {'label': _('Sale Doc.'),
                                  'order': 'partner_sale_doc desc'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'draft': {'label': _('Draft'), 'domain': [('state', '=', 'draft')]},
            'partial': {'label': _('Partial'), 'domain': [('state', '=', 'partial')]},
            'received': {'label': _('Received'), 'domain': [('state', '=', 'received')]},
            'confirmed': {'label': _('Confirmed'), 'domain': [('state', '=', 'confirmed')]},
            'closed': {'label': _('Closed'), 'domain': [('state', '=', 'closed')]},
            'cancel': {'label': _('Cancelled'), 'domain': [('state', '=', 'cancel')]},
            'invoiced': {'label': _('Invoiced'), 'domain': [('state', '=', 'invoiced')]},
        }
        searchbar_inputs = {
            'all': {'input': 'all', 'label': _('Search in All')},
            'name': {'input': 'name', 'label': _('Search in Expedition')},
            'delivery_name': {'input': 'delivery_name',
                              'label': _('Search in Delivery Name')},
            'partner_delivery_note': {'input': 'partner_delivery_note',
                                      'label': _('Search in Delivery Note')},
            'partner_order_doc': {'input': 'partner_order_doc',
                                  'label': _('Search in Order')},
            'partner_sale_doc': {'input': 'partner_sale_doc',
                                  'label': _('Search in Sale Doc.')},
        }

        # default sort by order
        if not sortby:
            sortby = 'name'
        order = searchbar_sortings[sortby]['order']
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain = searchbar_filters[filterby]['domain']

        # archive groups - Default Group By 'sate_order'
        # archive_groups = self._get_archive_groups('fms.freight', domain)
        # if date_begin and date_end:
        #     domain += [('date_order', '>', date_begin), ('date_order', '<=', date_end)]

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('name', 'all'):
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in in ('delivery_name', 'all'):
                search_domain = OR([search_domain, [('delivery_name', 'ilike', search)]])
            if search_in in ('partner_delivery_note', 'all'):
                search_domain = OR([search_domain, [('partner_delivery_note', 'ilike', search)]])
            if search_in in ('partner_order_doc', 'all'):
                search_domain = OR([search_domain, [('partner_order_doc', 'ilike', search)]])
            if search_in in ('partner_sale_doc', 'all'):
                search_domain = OR([search_domain, [('partner_sale_doc', 'ilike', search)]])
            domain += search_domain



        # count for pager
        expedition_count = AccountExpedition.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/expeditions",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=expedition_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        expeditions = AccountExpedition.search(domain, order=order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_expeditions_history'] = expeditions.ids[:100]

        values.update({
            'date_order': date_begin,
            'expeditions': expeditions,
            'page_name': 'expedition',
            'pager': pager,
            # 'archive_groups': archive_groups,
            'default_url': '/my/expeditions',
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': searchbar_filters,
            'filterby': filterby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in,
        })
        return request.render("fms.portal_my_expeditions", values)

    @http.route(['/my/expeditions/<int:expedition_id>'], type='http', auth="public", website=True)
    def portal_my_expedition_detail(self, expedition_id, access_token=None, report_type=None, download=False, **kw):
        try:
            expedition_sudo = self._document_check_access('fms.freight', expedition_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=expedition_sudo, report_type=report_type, report_ref='fms.fms_freight_report_action', download=download)

        values = self._expedition_get_page_view_values(expedition_sudo, access_token, **kw)
        return request.render("fms.portal_expedition_page", values)


class PortalAccount(CustomerPortal):

    @http.route(['/my/invoices/<int:invoice_id>'], type='http', auth="public", website=True)
    def portal_my_invoice_detail(self, invoice_id, access_token=None, report_type=None, download=False, **kw):
        try:
            invoice_sudo = self._document_check_access('account.invoice', invoice_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=invoice_sudo,
                    report_type=report_type,
                    report_ref='fms_custom.account_expedition_invoices',
                    download=download)

        values = self._invoice_get_page_view_values(invoice_sudo, access_token, **kw)
        # PaymentProcessing.remove_payment_transaction(invoice_sudo.transaction_ids)
        return request.render("account.portal_invoice_page", values)