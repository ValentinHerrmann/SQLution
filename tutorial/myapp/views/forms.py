# forms.py
from django import forms

class SQLQueryForm(forms.Form):
    query = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 6, "style": "width: 100%;"}), 
        label=""
    )

class SQLFileForm(forms.Form):
    sqlfile = forms.CharField(
        widget=forms.TextInput(), 
        label=""
    ) 
    
class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()

class QRGeneratorForm(forms.Form):
    LOGO_CHOICES = [
        ('dataspark', 'SQLution Logo (Standard)'),
        ('custom', 'Eigenes Logo hochladen'),
        ('none', 'Kein Logo'),
    ]
    
    BACKGROUND_CHOICES = [
        ('transparent', 'Transparent'),
        ('white', 'Weiß'),
    ]
    
    FRAME_CHOICES = [
        ('none', 'Kein Rahmen'),
        ('simple', 'Einfacher Rahmen'),
        ('rounded', 'Abgerundeter Rahmen'),
    ]
    
    content = forms.CharField(
        initial='https://db.valentin-herrmann.com',
        widget=forms.TextInput(attrs={"placeholder": "Text oder URL eingeben..."}),
        label="QR Code Inhalt"
    )
    
    logo_option = forms.ChoiceField(
        choices=LOGO_CHOICES,
        initial='dataspark',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Logo Option"
    )
    
    custom_logo = forms.ImageField(
        required=False,
        label="Eigenes Logo",
        help_text="PNG, JPG oder SVG Datei hochladen (nur bei 'Eigenes Logo' Option)."
    )
    
    qr_color = forms.CharField(
        initial='#000000',
        widget=forms.TextInput(attrs={'type': 'color', 'style': 'width: 80px; height: 40px;'}),
        label="QR Code Farbe"
    )
    
    background_type = forms.ChoiceField(
        choices=BACKGROUND_CHOICES,
        initial='transparent',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Hintergrund"
    )
    
    frame_type = forms.ChoiceField(
        choices=FRAME_CHOICES,
        initial='rounded',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Rahmen"
    )
    
    frame_color = forms.CharField(
        initial='#000000',
        widget=forms.TextInput(attrs={'type': 'color', 'style': 'width: 80px; height: 40px;'}),
        label="Rahmen Farbe"
    )