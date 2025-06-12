from wtforms import Form, StringField, BooleanField
from wtforms.validators import DataRequired, Optional, Length

class SearchForm(Form):
    prompt = StringField(
        'Search Query',
        validators=[
            DataRequired(message="Search query is required."),
            Length(max=60, message="Query must be 60 characters or fewer.")
        ]
    )
    lang = StringField('Language', validators=[Optional()])
    country = StringField('Country', validators=[Optional()])
    tbs = StringField('Time Filter', validators=[Optional()])
    include_markdown = BooleanField('Include Markdown')
    include_links = BooleanField('Include Links')
    html_type = StringField('HTML Type', validators=[Optional()])
    screenshot_type = StringField('Screenshot Type', validators=[Optional()])
