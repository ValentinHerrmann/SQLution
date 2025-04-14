# forms.py
from django import forms

class SQLQueryForm(forms.Form):
    query = forms.CharField(widget=forms.Textarea(attrs={"rows": 5}), label="SQL-Abfrage")
    
