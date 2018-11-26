# -*- coding: utf-8 -*-
import unittest
from copy import deepcopy

from openprocurement.auctions.core.tests.base import (
    RelatedProcessesTestMixinBase,
)
from openprocurement.auctions.swiftsure.tests.base import (
    BaseAuctionWebTest,
    test_auction_data,
)

from openprocurement.auctions.core.tests.fixtures.related_process import (
    test_related_process_data,
)


class RelatedProcessesTestMixin(RelatedProcessesTestMixinBase):
    """These methods adapt test blank to the test case

    This adaptation is required because the mixin would test different types
    of resources, e.g. auctions, lots, assets.
    """

    def mixinSetUp(self):
        self.base_resource_collection_url = '/auctions'
        self.base_resource_url = '/auctions/{0}'.format(self.auction_id)

        token = self.db[self.auction_id]['owner_token']
        self.access_header = {'X-Access-Token': str(token)}

        self.base_resource_initial_data = test_auction_data
        self.initial_related_process_data = test_related_process_data

        # only concierge can edit relatedProcesses
        self.app.authorization = ('Basic', ('concierge', ''))

    def test_create_related_process_batch_mode(self):
        """Overrides test frm original test mixin, bcs of auction creation logic"""
        self.mixinSetUp()

        data = deepcopy(self.base_resource_initial_data)
        related_process_1 = {
            'id': '1' * 32,
            'identifier': 'SOME-IDENTIFIER',
            'type': 'asset',
            'relatedProcessID': '2' * 32
        }
        data['relatedProcesses'] = [
           related_process_1
        ]
        data['status'] = 'draft'
        response = self.app.post_json(self.base_resource_collection_url, params={'data': data})
        parent_id = response.json['data']['id']
        self.assertEqual(response.status, '201 Created')
        self.assertEqual(len(response.json['data']['relatedProcesses']), 1)
        self.assertEqual(response.json['data']['relatedProcesses'][0]['type'], related_process_1['type'])
        self.assertEqual(
            response.json['data']['relatedProcesses'][0]['relatedProcessID'],
            related_process_1['relatedProcessID']
        )
        self.assertNotEqual(response.json['data']['relatedProcesses'][0]['id'], related_process_1['id'])
        self.assertIn('identifier', response.json['data']['relatedProcesses'][0])

        related_process_id = response.json['data']['relatedProcesses'][0]['id']

        # Check relatedProcess resource
        # due to test universality, there's a trying to avoid tight places
        templates = ('/{0}', '{0}')
        for t in templates:
            try:
                response = self.app.get(
                    self.base_resource_collection_url +
                    t.format(parent_id) +
                    self.RESOURCE_ID_POSTFIX.format(related_process_id)
                )
            except Exception:
                continue
        self.assertEqual(response.json['data']['type'], related_process_1['type'])
        self.assertEqual(response.json['data']['relatedProcessID'], related_process_1['relatedProcessID'])
        self.assertNotEqual(response.json['data']['id'], related_process_1['id'])
        self.assertIn('identifier', response.json['data'])


class SwiftsureAuctionRelatedProcessResourceTest(BaseAuctionWebTest, RelatedProcessesTestMixin):
    initial_status = 'active.tendering'
    initial_data = test_auction_data


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SwiftsureAuctionRelatedProcessResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
