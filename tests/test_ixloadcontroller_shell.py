#!/usr/bin/python
# -*- coding: utf-8 -*-

from os import path
import sys
import json
import unittest

from cloudshell.api.cloudshell_api import AttributeNameValue, InputNameValue
from cloudshell.traffic.tg_helper import get_reservation_resources, set_family_attribute
from shellfoundry.releasetools.test_helper import (create_session_from_cloudshell_config, create_command_context,
                                                   end_reservation)

controller = '192.168.15.23'
port = '8080'
version = '8.01.106.3'
version = '8.40.0.277'

attributes = [AttributeNameValue('Controller Version', version),
              AttributeNameValue('Controller Address', controller),
              AttributeNameValue('Controller TCP Port', port)]

ports = ['PS-2G/Module1/Port1', 'PS-2G/Module1/Port2']
ports = ['IxVM 801/Module1/Port1', 'IxVM 801/Module2/Port1']
ports = ['ixia 2g/Module1/Port1', 'ixia 2g/Module2/Port1']
ports = ['184/Module1/Port1', '185/Module1/Port1']


class TestIxLoadControllerDriver(unittest.TestCase):

    def setUp(self):
        self.session = create_session_from_cloudshell_config()
        self.context = create_command_context(self.session, ports, 'IxLoad Controller', attributes)

    def tearDown(self):
        self.session.EndReservation(self.context.reservation.reservation_id)
        end_reservation(self.session, self.context.reservation.reservation_id)

    def test_load_config(self):
        self._load_config(path.join(path.dirname(__file__), 'test_config.rxf'))

    def test_run_traffic(self):
        self._load_config(path.join(path.dirname(__file__), 'test_config.rxf'))
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxLoad Controller', 'Service',
                                    'start_test', [InputNameValue('blocking', 'True')])
        stats = self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxLoad Controller', 'Service',
                                            'get_statistics', [InputNameValue('view_name', 'Test_Client'),
                                                               InputNameValue('output_type', 'JSON')])
        assert(int(json.loads(stats.Output)['20']['TCP Connections Established']) >= 0)

        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxLoad Controller', 'Service',
                                    'start_test', [InputNameValue('blocking', 'False')])
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxLoad Controller', 'Service',
                                    'stop_test')
        stats = self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxLoad Controller', 'Service',
                                            'get_statistics', [InputNameValue('view_name', 'Test_Client'),
                                                               InputNameValue('output_type', 'JSON')])
        try:
            assert(int(json.loads(stats.Output)['20']['TCP Connections Established']) >= 0)
        except KeyError as _:
            return
        raise Exception('Too many entries in stats...')

    def _load_config(self, config):
        reservation_ports = get_reservation_resources(self.session, self.context.reservation.reservation_id,
                                                      'Generic Traffic Generator Port',
                                                      'PerfectStorm Chassis Shell 2G.GenericTrafficGeneratorPort',
                                                      'Ixia Chassis Shell 2G.GenericTrafficGeneratorPort')
        set_family_attribute(self.session, reservation_ports[0], 'Logical Name', 'Traffic1@Network1')
        set_family_attribute(self.session, reservation_ports[1], 'Logical Name', 'Traffic2@Network2')
        self.session.ExecuteCommand(self.context.reservation.reservation_id, 'IxLoad Controller', 'Service',
                                    'load_config', [InputNameValue('ixl_config_file_name', config)])


if __name__ == '__main__':
    sys.exit(unittest.main())
