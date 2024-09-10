import click
import sqlite3
import random
from datetime import datetime, timedelta
from enum import Enum

class InvalidParameterError(Exception):
    """Exception in case we are missing parameters or there is a wrong parameter in the habit instantiation"""

class Periodicity(Enum):
    """Enum for periodicity"""
    DAILY = 0
    WEEKLY = 1

def adjust_week(date):
    """Normalises week inputs"""
    adjusted_date = date - timedelta(days=date.weekday())
    return adjusted_date

class Habit:
    """The Class to create habits and check off habits, it takes the arguments name, description, priority and periodicity."""
    def __init__(self, db, name: str = None, description: str = None, priority: int = None, periodicity: Periodicity = None) -> None:
        if not name or not description or not priority or not periodicity:
            raise InvalidParameterError("You are missing one or more parameters in your habit. Please check!")

        self.name = name
        self.description = description
        self.priority = self.validate_priority(priority)
        self.periodicity = periodicity
        self.current_streak = None
        self.longest_streak = 0
        self.longest_break = 0
        self.creation_time = datetime.now()
        self.db = db

    def validate_priority(self, priority):
        """validates that the priority is set between 1 and 10"""
        if 1 <= priority <= 10:
            return priority
        raise InvalidParameterError("Your Habit needs a priority between 1 and 10!")

    def check(self, name, startdate=None, enddate=None):
        """Checks of a habit given its name for the current day, 
        unless you specify a start and end date as a year-month-day for a time period that you want to check."""
        #validates if a habit with the name exists
        exists = self.db.db_query_by_name(name, "COUNT(1)", "habitdata")[0]
        #makes sure that exists is not a tuple for comparison
        exists= exists[0]
        #converting to correct time format
        if startdate and enddate:
            start_date = datetime.strptime(startdate, '%Y-%m-%d')
            end_date = datetime.strptime(enddate, '%Y-%m-%d')
        #this one there in case we directly use check, the CLI requires two inputs
        else:
            start_date = end_date = datetime.now()

        if exists > 0:
            periodicity = self.db.db_query_by_name(name, "periodicity", "habitdata")[0]
            creation_time_tuple = self.db.db_query_by_name(name, "creation_time", "habitdata")
            # This one comes up a couple times throughout the code, and makes sure that lists of tuples are correcly handled so singular values can be obtained
            if isinstance(creation_time_tuple[0], tuple):
                creation_time_str = creation_time_tuple[0][0] 
            else:
                creation_time_str = creation_time_tuple[0]

            creation_time = datetime.strptime(creation_time_str.split(' ')[0], '%Y-%m-%d')
            # here (0,) is used because the queried periodicity return either that or (1,) for DAILY or WEEKLY habits
            # these are to validate that the habit is within the creation date and todays date
            if periodicity == (0,):
                end_validate = datetime.now() >= end_date
                start_validate = start_date >= creation_time
            #for weeks you'll find this structure appear more often
            else:
                end_validate = adjust_week(datetime.now()) >= adjust_week(end_date)
                start_validate = adjust_week(start_date) >= adjust_week(creation_time)
            #code for creating checks
            if start_validate and end_validate:
                check_list = []
                if periodicity == (0,):
                    for x in range((end_date - start_date).days + 1):
                        datemodify = (start_date + timedelta(days=x)).strftime('%Y-%m-%d')
                        check_list.append((name, datemodify, 1))
                else:
                    for x in range((adjust_week(end_date) - adjust_week(start_date)).days // 7 + 1):
                        datemodify = (start_date + timedelta(weeks=x)).strftime('%Y-%m-%d')
                        check_list.append((name, datemodify, 1))
                self.db.db_insert_check(check_list)
                streaks = Streaks(self.db, name)
                current_streak_value = streaks.current_streak()
                longest_streak_value, longest_break_value = streaks.longest_streak()
                self.db.update_streaks(name, current_streak_value, longest_streak_value, longest_break_value)
            else:
                raise InvalidParameterError("The time frame you selected is not within the habit creation and today's date")
        else:
            raise InvalidParameterError("The habit you selected is not in the database")

class DataBase:
    """DataBase class"""
    def __init__(self, db_path='habit_database.db') -> None:
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()
        self.create_table()
    #the tables with the fitting data types and Key dependencies(design diagram in powerpoint), to make sure deletion are carried out correctly(or for future functionalities like changing the name of a habit)
    def create_table(self):
        """creates tables if they don't exist yet for the database"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS habitdata (
                name VARCHAR UNIQUE,
                description TEXT,
                priority INTEGER,
                periodicity INTEGER,
                current_streak INTEGER,
                longest_streak INTEGER,
                longest_break INTEGER,
                creation_time TIMESTAMP
            ) """
        )
        #combined UNIQUE statment as every habit can only be checked for each day once, but for several names
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkdata (
                name VARCHAR,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                datemodify DATE,
                checks INTEGER,
                UNIQUE(name, datemodify)
                FOREIGN KEY(name) REFERENCES habitdata(name) ON UPDATE CASCADE ON DELETE CASCADE
            )"""
        )
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS streakdata (
                name VARCHAR,
                start_date DATE,
                end_date DATE,
                streak_type VARCHAR,
                count INTEGER,
                FOREIGN KEY(name) REFERENCES habitdata(name) ON UPDATE CASCADE ON DELETE CASCADE
            )"""
        )
        self.connection.commit()

    def clear_all_tables(self):
        """Drops all tables in the database to clear all data."""
        self.cursor.execute("DROP TABLE IF EXISTS habitdata")
        self.cursor.execute("DROP TABLE IF EXISTS checkdata")
        self.cursor.execute("DROP TABLE IF EXISTS streakdata")
        self.connection.commit()

    def db_insert(self, habit: Habit) -> None:
        """Inserts specifically Habit class habit data into the database."""
        habit_data = (
            habit.name,
            habit.description,
            habit.priority,
            habit.periodicity.value,
            habit.current_streak,
            habit.longest_streak,
            habit.longest_break, 
            habit.creation_time
        )
        self.cursor.execute(
            "INSERT OR IGNORE INTO habitdata VALUES (?, ?, ?, ?, ?, ?, ?, ?)", habit_data
        )
        self.connection.commit()

    def db_insert_check(self, check_list) -> None:
        """Inserts check data into the database."""
        self.cursor.executemany(
            "INSERT INTO checkdata (name, datemodify, checks) VALUES (?, ?, ?)", check_list
        )
        self.connection.commit()

    def db_insert_streak(self, streak_list) -> None:
        """Inserts streak data into the database."""
        self.cursor.executemany("INSERT OR IGNORE INTO streakdata VALUES (?, ?, ?, ?, ?)", streak_list)
        self.connection.commit()
    
    def clear_streaks_for_habit(self, habit_name):
        """If a habit is checked to prevent duplicates this function deletes the streaddata associated with the habit"""
        self.cursor.execute("DELETE FROM streakdata WHERE name = ?", (habit_name,))
        self.connection.commit()

    # the structure is to control output columns for analysis purpose
    def db_query_by_name(self, name, typ, tb):
        """Selects data from any table with or without specified column of the database."""
        if name == "all":
            if typ == "all":
                self.cursor.execute(f"SELECT * FROM {tb}")
                return self.cursor.fetchall()
            elif typ:
                self.cursor.execute(f"SELECT {typ} FROM {tb}")
                return self.cursor.fetchall()
            else:
                raise InvalidParameterError("This column or database doesn't exist")
        elif name:
            if typ == "all":
                self.cursor.execute(f"SELECT * FROM {tb} WHERE name = ?", (name,))
                return self.cursor.fetchall()
            elif typ:
                self.cursor.execute(f"SELECT {typ} FROM {tb} WHERE name = ?", (name,))
                return self.cursor.fetchall()
            else:
                raise InvalidParameterError("This column or database doesn't exist")
        else:
            raise InvalidParameterError("You entered a habit that does not exist")
    
    def update_streaks(self, name, current_streak, longest_streak, longest_break):
        """Updates the streak values for a given habit."""
        self.cursor.execute("""
            UPDATE habitdata
            SET current_streak = ?, longest_streak = ?, longest_break = ?
            WHERE name = ?
            """, (current_streak, longest_streak, longest_break, name)
        )
        self.connection.commit()
    #updated, but kept code safetywise, Reference structure should handle deletions properly
    def delete_habit(self, name):
        """Deletes a specified habit from the database using the name"""
        self.cursor.execute(f"DELETE FROM habitdata WHERE name = ?", (name,))
        self.cursor.execute(f"DELETE FROM checkdata WHERE name = ?", (name,))
        self.cursor.execute(f"DELETE FROM streakdata WHERE name = ?", (name,))
        self.connection.commit()

    def close(self):
        self.connection.close()

db = DataBase()
def init_predefined_habits(db: DataBase, habit_name: str) -> None:
    """Initialises the predefined Habits"""
    predefined_habits = {
        "reading": ("reading", "10 minutes of daily reading", 4, Periodicity.DAILY),
        "cdcworkout": ("CDC workout", "CDC recommended workout 180 minutes of moderate activity per week", 2, Periodicity.WEEKLY),
        "vegandiet": ("vegan diet", "Following a healthy plant-based diet", 4, Periodicity.DAILY),
        "smokingcessation": ("smoking cessation", "Not having smoked today", 8, Periodicity.DAILY),
        "meditate": ("meditate", "10 minutes of meditation at any time of the day", 8, Periodicity.DAILY),
    }
    # pre-generated check data
    habit_check_data = {
    'reading': [
        ('reading', '2024-08-12', 1),
        ('reading', '2024-08-14', 1),
        ('reading', '2024-08-19', 1),
        ('reading', '2024-08-22', 1),
        ('reading', '2024-08-23', 1),
        ('reading', '2024-08-30', 1),
        ('reading', '2024-08-31', 1),
        ('reading', '2024-09-01', 1),
        ('reading', '2024-09-02', 1),
        ('reading', '2024-09-03', 1),
        ('reading', '2024-09-04', 1),
        ('reading', '2024-09-05', 1),
        ('reading', '2024-09-08', 1)
    ],
    'CDC workout': [
        ('CDC workout', '2024-08-12', 1),
        ('CDC workout', '2024-08-14', 1),
        ('CDC workout', '2024-08-15', 1),
        ('CDC workout', '2024-08-17', 1),
        ('CDC workout', '2024-08-20', 1),
        ('CDC workout', '2024-08-23', 1),
        ('CDC workout', '2024-08-27', 1),
        ('CDC workout', '2024-08-28', 1),
        ('CDC workout', '2024-08-30', 1),
        ('CDC workout', '2024-09-01', 1),
        ('CDC workout', '2024-09-02', 1),
        ('CDC workout', '2024-09-03', 1),
        ('CDC workout', '2024-09-05', 1),
        ('CDC workout', '2024-09-06', 1),
        ('CDC workout', '2024-09-08', 1)
    ],
    'vegan diet': [
        ('vegan diet', '2024-08-12', 1),
        ('vegan diet', '2024-08-15', 1),
        ('vegan diet', '2024-08-16', 1),
        ('vegan diet', '2024-08-17', 1),
        ('vegan diet', '2024-08-18', 1),
        ('vegan diet', '2024-08-20', 1),
        ('vegan diet', '2024-08-22', 1),
        ('vegan diet', '2024-08-23', 1),
        ('vegan diet', '2024-08-27', 1),
        ('vegan diet', '2024-08-28', 1),
        ('vegan diet', '2024-08-30', 1),
        ('vegan diet', '2024-09-02', 1),
        ('vegan diet', '2024-09-03', 1),
        ('vegan diet', '2024-09-04', 1),
        ('vegan diet', '2024-09-05', 1)
    ],
    'smoking cessation': [
        ('smoking cessation', '2024-08-12', 1),
        ('smoking cessation', '2024-08-14', 1),
        ('smoking cessation', '2024-08-15', 1),
        ('smoking cessation', '2024-08-16', 1),
        ('smoking cessation', '2024-08-17', 1),
        ('smoking cessation', '2024-08-19', 1),
        ('smoking cessation', '2024-08-23', 1),
        ('smoking cessation', '2024-08-25', 1),
        ('smoking cessation', '2024-08-28', 1),
        ('smoking cessation', '2024-08-29', 1),
        ('smoking cessation', '2024-08-30', 1),
        ('smoking cessation', '2024-09-04', 1),
        ('smoking cessation', '2024-09-06', 1),
        ('smoking cessation', '2024-09-08', 1)
    ],
    'meditate': [
        ('meditate', '2024-08-12', 1),
        ('meditate', '2024-08-16', 1),
        ('meditate', '2024-08-17', 1),
        ('meditate', '2024-08-20', 1),
        ('meditate', '2024-08-21', 1),
        ('meditate', '2024-08-22', 1),
        ('meditate', '2024-08-26', 1),
        ('meditate', '2024-08-27', 1),
        ('meditate', '2024-08-28', 1),
        ('meditate', '2024-08-31', 1)
    ]
    }

    add_habit = predefined_habits.get(habit_name.lower())
    if add_habit:
        habit = Habit(db, add_habit[0], add_habit[1], add_habit[2], add_habit[3])
        
        habit.current_streak = None
        habit.longest_streak = 0
        habit.longest_break = 0
        habit.creation_time = datetime.strptime("2024-08-12", "%Y-%m-%d")
        db.db_insert(habit)

        check_list= habit_check_data.get(habit_name,[])

        if check_list:
            db.db_insert_check(check_list)
        streaks = Streaks(db, habit.name)
        current_streak_value = streaks.current_streak()
        longest_streak_value, longest_break_value = streaks.longest_streak()
        db.update_streaks(habit.name, current_streak_value, longest_streak_value, longest_break_value)
    
    else:
        raise InvalidParameterError(
            f"The habit {habit_name} is not one of the predefined habits: \"reading\", \"cdcworkout\", \"vegandiet\", \"smokingceassation\", \"meditate\"."
        )

class Streaks:
    """Streaks Class"""
    def __init__(self, db, name) -> None:
        self.db = db
        self.name = name
        check_list = self.db.db_query_by_name(name, "datemodify", "checkdata")
        check_list_sorted = sorted(check_list, reverse=False) 
        if all(isinstance(date, str) for date in check_list_sorted):
            check_list_sorted = [(date,) for date in check_list_sorted]
        streak_list = []
        periodicity = self.db.db_query_by_name(name, "periodicity", "habitdata")[0]

        if periodicity == (0,):
            self.calculate_streaks(check_list_sorted, timedelta(days=1), '%Y-%m-%d', streak_list)
        elif periodicity == (1,):
            self.calculate_streaks(check_list_sorted, timedelta(weeks=1), '%Y-%m-%d', streak_list)
        else:
            raise InvalidParameterError(f"Invalid periodicity: {periodicity}")

        
        self.db.db_insert_streak(streak_list)

    def calculate_streaks(self, check_list_sorted, delta, strftime_format, streak_list):
        habit_data = self.db.db_query_by_name(self.name, "creation_time", "habitdata")
        creation_date_tuple = habit_data[0][0] 
        creation_date = datetime.strptime(creation_date_tuple.split(' ')[0], '%Y-%m-%d').date()  # Convert to date
        if len(check_list_sorted) == 1:
            # Handles the case where there is only one date in the list e.g. if you check a newly created habit
            current_date = datetime.strptime(check_list_sorted[0][0], strftime_format)
            streak_list.append((self.name, current_date.strftime('%Y-%m-%d'), current_date.strftime('%Y-%m-%d'), "streak", 1))
            return

        countif = 0
        countelif = 0
        previous_date = None
        streak_type = None 
        start_date = None
        first_checked_date = datetime.strptime(check_list_sorted[0][0], strftime_format).date()
        #handles breaks prior the first checked day as the following structure only computes inbetween the first and last checked day
        if creation_date < first_checked_date:
            break_days = (first_checked_date - creation_date).days
            if break_days > 0:
                streak_list.append((self.name, creation_date.strftime('%Y-%m-%d'), (first_checked_date - timedelta(days=1)).strftime('%Y-%m-%d'), "break", break_days))
        #whole code for handling inbetween checks and streaks, note that I this code does not include singular checks as streaks(assumtion that a streak begins with 2 consecutive checked days)
        for current_date in check_list_sorted:
            current_date = datetime.strptime(current_date[0], strftime_format).date() 
            
            if previous_date:
            
                date_difference = (current_date - previous_date).days
                #if the difference is 1 or 7 we know that we are working with a streak
                if date_difference == delta.days:
                    if streak_type != "streak":
                        if streak_type == "break" and countelif > 0:
                            streak_list.append((self.name, start_date, previous_date, "break", countelif))
                        start_date = previous_date
                        #this is initialiased as 2, assuming that two consecutive checks would be a two day streak
                        countif = 2
                    else:
                        countif += 1
                    
                    streak_type = "streak"
                #when checked dates are longer apart than a day they count as breaks
                elif date_difference > delta.days:
                    if streak_type != "break":
                        if streak_type == "streak" and countif > 0:
                            streak_list.append((self.name, start_date, previous_date, "streak", countif))
                        start_date = previous_date + timedelta(days=1)
                        countelif = date_difference - 1
                    else:
                        countelif += date_difference - 1

                    streak_type = "break"

            previous_date = current_date
        #to handle final appends
        if streak_type == "streak" and countif > 0:
            streak_list.append((self.name, start_date, previous_date, "streak", countif))
        elif streak_type == "break" and countelif > 0:
            streak_list.append((self.name, start_date, previous_date, "break", countelif))
        last_checked_date = previous_date
        #this is for adding breaks after the last checked date and todays date
        current_date = datetime.now().date()
        if last_checked_date < current_date:
            break_days = (current_date - last_checked_date).days - 1  # Days between last check and today
            if break_days > 0:
                streak_list.append((self.name, (last_checked_date + timedelta(days=1)).strftime('%Y-%m-%d'), current_date.strftime('%Y-%m-%d'), "break", break_days))

    def current_streak(self):
        """Returns the current streak for a specified habit"""
        query_object = self.db.db_query_by_name(self.name, "all", "streakdata")

        # we had this before
        if isinstance(query_object, tuple) and not isinstance(query_object[0], tuple):
            query_object = [query_object]

        current_date = datetime.now()
        current_date_string_day = current_date.strftime('%Y-%m-%d')
        current_date_string_week = current_date.strftime('%Y-%m-%d')

        current_streak_value = 0  # Default to 0 if no match is found

        for item in query_object:
            if item[3] == 'streak' and (item[2] == current_date_string_day or item[2] == current_date_string_week):
                current_streak_value = item[4]
                break

        return current_streak_value
   
    def longest_streak(self):
        """Returns the longest streak and break for a specified habit"""
        query_object = self.db.db_query_by_name(self.name, "all", "streakdata")
        if isinstance(query_object, tuple):
            query_object = [query_object]
        filtered_query_streak = [streak_type for streak_type in query_object if streak_type[3] == 'streak']
        filtered_query_break = [streak_type for streak_type in query_object if streak_type[3] == 'break']
        longest_streak = max(filtered_query_streak, key=lambda x: x[4])[4] if filtered_query_streak else 0
        longest_break = max(filtered_query_break, key=lambda x: x[4])[4] if filtered_query_break else 0
        return longest_streak, longest_break
        
class Analyse:
    """Analyse Class"""
    def __init__(self, db):
        self.db = db
   
    def convert_to_index(self, column):
        """Returns the index of the given habitdata column, to use in max and sort functions, as db_query_by_name is in tuple form."""
        columns = ["name", "description", "priority", "periodicity", "current_streak", "longest_streak", "longest_break", "creation_time"]
        if column in columns:
            return columns.index(column)
        else:
            raise ValueError(f"Column name '{column}' is not valid.")

    def keep_column(self, data, column_keep):
        """Keeps only specified columns for a later print operation"""
        filtered_data = []
        for row in data:
            filtered_row = [row[i] for i in column_keep]
        return filtered_row

    def max_typ(self, typ):
        """Fetches the maximum of either priority, current_streak, longest_streak, longest_break"""
        query_object = self.db.db_query_by_name("all", "all", "habitdata")
        index = self.convert_to_index(typ)
        max_value = max(query_object, key=lambda x: x[index])
        max_values = [x for x in query_object if x[index] == max_value[index]]
        habit_names = ", ".join([x[0] for x in max_values])
        sorted_query_object = f"The greatest {typ} belongs to the habit(s): {habit_names}, with a {typ} of {max_value[index]}"
        print(sorted_query_object)
        return habit_names

    def same(self, typ, same):
        """Fetches the Habits containing the same values for: 2. priority(1-10) and 3. periodicity(DAILY, WEEKLY)"""
        query_object = self.db.db_query_by_name("all", "all", "habitdata")
        index = self.convert_to_index(typ)
        
        if typ == "periodicity":
            same = Periodicity[same.upper()].value
        else:
            same = int(same)
        same_value = [row for row in query_object if row[index] == same]
        same_values = ", ".join([x[0] for x in same_value])
        sorted_query_object = f"The habits:{same_values} have the same {typ}: {same}"
        print(sorted_query_object)
        return same_values

    def select(self, name, typ, only, order):
        """Selects a un/sorted list of the Habits or a Habit important parameters(which can be specified)"""
        query_object = self.db.db_query_by_name(name, "all", "habitdata")
        if typ != "all":
            index = self.convert_to_index(typ)
            if index == 0:
                    sorted_query = sorted(query_object, key=lambda x: x[index], reverse=order)
                    sorted_query_object = [(x[0]) for x in sorted_query]
            else:
                if only=='True':
                    sorted_query = sorted(query_object, key=lambda x: x[index], reverse=order)
                    sorted_query_object = self.keep_column(sorted_query, [0, index])
                else:
                    sorted_query = sorted(query_object, key=lambda x: x[index], reverse=order)
                    sorted_query_object = [(x[0], x[index]) for x in sorted_query]
        else:
            sorted_query_object = query_object
        sorted_query_object = f"Here is your list: {sorted_query_object}"
        print(sorted_query_object)
        return sorted_query_object