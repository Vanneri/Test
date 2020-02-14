from datetime import datetime, timedelta, date
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, AccessError
from ast import literal_eval


class MaterialRequest(models.Model):
    _name = "material.request"
    _description = "Internal Material Request"

    name = fields.Char(
        'Sequence', default='New',
        copy=False, index=True)
    reference = fields.Char(string="Reference")
    state = fields.Selection([
        ('draft', 'Draft'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting For Approval'),
        ('approved', 'Approved'), ('done', 'Done')], string='Status', index=True, default='draft',
        store=True, help=" * Draft: not confirmed yet and will not be scheduled until confirmed\n"
                         " * Cancelled: has been cancelled, can't be confirmed anymore")
    requested_from = fields.Many2one('stock.location', string="Requested From",domain=[('usage', '=', 'internal')])
    requested_to = fields.Many2one('stock.location', string="Requested To",domain=[('usage', '=', 'internal')])
    transfer_date = fields.Datetime(string="Scheduled Date", required=True, default=fields.Datetime.now)
    material_line_ids = fields.One2many('material.request.line', 'material_id', string="Material Request Line")
    picking_type_id = fields.Many2one('stock.picking.type', string="Stock Picking Type")
    transfer_reference = fields.Many2one('stock.picking', string="Transfer Reference", readonly=True)
    origin = fields.Char(string="Origin", readonly=True)
    transfer_id = fields.Char(string="Transfer")
    intransit = fields.Boolean("In Transit", default=False)

    @api.onchange('requested_to')
    def onchange_requested_to(self):
        if self.requested_to:
            if self.requested_from and self.requested_from == self.requested_to:
                raise UserError(
                    _('You can not choose same location '))
        picking_obj = self.env['stock.picking.type']
        self.picking_type_id = picking_obj.sudo().search(
            [('code', '=', 'internal'), ('default_location_src_id', '=', self.requested_to.id)]).id

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('material.request') or '/'
        result = super(MaterialRequest, self).create(vals)
        return result

    @api.multi
    def do_confirm(self):
        self.write({'state': 'waiting'})

    @api.multi
    def approve_product(self):
        '''
        This function approves the transfer of materials
        :return:
        '''
        transit = self.env['stock.location'].sudo().search([('usage', '=', 'transit')], limit=1)
        picking_obj = self.env['stock.picking.type'].sudo().search(
            [('code', '=', 'internal'), ('default_location_src_id', '=', self.requested_to.id)]).id
        for vals in self:
            pick = {
                'origin': vals.name,
                'picking_type_id': picking_obj,
                'location_id': self.requested_to.id,
                'location_dest_id': self.requested_from.id,
                'min_date': vals.transfer_date,
                'company_id': self.requested_to.company_id.id
            }
        picking = self.env['stock.picking'].sudo().create(pick)
        for line in self.material_line_ids:
            move = {
                'name': vals.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity if line.quantity < line.product_id.qty_available else line.product_id.qty_available,
                'product_uom': line.unit_of_measure.id,
                'location_id': self.requested_to.id,
                'location_dest_id': self.requested_from.id,
                'picking_id': picking.id,
                'company_id': self.requested_to.company_id.id,
            }
            self.env['stock.move'].sudo().create(move)
        picking.sudo().action_assign()
        self.transfer_reference = picking.id
        self.transfer_id = self.transfer_reference.name
        self.write({'state': 'approved'})

    @api.multi
    def do_approve(self):
        
        for line in self.material_line_ids:
            if line.product_id.with_context({'location': self.requested_to.id}).sudo().qty_available < 0:
                raise UserError(_("Material %s is not available") % line.product_id.name)
            elif line.quantity > line.product_id.with_context({'location': self.requested_to.id}).sudo().qty_available:
                raise UserError(_("%s Available quantity is %s") % (line.product_id.name, line.product_id.with_context({
                    'location':self.requested_to.id}).qty_available))
        self.approve_product()

    @api.multi
    def done_transfer(self):
        picking1 = self.env['stock.picking'].search([('id', '=', self.transfer_reference.id)], limit=1)
        picking1.action_assign()
        transfer = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, picking1.id)]})
        transfer.process()
        self.write({'state': 'done'})


class MaterialRequestLine(models.Model):
    _name = 'material.request.line'

    product_id = fields.Many2one('product.product')
    quantity = fields.Float(string="Intial Demand", default=1.0)
    quantity_done = fields.Float(string="Quantity Delivered", default=0.0)
    unit_of_measure = fields.Many2one('uom.uom', string="Unit Of Measure")
    product_cost = fields.Float(string="Cost")
    product_unit_price = fields.Float(string="Unit Price")
    material_id = fields.Many2one('material.request', string="Material Request")

    @api.onchange('quantity_done')
    def _onchange_quantity_done(self):
        if self.quantity_done > self.quantity:
            raise UserError(_(
                'You have processed more than what was initially planned for the product %s' % (self.product_id.name)))

    @api.onchange('product_id')
    def onchange_product_id(self):
        for vals in self:
            if vals.product_id:
                vals.unit_of_measure = vals.product_id.uom_id
                vals.product_cost = vals.product_id.standard_price
                vals.product_unit_price = vals.product_id.list_price
