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
from z3c.form.browser.textlines import TextLinesFieldWidget

from plone.directives import dexterity, form
from plone.app.textfield import RichText
from plone.namedfile.interfaces import IImageScaleTraversable
from plone.dexterity.browser.view import DefaultView

from zope.schema.fieldproperty import FieldProperty
from collective.leadmedia.adapters import ICanContainMedia

from collective.object import MessageFactory as _

from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.blockdatagridfield import BlockDataGridFieldFactory
from collective import dexteritytextindexer
from plone.dexterity.browser import add, edit
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.interface import alsoProvides
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

class ListField(schema.List):
    """We need to have a unique class for the field list so that we
    can apply a custom adapter."""
    pass

# # # # # # # # # # # # #
# Widget interface      #
# # # # # # # # # # # # #

class IFormWidget(Interface):
    pass


# # # # # # # # # # # # # #
# Vocabularies            #
# # # # # # # # # # # # # #

### !TODO! Move this vocabularies to a single file per fieldset [for the sake of reusability]

def _createInsuranceTypeVocabulary():
    insurance_types = {
        "commercial": _(u"Commercial"),
        "indemnity": _(u"Indemnity"),
    }

    for key, name in insurance_types.items():
        term = SimpleTerm(value=key, token=str(key), title=name)
        yield term

def _createPriorityVocabulary():
    priorities = {
        "low": _(u"low"),
        "medium": _(u"medium"),
        "high": _(u"high"),
        "urgent": _(u"urgent")
    }

    for key, name in priorities.items():
        term = SimpleTerm(value=key, token=str(key), title=name)
        yield term

priority_vocabulary = SimpleVocabulary(list(_createPriorityVocabulary()))
insurance_type_vocabulary = SimpleVocabulary(list(_createInsuranceTypeVocabulary()))

# # # # # # # # # # # # # #
# DataGrid interfaces     # 
# # # # # # # # # # # # # #

### !TODO! Move this interfaces to a single file per fieldset [for the sake of reusability]

class IKeyword(Interface):
    part = schema.TextLine(title=_(u'Part'), required=False)
    aspect = schema.TextLine(title=_(u'Aspect'), required=False)
    keyword = schema.TextLine(title=_(u'Keyword'), required=False)
    notes = schema.TextLine(title=_(u'Notes'), required=False)

class ITechnique(Interface):
    part = schema.TextLine(title=_(u'Part'), required=False)
    technique = schema.TextLine(title=_(u'Technique'), required=False)
    notes = schema.TextLine(title=_(u'Notes'), required=False)

class IMaterial(Interface):
    part = schema.TextLine(title=_(u'Part'), required=False)
    material = schema.TextLine(title=_(u'Material'), required=False)
    notes = schema.TextLine(title=_(u'Notes'), required=False)

class IDimension(Interface):
    part = schema.TextLine(title=_(u'Part'), required=False)
    dimension = schema.TextLine(title=_(u'Dimension'), required=False)
    value = schema.TextLine(title=_(u'Value'), required=False)
    unit = schema.TextLine(title=_(u'Unit'), required=False)
    precision = schema.TextLine(title=_(u'Precision'), required=False)
    notes = schema.TextLine(title=_(u'Notes'), required=False)

class IPeriod(Interface):
    period = schema.TextLine(title=_(u'Period'), required=False)
    date_early = schema.TextLine(title=_(u'Date (early)'), required=False)
    date_early_precision = schema.TextLine(title=_(u'Precision'), required=False)
    date_late = schema.TextLine(title=_(u'Date (late)'), required=False)
    date_late_precision = schema.TextLine(title=_(u'Precision'), required=False)

## Condition & Conservation Interfaces
class ICompleteness(Interface):
    completeness = schema.TextLine(title=_(u'Completeness'), required=False)
    notes = schema.TextLine(title=_(u'Notes'), required=False)
    checked_by = schema.TextLine(title=_(u'Checked by'), required=False)
    date = schema.TextLine(title=_(u'Date'), required=False)

class ICondition(Interface):
    part = schema.TextLine(title=_(u'Part'), required=False)
    condition = schema.TextLine(title=_(u'Condition'), required=False)
    notes = schema.TextLine(title=_(u'Notes'), required=False)
    checked_by = schema.TextLine(title=_(u'Checked by'), required=False)
    date = schema.TextLine(title=_(u'Date'), required=False)

class IEnvCondition(Interface):
    preservation_form = schema.TextLine(title=_(u'Preservation form'), required=False)
    notes = schema.TextLine(title=_(u'Notes'), required=False)
    date = schema.TextLine(title=_(u'Date'), required=False)

class IConsRequest(Interface):
    treatment = schema.TextLine(title=_(u'Treatment'), required=False)
    requester = schema.TextLine(title=_(u'Requester'), required=False)
    reason = schema.TextLine(title=_(u'Reason'), required=False)
    status = schema.TextLine(title=_(u'Status'), required=False)
    date = schema.TextLine(title=_(u'Date'), required=False)

## Inscriptions and Markings

class IInscription(Interface):
    type = schema.TextLine(title=_(u'Type'), required=False)
    position = schema.TextLine(title=_(u'Position'),required=False)
    method = schema.TextLine(title=_(u'Method'), required=False)
    date = schema.TextLine(title=_(u'Date'), required=False)
    creator = schema.TextLine(title=_(u'Creator'), required=False)
    creator_role = schema.TextLine(title=_(u'Role'), required=False)
    content = schema.TextLine(title=_(u'Content'), required=False)
    description = schema.TextLine(title=_(u'Description'), required=False)
    interpretation = schema.TextLine(title=_(u'Interpretation'), required=False)
    language = schema.TextLine(title=_(u'Language'), required=False)
    notes = schema.TextLine(title=_(u'Notes'), required=False)

# Value & Insurance
class IValuation(Interface):
    value = schema.TextLine(title=_(u'Value'), required=False)
    curr = schema.TextLine(title=_(u'Curr.'), required=False)
    valuer = schema.TextLine(title=_(u'Valuer'), required=False)
    date = schema.TextLine(title=_(u'Date'), required=False)
    reference = schema.TextLine(title=_(u'Reference'), required=False)
    notes = schema.TextLine(title=_(u'Notes'), required=False)

class IInsurance(Interface):
    type = schema.Choice(
        vocabulary=insurance_type_vocabulary,
        title=_(u'Type'),
        required=False
    )
    value = schema.TextLine(title=_(u'Value'), required=False)
    curr = schema.TextLine(title=_(u'Curr.'), required=False)
    valuer = schema.TextLine(title=_(u'Valuer'), required=False)
    date = schema.TextLine(title=_(u'Date'), required=False)
    policy_number = schema.TextLine(title=_(u'Policy number'), required=False)
    insurance_company = schema.TextLine(title=_(u'Insurance company'), required=False)
    confirmation_date = schema.TextLine(title=_(u'Confirmation date'), required=False)
    renewal_date = schema.TextLine(title=_(u'Renewal date'), required=False)
    reference = schema.TextLine(title=_(u'Reference'), required=False)
    conditions = schema.TextLine(title=_(u'Conditions'), required=False)
    notes = schema.TextLine(title=_(u'Notes'), required=False)

# Aquisition
class IFunding(Interface):
    amount = schema.TextLine(title=_(u'Amount'), required=False)
    curr = schema.TextLine(title=_(u'Curr.'), required=False)
    source = schema.TextLine(title=_(u'Source'), required=False)
    provisos = schema.TextLine(title=_(u'Provisos'), required=False)

class IDocumentation(Interface):
    description = schema.TextLine(title=_(u'Description'), required=False)
    reference = schema.TextLine(title=_(u'Reference'), required=False)


class IObject(form.Schema):
    text = RichText(
        title=_(u"Body"),
        required=False
    )

    # # # # # # # # # # # # # # 
    # Identification fieldset #
    # # # # # # # # # # # # # # 
    
    model.fieldset('identification', label=_(u'Identification'), 
        fields=['institution_name', 'administrative_name', 'collection', 'object_number',
                'rec_type', 'part', 'tot_number', 'copy_number', 'edition', 'distinguish_features', 
                'object_category', 'object_name', 'other_name']
    )

    # Identification #
    institution_name = schema.TextLine(
        title=_(u'Institution name'), 
        required=False,
        description=_(u"Institution name<br><br>The name of the institution responsible for managing the object.<br><br>Enter the common name of your institution, possibly shortened and with a place name. This field is especially relevant if object descriptions are used by third parties.<br><br> Examples:<br>National Museums of Scotland<br>NMS<br>REME<br>Met")
    )
    dexteritytextindexer.searchable('institution_name')

    administrative_name = schema.TextLine(
        title=_(u'Administrative name'), 
        required=False,
        description=_(u"Administration name<br><br>The name of the department responsible for the object itself and for the documentation about the object.<br><br>Examples:<br>Textiles<br>Geology<br>Glass and ceramics")
    )
    dexteritytextindexer.searchable('administrative_name')

    collection = schema.TextLine(
        title=_(u'Collection'), 
        required=False,
        description=_(u"Collection<br><br>If this object is part of a specific collection within the overall museum collection, use this field to enter its name.<br><br>Examples:<br>manuscripts<br>Muller")
    )
    dexteritytextindexer.searchable('collection')

    object_number = schema.TextLine(
        title=_(u'Object number'),
        required=False
    )
    dexteritytextindexer.searchable('object_number')

    rec_type = schema.TextLine(
        title=_(u'Rec. type'),
        required=False
    )
    dexteritytextindexer.searchable('rec_type')

    part = schema.TextLine(
        title=_(u'Part'),
        required=False
    )
    dexteritytextindexer.searchable('part')

    tot_number = schema.TextLine(
        title=_(u'Tot. Number'),
        required=False
    )
    dexteritytextindexer.searchable('tot_number')

    copy_number = schema.TextLine(
        title=_(u'Copy number'),
        required=False
    )
    dexteritytextindexer.searchable('copy_number')

    edition = schema.TextLine(
        title=_(u'Edition'),
        required=False
    )
    dexteritytextindexer.searchable('edition')

    distinguish_features = schema.TextLine(
        title=_(u'Distinguish features'),
        required=False
    )
    dexteritytextindexer.searchable('distinguish_features')

    # Object name #
    object_category = schema.TextLine(
        title=_(u'Object Category'),
        required=False
    )
    dexteritytextindexer.searchable('object_category')

    object_name = schema.TextLine(
        title=_(u'Object name'),
        required=False
    )
    dexteritytextindexer.searchable('object_name')

    other_name = schema.TextLine(
        title=_(u'Other name'),
        required=False
    )
    dexteritytextindexer.searchable('other_name')


    # # # # # # # # # # # # # # # # #
    # Physical Characteristics      #
    # # # # # # # # # # # # # # # # #

    model.fieldset('physical_characteristics', label=_(u'Physical Characteristics'), 
        fields=['physical_description', 'keywords',
                'techniques', 'materials', 'dimensions', 'dimensions_free_text',
                'frame', 'frame_detail']
    )

    # Physical Description
    physical_description = schema.TextLine(
        title=_(u'Description'),
        required=False
    )
    dexteritytextindexer.searchable('physical_description')

    # Keywords #
    keywords = ListField(title=_(u'Keywords'),
        value_type=schema.Object(title=_(u'Keywords'), schema=IKeyword),
        required=False)
    form.widget(keywords=DataGridFieldFactory)

    # Techniques #
    techniques = ListField(title=_(u'Techniques'),
        value_type=schema.Object(title=_(u'Techniques'), schema=ITechnique),
        required=False)
    form.widget(techniques=DataGridFieldFactory)

    # Materials #
    materials = ListField(title=_(u'Materials'),
        value_type=schema.Object(title=_(u'Materials'), schema=IMaterial),
        required=False)
    form.widget(materials=DataGridFieldFactory)

    # Dimensions #
    dimensions = ListField(title=_(u'Dimensions'),
        value_type=schema.Object(title=_(u'Dimensions'), schema=IDimension),
        required=False)
    form.widget(dimensions=DataGridFieldFactory)

    dimensions_free_text = schema.TextLine(
        title=_(u'Dimensions (free text)'),
        required=False
    )

    # Frame #
    frame = schema.TextLine(
        title=_(u'Frame'),
        required=False
    )
    dexteritytextindexer.searchable('frame')

    frame_detail = schema.TextLine(
        title=_(u'Detail'),
        required=False
    )
    dexteritytextindexer.searchable('frame_detail')


    # # # # # # # # # # # # # # # # #
    # Production | Dating           #
    # # # # # # # # # # # # # # # # #

    model.fieldset('production_dating', label=_(u'Production | Dating'), 
        fields=['production_creator', 'production_qualifier',
                'production_role', 'production_place', 'production_school', 'production_notes',
                'production_reason', 'production_period', 'production_dating_notes']
    )

    production_creator = schema.TextLine(
        title=_(u'Creator'),
        required=False
    )
    dexteritytextindexer.searchable('production_creator')

    production_qualifier = schema.TextLine(
        title=_(u'Qualifier'),
        required=False
    )
    dexteritytextindexer.searchable('production_qualifier')

    production_role = schema.TextLine(
        title=_(u'Role'),
        required=False
    )
    dexteritytextindexer.searchable('production_role')

    production_place = schema.TextLine(
        title=_(u'Place'),
        required=False
    )
    dexteritytextindexer.searchable('production_place')

    production_school = schema.TextLine(
        title=_(u'School / style'),
        required=False
    )
    dexteritytextindexer.searchable('production_school')

    production_notes = schema.TextLine(
        title=_(u'Production notes'),
        required=False
    )
    dexteritytextindexer.searchable('production_notes')

    production_reason = schema.TextLine(
        title=_(u'Production reason'),
        required=False
    )
    dexteritytextindexer.searchable('production_reason')

    # Dating #
    production_period = ListField(title=_(u'Period'),
        value_type=schema.Object(title=_(u'Period'), schema=IPeriod),
        required=False)
    form.widget(production_period=DataGridFieldFactory)
    dexteritytextindexer.searchable('production_period')

    production_dating_notes = schema.TextLine(
        title=_(u'Notes'),
        required=False
    )
    dexteritytextindexer.searchable('production_dating_notes')


    # # # # # # # # # # # # # # #
    # Condition & Conservation  #
    # # # # # # # # # # # # # # #

    model.fieldset('condition_conservation', label=_(u'Condition & Conservation'), 
        fields=['conservation_priority', 'conservation_next_condition_check', 'conservation_date',
                'completeness', 'condition', 'enviromental_condition', 'conservation_request']
    )

    # Conservation treatment

    # Choice field
    conservation_priority = schema.Choice(
        vocabulary=priority_vocabulary,
        title=_(u'Priority'),
        required=False
    )
    dexteritytextindexer.searchable('conservation_priority')

    conservation_next_condition_check = schema.TextLine(
        title=_(u'Next condition check'),
        required=False
    )
    dexteritytextindexer.searchable('conservation_next_condition_check')

    conservation_date = schema.TextLine(
        title=_(u'Date'),
        required=False
    )
    dexteritytextindexer.searchable('conservation_date')

    # Completeness*
    completeness = ListField(title=_(u'Completeness'),
        value_type=schema.Object(title=_(u'Completeness'), schema=ICompleteness),
        required=False)
    form.widget(completeness=DataGridFieldFactory)
    dexteritytextindexer.searchable('completeness')

    # Condition*
    condition = ListField(title=_(u'Condition'),
        value_type=schema.Object(title=_(u'Condition'), schema=ICondition),
        required=False)
    form.widget(condition=DataGridFieldFactory)
    dexteritytextindexer.searchable('condition')

    # Enviromental condition*
    enviromental_condition = ListField(title=_(u'Enviromental condition'),
        value_type=schema.Object(title=_(u'Enviromental condition'), schema=IEnvCondition),
        required=False)
    form.widget(enviromental_condition=DataGridFieldFactory)
    dexteritytextindexer.searchable('enviromental_condition')

    # Conservation request*
    conservation_request = ListField(title=_(u'Conservation request'),
        value_type=schema.Object(title=_(u'Conservation request'), schema=IConsRequest),
        required=False)
    form.widget(conservation_request=DataGridFieldFactory)
    dexteritytextindexer.searchable('conservation_request')


    # # # # # # # # # # # # # # #
    # Inscriptions & Markings   #
    # # # # # # # # # # # # # # #

    model.fieldset('inscriptions_markings', label=_(u'Inscriptions and markings'), 
        fields=['inscriptions']
    )

    inscriptions = ListField(title=_(u'Inscriptions and markings'),
        value_type=schema.Object(title=_(u'Inscriptions and markings'), schema=IInscription),
        required=False)
    form.widget(inscriptions=BlockDataGridFieldFactory)
    dexteritytextindexer.searchable('inscriptions')

    # # # # # # # # # # #
    # Value & Insurance #
    # # # # # # # # # # #

    model.fieldset('value_insurance', label=_(u'Value & Insurance'), 
        fields=['valuation', 'insurance']
    )

    valuation = ListField(title=_(u'Valuation'),
        value_type=schema.Object(title=_(u'Valuation'), schema=IValuation),
        required=False)
    form.widget(valuation=BlockDataGridFieldFactory)
    dexteritytextindexer.searchable('valuation')

    insurance = ListField(title=_(u'Insurance'),
        value_type=schema.Object(title=_(u'Insurance'), schema=IInsurance),
        required=False)
    form.widget(insurance=BlockDataGridFieldFactory)
    dexteritytextindexer.searchable('insurance')

    # # # # # # # # # #
    # Acquisition     #
    # # # # # # # # # #

    model.fieldset('acquisition', label=_(u'Acquisition'), 
        fields=['accession_date', 'acquisition_number', 'acquisition_date', 'acquisition_precision',
                'acquisition_method', 'acquisition_rec_no', 'acquisition_lot_no',
                'acquisition_from', 'acquisition_auction', 'acquisition_place', 'acquisition_reason',
                'acquisition_conditions', 'authorization_authorizer', 'authorization_date',
                'costs_offer_price', 'costs_offer_price_curr', 'costs_purchase_price',
                'costs_purchase_price_curr', 'costs_notes', 'funding', 'documentation',
                'acquisition_copyright', 'acquisition_notes']
    )

    # Accession
    accession_date = schema.TextLine(
        title=_(u'Accession date'),
        required=False
    )
    dexteritytextindexer.searchable('accession_date')

    # Acquisition
    acquisition_number = schema.TextLine(
        title=_(u'Acquisition number'),
        required=False
    )
    dexteritytextindexer.searchable('acquisition_number')

    acquisition_date = schema.TextLine(
        title=_(u'Date'),
        required=False
    )
    dexteritytextindexer.searchable('acquisition_date')

    acquisition_precision = schema.TextLine(
        title=_(u'Precision'),
        required=False
    )
    dexteritytextindexer.searchable('acquisition_precision')

    acquisition_method = schema.TextLine(
        title=_(u'Method'),
        required=False
    )
    dexteritytextindexer.searchable('acquisition_method')

    acquisition_rec_no = schema.TextLine(
        title=_(u'Rec.no.'),
        required=False
    )
    dexteritytextindexer.searchable('acquisition_rec_no')

    acquisition_lot_no = schema.TextLine(
        title=_(u'Lot no.'),
        required=False
    )
    dexteritytextindexer.searchable('acquisition_lot_no')


    acquisition_from = schema.TextLine(
        title=_(u'From'),
        required=False
    )
    dexteritytextindexer.searchable('acquisition_from')

    acquisition_auction = schema.TextLine(
        title=_(u'Auction'),
        required=False
    )
    dexteritytextindexer.searchable('acquisition_auction')

    acquisition_place = schema.TextLine(
        title=_(u'Place'),
        required=False
    )
    dexteritytextindexer.searchable('acquisition_place')

    acquisition_reason = schema.TextLine(
        title=_(u'Reason'),
        required=False
    )
    dexteritytextindexer.searchable('acquisition_reason')

    acquisition_conditions = schema.TextLine(
        title=_(u'Conditions'),
        required=False
    )
    dexteritytextindexer.searchable('acquisition_conditions')

    # Authorization
    authorization_authorizer = schema.TextLine(
        title=_(u'Authorizer'),
        required=False
    )
    dexteritytextindexer.searchable('authorization_authorizer')

    authorization_date = schema.TextLine(
        title=_(u'Date'),
        required=False
    )
    dexteritytextindexer.searchable('authorization_date')

    # Costs
    costs_offer_price = schema.TextLine(
        title=_(u'Offer price'),
        required=False
    )
    dexteritytextindexer.searchable('costs_offer_price')

    costs_offer_price_curr = schema.TextLine(
        title=_(u'Curr.'),
        required=False
    )
    dexteritytextindexer.searchable('costs_offer_price_curr')

    costs_purchase_price = schema.TextLine(
        title=_(u'Purchase price'),
        required=False
    )
    dexteritytextindexer.searchable('costs_purchase_price')

    costs_purchase_price_curr = schema.TextLine(
        title=_(u'Curr.'),
        required=False
    )
    dexteritytextindexer.searchable('costs_purchase_price_curr')

    costs_notes = schema.TextLine(
        title=_(u'Notes'),
        required=False
    )
    dexteritytextindexer.searchable('costs_notes')

    # Funding *
    funding = ListField(title=_(u'Funding'),
        value_type=schema.Object(title=_(u'Funding'), schema=IFunding),
        required=False)
    form.widget(funding=BlockDataGridFieldFactory)
    dexteritytextindexer.searchable('funding')

    # Documentation *
    documentation = ListField(title=_(u'Documentation'),
        value_type=schema.Object(title=_(u'Documentation'), schema=IDocumentation),
        required=False)
    form.widget(documentation=DataGridFieldFactory)
    dexteritytextindexer.searchable('documentation')

    # Copyright
    acquisition_copyright = schema.TextLine(
        title=_(u'Copyright'),
        required=False
    )
    dexteritytextindexer.searchable('acquisition_copyright')

    # Notes
    acquisition_notes = schema.TextLine(
        title=_(u'Notes'),
        required=False
    )
    dexteritytextindexer.searchable('acquisition_notes')



# # # # # # # # # # # # #
# Object declaration    #
# # # # # # # # # # # # #

class Object(Container):
    grok.implements(IObject)
    pass

# # # # # # # # # # # # # #
# Object add/edit views   # 
# # # # # # # # # # # # # #

class AddForm(add.DefaultAddForm):
    template = ViewPageTemplateFile('object_templates/add.pt')
    def update(self):
        super(AddForm, self).update()
        for group in self.groups:
            for widget in group.widgets.values():
                alsoProvides(widget, IFormWidget)

class AddView(add.DefaultAddView):
    form = AddForm
    

class EditForm(edit.DefaultEditForm):
    template = ViewPageTemplateFile('object_templates/edit.pt')
    
    def update(self):
        super(EditForm, self).update()
        for group in self.groups:
            for widget in group.widgets.values():
                alsoProvides(widget, IFormWidget)

#
# Declare widgets
#
#form.widget(dimension=DataGridFieldFactory)


# # # # # # # # # # # # #
# View specific methods #
# # # # # # # # # # # # #

class ObjectView(DefaultView):
    """ View class """

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
        details["site_name"] = "ZM"
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
