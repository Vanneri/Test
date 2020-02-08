# -*- coding: utf-8 -*-
from odoo import http

# class Trading(http.Controller):
#     @http.route('/trading/trading/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/trading/trading/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('trading.listing', {
#             'root': '/trading/trading',
#             'objects': http.request.env['trading.trading'].search([]),
#         })

#     @http.route('/trading/trading/objects/<model("trading.trading"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('trading.object', {
#             'object': obj
#         })