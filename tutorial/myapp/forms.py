# forms.py
from django import forms

class SQLQueryForm(forms.Form):
    query = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 6, "style": "width: 100%;"}), 
        label=""
    )
    
class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()