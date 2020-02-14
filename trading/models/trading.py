from odoo import models, fields, api


class Trading(models.Model):
    _name = 'trading.types'
    _rec_name = 'name'
    _description = 'Trading Types'

    @api.multi
    def _compute_sopo_count(self):
        for t in self:
            t.count_trading_so = len(self.env['sale.order'].search([('trading_id','=',t.id)]).ids)
            t.count_trading_po = len(self.env['purchase.order'].search([('trading_id','=',t.id)]).ids)


    name = fields.Char()
    color = fields.Integer('Color')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    count_trading_so = fields.Integer(compute='_compute_sopo_count')
    count_trading_po = fields.Integer(compute='_compute_sopo_count')

    def _get_action(self, action_xmlid):
        # TDE TODO check to have one view + custo in methods
        action = self.env.ref(action_xmlid).read()[0]
        if self:
            action['display_name'] = self.display_name
        return action

    def get_action_trading_tree_saleorder(self):
        return self._get_action('sale.action_orders')

    def get_action_trading_tree_purchaseorder(self):
        return self._get_action('purchase.purchase_form_action')

