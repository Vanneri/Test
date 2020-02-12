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

    trading_id = fields.Many2one(comodel_name="trading.types", string="Trading Type", required=False, )
    partner_customer_id = fields.Many2one(comodel_name="res.partner", string="Customer", required=False)
    sale_id = fields.Many2one(comodel_name="sale.order", string="SO", required=False )
