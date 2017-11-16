# -*- coding: utf-8 -*-
##############################################################################
#
#    crm_intrevention module for OpenERP, Managing intervention in CRM
#    Copyright (C) 2017 Christophe CHAUVET <christophe.chauvet@gmail.com>
#
#    This file is a part of crm_intrevention
#
#    crm_intrevention is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    crm_intrevention is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging

__name__ = "Upgrade existing duration"
_logger = logging.getLogger(__name__)


def migrate(cr, v):
    """
    Put your explanation here

    :param cr: Current cursor to the database
    :param v:
    """
    # First we fix, the entry with no ended date
    cr.execute("""UPDATE crm_intervention
                     SET date_effective_end = date_effective_start + '9 hour'::interval,
                         duration_effective = 8.0, pause_effective = 1.0
                  WHERE date_effective_end IS NULL
                    AND alldays_effective = true;""")
    cr.execute("""UPDATE crm_intervention
                     SET duration_effective = (date_part('epoch', (date_effective_end - date_effective_start)) / 3600) - pause_effective
                   WHERE date_effective_end IS NOT NULL;""")
    _logger.info('End upgrade intervention version %s' % v)
    cr.commit()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
