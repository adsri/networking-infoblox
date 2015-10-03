# Copyright (c) 2015 Infoblox Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock

from neutron import context
from neutron.tests.unit import testlib_api

from networking_infoblox.neutron.common import exceptions as exc
from networking_infoblox.neutron.common import grid
from networking_infoblox.neutron.common import member
from networking_infoblox.neutron.common import utils
from networking_infoblox.neutron.db import infoblox_db as dbi
from networking_infoblox.tests import base


class GridTestCase(base.TestCase, testlib_api.SqlTestCase):

    def setUp(self):
        super(GridTestCase, self).setUp()
        self.ctx = context.get_admin_context()

        self.test_grid_config = grid.GridConfiguration(self.ctx)
        self.test_grid_config.gm_connector = mock.Mock()
        self.test_grid_config.grid_id = 100
        self.test_grid_config.grid_name = "Test Grid 1"
        self.test_grid_config.grid_master_host = '192.168.1.7'
        self.test_grid_config.admin_username = 'admin'
        self.test_grid_config.admin_password = 'infoblox'
        self.test_grid_config.wapi_version = '2.2'

    def _prepare_grid_member(self):
        # create grid
        member_mgr = member.GridMemberManager(self.test_grid_config)
        member_mgr.sync_grid()

        # create members
        member_json = self.connector_fixture.get_object(
            base.FixtureResourceMap.FAKE_MEMBERS_WITH_CLOUD)
        member_mgr._discover_members = mock.Mock()
        member_mgr._discover_members.return_value = member_json

        member_mgr._discover_member_licenses = mock.Mock()
        member_mgr._discover_member_licenses.return_value = None

        member_mgr.sync_members()

    def test_grid_configuration_without_grid_member(self):
        # grid member sync is required; thus it throws an exception when
        # grid member discovery is not performed
        self.assertRaises(exc.InfobloxCannotFindMember,
                          self.test_grid_config.sync)

    def test_grid_configuration_with_grid_member(self):
        # prepare grid members.
        self._prepare_grid_member()

        # check if GM exists
        db_members = dbi.get_members(self.ctx.session,
                                     grid_id=self.test_grid_config.grid_id,
                                     member_type='GM')
        self.assertEqual('GM', db_members[0]['member_type'])

        # get grid config from GM
        config_json = self.connector_fixture.get_object(
            base.FixtureResourceMap.FAKE_GRID_MASTER_GRID_CONFIGURATION)
        self.test_grid_config._discover_config = mock.Mock()
        self.test_grid_config._discover_config.return_value = config_json
        self.test_grid_config.sync()

        # verify if grid config object fields are set correctly
        expected = utils.get_ea_value('Default Network View Scope',
                                      config_json)
        self.assertEqual(expected,
                         self.test_grid_config.default_network_view_scope)
        expected = utils.get_ea_value('Default Network View', config_json)
        self.assertEqual(expected,
                         self.test_grid_config.default_network_view)
        expected = utils.get_ea_value('IP Allocation Strategy', config_json)
        self.assertEqual(expected,
                         self.test_grid_config.ip_allocation_strategy)
        expected = utils.get_ea_value('Default Domain Name Pattern',
                                      config_json)
        self.assertEqual(expected,
                         self.test_grid_config.default_domain_name_pattern)
        expected = utils.get_ea_value('Default Host Name Pattern',
                                      config_json)
        self.assertEqual(expected,
                         self.test_grid_config.default_host_name_pattern)
        expected = utils.get_ea_value('DNS Record Binding Types',
                                      config_json)
        self.assertEqual(expected,
                         self.test_grid_config.dns_record_binding_types)