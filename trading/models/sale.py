from odoo import api, exceptions, fields, models, _
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, \
    pycompat, date_utils
from odoo.tools.misc import formatLang

from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

from odoo.addons import decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    @api.depends('order_line.purchase_order_lines.order_id')
    def _compute_po(self):
        for order in self:
            pos = self.env['purchase.order']
            for line in order.order_line:
                pos |= line.purchase_order_lines.mapped('order_id')
            order.purchase_order_ids = pos
            order.po_count = len(pos)

    @api.multi
    @api.depends('order_line.qty_delivered')
    def _get_delivery_status(self):
        for order in self:
            deliver_quantity = sum(
                order.mapped('order_line').filtered(lambda r: r.product_id.type != 'service').mapped('qty_delivered'))
            order_quantity = sum(
                order.mapped('order_line').filtered(lambda r: r.product_id.type != 'service').mapped('product_uom_qty'))
            if order_quantity != deliver_quantity > 0:
                order.delivery_status = 'partially delivered'
            elif order_quantity == deliver_quantity:
                order.delivery_status = 'delivered'
            else:
                order.delivery_status = 'not delivered'

    trading_id = fields.Many2one(comodel_name="trading.types", string="Trading Type", required=False, )

    delivery_status = fields.Selection([
        ('not delivered', 'Not Delivered'),
        ('partially delivered', 'Partially Delivered'),
        ('delivered', 'Fully Delivered')
    ], string='Delivery Status', compute="_get_delivery_status", store=True, readonly=True)

    po_count = fields.Integer(compute="_compute_po", string='Po Count', copy=False, default=0, store=True)
    purchase_order_ids = fields.Many2many('purchase.order', compute="_compute_po", string='POs', copy=False,
                                   store=True)

    @api.multi
    def action_view_po(self):
        '''
        This function returns an action that display existing Purchase order of given sale order ids.
        When only one found, show the purchase order immediately.
        '''
        action = self.env.ref('purchase.purchase_form_action')
        result = action.read()[0]
        create_po = self.env.context.get('create_po', False)
        # override the context to get rid of the default filtering
        result['context'] = {
            'default_trading_id': self.trading_id.id,
            'default_partner_customer_id': self.partner_id.id,
            'default_sale_id': self.id,
            'default_currency_id': self.currency_id.id,
            'default_company_id': self.company_id.id,
            'company_id': self.company_id.id
        }
        # choose the view_mode accordingly
        if len(self.purchase_order_ids) > 1:
            result['domain'] = "[('id', 'in', " + str(self.purchase_order_ids.ids) + ")]"
        else:
            res = self.env.ref('purchase.purchase_order_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            # Do not set an sale_id if we want to create a new po.
            if not create_po:
                result['res_id'] = self.purchase_order_ids.id or False
        return result



class SaleOrderLine(models.Model):
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'

    @api.multi
    @api.depends('qty_delivered')
    def _get_delivery_status(self):
        for line in self:
            if line.product_uom_qty != line.qty_delivered > 0:
                line.delivery_status = 'partially delivered'
            elif line.product_uom_qty == line.qty_delivered:
                line.delivery_status = 'delivered'
            else:
                line.delivery_status = 'not delivered'

    delivery_status = fields.Selection([
        ('not delivered', 'Not Delivered'),
        ('partially delivered', 'Partially Delivered'),
        ('delivered', 'Fully Delivered')
    ], string='Delivery Status', compute="_get_delivery_status", store=True, readonly=True)

    purchase_order_lines = fields.One2many('purchase.order.line', 'sale_line_id', string="Po Lines", readonly=True,
                                    copy=False)