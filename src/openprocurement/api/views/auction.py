# -*- coding: utf-8 -*-
from cornice.service import Service
from openprocurement.api.utils import (
    apply_data_patch,
    filter_data,
    save_tender,
)
from openprocurement.api.validation import (
    validate_tender_auction_data,
    validate_tender_exists_by_tender_id,
)


auction = Service(name='Tender Auction', path='/tenders/{tender_id}/auction', renderer='json')


@auction.get(renderer='json', validators=(validate_tender_exists_by_tender_id,))
def get_auction(request):
    """Get auction info.

    Get tender auction info
    -----------------------

    Example request to get tender auction information:

    .. sourcecode:: http

        GET /tenders/4879d3f8ee2443169b5fbbc9f89fa607/auction HTTP/1.1
        Host: example.com
        Accept: application/json

    This is what one should expect in response:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "data": {
                "dateModified": "2014-10-27T08:06:58.158Z",
                "bids": [
                    {
                        "value": {
                            "amount": 500,
                            "currency": "UAH",
                            "valueAddedTaxIncluded": true
                        }
                    },
                    {
                        "value": {
                            "amount": 485,
                            "currency": "UAH",
                            "valueAddedTaxIncluded": true
                        }
                    }
                ],
                "minimalStep":{
                    "amount": 35,
                    "currency": "UAH"
                },
                "tenderPeriod":{
                    "startDate": "2014-11-04T08:00:00"
                }
            }
        }

    """
    tender = request.validated['tender']
    if tender.status != 'active.auction':
        request.errors.add('body', 'data', 'Can\'t get auction info in current tender status')
        request.errors.status = 403
        return
    auction_info = tender.serialize("auction_view")
    return {'data': auction_info}


@auction.patch(content_type="application/json", validators=(validate_tender_auction_data), renderer='json')
def patch_auction(request):
    """Report auction results.

    Report auction results
    ----------------------

    Example request to report auction results:

    .. sourcecode:: http

        PATCH /tenders/4879d3f8ee2443169b5fbbc9f89fa607/auction HTTP/1.1
        Host: example.com
        Accept: application/json

        {
            "data": {
                "dateModified": "2014-10-27T08:06:58.158Z",
                "bids": [
                    {
                        "value": {
                            "amount": 400,
                            "currency": "UAH"
                        }
                    },
                    {
                        "value": {
                            "amount": 385,
                            "currency": "UAH"
                        }
                    }
                ]
            }
        }

    This is what one should expect in response:

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
            "data": {
                "dateModified": "2014-10-27T08:06:58.158Z",
                "bids": [
                    {
                        "value": {
                            "amount": 400,
                            "currency": "UAH",
                            "valueAddedTaxIncluded": true
                        }
                    },
                    {
                        "value": {
                            "amount": 385,
                            "currency": "UAH",
                            "valueAddedTaxIncluded": true
                        }
                    }
                ],
                "minimalStep":{
                    "amount": 35,
                    "currency": "UAH"
                },
                "tenderPeriod":{
                    "startDate": "2014-11-04T08:00:00"
                }
            }
        }

    """
    tender = request.validated['tender']
    auction_data = filter_data(request.validated['data'])
    if auction_data:
        auction_data['tenderID'] = tender.tenderID
        bids = auction_data.get('bids', [])
        tender_bids_ids = [i.id for i in tender.bids]
        auction_data['bids'] = [x for (y, x) in sorted(zip([tender_bids_ids.index(i['id']) for i in bids], bids))]
        auction_data['status'] = 'active.qualification'
        src = tender.serialize("plain")
        tender.import_data(apply_data_patch(src, auction_data))
        save_tender(tender, src, request)
    return {'data': tender.serialize(tender.status)}
