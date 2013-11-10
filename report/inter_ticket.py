# -*- coding: utf-8 -*-
##############################################################################
#
#    Crm_intervention_report module for OpenERP, add reports in intervention
#    Copyright (C) 2009 SYLEAM (<http://www.Syleam.fr>) Sebastien LANGE
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from openerp.report import report_sxw
from openerp.tools.translate import _



class inter_ticket(report_sxw.rml_parse):

        def upcase(self, name):
                return name.upper()

        def fill(self, name, nbr):
                return str(name).zfill(nbr)

        def weekdayname(self, numberDay, context=None):
            weekdayname = [
                _("sunday"),
                _("monday"),
                _("tuesday"),
                _("wednesday"),
                _("thursday"),
                _("friday"),
                _("saturday"),
            ]
            return weekdayname[int(numberDay)]

        def __init__(self, cr, uid, name, context):
                super(inter_ticket, self).__init__(cr, uid, name, context)
                self.localcontext.update({
                        'time': time,
                        'upcase': self.upcase,
                        'fill': self.fill,
                        'weekdayname': self.weekdayname,
                })
#
# Mettre header=False pour ne pas utiliser le bandeau en haut et en bas
#
report_sxw.report_sxw(
    'report.crm_intervention.inter_ticket',
    'crm.intervention',
    'addons/crm_intervention/report/inter_ticket.rml',
    parser=inter_ticket,
    header=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
