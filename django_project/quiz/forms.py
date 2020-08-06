from django import forms



class SelectTime(forms.Form):
    option = []
    selection = forms.ChoiceField(required=True, choices=option)

    def __init__(self, timelist):
        contents = []
        for time in timelist:
            content = (time, time)
            contents.append(content)
        contents = tuple(contents)
        self.option = contents
