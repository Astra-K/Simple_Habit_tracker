import pytest
from cli import same_value
from habit_tracker import DataBase, Habit, Periodicity, Analyse, InvalidParameterError, init_predefined_habits
from datetime import datetime, timedelta
class TestHabitTracker:

    def setup_method(self):
        """Setup method for creating a new in-memory database before each test."""
        self.db = DataBase(':memory:')  # Initialize an in-memory database
        
        # Initialize predefined habits
        init_predefined_habits(self.db, 'meditate')
        habit = Habit(self.db, 'Test Habit', 'Test Description', 8, Periodicity.DAILY)
        self.db.db_insert(habit)
    def test_create_habit(self):
        """Test for creating a custom habit."""
        habit = Habit(self.db, 'Test Habit', 'Test Description', 8, Periodicity.DAILY)
        self.db.db_insert(habit)
        assert habit.name == 'Test Habit'
        assert habit.description == 'Test Description'
        assert habit.priority == 8
        assert habit.periodicity == Periodicity.DAILY
    
    def test_streaks_predefined(self):
        """Test to verify streaks and breaks for the 'meditate' habit based on predefined data."""
        
        # Expected output (list of tuples: name, start_date, end_date, type, length)
        break_length = (datetime.now() - datetime.strptime('2024-09-01', '%Y-%m-%d')).days
        current_date = datetime.now().strftime('%Y-%m-%d')
        expected_results = [
            ('meditate', '2024-08-13', '2024-08-16', 'break', 3),
            ('meditate', '2024-08-16', '2024-08-17', 'streak', 2),
            ('meditate', '2024-08-18', '2024-08-20', 'break', 2),
            ('meditate', '2024-08-20', '2024-08-22', 'streak', 3),
            ('meditate', '2024-08-23', '2024-08-26', 'break', 3),
            ('meditate', '2024-08-26', '2024-08-28', 'streak', 3),
            ('meditate', '2024-08-29', '2024-08-31', 'break', 2),
            ('meditate', '2024-09-01', current_date, 'break', break_length)
        ]
        streaks = self.db.db_query_by_name('meditate', 'all', 'streakdata')
        
        assert streaks == expected_results, f"Expected streaks and breaks do not match the actual results"

    def test_check_predefined_habit(self):
        """Test for checking a predefined habit 'meditate'."""
        habit_data = self.db.db_query_by_name('meditate', 'all', 'habitdata')
        
        assert habit_data, "Predefined habit 'meditate' not found in the database."

        habit = Habit(self.db, habit_data[0][0], habit_data[0][1], habit_data[0][2], Periodicity(habit_data[0][3]))
        habit.check('meditate')
        
        checks = self.db.db_query_by_name('meditate', 'all', 'checkdata')
        assert len(checks) > 0, "No check entries found for the 'meditate' habit."
    
    def test_longest_streak_all(self):
        """Test for finding the max priority habit."""
        analyse = Analyse(self.db)
        longest_streak= analyse.max_typ('longest_streak')
        assert longest_streak == 'meditate'
    
    def test_longest_streak_specific(self):
        analyse = Analyse(self.db)
        longest_streak_specific = analyse.select(name="meditate", typ='longest_streak', only=True, order=False)
        assert longest_streak_specific == "Here is your list: [('meditate', 3)]"
    
    def test_struggled_most(self):
        analyse = Analyse(self.db)
        longest_break=analyse.max_typ('longest_break')
        assert longest_break == 'meditate'

    def test_same_periodicity(self):
        analyse = Analyse(self.db)
        same_values = analyse.same('periodicity','DAILY')
        assert same_values == 'meditate, Test Habit'
    
    def test_same_priority(self):
        """Test for habits with the same priority."""
        analyse = Analyse(self.db)
        same_values = analyse.same('priority', 8)
        assert same_values == 'meditate, Test Habit'
    
    def test_list_all_habits(self):
        """Test for selecting habits by name."""
        analyse = Analyse(self.db)
        names=analyse.select(name="all", typ="name", only=False, order=True)
        assert names=="Here is your list: ['meditate', 'Test Habit']"
 
    def test_delete_habit(self):
        """Test for deleting a habit and associated data."""
        self.db.delete_habit('meditate')
        result = self.db.cursor.execute("SELECT * FROM habitdata WHERE name = ?", ('meditate',)).fetchone()
        assert result is None, "The habit should be deleted from habitdata."
        result = self.db.cursor.execute("SELECT * FROM streakdata WHERE name = ?", ('meditate',)).fetchone()
        assert result is None, "The streak data should be deleted from streakdata."
    
    def teardown_method(self):
        """Teardown method to clear the database after each test."""
        self.db.clear_all_tables()
