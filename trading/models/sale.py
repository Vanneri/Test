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

    @api.multi
    def button_create_po(self):
        pass


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