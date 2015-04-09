#!/usr/bin/python
# -*- coding: utf-8 -*-

from five import grok

from z3c.form import group, field
from zope import schema
from zope.interface import invariant, Invalid, Interface, implements
from plone.supermodel import model
from plone.dexterity.content import Container
from zope.component import getMultiAdapter
from z3c.form.form import extends

from plone.directives import dexterity, form
from plone.app.textfield import RichText
from plone.namedfile.interfaces import IImageScaleTraversable
from plone.dexterity.browser.view import DefaultView

from zope.schema.fieldproperty import FieldProperty

from collective.object import MessageFactory as _

from collective.z3cform.datagridfield import DataGridFieldFactory, IDataGridField
from collective.leadmedia.interfaces import ICanContainMedia
from collective import dexteritytextindexer

class DimensionListField(schema.List):
    """We need to have a unique class for the field list so that we
    can apply a custom adapter."""
    pass

class IDimension(Interface):
    dimension = schema.TextLine(title=u'Dimension', required=False)
    value = schema.TextLine(title=u'Value', required=False)
    unit = schema.TextLine(title=u'Unit', required=False)
    part = schema.TextLine(title=u'Part', required=False)
    precision = schema.TextLine(title=u'Precision', required=False)
    notes = schema.TextLine(title=u'Notes', required=False)

class IObject(form.Schema):
    text = RichText(
        title=_(u"Body text"),
        required=False
    )

    # searchable fields
    dexteritytextindexer.searchable('artist')
    dexteritytextindexer.searchable('object_type')
    dexteritytextindexer.searchable('dating')
    dexteritytextindexer.searchable('material')
    dexteritytextindexer.searchable('technique')
    dexteritytextindexer.searchable('object_number')
    

    # Define Collection fieldset
    model.fieldset('collection', label=_(u'Collection'), 
        fields=['artist', 'object_type', 'dating', 'material', 'technique', 'object_number', 'dimension', 'dimension_free_text']
    )

    form.widget(dimension=DataGridFieldFactory)

    # Regular fields
    artist = schema.TextLine(title=_(u'Artist'), required=False)
    object_type = schema.TextLine(title=_(u'Objecttype'), required=False)
    dating = schema.TextLine(title=_(u'Dating'), required=False)
    material = schema.TextLine(title=_(u'Material'), required=False)
    technique = schema.TextLine(title=_(u'Technique'), required=False)
    object_number = schema.TextLine(title=_(u'Objectnumber'), required=False)

    # Data grid fields 
    dimension = DimensionListField(title=_(u'Measurements'), 
        value_type=schema.Object(title=_(u'Measurements'), schema=IDimension), 
        required=False)

    dimension_free_text = schema.TextLine(title=_(u'Dimension free text'), required=False)

class Object(Container):
    grok.implements(IObject)
    pass


class EditForm(form.EditForm):
    extends(form.EditForm)
    grok.context(IObject)
    grok.require('zope2.View')
    fields = field.Fields(IObject)

    fields['dimension'].widgetFactory = DataGridFieldFactory


class ObjectView(DefaultView):
    """ sample view class """

    def trim_white_spaces(self, text):
        if text != "" and text != None:
            if len(text) > 0:
                if text[0] == " ":
                    text = text[1:]
                if len(text) > 0:
                    if text[-1] == " ":
                        text = text[:-1]
                return text
            else:
                return ""
        else:
            return ""

    def create_author_name(self, value):
        comma_split = value.split(",")

        for i in range(len(comma_split)):       
            name_split = comma_split[i].split('(')
            
            raw_name = name_split[0]
            name_split[0] = self.trim_white_spaces(raw_name)
            name_artist = name_split[0]
            
            name_artist_link = '<a href="/'+self.context.language+'/search?SearchableText=%s">%s</a>' % (name_artist, name_artist)
            name_split[0] = name_artist_link

            if len(name_split) > 1:
                if len(name_split[1]) > 0:
                    name_split[0] = name_artist_link + " "
        
            comma_split[i] = '('.join(name_split)

        _value = ", ".join(comma_split)

        return _value

    def create_materials(self, value):
        materials = value.split(',')
        _value = ""
        for i, mat in enumerate(materials):
            if i == (len(materials)-1):
                _value += '<a href="/'+self.context.language+'/search?SearchableText=%s">%s</a>' % (mat, mat)
            else:
                _value += '<a href="/'+self.context.language+'/search?SearchableText=%s">%s</a>, ' % (mat, mat)

        return _value

    def getSearchableValue(self, name, value):
        _value = ""

        if (name == 'artist') or (name == 'author'):
            _value = self.create_author_name(value)
        elif (name == 'material') or (name == 'technique'):
            _value = self.create_materials(value)
        else:
            _value = '<a href="/'+self.context.language+'/search?SearchableText=%s">%s</a>' % (value, value)

        return _value

    def getFBdetails(self):
        item = self.context
        
        state = getMultiAdapter(
                (item, self.request),
                name=u'plone_context_state')

        # Check view type
        view_type = state.view_template_id()

        obj = ICanContainMedia(item)

        details = {}
        details["title"] = item.Title()
        details["type"] = "article"
        details["site_name"] = "Teylers Museum"
        details["url"] = item.absolute_url()
        details["description"] = item.Description()
        details["double_image"] = ""
        details["image"] = ""
        
        if view_type == "instruments_view":
            if hasattr(item, 'slideshow'):
                catalog = getToolByName(self.context, 'portal_catalog')
                slideshow = item['slideshow']
                path = '/'.join(slideshow.getPhysicalPath())
                results = catalog.searchResults(path={'query': path, 'depth': 1, 'portal_type': 'Image'}, sort_on='sortable_title')
                if len(results) > 0:
                    lead_image = results[0]
                    if lead_image.portal_type == "Image":
                        details["image"] = lead_image.getObject().absolute_url()+"/@@images/image/large"
                else:
                    details["image"] = ""
                

        if details["image"] == "":
            if obj.hasMedia():
                image = obj.getLeadMedia()
                details["image"] = image.absolute_url()+"/@@images/image/large"
                
                if view_type == "double_view":
                    if hasattr(item, 'slideshow'):
                        slideshow = item['slideshow']
                        if len(slideshow.objectIds()) > 1:
                            double_image = slideshow[slideshow.objectIds()[1]]
                            if double_image.portal_type == "Image":
                                details["double_image"] = double_image.absolute_url()+"/@@images/image/large"
            else:
                details["image"] = ""

        return details
