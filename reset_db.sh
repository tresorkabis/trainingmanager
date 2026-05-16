#!/bin/bash

echo "--- Starting Django Database Reset ---"
echo ""
echo "IMPORTANT: Please ensure your Django development server is STOPPED before running this script."
read -p "Press Enter to continue, or Ctrl+C to abort."

echo ""
echo "1. Deleting old migration files..."
# Adjust these paths if your app names are different or you have more apps
find intern/migrations/ -type f -name '0*.py' -delete
find users/migrations/ -type f -name '0*.py' -delete
find training/migrations/ -type f -name '0*.py' -delete
find progress/migrations/ -type f -name '0*.py' -delete
echo "   Old migration files deleted."
echo ""

echo "2. Deleting database file (db.sqlite3)..."
rm -f db.sqlite3
echo "   Database file deleted."
echo ""

echo "3. Creating new migration files..."
python manage.py makemigrations users
python manage.py makemigrations intern
python manage.py makemigrations training
python manage.py makemigrations progress
python manage.py createprofile
echo "   New migration files created."
echo ""

echo "4. Applying new migrations..."
python manage.py migrate
echo "   New migrations applied."
echo ""

echo "5. Seeding demo data..."
python manage.py seed_demo_data
echo "   Demo data seeded."
echo ""

echo "--- Django Database Reset Complete! ---"
echo "You can now start your Django server: python manage.py runserver"
read -p "Press Enter to exit."