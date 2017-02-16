"""Command-line Worklog program.
Author: Christian Loveridge
Version 1.0 date: 02/07/2017
A simple command-line tool which stores, displays, and saves a CRUD-y
worklog for the user. Each entry can hold a date, a taskname, the number
of minutes spent working on it, and some notes about what was accomplished.

Entries are stored in a CSV file named "tasklog.csv", and can be displayed
through a text menu.

Ideas for future updates:
1) Date list:
    - If the list of worklog dates spans more than a month, add a layer
      to the list which summarizes by month. (And again for the year).
    - For each date entry, display something like
      "MM/DD/YYYY (3 entries, 2:24 worked)"
2) Editing entries:
    - Prefilled command-line text when editing entries. (Entries don't
      have to be retyped from scratch when editing).
        + Save the entry in a .txt file, then open that in Vim or a text
          editor.
"""


from datetime import date, time, timedelta, datetime
import os
import re
import csv
import pytz

from entry import Entry


def cls():
    """Clears the screen using the system, or printing 100 newlines"""
    try:
        os.system("clear")
    finally:
        print("\n" * 100)


def edit_text(text):
    with open("temp.txt","w") as file:
        file.write(text)
    try:
        os.system("open -a TextEdit \"temp.txt\"")
        input("[Press Enter when you've finished and saved the text file.")
        with open("temp.txt", "r") as file:
            new_text = file.read()
        os.system("rm -Rf \"temp.txt\"")
    except:
        print("Advanced text editing isn't available on your device.")
        new_text = input("Please enter the new value:\n> ")

    return new_text


def search_menu(complete_list):
    """The menu which appears to let users choose a search method.

    Allows the user to select a search method, then searches through the
    complete list and passes only matching entries to the display function.
    Any edited or deleted entries are fixed, and returned.

    :param complete_list: The complete list from the "tasklog.csv" file.

    :return: An updated version of the list, which omits deleted entries
            and updates edited entries.
    """

    while True:
        cls()
        print("---------------------")
        print("|Search Option Menu:|")
        print("---------------------")
        print("[D]ate - Search for a specific date or a range of dates")
        print("[R]egex - Search for a specific Regex pattern")
        print("[S]tring - Search for a specific string keyword or phrase")
        print("[T]ime Spent - Search by the amount of time spent")
        print("[B]ack to the main menu")
        print("---------------------")
        try:
            read_input = input("> ")[0].upper()
        except:
            continue

        SEARCH_TYPES = ["D", "R", "S", "T"]
        filtered_list = []
        deleted_ids = []

        if read_input == "B":
            return complete_list
        elif read_input not in SEARCH_TYPES:
            input("[Press Enter] and then please type D, R, S, T or B")
            continue

        # Gets a filtered list, based on date, string, regex, or minutes
        if read_input == "D":
            filtered_list = date_filter(complete_list)
        elif read_input == "R":
            filtered_list = regex_filter(complete_list)
        elif read_input == "S":
            filtered_list = string_filter(complete_list)
        elif read_input == "T":
            filtered_list = minutes_filter(complete_list)

        # Passes the filtered list to the display function
        if len(filtered_list):
            filtered_list, deleted_ids = display_list(filtered_list)
            for item in complete_list:
                # Removes deleted items, and updates edited items
                if item.entry_ID in deleted_ids:
                    complete_list.remove(item)
                    continue
                for inner_item in filtered_list:
                    if item.entry_ID == inner_item.entry_ID:
                        item.entry_date = inner_item.entry_date
                        item.task_name = inner_item.task_name.capitalize()
                        item.mins_spent = inner_item.mins_spent
                        item.notes = inner_item.notes
                        continue
        else:
            print("There is nothing to display.")
            input("[Press Enter]")
        break

    return complete_list


def date_filter(complete_list):
    """Takes a list and filters it based on date.

    Receives a list of Entry objects, then prompts users to either choose a
    valid, specific date from a list, or to provide a range of dates. Then it
    finds all corresponding entries, and returns the filtered list.

    :param complete_list: an unfiltered list of all entries.

    :returns: a list of relevant entries
    """
    filtered_list = []
    date1 = ""
    date2 = ""
    while True:
        cls()
        print("Would you like a [L]ist of dates, or choose a [R]ange?")
        try:
            read_input = input("> ")[0].upper()
        except:
            continue
        if read_input == "L":
            # Display a list of dates to choose from
            chosen_date = ""
            while True:
                # Display a list of dates, and have them pick one
                cls()
                dates_to_display = []
                for item in complete_list:
                    add_date = item.entry_date
                    if add_date not in dates_to_display:
                        dates_to_display.append(add_date)
                print("Available Dates:")
                for display_date in dates_to_display:
                    print(display_date)
                print("[C]ancel")
                print("============")


                print("Which date? (Exactly as it appears above)")
                chosen_date = input("> ")
                try:
                    if chosen_date[0].upper() == "C":
                        break
                    elif chosen_date in dates_to_display:
                        break
                    else:
                        input("[Press Enter] then please type a date above")
                        continue
                except:
                    input("[Press Enter] then please type a date above")
                    continue
            for item in complete_list:
                if item.entry_date == chosen_date:
                    filtered_list.append(item)
            break
        elif read_input == "R":
            # Get 2 dates to search between
            date1, date2 = get_date_range()
            for item in complete_list:
                entry_date = item.get_readable_date()
                temp_date = date(
                    int(entry_date[6:10]),
                    int(entry_date[0:2]),
                    int(entry_date[3:5])
                )
                if date1 <= temp_date <= date2:
                    filtered_list.append(item)
            break
        else:
            input("[Press Enter] and then please type L or R")
    return filtered_list


def regex_filter(complete_list):
    """Takes a list and filters it based on a regex pattern.

    Receives a list of Entry objects, then prompts users to provide a
    regex pattern. Then it finds all corresponding entries, and returns
    the filtered list.

    :param complete_list: an unfiltered list of all entries.

    :returns: a list of relevant entries
    """
    filtered_list = []
    while True:
        cls()
        print("Please enter the Regex pattern to search for, without quotes:")
        print("Example usage: input of ""\d{3}-\d{4}"" would return ")
        print("a result like 555-5555. Use \w for letters and \s for spaces.")
        print("[C]ancel")
        read_input = input("> ")
        if read_input.upper() == "C":
            break
        regex = re.compile(read_input, re.IGNORECASE)
        for item in complete_list:
            try:
                if regex.search(item.task_name) is not None \
                        or regex.search(item.notes) is not None:
                    filtered_list.append(item)
            except:
                input("Improper Regex format. [Press Enter]")
        break

    return filtered_list


def string_filter(complete_list):
    """Takes a list and filters it based on a string.

    Receives a list of Entry objects, then prompts users to provide a
    search string. Then it finds all corresponding entries, and returns
    the filtered list.

    :param complete_list: an unfiltered list of all entries.

    :returns: a list of relevant entries
    """
    filtered_list = []
    while True:
        cls()
        print("Please type an exact phrase to find (Case-insensitive)")
        print("To go back, type \"CANCEL\" in all-caps")
        read_input = input("> ")
        if read_input == "CANCEL":
            break
        elif not read_input:
            continue
        else:
            read_input = re.compile(read_input, re.IGNORECASE)
            for item in complete_list:
                if read_input.search(item.task_name) is not None \
                        or read_input.search(item.notes) is not None:
                    filtered_list.append(item)
            break
    return filtered_list


def get_date_range():
    """Prompts the user to provide a range of two formatted dates.

    :return date1, date2: Two dates which can be searched between.
    """
    date1 = date(1900, 1, 1)
    date2 = date(1900, 1, 1)
    while True:
        cls()
        print("Using MM/DD/YYYY format, please enter the start date:")
        raw_date = input("> ")
        if re.match(r"\d{2}/\d{2}/\d{4}", raw_date) is not None:
            try:
                date1 = date(int(raw_date[6:10]),
                             int(raw_date[0:2]),
                             int(raw_date[3:5]))
                break
            except:
                input("[Press Enter] That was not a valid format. Use MM/DD/YYYY")
                continue
        else:
            input("[Press Enter] That was not a valid format. Use MM/DD/YYYY")
            continue
    while True:
        cls()
        print("Using MM/DD/YYYY format, please enter the ending date:")
        raw_date = input("> ")
        if re.match(r"\d{2}/\d{2}/\d{4}", raw_date) is not None:
            date2 = date(int(raw_date[6:10]),
                         int(raw_date[0:2]),
                         int(raw_date[3:5]))
            if date2 >= date1:
                break
            else:
                input("[Press Enter] This date must"
                      " be later than {}/{}/{}".format(
                    date1.month, date1.day, date1.year))
                continue
        else:
            input("[Press Enter] That was not a valid format. Use MM/DD/YYYY")
            continue
    return date1, date2


def minutes_filter(complete_list):
    """Takes a list and filters it based on minutes worked.

    Receives a list of Entry objects, then prompts users to choose a range
    of numbers. Then it finds all corresponding entries, and returns the
    filtered list.

    :param complete_list: an unfiltered list of all entries.

    :returns: a list of relevant entries
    """
    filtered_list = []
    first_num = 0
    second_num = 0
    while True:
        cls()
        print("Please enter the lowest (or exact) number of minutes to search.")
        try:
            first_num = int(input("> "))
        except ValueError:
            input("[Press Enter] and try a number greater than zero.")
        except TypeError:
            input("[Press Enter] and try a number greater than zero.")
        else:
            if first_num > 0:
                break
            continue
    while True:
        cls()
        print("Please enter a number higher than {}, or [Press Enter].".format(
            first_num
        ))
        try:
            second_num = input("> ")
            if not second_num:
                second_num = int(first_num)
            elif int(second_num) >= first_num:
                second_num = int(second_num)
            else:
                continue
            break
        except ValueError:
            input("[Press Enter] and try a number greater than zero.")
        except TypeError:
            input("[Press Enter] and try a number greater than zero.")
        finally:
            break

    for item in complete_list:
        if int(item.mins_spent) >= first_num and int(item.mins_spent) <= second_num:
            filtered_list.append(item)
    return filtered_list


def new_entry(count):
    """Prompts for a new entry to the existing list of Entry objects.

    :return: the new Entry to be appended to the list.
    """
    new_date = str(date.today())
    new_date = "{}/{}/{}".format(new_date[5:7], new_date[8:10], new_date[2:4])

    task_name = ""
    mins = use_time_marker()

    while not task_name:
        cls()
        task_name = input("Please enter the task name (Required).\n> ")
    while mins < 1:
        cls()
        try:
            mins = int(input("Please enter minutes spent (Required)\n> "))
        except:
            input("[Press Enter] and enter a number greater than 0.")
    cls()
    td = timedelta(minutes=-mins)
    time2 = datetime.now()
    time1 = time2 + td
    print_time = time1.strftime("(%I:%M%p - ") + time2.strftime("%I:%M%p)")
    notes = print_time
    add_notes = input("Add notes (Optional):\n> ")
    while not add_notes:
        read_input = input("Leave blank? y/n\n> ")[0].upper()
        if not read_input:
            continue
        if read_input == "Y":
            break
        else:
            cls()
            add_notes = input("Add notes (Optional):\n> ")

    notes = notes + " " + add_notes
    add_entry = Entry(count, new_date, task_name, mins, notes)

    return add_entry


def new_time_marker():
    overwrite = True
    if os.path.exists("time_marker.txt"):
        with open("time_marker.txt","r") as file:
            marker = file.read()
        if input("There is already a marker at {}. "
                 "Would you like to replace it? Y/N\n> ".format(
                 marker
                 ))[0].upper() == "N":
            overwrite = False

    if overwrite:
        print_time = datetime.now().strftime("%I:%M%p")
        with open("time_marker.txt", "w") as file:
            file.write(print_time)
        input("[Press Enter] Time saved as "
              + print_time
              + " for later use when creating an entry.")


def use_time_marker():

    try:
        mins = timedelta()
        with open("time_marker.txt", "r") as file:
            marker = datetime.strptime(file.read(), "%I:%M%p")
            mins = datetime.now() - datetime(year=datetime.now().year,
                                             month=datetime.now().month,
                                             day=datetime.now().day,
                                             hour=marker.hour,
                                             minute=marker.minute,
                                             second=0
                                             )
        read_input = ""
        while not read_input:
            cls()
            read_input = input("There is a marker at {}. Would you like to use "
                               "this as your start time? Y/N\n> ".format(
                                marker.strftime("%I:%M%p")
                                ))[0].upper()
            if read_input == "Y":
                try:
                    os.system("rm -Rf time_marker.txt")
                except:
                    pass
                return int(mins.seconds/60)
            elif read_input == "N":
                return 0
            else:
                input("[Press Enter] Then please type Y or N.")

    except:
        return 0


def load_csv():
    """Loads the CSV file and returns a list of Entry objects.

    :return: A list of Entry objects.
    """
    complete_list = []
    count = 0

    if os.path.exists("tasklog.csv"):
        with open("tasklog.csv") as csvfile:
            rows = list(csv.DictReader(csvfile))
            for row in rows:
                count += 1
                add_entry = Entry(
                    count,
                    row["entry_date"],
                    str(row["task_name"]),
                    row["mins_spent"],
                    row["notes"]
                )

                complete_list.append(add_entry)

    return complete_list


def save_csv(updated_list):
    """Saves the CSV file."""
    with open("tasklog.csv", "w") as csvfile:
        fieldnames = ["entry_date", "task_name", "mins_spent", "notes"]
        csvwriter = csv.DictWriter(csvfile, fieldnames=fieldnames)

        csvwriter.writeheader()
        for item in updated_list:
            csvwriter.writerow({
                "entry_date": item.entry_date,
                "task_name": item.task_name,
                "mins_spent": item.mins_spent,
                "notes": item.notes
            })

def backup_csv(updated_list):
    """Saves the CSV file."""
    with open("backup.csv", "w") as csvfile:
        fieldnames = ["entry_date", "task_name", "mins_spent", "notes"]
        csvwriter = csv.DictWriter(csvfile, fieldnames=fieldnames)

        csvwriter.writeheader()
        for item in updated_list:
            csvwriter.writerow({
                "entry_date": item.entry_date,
                "task_name": item.task_name,
                "mins_spent": item.mins_spent,
                "notes": item.notes
            })
    cls()
    input("[Press Enter] Backup created!")

def load_backup():
    complete_list = []
    count = 0
    if os.path.exists("backup.csv"):
        with open("backup.csv") as csvfile:
            rows = list(csv.DictReader(csvfile))
            for row in rows:
                count += 1
                add_entry = Entry(
                    count,
                    row["entry_date"],
                    str(row["task_name"]),
                    int(row["mins_spent"]),
                    row["notes"]
                )

                complete_list.append(add_entry)
        if len(complete_list):
            save_csv(complete_list)
    else:
        input("[Press Enter] There is no backup file yet.")

def display_list(entries):
    """Prints out any list of entries.

    The menu which appears upon displaying search results.

    Keyword Arguments:
    entries -- a list of entries which can be edited, deleted, or iterated.
    This list of entries should be filtered beforehand. For example, if
    searching by "task_name", this would be a list of only valid entries.

    :returns: the edited list of entries, and a list of any deleted entries.
    """
    count = 0
    deleted_ids = []
    while True:
        if not len(entries):
            input("This list is now empty. [Press Enter]")
            break
        cls()
        print("==============================")
        print("Task No.:    {}/{}".format(count + 1, len(entries)))
        print("Task Name:   {}".format(entries[count].task_name))
        print("Timestamp:   {}".format(entries[count].get_readable_date()))
        print("Time (Mins): {}".format(entries[count].mins_spent))
        print("Task Notes:  {}".format(entries[count].notes))
        print("==============================")

        menu_options = "[P]revious | [N]ext | [E]dit | [D]elete | [B]ack"
        print(menu_options)
        try:
            choice = input("> ").upper()
        except:
            continue
        if choice == "B":
            break
        elif choice == "N":
            if count < len(entries) - 1:
                count += 1
            else:
                count = 0
        elif choice == "P":
            if count > 0:
                count -= 1
            else:
                count = len(entries) - 1
        elif choice == "D":
            try:
                if input("Are you sure? (y/n)\n> ")[0].lower() == "y":
                    deleted_ids.append(entries[count].entry_ID)
                    del (entries[count])
                    count -= 1
                    if count < 0:
                        count = 0
            except:
                continue
        elif choice == "E":
            while True:
                cls()
                print("\nWhich field would you like to edit?")
                print("[D]ate ({})".format(entries[count].get_readable_date()))
                print("[T]ask Name ({})".format(entries[count].task_name))
                print("[M]inutes Spent ({})".format(entries[count].mins_spent))
                print("[N]otes ({})".format(entries[count].notes))
                print("[F]inished")
                try:
                    read_input = input("> ")[0].upper()
                except:
                    continue
                if read_input == "T":
                    while True:
                        new_task_name = input("New name: (Cannot be blank)\n> ")
                        if new_task_name != "":
                            entries[count].task_name = new_task_name
                            break
                elif read_input == "M":
                    while True:
                        try:
                            new_mins = int(input("New mins: (Must be > 0)\n> "))
                        except:
                            continue
                        if new_mins > 0:
                            entries[count].mins_spent = new_mins
                            break
                elif read_input == "N":
                    while True:
                        try:
                            new_notes = edit_text(entries[count].notes)
                            if new_notes != "":
                                entries[count].notes = new_notes
                                break
                            elif input("It's blank? y/n\n> ")[0].upper() == "Y":
                                entries[count].notes = ""
                                break
                        except:
                            continue
                elif read_input == "D":
                    while True:
                        new_date = input("New date (MM/DD/YYYY)\n> ")
                        if re.match(r'\d{2}/\d{2}/\d{4}', new_date) is not None:
                            entries[count].entry_date = "{}/{}/{}".format(
                                str(new_date[0:2]),
                                str(new_date[3:5]),
                                str(new_date[8:10]))
                            break
                        else:
                            input("[Press Enter] format date in MM/DD/YYYY")
                elif read_input == "F":
                    break
                else:
                    input("[Press Enter] and then please type T, M, N, or C")
        else:
            input("[Press Enter] and then please type P, N, D, E, or B")
    return entries, deleted_ids


if __name__ == "__main__":

    while True:
        cls()
        marker = ""
        if os.path.exists("time_marker.txt"):
            with open("time_marker.txt", "r") as file:
                marker = "\n   -Currently set to: " + file.read()

        print("--------------------------------")
        print("|  Project Tracklog Main Menu  |")
        print("--------------------------------")
        print("[N]ew entry")
        print("[M]arker (Logs the current time){}".format(
            marker
        ))
        print("[B]rowse entries")
        print("[S]earch entries")
        print("[C]reate backup")
        print("[L]oad backup")
        print("[Q]uit the program")
        print("--------------------------------")
        try:
            read_input = input("> ")[0].upper()
        except:
            continue
        if read_input == "N":
            save_list = load_csv()
            count = len(save_list) + 1
            save_list.append(new_entry(count))
            save_csv(save_list)
        elif read_input == "M":
            new_time_marker()
        elif read_input == "B":
            save_list = load_csv()
            if len(save_list):
                save_list, ignore_list = display_list(save_list)
                save_csv(save_list)
            else:
                input("There are no entries to display. [Press Enter]")
        elif read_input == "S":
            save_list = load_csv()
            if len(save_list):
                save_list = search_menu(save_list)
            else:
                input("There are no entries to display. [Press Enter]")
        elif read_input == "C":
            save_list = load_csv()
            if len(save_list):
                backup_csv(save_list)
            else:
                input("[Press Enter] Cannot save a blank tasklog.")
        elif read_input == "L":
            load_backup()
        elif read_input == "Q":
            cls()
            print("Exiting program.")
            exit()
        else:
            input("[Press Enter] and then please type N, M, B, S, C, L, or Q")
