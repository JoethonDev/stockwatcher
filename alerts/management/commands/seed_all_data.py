from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from alerts.models import Company, Alert

# A list of all stocks to start with
DEFAULT_STOCKS = ['AAPL', 'TSLA', 'AMZN', 'MSFT', 'NVDA', 'GOOGL', 'META', 'NFLX', 'JPM', 'V', 'BAC', 'AMD', 'PYPL', 'DIS', 'T', 'PFE', 'COST', 'INTC', 'KO', 'TGT', 'NKE', 'SPY', 'BA', 'BABA', 'XOM', 'WMT', 'GE', 'CSCO', 'VZ', 'JNJ', 'CVX', 'PLTR', 'SQ', 'SHOP', 'SBUX', 'SOFI', 'HOOD', 'RBLX', 'SNAP', 'AMD', 'UBER', 'FDX', 'ABBV', 'ETSY', 'MRNA', 'LMT', 'GM', 'F', 'RIVN', 'LCID', 'CCL', 'DAL', 'UAL', 'AAL', 'TSM', 'SONY', 'ET', 'NOK', 'MRO', 'COIN', 'RIVN', 'SIRI', 'SOFI', 'RIOT', 'CPRX', 'PYPL', 'TGT', 'VWO', 'SPYG', 'NOK', 'ROKU', 'HOOD', 'VIAC', 'ATVI', 'BIDU', 'DOCU', 'ZM', 'PINS', 'TLRY', 'WBA', 'VIAC', 'MGM', 'NFLX', 'NIO', 'C', 'GS', 'WFC', 'ADBE', 'PEP', 'UNH', 'CARR', 'FUBO', 'HCA', 'TWTR', 'BILI', 'SIRI', 'VIAC', 'FUBO', 'RKT']

class Command(BaseCommand):
    help = 'Seeds the database with a demo user, predefined companies, and sample alerts.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('--- Starting Database Seeding ---'))

        # 1. Seed Companies
        self.stdout.write('Seeding company data...')
        created_companies = []
        for symbol in DEFAULT_STOCKS:
            company, created = Company.objects.get_or_create(stock_symbol=symbol)
            if created:
                created_companies.append(company)
        self.stdout.write(self.style.SUCCESS(f'Created {len(created_companies)} new companies.'))

        # 2. Create a Demo User
        self.stdout.write('Creating demo user...')
        demo_user, user_created = User.objects.get_or_create(
            username='demouser',
            defaults={'email': 'demouser@example.com'}
        )
        if user_created:
            demo_user.set_password('demopassword123')
            demo_user.save()
            self.stdout.write(self.style.SUCCESS(
                "Created demo user 'demouser' with password 'demopassword123'."
            ))
        else:
            self.stdout.write(self.style.WARNING("Demo user 'demouser' already exists."))

        # 3. Create Sample Alerts for the Demo User
        self.stdout.write('Creating sample alerts for demo user...')
        if user_created:
            aapl = Company.objects.get(stock_symbol='AAPL')
            tsla = Company.objects.get(stock_symbol='TSLA')

            # Sample Threshold Alert
            Alert.objects.create(
                user=demo_user,
                company=aapl,
                alert_type=Alert.AlertType.PRICE_THRESHOLD,
                condition=Alert.TriggerCondition.GREATER_THAN,
                threshold=200.0
            )

            # Sample Duration Alert
            Alert.objects.create(
                user=demo_user,
                company=tsla,
                alert_type=Alert.AlertType.PRICE_DURATION,
                condition=Alert.TriggerCondition.LESS_THAN,
                threshold=600.0,
                duration_minutes=120 # 2 hours
            )
            self.stdout.write(self.style.SUCCESS('Created 2 sample alerts for demouser.'))
        else:
             self.stdout.write(self.style.WARNING('Skipping alert creation as demo user already existed.'))

        self.stdout.write(self.style.SUCCESS('--- Database Seeding Complete! ---'))
