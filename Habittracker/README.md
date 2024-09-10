# Habit Tracker

## Project Description

The Habit Tracker is a command-line application designed to help users create, manage, and analyze their habits. The tracker allows users to set daily or weekly habits, check habits, and view streaks and breaks. The app also provides analytical features such as identifying the longest habit streak, current streaks, and habits with the longest breaks. Data is stored locally using SQLite.

## Installation Instructions

### Prerequisites

Before you begin, ensure you have met the following requirements:
- You have installed Python 3.8 or higher.
- You have access to a terminal or command-line interface to run Python scripts.

### Step-by-Step Installation

1. **Clone the repository**  
   Clone the project repository to your local machine using the following command:
git clone <repository-url>


3. **Install the required dependencies**  
Manually install the required Python modules using `pip`:
pip install click pip install sqlite3 pip install random
These modules are used in the project:
- **Click**: Used for creating the command-line interface (CLI).
- **SQLite3**: Used for managing the habit data storage in a local database.
- **Pytest**
- **random**
- **datetime**
- **enum**

4. **Run the application**  
After installing the dependencies, run the following command to get a list of available commands:
python cli.py or in some cases python3 cli.py

---

Now the project is set up and ready to use. Follow the [Usage Instructions](#usage-instructions) for more details on how to interact with the CLI.

## Usage Instructions

### General CLI Information
- Every command should be run as: `python cli.py <command>`.
- The **database is handled automatically**, so no setup is needed.
- You can see a list of all available commands by simply running:
python cli.py
- Each command includes options that you can choose from, and the system will guide you through input prompts after running the command.
- Generally speaking you can analyse, create and check habits in any way defined by the command tool
- The following will show you list of possible functionalities
* you can use the whole commmands directly, instead going through them step by step for some

---

### 1. Creating a Habit

To create a new habit, use the `create` command.

**Commands**:
python cli.py create
**Steps**:
- You will be prompted to enter:
  **Name**: Choose any name for your habit.
  **Description**: Provide a short description of the habit.
  **Priority**: Choose a priority (1-10) to signify how important the habit is.
  **Periodicity**: Select whether the habit is `DAILY` or `WEEKLY`.

---

### 2. Checking Habits

To mark a habit as completed for a specific day or date range, use the `check` command.

**Command**:
python cli.py check
**Steps**:
- You will be prompted to enter:
  **Name of the habit**: Type the name of the habit you want to check.
  **Start date**: Specify the start date for the timeframe (format: YYYY-MM-DD).
  **End date**: Specify the end date for the timeframe (format: YYYY-MM-DD).

**Notes**:
- You can only check a habit within its **creation date** and today's date.
- When you check a habit, the **streaks** and **breaks** are automatically calculated.

---

### 3. Longest Habit Streak of All Habits and specific

To find the habit with the longest streak, use the `max_value` command with `longest_streak`.

**Command**:
python cli.py max-value --type=longest_streak or python cli.py select-habits --name=all --type=longest_streak --only=True --order=DESC

**Steps**:
- You will be prompted to enter:
 - **habit attribute**: type longest_streak
-Or
 - **Name of the habit you wanna choose or 'all'**:Type the name or all
 - **The attribute you wanna choose for your habit**: type longest_streak
 - **(True, False):**type True
 - **ASC or DESC**: type DESC

---

### 4. Current Daily or Weekly Streak

To get the current streak (either daily or weekly) for a specific habit or all habits, use the `select_habits` command.

**Command**:
python cli.py select_habits --name=all --type=current_streak --only=True --order=DESC

**Steps**:
- You will be prompted to
  - **name**: Specify the habit name or type "all" for all habits.
  - **type**: Set to current_streak to return the current streaks.
  - **only**: Set to True to see only the current streak value.
  - **order**: Use ASC for ascending or DESC for descending order.

---

### 5. Most Struggled Habit (Longest Break)

To find the habit you’ve struggled with the most (i.e., the one with the longest break), use the `max_value` command with `longest_break`.

**Command**:
python cli.py max-value --type=longest_break

**Steps**:
- You will be prompted to provide:
 -**type**: type longest_break

---

### 6. Return a List of All Currently Tracked Habits

To get a list of all habits currently being tracked, use the `select_habits` command.

**Command**:
python cli.py select_habits --name=all --type=name --only=False --order=ASC

**Steps**
- You will be prompted to:
 - **select the habit attribute**: type longest_streak
-Or
 - **Name of the habit you wanna choose or 'all'**:Type the name or all
 - **The attribute you wanna choose for your habit**: type name
 - **(True, False)**: type False
 - **ASC or DESC**: type ASC

---

### 7. Return a List of All Habits with the Same Periodicity

To list all habits with the same periodicity (either `DAILY` or `WEEKLY`), use the `same_value` command.

**Command**:
python cli.py same_value --type=periodicity --value=DAILY

**Steps**:
- You will be prompted to:
  1. **Choose the type**: Type periodicity
  2. **Choose the value**: Type DAILY or WEEKLY to return the matching habits.

---

### 8. Deleting a Habit

To delete a habit, use the `delete` command.

**Command**:
python cli.py delete

**Steps**:
- You will be prompted to enter the name of the habit you want to delete.
 - **Habit you want to delete**: type the name

---

### 9. Adding Predefined Habits

To try out different functionalities with predefined habits, use the `select_predefined` command.

**Commands**:  
python cli.py select_predefined

**Steps**:

- You will be prompted to select from the following predefined habits:
 - reading: "Reading 10 minutes of daily reading"
 - cdcworkout: "CDC recommended workout, 180 minutes of moderate activity per week"
 - vegandiet: "Following a healthy plant-based diet"
 - smokingcessation: "Not having smoked today"
 - meditate: "10 minutes of meditation at any time of the day"
These predefined habits will be added to your habit tracker and allow you to explore checking, streaks, and analysis without entering your own data.

## Pytest
you can simply run pytest using the pytest file test_habit_tracker.py typing in pytest