from __future__ import absolute_import, unicode_literals
import requests
from integration.models import Integration
from core import celery_app
from rest_framework.response import Response
from dateutil import parser
from django.utils import timezone

@celery_app.task
def get_data_from_url():
    """ Fetching data from (https://search.cannabis.ca.gov/results?searchQuery=) URL 
        and Set up celery & adding async tasks to trigger periodic data save task for above fields. """
    url = 'https://as-cdt-pub-vip-cannabis-ww-p-002.azurewebsites.net/licenses/filteredSearch?pageSize=&pageNumber='
    totalPages = requests.get(url).json()["metadata"]["totalPages"]
    for page in range(1,totalPages+1):
        res = requests.get(url + str(page))
        insert_list = []
        for val in res.json()["data"]:
            val_dict = {'dcc_number':val['id'],'license_number':val['licenseNumber'],'license_status':val['licenseStatus'],
                'license_status_date':convert(val['licenseStatusDate']),'license_term':val['licenseTerm'],'license_type':val['licenseType'],
                'license_designation':val['licenseDesignation'],'issue_date':convert(val['issueDate']),'expiration_date':convert(val['expirationDate']),
                'licensing_authority_id':val['licensingAuthorityId'],'licensing_authority':val['licensingAuthority'],'business_legal_name':val['businessLegalName'],
                'business_dba_name':val['businessDbaName'],'business_owner_name':val['businessOwnerName'],'business_structure':val['businessStructure'],
                'activity':sort_activity(val['activity']),'premise_street_address':val['premiseStreetAddress'],'premise_city':val['premiseCity'],
                'premise_state':val['premiseState'],'premise_county':val['premiseCounty'],'premise_zip_code':val['premiseZipCode'],
                'business_email':val['businessEmail'],'business_phone':val['businessPhone'],'parcel_number':val['parcelNumber'],
                'premise_latitude':val['premiseLatitude'],'premise_longitude':val['premiseLongitude'],'data_refreshed_date':convert(val['dataRefreshedDate'])}
            insert_list.append(Integration(**val_dict))
        Integration.objects.bulk_update_or_create(insert_list, list(val_dict.keys()), match_field='license_number')
    return Response({'message': 'Fetching Data is Done'})

def convert(date_time_str):
    if date_time_str:
        try:
            return parser.parse(date_time_str)
        except:
            print("Problem in Date Feild Parser",date_time_str)

def sort_activity(activity):
    res = []
    if activity:
        if activity == 'Data Not Available':
            return ["N/A"]
        for i in activity.split(","):
            res.append(i.strip())
        return res
    return ["N/A"]
