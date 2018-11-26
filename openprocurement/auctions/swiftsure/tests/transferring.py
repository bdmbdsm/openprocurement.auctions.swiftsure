# -*- coding: utf-8 -*-
import unittest

from openprocurement.auctions.core.tests.base import snitch
from openprocurement.auctions.core.tests.plugins.transferring.blanks.resource_blanks import (
    create_auction_by_concierge)
from openprocurement.auctions.core.tests.plugins.transferring.mixins import (
    AuctionOwnershipChangeTestCaseMixin
)
from openprocurement.auctions.core.tests.fixtures.related_process import (
    test_related_process_data,
)
from openprocurement.auctions.swiftsure.tests.base import BaseAuctionWebTest


class AuctionOwnershipChangeResourceTest(BaseAuctionWebTest,
                                         AuctionOwnershipChangeTestCaseMixin):

    first_owner = 'broker3'
    second_owner = 'broker3'
    concierge = 'concierge'
    test_owner = 'broker3t'
    invalid_owner = 'broker1'
    initial_auth = ('Basic', (first_owner, ''))

    # swiftsure auction can not be changed during enquiryPeriod
    test_new_owner_can_change = None

    def setUp(self):
        super(AuctionOwnershipChangeResourceTest, self).setUp()
        self.not_used_transfer = self.create_transfer()

    def create_auction_by_concierge(self):
        self.app.authorization = ('Basic', (self.concierge, ''))
        transfer_token = sha512(self.not_used_transfer['access']['transfer']).hexdigest()
        data = deepcopy(self.initial_data)
        data['transfer_token'] = transfer_token
        data['status'] = 'pending.activation'
        data['relatedProcesses'] = [deepcopy(test_related_process_data)]
        data['relatedProcesses'][0]['type'] = 'lot'

        # passing SHA-512 hash of transfer token as a header
        response = self.app.post_json('/auctions', {'data': data})
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(response.content_type, 'application/json')
        self.assertNotIn('transfer', response.json['access'])
        auction_id = response.json['data']['id']

        self.app.authorization = ('Basic', (self.first_owner, ''))

        transfer = self.create_transfer()

        # trying to change ownership
        self.use_transfer(transfer,
                          auction_id,
                          self.not_used_transfer['access']['transfer'])

        # assuring that transfer is used properly
        response = self.app.get('/transfers/{}'.format(transfer['data']['id']))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(
            response.json['data']['usedFor'], '/auctions/{}'.format(auction_id)
        )

        # assuring that ownership changed successfully
        response = self.app.get('/auctions/{}'.format(auction_id))
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.json['data']['owner'], self.app.authorization[1][0])


def suite():
    tests = unittest.TestSuite()
    tests.addTest(unittest.makeSuite(AuctionOwnershipChangeResourceTest))
    return tests


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
