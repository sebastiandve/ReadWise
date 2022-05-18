import pandas as pd
from datetime import datetime
import numpy as np
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime


class Reader:

    def __init__(self):
        self.text_location = 'Kindle Highlights.txt'
        self.quotes = None
        self.num_quotes = 5
        self.receiver_email = os.environ['EMAIL']

    @staticmethod
    def extract_date(string):
        start = string.find('Added')
        if start == -1:
            return None
        end = string.find('\n', start)
        return string[start:end]

    @staticmethod
    def format_date(string):
        pieces = string.split(',')
        if len(pieces) == 2:
            date = pieces[1][:-9]
            return datetime.strptime(date, ' %d %B %Y')
        elif len(pieces) == 3:
            date = pieces[1] + pieces[2][0:5]
            return datetime.strptime(date, ' %B %d %Y')
        else:
            return

    def process_text(self):
        text_file = open(self.text_location, 'r')
        text = text_file.read().split('==========')
        text[0] = '\n' + text[0]
        text.pop(-1)
        text_file.close()

        df = pd.DataFrame(text, columns=['raw'])
        df['title_author'] = df.raw.apply(lambda x: x.split('-')[0].strip())
        df['date_added'] = df.raw.apply(lambda x: self.extract_date(x))
        df['date_added'] = df.date_added.apply(lambda x: self.format_date(x))
        df['quote'] = df.raw.apply(lambda x: x.split('\n')[4])
        df.drop('raw', axis=1, inplace=True)
        self.quotes = df

    def get_quotes(self):
        length = len(self.quotes)
        ixs = np.random.randint(0, length, self.num_quotes)
        return self.quotes.quote.iloc[ixs].values, self.quotes.title_author.iloc[ixs].values

    def create_email_text(self):
        quotes, titles = self.get_quotes()
        text = ''
        for i, q in enumerate(quotes):
            text = text + '<p>' + q + '<br>' + titles[i] + '<br>' + '</p>'
        return text

    def send_email(self):
        message = Mail(
            from_email='daily@quotes.com',
            to_emails=self.receiver_email,
            subject='Your daily quotes!',
            html_content=self.create_email_text())
        try:
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception:
            print('Email not sent')

    def export_quotes(self, title):
        q = self.quotes[self.quotes.title_author == title]
        q.quote.to_csv('quotes.csv', index=False)


if datetime.today().weekday() in [1, 3, 5]:
    r = Reader()
    r.process_text()
    r.send_email()
