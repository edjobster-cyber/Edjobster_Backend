from django.core.management.base import BaseCommand
from settings.models import Plan, BillingCycle, PlanPricing

class Command(BaseCommand):
    help = 'Setup initial plans, billing cycles, and pricing'

    def handle(self, *args, **options):
        self.stdout.write("Setting up plans and pricing...")
        
        # Create or update billing cycles
        monthly, _ = BillingCycle.objects.get_or_create(
            name='Monthly',
            defaults={'duration_in_months': 1}
        )
        
        half_yearly, _ = BillingCycle.objects.get_or_create(
            name='Half-Yearly',
            defaults={'duration_in_months': 6}
        )
        
        yearly, _ = BillingCycle.objects.get_or_create(
            name='Annually',
            defaults={'duration_in_months': 12}
        )
        
        # Create or update plans
        plans_data = [
            {
                'name': '14 Day FREE Trial',
                'description': '14 days free trial with basic features',
                'pricing': {
                    'Monthly': None,
                    'Half-Yearly': None,
                    'Annually': None
                }
            },
            {
                'name': 'Starter',
                'description': 'Starter plan with essential features',
                'pricing': {
                    'Monthly': 3999,
                    'Half-Yearly': 21999,
                    'Annually': 39999
                }
            },
            {
                'name': 'Growth',
                'description': 'Growth plan with advanced features',
                'pricing': {
                    'Monthly': 6999,
                    'Half-Yearly': 39999,
                    'Annually': 69999
                }
            },
            {
                'name': 'Pro',
                'description': 'Professional plan with all features',
                'pricing': {
                    'Monthly': 9999,
                    'Half-Yearly': 54999,
                    'Annually': 99999
                }
            }
        ]
        
        for plan_data in plans_data:
            plan, created = Plan.objects.update_or_create(
                name=plan_data['name'],
                defaults={'description': plan_data['description']}
            )
            
            action = 'Created' if created else 'Updated'
            self.stdout.write(f"{action} plan: {plan.name}")
            
            # Set up pricing for each billing cycle
            for cycle_name, price in plan_data['pricing'].items():
                if price is not None:
                    cycle = BillingCycle.objects.get(name=cycle_name)
                    plan_price, created = PlanPricing.objects.update_or_create(
                        plan=plan,
                        billing_cycle=cycle,
                        defaults={'price': price}
                    )
                    self.stdout.write(f"  - Set {cycle.name} price: ₹{price}")
        
        self.stdout.write(self.style.SUCCESS('Successfully set up plans and pricing!'))
