from odoo import models, fields, api


class Trading(models.Model):
    _name = 'trading.types'
    _rec_name = 'name'
    _description = 'Trading Types'

    name = fields.Char()
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)


