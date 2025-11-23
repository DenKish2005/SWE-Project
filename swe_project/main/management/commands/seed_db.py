from django.core.management.base import BaseCommand
from main.models import Category, Item, Request
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Seeds the database with farmer\'s market data'

    def handle(self, *args, **kwargs):
        # Clear existing data
        self.stdout.write('Clearing existing data...')
        Request.objects.all().delete()
        Item.objects.all().delete()
        Category.objects.all().delete()

        # Create Categories
        self.stdout.write('Creating categories...')
        categories_data = [
            'Vegetables',
            'Fruits',
            'Dairy',
            'Meat & Poultry',
            'Eggs',
            'Honey & Preserves',
            'Baked Goods',
            'Herbs & Spices',
            'Grains & Seeds',
            'Beverages'
        ]

        categories = {}
        for cat_name in categories_data:
            category = Category.objects.create(name=cat_name)
            categories[cat_name] = category
            self.stdout.write(f'  ✓ Created category: {cat_name}')

        # Create Items
        self.stdout.write('\nCreating items...')

        items_data = [
            # Vegetables
            ('Organic Tomatoes', 'Fresh vine-ripened tomatoes', 3.50, 0.5, 150, 101, 'Vegetables'),
            ('Carrots', 'Crunchy orange carrots', 2.00, 1.0, 200, 101, 'Vegetables'),
            ('Bell Peppers', 'Mixed color bell peppers', 4.00, 0.3, 80, 102, 'Vegetables'),
            ('Cucumbers', 'Fresh garden cucumbers', 2.50, 0.4, 120, 102, 'Vegetables'),
            ('Lettuce', 'Crispy green lettuce heads', 2.75, 0.3, 90, 103, 'Vegetables'),
            ('Zucchini', 'Fresh zucchini', 3.00, 0.5, 100, 103, 'Vegetables'),
            ('Broccoli', 'Organic broccoli crowns', 3.25, 0.4, 70, 101, 'Vegetables'),
            ('Spinach', 'Baby spinach leaves', 4.50, 0.25, 60, 104, 'Vegetables'),

            # Fruits
            ('Strawberries', 'Sweet local strawberries', 5.00, 0.5, 100, 105, 'Fruits'),
            ('Apples', 'Crisp red apples', 3.00, 1.0, 200, 105, 'Fruits'),
            ('Blueberries', 'Fresh blueberries', 6.00, 0.3, 80, 106, 'Fruits'),
            ('Peaches', 'Juicy ripe peaches', 4.50, 0.6, 90, 106, 'Fruits'),
            ('Watermelon', 'Sweet seedless watermelon', 8.00, 5.0, 40, 107, 'Fruits'),
            ('Grapes', 'Seedless green grapes', 5.50, 0.5, 70, 107, 'Fruits'),
            ('Cherries', 'Sweet cherries', 7.00, 0.4, 50, 105, 'Fruits'),

            # Dairy
            ('Fresh Milk', 'Whole milk from grass-fed cows', 4.50, 1.0, 80, 108, 'Dairy'),
            ('Artisan Cheese', 'Handcrafted cheddar cheese', 8.00, 0.5, 50, 108, 'Dairy'),
            ('Greek Yogurt', 'Creamy Greek yogurt', 5.00, 0.5, 60, 109, 'Dairy'),
            ('Butter', 'Organic salted butter', 6.00, 0.5, 70, 108, 'Dairy'),
            ('Cottage Cheese', 'Low-fat cottage cheese', 4.00, 0.4, 45, 109, 'Dairy'),

            # Meat & Poultry
            ('Chicken Breast', 'Free-range chicken breast', 12.00, 1.0, 40, 110, 'Meat & Poultry'),
            ('Ground Beef', 'Grass-fed ground beef', 10.00, 1.0, 50, 110, 'Meat & Poultry'),
            ('Pork Chops', 'Heritage breed pork chops', 11.00, 0.8, 35, 111, 'Meat & Poultry'),
            ('Turkey', 'Whole free-range turkey', 25.00, 5.0, 20, 111, 'Meat & Poultry'),
            ('Bacon', 'Smoked bacon strips', 9.00, 0.5, 60, 110, 'Meat & Poultry'),

            # Eggs
            ('Farm Fresh Eggs', 'Free-range chicken eggs (dozen)', 6.00, 0.7, 100, 112, 'Eggs'),
            ('Duck Eggs', 'Fresh duck eggs (6 pack)', 7.00, 0.5, 40, 112, 'Eggs'),
            ('Quail Eggs', 'Delicate quail eggs (dozen)', 5.00, 0.2, 30, 113, 'Eggs'),

            # Honey & Preserves
            ('Raw Honey', 'Local wildflower honey', 12.00, 0.5, 80, 114, 'Honey & Preserves'),
            ('Strawberry Jam', 'Homemade strawberry jam', 8.00, 0.4, 50, 114, 'Honey & Preserves'),
            ('Apple Butter', 'Spiced apple butter', 7.00, 0.4, 45, 115, 'Honey & Preserves'),
            ('Maple Syrup', 'Pure maple syrup', 15.00, 0.5, 35, 115, 'Honey & Preserves'),

            # Baked Goods
            ('Sourdough Bread', 'Traditional sourdough loaf', 6.00, 0.6, 60, 116, 'Baked Goods'),
            ('Croissants', 'Butter croissants (4 pack)', 8.00, 0.3, 40, 116, 'Baked Goods'),
            ('Blueberry Muffins', 'Fresh blueberry muffins (6 pack)', 10.00, 0.5, 35, 117, 'Baked Goods'),
            ('Whole Wheat Bread', 'Organic whole wheat bread', 5.50, 0.6, 50, 117, 'Baked Goods'),

            # Herbs & Spices
            ('Fresh Basil', 'Organic basil bunch', 3.00, 0.1, 70, 118, 'Herbs & Spices'),
            ('Rosemary', 'Fresh rosemary sprigs', 2.50, 0.05, 60, 118, 'Herbs & Spices'),
            ('Oregano', 'Dried oregano', 4.00, 0.05, 50, 119, 'Herbs & Spices'),
            ('Thyme', 'Fresh thyme bunch', 2.75, 0.05, 55, 118, 'Herbs & Spices'),

            # Grains & Seeds
            ('Quinoa', 'Organic quinoa', 8.00, 1.0, 40, 120, 'Grains & Seeds'),
            ('Brown Rice', 'Long grain brown rice', 5.00, 2.0, 60, 120, 'Grains & Seeds'),
            ('Sunflower Seeds', 'Raw sunflower seeds', 6.00, 0.5, 50, 121, 'Grains & Seeds'),
            ('Pumpkin Seeds', 'Roasted pumpkin seeds', 7.00, 0.5, 45, 121, 'Grains & Seeds'),

            # Beverages
            ('Apple Cider', 'Fresh pressed apple cider', 7.00, 1.0, 50, 122, 'Beverages'),
            ('Herbal Tea', 'Handpicked herbal tea blend', 10.00, 0.1, 40, 123, 'Beverages'),
            ('Lemonade', 'Fresh squeezed lemonade', 5.00, 1.0, 35, 122, 'Beverages'),
        ]

        items = []
        for name, desc, price, weight, qty, supplier, cat_name in items_data:
            item = Item.objects.create(
                name=name,
                description=desc,
                price=price,
                weight=weight,
                quantity=qty,
                supplierID=supplier,
                category=categories[cat_name]
            )
            items.append(item)
            self.stdout.write(f'  ✓ Created item: {name}')

        # Create some sample requests
        self.stdout.write('\nCreating sample requests...')

        consumer_ids = [201, 202, 203, 204, 205]
        statuses = [Request.Status.PENDING, Request.Status.APPROVED, Request.Status.REJECTED]
        comments = [
            'Please deliver by morning',
            'Need fresh produce for weekend market',
            'Regular weekly order',
            'Special event catering',
            'First time order, please confirm availability',
            'Requesting bulk discount',
            ''
        ]

        for i in range(15):
            days_ago = random.randint(0, 30)
            request_date = date.today() - timedelta(days=days_ago)

            Request.objects.create(
                consumerID=random.choice(consumer_ids),
                supplierID=random.randint(101, 123),
                status=random.choice(statuses),
                consumerComment=random.choice(comments)
            )

        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created:'))
        self.stdout.write(self.style.SUCCESS(f'   - {len(categories_data)} categories'))
        self.stdout.write(self.style.SUCCESS(f'   - {len(items_data)} items'))
        self.stdout.write(self.style.SUCCESS(f'   - 15 sample requests'))