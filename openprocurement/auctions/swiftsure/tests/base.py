# -*- coding: utf-8 -*-
import os
from uuid import uuid4
from datetime import datetime, timedelta
from copy import deepcopy

from openprocurement.auctions.core.utils import (
    apply_data_patch,
    SANDBOX_MODE,
    calculate_business_date as cbd,
)

from openprocurement.auctions.core.tests.base import (
    BaseWebTest as CoreBaseWebTest,
    BaseAuctionWebTest as CoreBaseAuctionWebTest,
    test_organization, test_procuringEntity, base_test_bids
)

from openprocurement.auctions.swiftsure.constants import (
    DEFAULT_PROCUREMENT_METHOD_TYPE,
)

from openprocurement.auctions.swiftsure.tests.fixtures import (
    PARTIAL_MOCK_CONFIG,
    post_related_lot,
)

from openprocurement.auctions.core.tests.base import MOCK_CONFIG as BASE_MOCK_CONFIG
from openprocurement.auctions.core.utils import connection_mock_config

now = datetime.now()
test_auction_data = {
    "title": u"футляри до державних нагород",
    "tenderAttempts": 1,
    "auctionParameters": {
        "type": "english"
    },
    "procuringEntity": test_procuringEntity,
    "value": {
        "amount": 100,
        "currency": u"UAH"
    },
    "minimalStep": {
        "amount": 35,
        "currency": u"UAH"
    },
    "items": [
        {
            "description": u"Земля для військовослужбовців",
            "classification": {
                "scheme": u"CPV",
                "id": u"66113000-5",
                "description": u"Земельні ділянки"
            },
            "unit": {
                "name": u"item",
                "code": u"44617100-9"
            },
            "quantity": 5,
            "registrationDetails": {
                "status": "unknown",
            },
            "address": {
                "countryName": u"Україна",
                "postalCode": "79000",
                "region": u"м. Київ",
                "locality": u"м. Київ",
                "streetAddress": u"вул. Банкова 1"
            }
        }
    ],
    "auctionPeriod": {
        "startDate": cbd(now.date(), timedelta(days=14), None).isoformat()
    },
    "procurementMethodType": DEFAULT_PROCUREMENT_METHOD_TYPE
}
if SANDBOX_MODE:
    test_auction_data['procurementMethodDetails'] = 'quick, accelerator=1440'
    test_auction_data['submissionMethodDetails'] = 'test submissionMethodDetails'

test_features_auction_data = test_auction_data.copy()
test_features_item = test_features_auction_data['items'][0].copy()
test_features_item['id'] = "1"
test_features_auction_data['items'] = [test_features_item]
test_features_auction_data["features"] = [{"code": "OCDS-123454-AIR-INTAKE",
                                           "featureOf": "item",
                                           "relatedItem": "1",
                                           "title": u"Потужність всмоктування",
                                           "title_en": "Air Intake",
                                           "description":
                                               u"Ефективна потужність всмоктування пилососа, в ватах (аероватах)",
                                           "enum": [{"value": 0.1,
                                                     "title": u"До 1000 Вт"},
                                                    {"value": 0.15,
                                                     "title": u"Більше 1000 Вт"}]},
                                          {"code": "OCDS-123454-YEARS",
                                           "featureOf": "tenderer",
                                           "title": u"Років на ринку",
                                           "title_en": "Years trading",
                                           "description": u"Кількість років, які організація учасник працює на ринку",
                                           "enum": [{"value": 0.05,
                                                     "title": u"До 3 років"},
                                                    {"value": 0.1,
                                                     "title": u"Більше 3 років, менше 5 років"},
                                                    {"value": 0.15,
                                                     "title": u"Більше 5 років"}]}]

test_bids = []
for i in base_test_bids:
    i = deepcopy(i)
    i.update({'qualified': True})
    test_bids.append(i)

test_lots = [
    {
        'title': 'lot title',
        'description': 'lot description',
        'value': test_auction_data['value'],
        'minimalStep': test_auction_data['minimalStep'],
    }
]
test_features = [
    {
        "code": "code_item",
        "featureOf": "item",
        "relatedItem": "1",
        "title": u"item feature",
        "enum": [
            {
                "value": 0.01,
                "title": u"good"
            },
            {
                "value": 0.02,
                "title": u"best"
            }
        ]
    },
    {
        "code": "code_tenderer",
        "featureOf": "tenderer",
        "title": u"tenderer feature",
        "enum": [
            {
                "value": 0.01,
                "title": u"good"
            },
            {
                "value": 0.02,
                "title": u"best"
            }
        ]
    }
]

test_documents = [
    {
        u'dateModified': u'2018-06-13T18:52:38.439672+03:00',
        u'datePublished': u'2018-06-13T18:52:38.439645+03:00',
        u'documentOf': u'auction',
        u'format': u'application/msword',
        u'id': u'5b15488495424a70873f9062f43996fd',
        u'title': u'first_document.doc',
        u'url': u'http://localhost/api/2.5/auctions/d391dc0e36e64e9599cadaff069555ca/documents/5b15488495424a70873f9062f43996fd?download=79e962b14487481d87996bcdffa05d58'  # noqa
    },
    {
        u'dateModified': u'2018-06-13T19:07:35.860955+03:00',
        u'datePublished': u'2018-06-13T19:07:35.860933+03:00',
        u'documentOf': u'lot',
        u'relatedItem': u'1' * 32,
        u'format': u'application/msword',
        u'id': u'0aa995cdfa234e4fa432ac24f7178763',
        u'title': u'second_document.doc',
        u'url': u'http://localhost/api/2.5/auctions/35e55ce810834138aa9e768e9a01ffdb/documents/0aa995cdfa234e4fa432ac24f7178763?download=7995192f6c3f41b497fdcdc9cc3f7c49'  # noqa
    }
]


MOCK_CONFIG = connection_mock_config(PARTIAL_MOCK_CONFIG,
                                     base=BASE_MOCK_CONFIG,
                                     connector=('plugins', 'api', 'plugins',
                                                'auctions.core', 'plugins'))


class BaseWebTest(CoreBaseWebTest):

    """Base Web Test to test openprocurement.auctions.swiftsure.

    It setups the database before each test and delete it after.
    """

    relative_to = os.path.dirname(__file__)
    mock_config = MOCK_CONFIG


class BaseAuctionWebTest(CoreBaseAuctionWebTest):
    relative_to = os.path.dirname(__file__)
    initial_data = test_auction_data
    initial_organization = test_organization
    mock_config = MOCK_CONFIG
    registry = False

    def create_auction(self):
        data = deepcopy(self.initial_data)
        if self.initial_lots:
            lots = []
            for i in self.initial_lots:
                lot = deepcopy(i)
                lot['id'] = uuid4().hex
                lots.append(lot)
            data['lots'] = self.initial_lots = lots
            for i, item in enumerate(data['items']):
                item['relatedLot'] = lots[i % len(lots)]['id']
        if self.registry:
            data.update(
                {
                    'status': "draft",
                    # 'merchandisingObject': uuid4().hex
                }
            )
            response = self.app.post_json('/auctions', {'data': data})
            auction = response.json['data']
            self.auction_token = response.json['access']['token']

            post_related_lot(self, auction['id'])

            self.auction_transfer = response.json['access']['transfer']
            self.auction_id = auction['id']
            authorization = self.app.authorization
            self.app.authorization = ('Basic', ('concierge', ''))
            response = self.app.patch_json('/auctions/{}'.format(self.auction_id),
                                           {'data': {'status': 'pending.activation'}})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(
                response.json['data']['status'],
                'pending.activation')
            self.app.authorization = authorization
            response = self.app.patch_json('/auctions/{}?acc_token={}'.format(
                self.auction_id, self.auction_token
            ), {'data': {'status': 'active.tendering'}})
            self.assertEqual(response.status, '200 OK')
            self.assertEqual(response.content_type, 'application/json')
            auction = response.json['data']
            self.assertEqual(auction['status'], 'active.tendering')
        else:
            response = self.app.post_json('/auctions', {'data': data})
            auction = response.json['data']
            self.auction_token = response.json['access']['token']

            self.auction_transfer = response.json['access']['transfer']
            self.auction_id = auction['id']
        status = auction['status']
        if self.initial_bids:
            self.initial_bids_tokens = {}
            response = self.set_status('active.tendering')
            status = response.json['data']['status']
            bids = []
            for i in self.initial_bids:
                if self.initial_lots:
                    i = i.copy()
                    value = i.pop('value')
                    i['lotValues'] = [
                        {
                            'value': value,
                            'relatedLot': l['id'],
                        }
                        for l in self.initial_lots
                    ]
                response = self.app.post_json(
                    '/auctions/{}/bids'.format(self.auction_id), {'data': i})
                self.assertEqual(response.status, '201 Created')
                bids.append(response.json['data'])
                self.initial_bids_tokens[response.json['data'][
                    'id']] = response.json['access']['token']
            self.initial_bids = bids
        if self.initial_status != status:
            self.set_status(self.initial_status)

    def set_status(self, status, extra=None):
        data = {'status': status}
        if status == 'active.tendering':
            data.update({
                "enquiryPeriod": {
                    "startDate": (now).isoformat(),
                    "endDate": cbd(now, timedelta(days=7), None).isoformat()
                },
                "tenderPeriod": {
                    "startDate": (now).isoformat(),
                    "endDate": cbd(now, timedelta(days=7), None).isoformat()
                }
            })
        elif status == 'active.auction':
            data.update({
                "enquiryPeriod": {
                    "startDate": cbd(now, -timedelta(days=7), None).isoformat(),
                    "endDate": (now).isoformat()
                },
                "tenderPeriod": {
                    "startDate": cbd(now, -timedelta(days=7), None).isoformat(),
                    "endDate": (now).isoformat()
                },
                "auctionPeriod": {
                    "startDate": (now).isoformat()
                }
            })
            if self.initial_lots:
                data.update({
                    'lots': [
                        {
                            "auctionPeriod": {
                                "startDate": (now).isoformat()
                            }
                        }
                        for i in self.initial_lots
                    ]
                })
        elif status == 'active.qualification':
            data.update({
                "enquiryPeriod": {
                    "startDate": cbd(now, -timedelta(days=8), None).isoformat(),
                    "endDate": cbd(now, -timedelta(days=1), None).isoformat()
                },
                "tenderPeriod": {
                    "startDate": cbd(now, -timedelta(days=8), None).isoformat(),
                    "endDate": cbd(now, -timedelta(days=1), None).isoformat()
                },
                "auctionPeriod": {
                    "startDate": cbd(now, -timedelta(days=1), None).isoformat(),
                    "endDate": (now).isoformat()
                },
                "awardPeriod": {
                    "startDate": (now).isoformat()
                }
            })
            if self.initial_lots:
                data.update({
                    'lots': [
                        {
                            "auctionPeriod": {
                                "startDate": cbd(now, -timedelta(days=1), None).isoformat(),
                                "endDate": (now).isoformat()
                            }
                        }
                        for i in self.initial_lots
                    ]
                })
        elif status == 'active.awarded':
            data.update({
                "enquiryPeriod": {
                    "startDate": cbd(now, -timedelta(days=8), None).isoformat(),
                    "endDate": cbd(now, -timedelta(days=1), None).isoformat()
                },
                "tenderPeriod": {
                    "startDate": cbd(now, -timedelta(days=8), None).isoformat(),
                    "endDate": cbd(now, -timedelta(days=1), None).isoformat()
                },
                "auctionPeriod": {
                    "startDate": cbd(now, -timedelta(days=1), None).isoformat(),
                    "endDate": (now).isoformat()
                },
                "awardPeriod": {
                    "startDate": (now).isoformat(),
                    "endDate": (now).isoformat()
                }
            })
            if self.initial_lots:
                data.update({
                    'lots': [
                        {
                            "auctionPeriod": {
                                "startDate": cbd(now, -timedelta(days=1), None).isoformat(),
                                "endDate": (now).isoformat()
                            }
                        }
                        for i in self.initial_lots
                    ]
                })
        elif status == 'complete':
            data.update({
                "enquiryPeriod": {
                    "startDate": cbd(now, -timedelta(days=18), None).isoformat(),
                    "endDate": cbd(now, -timedelta(days=11), None).isoformat()
                },
                "tenderPeriod": {
                    "startDate": cbd(now, -timedelta(days=18), None).isoformat(),
                    "endDate": cbd(now, -timedelta(days=11), None).isoformat()
                },
                "auctionPeriod": {
                    "startDate": cbd(now, -timedelta(days=11), None).isoformat(),
                    "endDate": cbd(now, -timedelta(days=10), None).isoformat()
                },
                "awardPeriod": {
                    "startDate": cbd(now, -timedelta(days=10), None).isoformat(),
                    "endDate": cbd(now, -timedelta(days=10), None).isoformat()
                }
            })
            if self.initial_lots:
                data.update({
                    'lots': [
                        {
                            "auctionPeriod": {
                                "startDate": cbd(now, -timedelta(days=11), None).isoformat(),
                                "endDate": cbd(now, -timedelta(days=10), None).isoformat()
                            }
                        }
                        for i in self.initial_lots
                    ]
                })
        if extra:
            data.update(extra)
        auction = self.db.get(self.auction_id)
        auction.update(apply_data_patch(auction, data))
        self.db.save(auction)
        authorization = self.app.authorization
        self.app.authorization = ('Basic', ('chronograph', ''))
        response = self.app.get('/auctions/{}'.format(self.auction_id))
        self.app.authorization = authorization
        self.assertEqual(response.status, '200 OK')
        self.assertEqual(response.content_type, 'application/json')
        return response
