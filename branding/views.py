# Copyright 2012 Nebula, Inc.
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

from django import shortcuts
from django.conf import settings
from django.http import HttpResponse

import django.views.decorators.vary

import horizon
from horizon import base
from horizon import exceptions

from mimetypes import guess_type

from openstack_dashboard.api import keystone

from os.path import dirname, exists, join as path_join

def get_user_home(user):
    dashboard = None
    if user.is_superuser:
        try:
            dashboard = horizon.get_dashboard('project')
        except base.NotRegistered:
            pass

    if dashboard is None:
        dashboard = horizon.get_default_dashboard()

    return dashboard.get_absolute_url()


@django.views.decorators.vary.vary_on_cookie
def splash(request):
    brand = request.GET.get('brand')
    if brand:
        # store brand id and reload splash page
        return set_brand(shortcuts.redirect('/'), brand)

    if not request.user.is_authenticated():
        raise exceptions.NotAuthenticated()

    response = shortcuts.redirect(horizon.get_user_home(request.user))
    if 'logout_reason' in request.COOKIES:
        response.delete_cookie('logout_reason')
    set_brand(response, get_brand(request))
    return response


#
# Branding
#

# get brand of current session
def get_brand(request):
    return request.COOKIES.get('brand', None) or 'default'

# make brand persistent
def set_brand(response, brand=None):
    if not brand:
        return response
    # default brand cookie max age (30 days)
    max_age = getattr(settings, 'BRAND_COOKIE_MAX_AGE', 2592000)
    response.set_cookie('brand', brand, max_age=max_age)
    return response

# return brand asset
def brand(request, asset):
    brand = get_brand(request)
    brand_root = getattr(settings, 'BRAND_ROOT', 'brand')
    asset_path = path_join(dirname(__file__), brand_root, brand, asset)
    (asset_type, _) = guess_type(asset)

    response = HttpResponse(content_type=asset_type)

    if exists(asset_path):
        # return brand asset
        response.content = open(asset_path, 'r')

    else:
        static_root = 'static/custom/'
        if asset_type.startswith('image/'):
            static_root += 'img'
        elif asset_type == 'text/css':
            static_root += 'css'

        asset_path = path_join(dirname(__file__), static_root, asset)

        if exists(asset_path):
            response.content = open(asset_path, 'r')

        else:
            response.content = None

    return set_brand(response, brand)

