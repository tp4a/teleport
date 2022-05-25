"""
"""

from wheezy.core.descriptors import attribute


class CaptchaMixin(object):
    @attribute
    def challenge_code(self):
        return self.captcha_context.get_challenge_code(self.request)

    def validate_captcha(self):
        return self.captcha_context.validate(self.request, self.errors, self._)

    def captcha_widget(self, path):
        ctx = self.captcha_context
        return (
            '<img id="captcha" src="%s?%s=%s" title="%s" />'
            '<input type="hidden" name="%s" value="%s" />'
            % (
                path,
                ctx.challenge_key,
                self.challenge_code,
                self._("If you cannot read, click to generate a new one."),
                ctx.challenge_key,
                self.challenge_code,
            )
        )
