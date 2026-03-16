import ssl
from django.core.mail.backends.smtp import EmailBackend as SMTPBackend


class CustomEmailBackend(SMTPBackend):
    def open(self):
        if self.connection:
            return False

        connection_params = {
            'timeout': self.timeout,
        }

        if self.use_ssl:
            connection_params['context'] = ssl._create_unverified_context()

        try:
            self.connection = self.connection_class(
                self.host, self.port, **connection_params
            )

            if not self.use_ssl and self.use_tls:
                self.connection.starttls(context=ssl._create_unverified_context())

            if self.username and self.password:
                self.connection.login(self.username, self.password)

            return True
        except Exception:
            if not self.fail_silently:
                raise
