# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django.utils.translation import ugettext_lazy as _

from horizon.tables import MultiTableView


class ResourceBrowserView(MultiTableView):
    browser_class = None

    def __init__(self, *args, **kwargs):
        if not self.browser_class:
            raise ValueError("You must specify a ResourceBrowser subclass "
                             "for the browser_class attribute on %s."
                             % self.__class__.__name__)
        self.table_classes = (self.browser_class.navigation_table_class,
                              self.browser_class.content_table_class)
        self.navigation_selection = False
        super(ResourceBrowserView, self).__init__(*args, **kwargs)

    def _get_data_dict(self):
        navigation_kwarg_name = self.browser_class.navigation_kwarg_name
        if self.kwargs.get(navigation_kwarg_name, None):
            self.navigation_selection = True
        if not self._data:
            if not self.navigation_selection:
                # If there is nothing being selected in the navigation table,
                # Try to fetch the navigtation items first, then assign the
                # name of first item of the navigatables to the
                # kwargs of this view.
                nav_tbl_name = self.browser_class \
                                   .navigation_table_class \
                                   ._meta.name
                content_tbl_name = self.browser_class \
                                       .content_table_class \
                                       ._meta.name
                tables = self.get_tables()
                navigation_data_funcs = self._data_methods.pop(nav_tbl_name)
                nav_data = []
                for func in navigation_data_funcs:
                    nav_data.extend(func())
                self._data[nav_tbl_name] = nav_data
                if nav_data:
                    first_navigatable = tables.get(nav_tbl_name) \
                                              .get_object_id(nav_data[0])
                    self.kwargs[navigation_kwarg_name] = first_navigatable
                content_data = []
                content_data_funcs = self._data_methods.pop(content_tbl_name)
                for func in content_data_funcs:
                    content_data.extend(func())
                self._data[content_tbl_name] = content_data
            else:
                super(ResourceBrowserView, self)._get_data_dict()
        return self._data

    def get_browser(self):
        if not hasattr(self, "browser"):
            self.browser = self.browser_class(self.request, **self.kwargs)
            self.browser.set_tables(self.get_tables())
            ct = self.browser.content_table
            if not self.navigation_selection and ct.data:
                item = self.browser.navigable_item_name.lower()
                ct._no_data_message = _("Select a %s to browse.") % item
        return self.browser

    def get_context_data(self, **kwargs):
        context = super(ResourceBrowserView, self).get_context_data(**kwargs)
        browser = self.get_browser()
        context["%s_browser" % browser.name] = browser
        return context
