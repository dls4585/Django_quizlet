from django import forms

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

class TimeForm(forms.Form):
    TIME_OPTIONS = (
        ('00 ~ 03', '00:00 ~ 03:00'),
        ('03 ~ 06', '03:00 ~ 06:00'),
        ('06 ~ 09', '06:00 ~ 09:00'),
        ('09 ~ 12', '09:00 ~ 12:00'),
        ('12 ~ 15', '12:00 ~ 15:00'),
        ('15 ~ 18', '15:00 ~ 18:00'),
        ('18 ~ 21', '18:00 ~ 21:00'),
        ('21 ~ 00', '21:00 ~ 00:00'),
    )
    select = forms.ChoiceField(label='Select Time', choices=TIME_OPTIONS)
