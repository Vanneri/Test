from odoo import models, fields, api


class Trading(models.Model):
    _name = 'trading.types'
    _rec_name = 'name'
    _description = 'Trading Types'

    name = fields.Char()

