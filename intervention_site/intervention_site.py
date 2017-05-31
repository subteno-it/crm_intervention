# -*- coding: utf-8 -*-

from openerp.osv import orm
from openerp.osv import fields


class InterventionSite(orm.Model):
    _name = 'intervention.site'
    _description = 'Site of the intervention'

    _columns = {
        'name': fields.char(
            'Name', size=64, required=True, help='Name of the site'),
        'partner_id': fields.many2one(
            'res.partner', 'Address', help='Select address for this site'),
        'customer_id': fields.many2one(
            'res.partner', 'Customer', help='Select customer for this site'),
        'active': fields.boolean(
            'Active', help='if check, this object is always available'),
        'contract_id': fields.many2one(
            'account.analytic.account', 'Contract',
            help='Contract relate to this site'),
        'equipment_ids': fields.one2many(
            'intervention.equipment', 'site_id', 'Equipments',
            help='Equipment in this site'),
    }

    _defaults = {
        'active': True,
    }
