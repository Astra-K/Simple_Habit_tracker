import click
import sqlite3
import random
from datetime import datetime, timedelta
from enum import Enum
from habit_tracker import db, Habit, Periodicity, InvalidParameterError, Analyse, init_predefined_habits

@click.group()
def interface():
    pass

@interface.command()
@click.option('--name', prompt='Name of the habit', help='The name of the habit.')
@click.option('--description', prompt='Description of the habit', help='A brief description of the habit.')
@click.option('--priority', prompt='Select Priority of the habit from (1-10)', type=click.IntRange(1,10), help='Priority of the habit with 10 highest and 1 lowest priority')
@click.option('--periodicity', prompt='Periodicity of the habit (DAILY/WEEKLY)', type=click.Choice(['DAILY', 'WEEKLY']), help='The periodicity of the habit.')
def create(name, description, priority, periodicity):
    try:
        habit = Habit(db, name, description, priority, Periodicity[periodicity])
        db.db_insert(habit)
        click.echo(f'You created the habit: {name}')
    except InvalidParameterError as e:
        click.echo(f'Error: {e}')

@interface.command()
@click.option('--name', prompt='Habit you want to delete', help='Select the name of the habit that you want to delete.')
def delete(name):
    try:
        # Check if the habit exists
        habit_exists = db.db_query_by_name(name, "all", "habitdata")
        
        if not habit_exists:
            click.echo(f'Error: No habit found with the name "{name}".')
            return

        # If the habit exists, proceed with deletion
        db.delete_habit(name)
        click.echo(f'Habit "{name}" deleted successfully!')
        
    except InvalidParameterError as e:
        click.echo(f'Error: {e}')

@interface.command()
@click.option('--name', prompt='Name of the Habit you wanna check', help='Enter the name of the habit you want to check')
@click.option('--startdate', prompt='Enter the start year-month-day of your chosen habit\'s streak, put the same day for both enddate and startdate if you only wanna check one day', default=None, required=False, help='Enter a date in the format of year-month-day, don\'t forget "-" in between. Leave empty if you just want to check today')
@click.option('--enddate', prompt='Enter the end year-month-day of your chosen habit\'s streak, put the same day for both enddate and startdate if you only wanna check one day', default=None, required=False, help='Enter a date in the format of year-month-day, don\'t forget "-" in between. Leave empty if you just want to check today')
def check(name, startdate=None, enddate=None):
    habit_data = db.db_query_by_name(name, "all", "habitdata")
    if not habit_data:
        raise InvalidParameterError(f"No habit found with the name '{name}'")
    db.clear_streaks_for_habit(name)
    #makes sure that habit_data is a list not a list of tuples
    habit_data = habit_data[0] 
    habit_name = habit_data[0]
    habit_description = habit_data[1]
    habit_priority = habit_data[2]
    habit_periodicity = Periodicity(habit_data[3])

    habit = Habit(
        db=db,
        name=habit_name,
        description=habit_description,
        priority=habit_priority,
        periodicity=habit_periodicity,
    )
    habit.check(name, startdate, enddate)
    click.echo(f'You checked "{name}" for the time frame of "{startdate}" till "{enddate}".')

@interface.command()
@click.option('--name',prompt='Enter the Name of one of the following habits:"reading","cdcworkout","vegandiet","smokingcessation","meditate".',type=click.Choice(['reading','cdcworkout','vegandiet','smokingcessation','meditate']), help='Enter one of the provided names, you don\'t have to worry about capitalisation.')
def select_predefined(name):
    try:
        init_predefined_habits(db, name)
        click.echo(f'You added "{name}" successfully.')
    except InvalidParameterError as e:
        click.echo(f'Error: {e}')

@interface.command()
@click.option('--type', prompt='select the habit attribute you want to have the greatest value for: priority, current_streak, longest_streak or longest break', type=click.Choice(['priority', 'current_streak', 'longest_streak', 'longest_break']), help='Type in: priority, current_streak, longest_streak or longest break, to get their respective greatest value e.g. which habit/s have/has the longest_streak.')
def max_value(type):
    try:
        analyse= Analyse(db)
        analyse.max_typ(type)
    except InvalidParameterError as e:
        click.echo(f'Error: {e}')

@interface.command()
@click.option('--type', prompt='The type of attribute you want to find matching Habits for', type=click.Choice(['priority', 'periodicity']), help='The type of habit detail to match.')
@click.option('--value', prompt='The value you want to find matching Habits for', help='A matching value like "DAILY" or "WEEKLY" for periodicity or 1-10 for priority.')
def same_value(type, value):
    try:
        analyse=Analyse(db)
        analyse.same(type, value)
    except InvalidParameterError as e:
        click.echo(f'Error: {e}')

@interface.command()
@click.option('--name', prompt='The name of the habit you wanna choose,if you wanna choose all habits in type in \'all\'', help='The name of the habit you want to check values for, or "all" to select all habits.')
@click.option('--type', prompt='The attribute you wanna choose for your habit,if you wanna choose all type in \'all\'', type=click.Choice(['name','priority', 'current_streak', 'longest_streak', 'longest_break','all']), help='The type of habit attribute you want to sort your habit list by or filter out.')
@click.option('--only', prompt='If you want only the greatest or smallest value of the attribute you selected', type=click.Choice(['True', 'False']), help='True if you only want to see the previously selected attribute for a given or all habits.')
@click.option('--order', prompt='If you decided to order the list by an attribute type in either if you wanna order ascending(largest->smallest) or descending(smallest->largest) otherwise type in either one.', type=click.Choice(['ASC', 'DESC']), help='Based on your attribute sorting criteria you can select ASC or DESC to sort your habits e.g. from 10-1 or 1-10 for priority.')
def select_habits(name, type, only, order):
    try:
        analyse=Analyse(db)
        analyse.select(name=name, typ=type, only=only, order=order)
    except InvalidParameterError as e:
        click.echo(f'Error: {e}')

@interface.command()
def clear_database():
    try:
        db.clear_all_tables()
        click.echo('All tables have been cleared from the database.')
    except Exception as e:
        click.echo(f'Error: {e}')

if __name__ == '__main__':
    interface()

