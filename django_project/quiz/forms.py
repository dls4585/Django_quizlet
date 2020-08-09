from django import forms
from django.contrib.admin.widgets import AdminDateWidget

class DateInput(forms.DateInput):
    input_type = 'date'

class TimeInput(forms.TimeInput):
    input_type = 'time'

class SearchForm(forms.Form):
        _from= forms.DateField(label='From', widget=DateInput)
        _to = forms.DateField(label='To', widget=DateInput)

class MakeSearchForm(forms.Form):
        _from = forms.DateTimeField(label='From', widget=DateInput)
        _to = forms.DateTimeField(label='To', widget=DateInput)