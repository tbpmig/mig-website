from django.db import models

comma_separated_time_list_re = re.compile('^(((((1?[0-2]|[1-9])(:[0-5][0-9])?(am|pm|AM|PM)?)|(?:0?[0-9]|1[0-9]|2[0-3])(:[0-5][0-9])?)\s*,\s*)*((((1?[0-2]|[1-9])(:[0-5][0-9])?(am|pm|AM|PM)?)|(?:0?[0-9]|1[0-9]|2[0-3])(:[0-5][0-9])?)\s*))$')
validate_comma_separated_time_list = RegexValidator(
              comma_separated_time_list_re, 
              _(u'Enter only times (12hr (optionally with am/pm) or 24hr separated by commas.'), 'invalid')

class CommaSeparatedTimeField(CharField):
    default_validators = [validators.validate_comma_separated_time_list]
    description = _("Comma-separated times")

    def formfield(self, **kwargs):
        defaults = {
            'error_messages': {
                'invalid': _(u'Enter only times (12hr (optionally with am/pm) or 24hr separated by commas.'),
            }
        }
        defaults.update(kwargs)
        return super(CommaSeparatedTimeField, self).formfield(**defaults)