from odoo import api, exceptions, fields, models, _
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, \
    pycompat, date_utils
from odoo.tools.misc import formatLang

from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

from odoo.addons import decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _name = 'purchase.order'
    _inherit = 'purchase.order'

    @api.multi
    @api.depends('order_line.qty_received')
    def _get_delivery_status(self):
        for order in self:
            received_quantity = sum(order.mapped('order_line').filtered(lambda r: r.product_id.type != 'service').mapped('qty_received'))
            order_quantity = sum(order.mapped('order_line').filtered(lambda r: r.product_id.type != 'service').mapped('product_qty'))
            if order_quantity != received_quantity > 0:
                order.delivery_status = 'partially delivered'
            elif order_quantity == received_quantity:
                order.delivery_status = 'delivered'
            else:
                order.delivery_status = 'not delivered'

    trading_id = fields.Many2one(comodel_name="trading.types", string="Trading Type", required=False, )
    partner_customer_id = fields.Many2one(comodel_name="res.partner", string="Customer", required=False)
    sale_id = fields.Many2one(comodel_name="sale.order", string="SO", required=False )

    delivery_status = fields.Selection([
        ('not delivered', 'Not Delivered'),
        ('partially delivered', 'Partially Delivered'),
        ('delivered', 'Fully Delivered')
    ], string='Delivery Status', compute="_get_delivery_status", store=True, readonly=True)


    @api.onchange('partner_customer_id')
    def _onchange_partner_customer_id(self):
        if self.partner_id and not self.trading_id:
            raise UserError(_('Choose Trading before choosing customer'))

    def _prepare_po_line_from_so_line(self, line):

        """Returns the PO lines from SO lines """

        taxes = line.tax_id
        po_line_tax_ids = line.order_id.fiscal_position_id.map_tax(taxes, line.product_id,
                                                                        line.order_id.partner_id)
        data = {
            'sale_line_id': line.id,
            'name': line.order_id.name + ': ' + line.name,
            'product_uom': line.product_uom.id,
            'product_id': line.product_id.id,
            'price_unit': line.order_id.currency_id._convert(
                line.price_unit, self.currency_id, line.company_id, fields.Date.today(), round=False),
            'product_qty': line.product_uom_qty,
            'taxes_id': po_line_tax_ids.ids
        }
        return data

    # Load all unsold SO lines
    @api.onchange('sale_id')
    def purchase_order_change(self):
        if not self.sale_id:
            return {}


        new_lines = self.env['purchase.order.line']
        for line in self.sale_id.order_line - self.order_line.mapped('sale_line_id'):
            data = self._prepare_po_line_from_so_line(line)
            new_line = new_lines.new(data)
            new_lines += new_line

        self.order_line += new_lines
        self.sale_id = False
        return {}

    @api.onchange('order_line')
    def _onchange_order_line(self):
        sale_ids = self.order_line.mapped('sale_id')
        if sale_ids:
            self.origin = ', '.join(sale_ids.mapped('name'))


class PurchaseOrderLine(models.Model):
    _name = 'purchase.order.line'
    _inherit = 'purchase.order.line'

    @api.multi
    @api.depends('qty_received')
    def _get_delivery_status(self):
        for line in self:
            if line.product_qty != line.qty_received > 0:
                line.delivery_status = 'partially delivered'
            elif line.product_qty == line.qty_received:
                line.delivery_status = 'delivered'
            else:
                line.delivery_status = 'not delivered'

    sale_line_id = fields.Many2one(comodel_name="sale.order.line", string="SO Line", required=False)
    sale_id = fields.Many2one(comodel_name="sale.order", string="SO", required=False,related='sale_line_id.order_id')

    delivery_status = fields.Selection([
        ('not delivered', 'Not Delivered'),
        ('partially delivered', 'Partially Delivered'),
        ('delivered', 'Fully Delivered')
    ], string='Delivery Status', compute="_get_delivery_status", store=True, readonly=True)




